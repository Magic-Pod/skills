# failures.json の形式

`redmine_sync.py sync --input` に渡すJSON。MagicPod MCPの取得結果から組み立てる。

## トップレベル

| キー | 必須 | 内容 | 取得元 |
|---|---|---|---|
| `organization` | | MagicPod組織名 | ユーザー指定 / URL |
| `project` | ✔ | MagicPodプロジェクト名（重複判定キーに使う） | ユーザー指定 / URL |
| `batch_run_number` | ✔ | 一括実行番号 | `list_batch_runs` |
| `batch_run_url` | | 一括実行のURL | 組み立て |
| `test_setting_name` | | テスト設定名 | `list_batch_runs.test_setting_name`（URLで番号が分かっていても `cursor` と `count: 1` で呼んで取る） |
| `condition_labels` | | 実行条件（例: `["Chrome 155", "Cloud"]`） | `list_batch_runs.test_condition_labels[].text` |
| `branch` | | ブランチ名 | `list_batch_runs.branch_name` |
| `started_at` / `ended_at` | | 一括実行の開始/終了日時 | `list_batch_runs` |
| `summary` | | 件数集計（例: `{"total": 20, "succeeded": 18, "failed": 2}`）。**テスト実行単位**で数える（データ駆動でデータパターンが複数失敗しても1） | `list_batch_run_test_runs` を集計 |
| `failures` | ✔ | 失敗の配列（下記） | |

## failures[] の各要素

| キー | 必須 | 内容 | 取得元 |
|---|---|---|---|
| `test_case_number` | ✔ | テストケース番号 | `list_batch_run_test_runs` |
| `test_case_name` | | テストケース名 | 同上 |
| `test_run_number` | | テスト実行番号（`test_case_run_number`） | 同上 |
| `status` | | `failed` / `aborted` など | 同上 `status_name` |
| `pattern` | | 実行パターン（例: `日本語Chrome \| Browser: Chrome 157 \| Environment: Cloud`） | 同上のグループ見出し（`Pattern N:` を除く） |
| `pattern_name` | | 実行パターンの名前（例: `日本語Chrome`）。`pattern_mode` が split のとき重複判定キーに使う（無ければ `pattern`） | グループ見出しの先頭の名前 |
| `data_pattern_number` | | データ駆動の失敗パターン番号（1始まり）。失敗したデータパターンごとに1要素にする | `data_pattern_result` |
| `data_pattern_values` | | データ駆動で失敗したデータパターンの値（例: `{"dp_url": "https://app.magicpod.com/"}`）。1行1変数で表示される | `get_test_case_detail.human_readable_steps` 先頭の表のN番目のデータ行 |
| `started_at` | | テスト実行の開始日時 | `list_batch_run_test_runs` |
| `failed_step` | | 失敗したステップ | `get_test_run` result `failed_lines` |
| `failure_ui` | | 失敗したUI要素 | `get_test_run` result `failure_ui` |
| `error_message` | | エラーメッセージ | `failed_lines` 内のエラー、または `log_search` |
| `failure_analysis` | | MagicPodのAI失敗分析（ユーザーがMagicPod上で実行した場合のみ。無ければ省略） | `get_test_run` `failure_analysis` |
| `test_steps` | | テストケースの全手順（テンプレートで使う場合のみ） | `get_test_case_detail.human_readable_steps` |
| `notes` | | テスト実行のメモ | `list_batch_run_test_runs.notes` |
| `test_case_url` | | `https://app.magicpod.com/{org}/{project}/{test_case_number}/` | 組み立て |
| `test_run_url` | | `https://app.magicpod.com/{org}/{project}/{test_case_number}/test-run/{test_run_number}/` | 組み立て |

`failed_lines` や `failure_ui` が配列・オブジェクトで返ってきた場合は、読みやすい文字列に整形して入れる
（例: 1行1ステップ、`ステップ 7: 「ログイン」ボタンをクリック`）。

### MagicPod の実際の返却値（2026-11 時点で確認）

`get_test_run` の `result`:

```json
{
  "status": "failed",
  "failed_lines": [{"step_number": "1", "message": "failed by the system", "loop_index": null, "expected_ui_ids": []}],
  "failure_ui": {"platform": "browser", "ui_elements": [{"id": 2, "name": "area(1)", "locator": "css=html"}]}
}
```

実行ログ（`test_run_log`）の該当行:

```
11:59:19  [0] openBrowser(app_reinstall)
11:59:19  [1] failWithMessage(failed by the system, {})
Error: failed by the system
```

→ `failed_step`: `ステップ 1: failWithMessage(failed by the system, {})`、`error_message`: `failed by the system`。
`expected_ui_ids` が空なので `failure_ui` は省略。

上記以外の項目も自由に追加でき、テンプレートから同じ名前で参照できる（`customization.md` 参照）。

## 例

```json
{
  "organization": "acme",
  "project": "web_regression",
  "batch_run_number": 128,
  "batch_run_url": "https://app.magicpod.com/acme/web_regression/batch-run/128/",
  "test_setting_name": "夜間回帰",
  "condition_labels": ["Chrome 155", "Cloud"],
  "branch": "main",
  "started_at": "2026-11-05T02:00:03+09:00",
  "ended_at": "2026-11-05T02:41:10+09:00",
  "summary": {"total": 42, "succeeded": 40, "failed": 2},
  "failures": [
    {
      "test_case_number": 17,
      "test_case_name": "ログイン後にマイページが表示される",
      "test_run_number": 311,
      "status": "failed",
      "pattern": "Browser: Chrome 155 / Environment: Cloud",
      "started_at": "2026-11-05T02:13:44+09:00",
      "failed_step": "ステップ 7: 「マイページ」が表示されていることを確認",
      "failure_ui": "マイページ見出し (h1)",
      "error_message": "要素が見つかりませんでした（タイムアウト 10秒）",
      "failure_analysis": "ログインAPIが500を返しており、画面遷移が発生していない可能性があります。",
      "test_case_url": "https://app.magicpod.com/acme/web_regression/17/",
      "test_run_url": "https://app.magicpod.com/acme/web_regression/17/test-run/311/"
    }
  ]
}
```
