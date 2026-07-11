#!/usr/bin/env python3
import os
import sys
import requests
import anthropic

DIFF_PATH = "/tmp/pr_diff.patch"
RULES_DIR = os.path.join(os.path.dirname(__file__), "..", ".claude", "rules")
MAX_DIFF_CHARS = 30_000
MODEL = "claude-opus-4-8"

REVIEW_INTRO = """\
You are an expert Swift iOS developer performing a thorough code review. \
Review the PR diff provided by the user, checking for both general code quality issues \
AND compliance with the Swift coding rules below.

## General Code Quality Checklist
- Logic errors and correctness issues
- Performance problems (unnecessary computation, retain cycles, blocking main thread)
- Security vulnerabilities (unsafe data handling, missing input validation)
- Missing error propagation or silent failures
- Unnecessary code duplication

## Swift Coding Rules
"""

REVIEW_FORMAT = f"""
## Output Format

Structure your review exactly as follows (omit any section that has no findings):

## 🤖 Claude Code Review

### 📋 Summary
(1–2 sentence overall assessment of the PR quality and key themes)

### 🔴 Critical（必須修正）
- `FileName.swift`: description of issue and how to fix it

### 🟡 Major（強く推奨）
- `FileName.swift`: description of issue and recommendation

### 🔵 Minor / Style（Swiftルール違反含む）
- `FileName.swift`: rule violated and correction

### ✅ Good Points
- What was done well in this PR

---
*Reviewed by Claude {MODEL} · autoReviews PR Review Bot*
"""


def _read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fp:
        return fp.read()


def _strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines[1:], start=1):
        if line.rstrip("\n") == "---":
            return "".join(lines[i + 1:]).lstrip("\n")
    return text


def load_system_prompt() -> str:
    if not os.path.isdir(RULES_DIR):
        raise FileNotFoundError(f"Rules directory not found: {RULES_DIR}")
    rules_files = sorted(f for f in os.listdir(RULES_DIR) if f.endswith(".md"))
    if not rules_files:
        raise RuntimeError(f"No .md rule files found in {RULES_DIR}")
    rules_body = "\n\n".join(
        _strip_frontmatter(_read_file(os.path.join(RULES_DIR, f)))
        for f in rules_files
    )
    return REVIEW_INTRO + rules_body + REVIEW_FORMAT


def load_diff() -> str:
    with open(DIFF_PATH, "r") as f:
        diff = f.read()
    if not diff.strip():
        return ""
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n\n[... diff truncated due to size ...]"
    return diff


def build_user_message(diff: str) -> str:
    pr_title = os.environ.get("PR_TITLE", "(no title)")
    pr_body = os.environ.get("PR_BODY", "") or "(no description)"
    return f"""## PR Title
{pr_title}

## PR Description
{pr_body}

## Diff
```diff
{diff}
```
"""


def call_claude(system_prompt: str, user_message: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def post_pr_review(review_body: str) -> None:
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["REPO"]
    pr_number = os.environ["PR_NUMBER"]

    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {"body": review_body, "event": "COMMENT"}

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    print(f"Review posted: {response.json().get('html_url', 'unknown URL')}")


def main() -> None:
    diff = load_diff()
    if not diff:
        print("Empty diff — skipping review.")
        sys.exit(0)

    system_prompt = load_system_prompt()
    user_message = build_user_message(diff)

    print("Calling Claude for review...")
    review = call_claude(system_prompt, user_message)

    print("Posting review to PR...")
    post_pr_review(review)


if __name__ == "__main__":
    main()
