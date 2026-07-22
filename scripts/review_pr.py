#!/usr/bin/env python3
import json
import os
import re
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

REVIEW_FORMAT = """
## Output Format

Return a single raw JSON object — no markdown fences, no prose outside the JSON.

{
  "summary": "1–2 sentence overall assessment of the PR",
  "comments": [
    {
      "path": "relative/path/to/File.swift",
      "line": <integer: line number in the NEW file (RIGHT side of diff)>,
      "severity": "critical" | "major" | "minor" | "good",
      "body": "Markdown comment text explaining the issue or praise"
    }
  ]
}

Rules for comments:
- Only reference lines that appear in the diff (added `+` lines or context lines on the RIGHT side)
- Use the exact file path from the diff header (the part after `+++ b/`)
- Omit the `b/` prefix from the path (e.g. `Sources/Foo.swift`, not `b/Sources/Foo.swift`)
- severity "good" is for positive observations worth calling out
- If a finding has no specific line to attach to, pick the nearest relevant line
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
    with open(DIFF_PATH, "r", encoding="utf-8") as f:
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


def call_claude(system_prompt: str, user_message: str) -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    text = response.content[0].text.strip()
    # Strip accidental markdown fences
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return json.loads(text)


SEVERITY_PREFIX = {
    "critical": "🔴 **Critical**",
    "major": "🟡 **Major**",
    "minor": "🔵 **Minor**",
    "good": "✅ **Good**",
}


def _build_inline_comments(comments: list) -> list:
    result = []
    for c in comments:
        if not c.get("path") or not c.get("line"):
            continue
        prefix = SEVERITY_PREFIX.get(c.get("severity", ""), "")
        body = f"{prefix}\n\n{c['body']}" if prefix else c["body"]
        result.append({"path": c["path"], "line": c["line"], "side": "RIGHT", "body": body})
    return result


def _build_fallback_body(review_data: dict) -> str:
    summary = review_data.get("summary", "")
    comments = review_data.get("comments", [])

    sections: dict[str, list] = {"critical": [], "major": [], "minor": [], "good": []}
    for c in comments:
        sev = c.get("severity", "minor")
        path = c.get("path", "")
        line = c.get("line", "")
        location = f"`{path}:{line}`" if path and line else f"`{path}`" if path else ""
        entry = f"- {location}: {c['body']}" if location else f"- {c['body']}"
        sections.get(sev, sections["minor"]).append(entry)

    parts = [f"## 🤖 Claude Code Review\n\n### 📋 Summary\n{summary}"]
    if sections["critical"]:
        parts.append("### 🔴 Critical（必須修正）\n" + "\n".join(sections["critical"]))
    if sections["major"]:
        parts.append("### 🟡 Major（強く推奨）\n" + "\n".join(sections["major"]))
    if sections["minor"]:
        parts.append("### 🔵 Minor / Style\n" + "\n".join(sections["minor"]))
    if sections["good"]:
        parts.append("### ✅ Good Points\n" + "\n".join(sections["good"]))
    parts.append(f"---\n*Reviewed by Claude {MODEL} · autoReviews PR Review Bot*")
    return "\n\n".join(parts)


def post_pr_review(review_data: dict) -> None:
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["REPO"]
    pr_number = os.environ["PR_NUMBER"]

    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    summary = review_data.get("summary", "")
    overall_body = (
        f"## 🤖 Claude Code Review\n\n### 📋 Summary\n{summary}\n\n"
        f"---\n*Reviewed by Claude {MODEL} · autoReviews PR Review Bot*"
    )
    inline_comments = _build_inline_comments(review_data.get("comments", []))

    payload = {"body": overall_body, "event": "COMMENT", "comments": inline_comments}
    response = requests.post(url, json=payload, headers=headers)

    if not response.ok:
        print(f"Inline review failed ({response.status_code}: {response.text}), falling back to single comment")
        fallback_payload = {"body": _build_fallback_body(review_data), "event": "COMMENT"}
        fallback = requests.post(url, json=fallback_payload, headers=headers)
        fallback.raise_for_status()
        print(f"Review posted (fallback): {fallback.json().get('html_url', 'unknown URL')}")
        return

    print(f"Review posted: {response.json().get('html_url', 'unknown URL')}")


def main() -> None:
    diff = load_diff()
    if not diff:
        print("Empty diff — skipping review.")
        sys.exit(0)

    system_prompt = load_system_prompt()
    user_message = build_user_message(diff)

    print("Calling Claude for review...")
    review_data = call_claude(system_prompt, user_message)

    print("Posting review to PR...")
    post_pr_review(review_data)


if __name__ == "__main__":
    main()
