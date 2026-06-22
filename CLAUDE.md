# autoReviews

SwiftプロジェクトのPR自動レビューシステム。PRが作成・更新されると、GitHub ActionsがClaudeを呼び出してレビューを行い、PRコメントとして投稿する。

## セットアップ

1. GitHubリポジトリの **Settings > Secrets and Variables > Actions** で以下を登録:
   - `ANTHROPIC_API_KEY`: Anthropic APIキー

2. `GITHUB_TOKEN` はGitHub Actionsが自動で提供するため設定不要。

## ファイル構成

```
.github/workflows/pr-review.yml   # ワークフロー定義
scripts/review_pr.py              # レビュースクリプト
prompts/swift_coding_rules.md     # Swiftルール + Claudeへの指示
```

## レビュー内容

- **一般的なコード品質**: ロジックエラー、パフォーマンス、セキュリティ
- **Swiftコーディングルール**: 命名、Optional処理、アクセス制御、型推論、クロージャ、エラーハンドリング、Swift Concurrency

## カスタマイズ

- `prompts/swift_coding_rules.md` を編集してルールを追加・変更
- `scripts/review_pr.py` の `MODEL` 変数でモデルを切り替え（デフォルト: `claude-opus-4-8`）
- `MAX_DIFF_CHARS` でdiffの最大サイズを調整（デフォルト: 30,000文字）
