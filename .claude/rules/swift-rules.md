---
paths: "**/*.swift"
---
# Swift Coding Rules

## 1. 命名規則 (Swift API Design Guidelines)
- 型・プロトコルは `UpperCamelCase`、それ以外は `lowerCamelCase`
- メソッドは使う側で文章として読めるように: `list.insert(item, at: index)` ✅ / `list.insert(item, position: index)` ❌
- Bool プロパティは断定的なプレフィックスを使う: `isEnabled`, `hasChanges`, `shouldReload`
- 能力を表すプロトコルは `-able`/`-ible` 接尾辞 (`Equatable`, `Codable`)、型を表すなら名詞 (`DataSource`)
- 副作用のあるメソッドは命令形 (`sort()`)、ないものは名詞/過去分詞 (`sorted()`)

## 2. ファイル/コード構成
- `extension` で関心ごとに分割し、`// MARK: -` で区切る
- プロトコル準拠は型本体と分けて `extension` に書く

```swift
final class ProfileViewController: UIViewController {
    // MARK: - Properties
    // MARK: - Lifecycle
}

// MARK: - UITableViewDataSource
extension ProfileViewController: UITableViewDataSource { ... }
```

## 3. Optional の扱い
- 強制アンラップ (`!`) は禁止（`@IBOutlet` とユニットテストのみ例外）
- `guard let` で早期 return、`if let` でローカルスコープ、`??` でデフォルト値
- Swift 5.7+ の短縮シャドーイングを使う: `guard let user else { return }` ✅

## 4. アクセス制御とクラス修飾
- デフォルトで最も狭いアクセスレベルにする（必要になったら緩める）
- 継承予定のないクラスは `final` を付ける
- プロパティは `private` または `private(set)` を基本にする

## 5. 型推論
- ローカル変数は型推論に任せ、冗長な型注釈を避ける
- 空配列・空辞書は型を明示する: `let names: [String] = []` ✅
- 公開APIのプロパティ・戻り値の型は明示する（可読性とコンパイル速度のため）

## 6. self の省略とクロージャの循環参照
- メソッド内では `self.` を省略する（コンパイラが要求する場面のみ付ける）
- エスケープクロージャでは `[weak self]` で循環参照を防ぐ
- クロージャ内で `guard let self else { return }` を使う
- `unowned` は self の寿命がクロージャより確実に長い場合のみ、迷ったら `weak`

## 7. エラーハンドリング
- `try?` でエラーを握りつぶさない（最低限ログを残す）
- 意味のあるエラー型を `Error` に準拠させて定義・伝播させる
- `Result<T, Error>` より `async/await + throws` を新規コードでは使う

## 8. 並行処理 (Swift Concurrency)
- 新規コードは `async/await` + `Actor` を基本にする（コールバックや RxSwift は既存コードのみ）
- UI 更新スレッドは `@MainActor` で型レベルに保証する（`DispatchQueue.main` は使わない）
- 長い処理では `Task.checkCancellation()` でキャンセルに対応する
- `Task { @MainActor in ... }` を回避策として使わず、関数自体に正しい Actor を付ける
