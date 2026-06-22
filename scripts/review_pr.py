#!/usr/bin/env python3
import os
import sys
import requests
import anthropic

DIFF_PATH = "/tmp/pr_diff.patch"
RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "swift_coding_rules.md")
MAX_DIFF_CHARS = 30_000
MODEL = "claude-opus-4-8"


def load_system_prompt() -> str:
    with open(RULES_PATH, "r") as f:
        return f.read()


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
