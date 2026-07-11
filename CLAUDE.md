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
.claude/rules/swift-rules.md      # Swiftコーディングルール
```

## レビュー内容

- **一般的なコード品質**: ロジックエラー、パフォーマンス、セキュリティ
- **Swiftコーディングルール**: `.claude/rules/` 配下の各ファイルで定義

## カスタマイズ

- ルールの追加・変更: `.claude/rules/swift-rules.md` を編集するだけで自動的にレビューに反映される
- モデルの変更: `scripts/review_pr.py` の `MODEL` 変数を編集
- diffサイズ上限の変更: `scripts/review_pr.py` の `MAX_DIFF_CHARS` を編集
