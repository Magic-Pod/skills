# チケット内容のカスタマイズ

チケットの件名・本文・追記内容と、トラッカーやカスタムフィールドなどの項目は、
**テンプレートフォルダ** のファイルで決まる。プログラムを変更せずに書き換えられる。

## 1. テンプレートフォルダを用意する

```bash
python3 scripts/redmine_sync.py init            # ./.magicpod-redmine/ に既定のテンプレートをコピー
python3 scripts/redmine_sync.py init --dir ~/.config/magicpod-redmine   # 全プロジェクト共通にする場合
```

既存のファイルは上書きしない（上書きするなら `--force`）。

### 探す順番

1. `--template-dir` オプション
2. 環境変数 `MAGICPOD_REDMINE_TEMPLATE_DIR`
3. 実行したフォルダの `./.magicpod-redmine/`
4. `~/.config/magicpod-redmine/`
5. スキル同梱の `assets/templates/`（既定）

ファイル単位で探すので、変えたいファイルだけを置けばよい（例: `description.md` だけ置けば、件名は既定のまま）。
スキル本体は書き換えないので、スキルを新しい版に更新してもカスタマイズは消えない。

## 2. ファイル一覧

| ファイル | 用途 |
|---|---|
| `subject.txt` | 件名（1行）。先頭には重複判定用の `[MagicPod:プロジェクト#番号]` が自動で付く |
| `description.md` / `description.textile` | 新規チケットの本文（`REDMINE_TEXT_FORMAT` に合わせてどちらかを使う） |
| `note.md` / `note.textile` | 既存チケットに追記する注記 |
| `config.json` | トラッカー・優先度・担当者・カテゴリ・カスタムフィールド、複数パターン失敗時の扱い（`pattern_mode`） |

## 3. テンプレートの書き方

- `{{名前}}` … 値に置き換わる
- `{{#名前}} ... {{/名前}}` … 値があるときだけ中身を出す（値が空なら見出しごと消える）

```markdown
### 概要
* テストケース: {{test_case_link}}
{{#branch}}
* ブランチ: {{branch}}
{{/branch}}
```

### 使える値

| 名前 | 内容 |
|---|---|
| `test_case_name` / `test_case_number` | テストケース名 / 番号 |
| `test_case_link` / `test_case_url` | テストケースへのリンク（書式に合わせて生成） / URL |
| `test_run_link` / `test_run_url` / `test_run_number` | テスト実行へのリンク / URL / 番号 |
| `batch_run_link` / `batch_run_url` / `batch_run_number` | 一括実行へのリンク / URL / 番号 |
| `status` | `failed` など |
| `test_setting_name` | テスト設定名 |
| `pattern` | 実行パターン（ブラウザ・端末など） |
| `condition_labels` | 実行条件（カンマ区切り） |
| `data_pattern_number` | データ駆動の失敗パターン番号 |
| `data_pattern_values` | そのデータパターンの値（`変数名 = 値` を1行ずつ） |
| `branch` | ブランチ |
| `started_at` | 実行日時 |
| `failed_step` | 失敗したステップ |
| `failure_ui` | 失敗したUI要素 |
| `error_message` | エラーメッセージ |
| `failure_analysis` | MagicPod の AI 失敗分析（ユーザーが MagicPod 上で実行した場合のみ値が入る。無ければ見出しごと消える） |
| `test_steps` | テストケースの全手順（再現手順に使える） |
| `notes` | テスト実行のメモ |
| `organization` / `project` | MagicPod の組織名 / プロジェクト名 |
| `summary_total` / `summary_succeeded` / `summary_failed` | 一括実行全体の件数 |
| `key` | 重複判定キー（件名の先頭に付くもの） |
| `run_id` | テスト実行のID（`{project}/tc{番号}/run{実行番号}`） |

本文（description）と注記（note）の末尾には、`MagicPod run ID: {{run_id}}` という行が自動で付く。
同じテスト実行の結果を二重に書き込まないための目印なので、テンプレートから消しても自動で付け直される。

このほか、`failures.json` に入っている項目はすべて同じ名前で使える。
新しい名前（例: `{{device_log}}`）を使った場合、`preview` / `sync` の出力の
`unknown_placeholders` にその名前が表示される。Claude はそれを見て MagicPod から値を取得し、`failures.json` に追加する。

## 4. config.json

```json
{
  "tracker_id": 1,
  "priority_id": 2,
  "assigned_to_id": 5,
  "category_id": null,
  "custom_fields": [
    {"id": 3, "value": "結合テスト"},
    {"id": 7, "value": "{{test_setting_name}}"},
    {"id": 9, "value": ["Chrome", "Edge"]}
  ],
  "pattern_mode": "merge",
  "data_pattern_mode": "split"
}
```

- `pattern_mode` は、1回の一括実行で同じテストケースが複数の実行パターン（ブラウザ・端末など）で失敗したときの扱い。
  - `merge`: チケットは1件にまとめ、2つ目以降のパターンは注記で追記する
  - `split`: 実行パターンごとに別のチケットにする（件名のキーが `[MagicPod:project#17@日本語Chrome]` のようになる）
  - `null`（未設定）: merge として動き、該当する失敗があると出力に `pattern_mode_undecided: true` が出る
  - `python3 scripts/redmine_sync.py set-pattern-mode merge|split` で保存できる。その回だけ変えるなら `preview` / `sync` に `--pattern-mode` を付ける。
  - 途中で変えると重複判定のキーが変わるため、変更前に作った未完了チケットには追記されず、新しいチケットになる。
    そのような古いチケットは、`sync` の結果に `other_open_tickets` として表示される。
- `data_pattern_mode` は、データ駆動テストが複数のデータパターンで失敗したときの扱い。
  - `merge`: テストケースごとにチケットは1件にまとめ、他のデータパターンは注記で追記する
  - `split`: データパターンごとに別のチケットにする（件名のキーが `[MagicPod:project#17-P2]` のようになる）
  - `null`（未設定）: split として動き（従来どおり）、該当する失敗があると出力に `data_pattern_mode_undecided: true` が出る
  - `set-data-pattern-mode merge|split` で保存、`--data-pattern-mode` でその回だけ上書きできる。

- ID は `python3 scripts/redmine_sync.py meta` で調べられる（カスタムフィールドの一覧は管理者の APIキーが必要）。
- カスタムフィールドの `value` にも `{{名前}}` が使える。複数選択のフィールドは配列で書く。
- `REDMINE_TRACKER_ID` などの環境変数が設定されている場合は、そちらが優先される。
- Redmine 側で必須のカスタムフィールドがあると、ここで値を入れないと起票時に `HTTP 422` になる。

## 5. 確認

```bash
python3 scripts/redmine_sync.py preview --input failures.json
```

Redmine に接続せずに、件名・本文・追記内容・項目を表示する。テンプレートを変えたら、まずこれで確認する。
