# MagicPod MCP の動きと対処

## ベースURLと言語の確かめ方

`list_test_settings` ではベースURLと言語はわからない。過去の実行の `settings` も、どのテスト設定で実行したかが出ないので当てにしない。**変換先のテストケースで、選んだテスト設定を使って実際に実行して確かめる。**

1. 計画では「ベースURLと言語は、最初のテストケースを作るときに確かめる」と書く。ユーザーがベースURLと言語を知っていれば、計画で聞いて控えておく
2. 最初のテストケースで、`manage_device`（start）に選んだテスト設定を指定し、`${BASE_URL}/…` を開くステップを部分実行する
3. その実行を `get_test_run`（kind=`settings`）で読み、`base_url`・`device_language`・`special_variables` を、元のコードの `baseURL`・`locale` と比べる
4. 食い違っていたら、作業を止めてユーザーに伝える

テスト設定にベースURLがないと、`navigate_to_url` が「Cannot navigate to invalid URL」で失敗し、`settings` の `special_variables` に `BASE_URL` が出ない。その場合は、(1) テスト設定にベースURLを設定してもらう（推奨）、(2) 完全なURLで作る、のどちらにするかをユーザーに確認する。

## こうなったら、こうする

| 起きること | 対処 |
|---|---|
| `manage_device`（start）が「All cloud devices for creating test case are in use or during termination now」で失敗する | 空いている端末がない（上限があり、終了した端末もすぐには空かない）。90秒以上待って start し直す（`sleep`、なければ `python3 -c "import time; time.sleep(90)"`）。「3回失敗したら報告」の数に入れず、90秒おきに5回まで試す |
| `execute_partial_steps` が「Device not started」を返す | `manage_device`（start）を呼び直し、最初から（`start_ref` なし）実行する。新しい端末の画面は空なので、途中からだと失敗する |
| 共有ステップを `edit_steps` で呼ぶと「is not registered in this project」 | `search_shared_steps` で名前をそのまま（`^` `$` を付けずに）検索し、ほかのツールと同時に呼ばず、結果を受け取ってから `edit_steps` する |
| `update_test_case` の後のステップの保存が「modified by another user」で失敗する | `read_test_case` を `force_refresh=True` で読み直してから編集する（`start_session` を呼び直さなくてよい） |
| 共有ステップの名前・説明を変えた後の `edit_shared_step` が「modified by another user」で失敗する | `read_shared_step` を `force_refresh=True` で読み直してから編集する（`ref` も変わる） |
| `edit_steps` などが「Step with ref … not found」で失敗する | `ref` が変わっている（`start_session`・`create_shared_step` の後など）。`read_test_case` で取り直す |
| 401（`Token is expired`）が返る | `start_session` を呼び直す。計画の承認待ちなどで時間があいた後は、呼び直してから続ける |
| `edit_ui_elements` が「This UI has already been edited」で失敗する | そのIDは最新版ではない（共有ステップの中身から読んだIDでも古いことがある）。MCPから最新版のIDを知る方法はないので、要素は足さず、既にある要素を使うかユーザーに確認する |
| `edit_ui_elements` の `delete_locator` が「No deletable locator found」で失敗する | 取り込んだときのロケーターは消せない。`add_locator` で置き換える |
| 共有UIそのものの名前（「UI51」など）を変えたい | MCPからは変えられない（`rename` は要素の名前だけ）。報告で任意の手作業として挙げる |
| `inspect_ui`（mode=`get`）に、付け替えた要素が出てこない | mode=`search`（または `full_regions=True`）で探す |
| 端末が数分で終了している | 画面ごとにまとめて作り、まとめて実行する。終了していたら start し直す |

## そのほかの注意

- ツール名は、MCPのバージョンで変わることがある。見つからなければ同じ働きのツールを使う
- `list_test_cases` の `depth` に `null` を渡すとエラーになることがある。下の階層まで取るなら `10` などを渡す。一覧は大きくなりやすいので、`folder_number` で絞る
- `list_test_runs` の `status` は当てにならない。成否は `get_test_run`（kind=`result`）で確かめる
- テストケースの `ai_generated_summary` は判断の根拠に使わない。中身は `get_test_case_detail` や `read_test_case` で確かめる
- 今の説明欄は `read_test_case` の応答に入っていない。`get_test_case_detail` で読む
- MCPからテストケースは削除できない
