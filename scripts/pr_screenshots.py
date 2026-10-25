#!/usr/bin/env python3
"""PRのBefore/Afterスクリーンショットを撮影し、PR本文を更新する。

1. ベースブランチ(Before)とHEAD(After)でXCUITestを実行し、XCTAttachmentのPNGを取り出す
2. 画像を専用ブランチ (pr-screenshots) の pr-<番号>/before|after/ にpushする
3. PR本文のスクリーンショットセクションをBefore/Afterの表に置き換える

Usage: python3 scripts/pr_screenshots.py <PR番号> [--base main]
設定: .claude/pr-screenshots.json (例: .claude/pr-screenshots.example.json)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

CONFIG_PATH = os.path.join(".claude", "pr-screenshots.json")
SCREENSHOTS_BRANCH = "pr-screenshots"
DEFAULT_DESTINATION = "platform=iOS Simulator,name=iPhone 16"
IMAGE_WIDTH = 300
SECTION_START = "<!-- screenshots:start -->"
SECTION_END = "<!-- screenshots:end -->"

# xcresulttool の suggestedHumanReadableName は "<name>_<index>_<UUID>.png" 形式
ATTACHMENT_NAME_PATTERN = re.compile(r"^(?P<name>.+)_\d+_[0-9A-Fa-f-]{36}(?P<ext>\.\w+)$")


def _run(cmd: list[str], cwd: str | None = None, check: bool = True) -> str:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        sys.exit(f"Command failed: {' '.join(cmd)}\n{result.stderr or result.stdout}")
    return result.stdout.strip()


def _load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        sys.exit(f"{CONFIG_PATH} が見つかりません。.claude/pr-screenshots.example.json を参考に作成してください。")
    with open(CONFIG_PATH, "r", encoding="utf-8") as fp:
        config = json.load(fp)
    for key in ("scheme", "test_identifier"):
        if not config.get(key):
            sys.exit(f"{CONFIG_PATH} に '{key}' がありません。")
    return config


def _xcodebuild_container_args(config: dict) -> list[str]:
    if config.get("workspace"):
        return ["-workspace", config["workspace"]]
    if config.get("project"):
        return ["-project", config["project"]]
    return []


def _capture(config: dict, source_dir: str, work_dir: str, output_dir: str) -> None:
    """source_dir でスクリーンショットテストを実行し、PNGを output_dir に書き出す。"""
    result_bundle = os.path.join(work_dir, "result.xcresult")
    cmd = [
        "xcodebuild", "test",
        *_xcodebuild_container_args(config),
        "-scheme", config["scheme"],
        "-destination", config.get("destination", DEFAULT_DESTINATION),
        "-derivedDataPath", os.path.join(work_dir, "DerivedData"),
        "-resultBundlePath", result_bundle,
        "-only-testing:" + config["test_identifier"],
    ]
    print(f"Running screenshot tests in {source_dir} ...", file=sys.stderr)
    # 新規画面などで一部のテストが失敗しても、撮れた分のスクリーンショットは使う
    _run(cmd, cwd=source_dir, check=False)
    if not os.path.exists(result_bundle):
        print(f"Warning: result bundle not created in {source_dir}", file=sys.stderr)
        return

    export_dir = os.path.join(work_dir, "attachments")
    _run(["xcrun", "xcresulttool", "export", "attachments",
          "--path", result_bundle, "--output-path", export_dir])
    with open(os.path.join(export_dir, "manifest.json"), "r", encoding="utf-8") as fp:
        manifest = json.load(fp)

    os.makedirs(output_dir, exist_ok=True)
    for test in manifest:
        for attachment in test["attachments"]:
            name = attachment["suggestedHumanReadableName"]
            if not name.lower().endswith(".png"):
                continue
            match = ATTACHMENT_NAME_PATTERN.match(name)
            if match:
                name = match.group("name") + match.group("ext")
            shutil.copy(os.path.join(export_dir, attachment["exportedFileName"]),
                        os.path.join(output_dir, name))


def _prepare_base_worktree(config: dict, base: str, worktree_dir: str) -> None:
    head_sha = _run(["git", "rev-parse", "HEAD"])
    _run(["git", "fetch", "origin", base])
    _run(["git", "worktree", "add", "--detach", worktree_dir, f"origin/{base}"])
    # スクリーンショットテストがこのPRで追加・変更された場合に備え、テストコードはHEADのものを使う
    for path in config.get("test_paths", []):
        _run(["git", "checkout", head_sha, "--", path], cwd=worktree_dir)


def _upload(pr_number: int, before_dir: str, after_dir: str, work_dir: str) -> str:
    """画像を専用ブランチにpushし、そのコミットSHAを返す。"""
    worktree_dir = os.path.join(work_dir, "screenshots-branch")
    branch_exists = _run(["git", "ls-remote", "--heads", "origin", SCREENSHOTS_BRANCH]) != ""
    if branch_exists:
        _run(["git", "fetch", "origin", SCREENSHOTS_BRANCH])
        _run(["git", "worktree", "add", "--detach", worktree_dir, f"origin/{SCREENSHOTS_BRANCH}"])
    else:
        _run(["git", "worktree", "add", "--detach", worktree_dir])
        _run(["git", "checkout", "--orphan", SCREENSHOTS_BRANCH], cwd=worktree_dir)
        _run(["git", "rm", "-rf", "--quiet", "."], cwd=worktree_dir)

    pr_dir = os.path.join(worktree_dir, f"pr-{pr_number}")
    shutil.rmtree(pr_dir, ignore_errors=True)
    for label, src in (("before", before_dir), ("after", after_dir)):
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(pr_dir, label))

    _run(["git", "add", "-A", "."], cwd=worktree_dir)
    if _run(["git", "status", "--porcelain"], cwd=worktree_dir):
        _run(["git", "commit", "-m", f"Update screenshots for PR #{pr_number}"], cwd=worktree_dir)
        _run(["git", "push", "origin", f"HEAD:refs/heads/{SCREENSHOTS_BRANCH}"], cwd=worktree_dir)
    return _run(["git", "rev-parse", "HEAD"], cwd=worktree_dir)


def _build_table(repo: str, sha: str, pr_number: int, before_dir: str, after_dir: str) -> str:
    def list_png(path: str) -> set[str]:
        return {f for f in os.listdir(path) if f.lower().endswith(".png")} if os.path.isdir(path) else set()

    def image(label: str, name: str) -> str:
        url = f"https://github.com/{repo}/blob/{sha}/pr-{pr_number}/{label}/{name}?raw=true"
        return f'<img src="{url}" width="{IMAGE_WIDTH}">'

    before, after = list_png(before_dir), list_png(after_dir)
    rows = []
    for name in sorted(before | after):
        before_cell = image("before", name) if name in before else "なし（新規）"
        after_cell = image("after", name) if name in after else "削除"
        rows.append(f"| {os.path.splitext(name)[0]} | {before_cell} | {after_cell} |")
    if not rows:
        return "スクリーンショットを取得できませんでした"
    return "\n".join(["| 画面 | Before | After |", "|------|--------|-------|", *rows])


def _update_pr_body(pr_number: int, table: str) -> None:
    body = _run(["gh", "pr", "view", str(pr_number), "--json", "body", "-q", ".body"])
    section = f"{SECTION_START}\n{table}\n{SECTION_END}"
    pattern = re.compile(re.escape(SECTION_START) + r".*?" + re.escape(SECTION_END), re.DOTALL)
    if pattern.search(body):
        body = pattern.sub(lambda _: section, body)
    else:
        body = f"{body}\n\n## スクリーンショット (Before / After)\n{section}\n"
    subprocess.run(["gh", "pr", "edit", str(pr_number), "--body-file", "-"],
                   input=body, text=True, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pr_number", type=int)
    parser.add_argument("--base", default="main")
    args = parser.parse_args()

    os.chdir(_run(["git", "rev-parse", "--show-toplevel"]))
    config = _load_config()
    repo = _run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])

    work_dir = tempfile.mkdtemp(prefix="pr-screenshots-")
    base_worktree = os.path.join(work_dir, "base")
    before_dir = os.path.join(work_dir, "before")
    after_dir = os.path.join(work_dir, "after")
    try:
        _prepare_base_worktree(config, args.base, base_worktree)
        _capture(config, base_worktree, os.path.join(work_dir, "build-before"), before_dir)
        _capture(config, os.getcwd(), os.path.join(work_dir, "build-after"), after_dir)
        sha = _upload(args.pr_number, before_dir, after_dir, work_dir)
        table = _build_table(repo, sha, args.pr_number, before_dir, after_dir)
        _update_pr_body(args.pr_number, table)
        print(table)
    finally:
        for name in ("base", "screenshots-branch"):
            path = os.path.join(work_dir, name)
            if os.path.exists(path):
                _run(["git", "worktree", "remove", "--force", path], check=False)
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
