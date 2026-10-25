現在のブランチの変更内容からPRを作成してください。

## 手順

1. `git status` と `git diff main...HEAD`、`git log main..HEAD --oneline` を実行して変更内容を把握する
2. リモートにプッシュされていなければ `git push -u origin HEAD` でプッシュする
3. 変更内容を分析し、以下のフォーマットでPRを作成する（`gh pr view` で既存PRがあれば `gh pr edit` で本文を更新する）
4. UI変更があるか判定し、ある場合はスクリーンショットを更新する（後述）

## PRフォーマット

```
gh pr create --title "<簡潔なタイトル>" --body "$(cat <<'EOF'
## 変更内容
<!-- 変更の概要を箇条書きで記載 -->
-

## 動作確認
<!-- 確認すべき項目をチェックリストで記載 -->
- [ ]

## 影響範囲
<!-- この変更が影響する範囲を記載 -->
-

## スクリーンショット (Before / After)
<!-- screenshots:start -->
UI変更なし
<!-- screenshots:end -->

## 備考
<!-- レビュアーへの補足事項など -->
-
EOF
)"
```

## スクリーンショットの更新

以下のいずれかが diff に含まれる場合は「UI変更あり」とみなす:

- SwiftUI の `View` / UIKit の `UIView`・`UIViewController` の実装変更
- `.storyboard` / `.xib` / `Assets.xcassets` / `Localizable.strings`・`.xcstrings` の変更
- 色・フォント・レイアウト定数など見た目に関わる定義の変更

UI変更ありの場合:

1. `.claude/pr-screenshots.json` が存在するか確認する。なければスクリーンショット欄に「UI変更あり（スクリーンショット未設定）」と記載し、`.claude/pr-screenshots.example.json` を参考に設定するようユーザーに伝えて終了する
2. 変更された画面がスクリーンショットテスト（設定の `test_identifier`）でカバーされているか確認する。カバーされていなければユーザーにその旨を伝える
3. PR番号を指定してスクリプトを実行する（ビルドとテストを2回行うため時間がかかる）:
   ```
   python3 scripts/pr_screenshots.py <PR番号> --base main
   ```
4. スクリプトが `<!-- screenshots:start -->` 〜 `<!-- screenshots:end -->` の間をBefore/Afterの表で置き換える。失敗した場合はエラー内容をユーザーに報告する

## 注意事項

- タイトルは70文字以内にする
- 変更内容はコミット履歴とdiffから正確に記載する
- 動作確認のチェックリストは変更内容に応じた具体的な項目にする
- 影響範囲は変更がシステムのどの部分に影響するか明記する
- スクリーンショット欄の `<!-- screenshots:start -->` / `<!-- screenshots:end -->` マーカーは削除しない（自動更新に使用する）
- 備考にはレビュー時に注意してほしいポイントを記載する
