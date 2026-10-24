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
.claude/commands/create-pr.md     # PR作成コマンド
scripts/pr_screenshots.py         # PRのBefore/Afterスクショ更新スクリプト
.claude/pr-screenshots.example.json  # スクショ撮影設定のサンプル
```

## Before/After スクリーンショット

`/create-pr` 実行時にUI変更があれば、`scripts/pr_screenshots.py` がスクリーンショットを自動更新する。

1. ベースブランチ(Before)とHEAD(After)でXCUITestを実行し、`XCTAttachment` のPNGを取り出す
2. 画像を `pr-screenshots` ブランチの `pr-<番号>/before|after/` にpushする
3. PR本文の `<!-- screenshots:start -->` 〜 `<!-- screenshots:end -->` をBefore/Afterの表で置き換える

### 準備

- `.claude/pr-screenshots.example.json` をコピーして `.claude/pr-screenshots.json` を作成
  - `test_identifier`: 撮影用UIテスト（`-only-testing` に渡す値）
  - `test_paths`: 撮影用UIテストのファイル。ベースブランチでもHEADのテストコードを使って撮影する
- 撮影用UIテストでは、画面ごとに名前付きのスクリーンショットを添付する（名前がBefore/Afterの対応付けに使われる）

```swift
final class ScreenshotTests: XCTestCase {
    func testHome() {
        let app = XCUIApplication()
        app.launch()
        attachScreenshot(named: "Home")
    }

    private func attachScreenshot(named name: String) {
        let attachment = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)
    }
}
```

- 必要なもの: Xcode 16以降（`xcresulttool export attachments`）、`gh` CLI

## レビュー内容

- **一般的なコード品質**: ロジックエラー、パフォーマンス、セキュリティ
- **Swiftコーディングルール**: `.claude/rules/` 配下の各ファイルで定義

## カスタマイズ

- ルールの追加・変更: `.claude/rules/swift-rules.md` を編集するだけで自動的にレビューに反映される
- モデルの変更: `scripts/review_pr.py` の `MODEL` 変数を編集
- diffサイズ上限の変更: `scripts/review_pr.py` の `MAX_DIFF_CHARS` を編集
