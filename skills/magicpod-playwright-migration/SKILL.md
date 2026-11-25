---
name: magicpod-playwright-migration
description: Converts Playwright test code (*.spec.ts / *.spec.js) into MagicPod browser test cases with the MagicPod MCP Server. It reads the code, shows a conversion plan with the points that need your decision, and after you approve, creates the steps in MagicPod and runs them to check. Use when asked, for example, "convert my Playwright tests to MagicPod", "migrate this spec file to MagicPod", or "recreate these Playwright tests in MagicPod". / Playwright のテストコード（*.spec.ts / *.spec.js）を、MagicPod MCP Server を使って MagicPod のブラウザテストケースに変換する。コードを読んで変換計画と確認したい点を示し、承認を得てから MagicPod でステップを作り、実行して確かめる。「Playwright のテストを MagicPod に変換して」「この spec ファイルを MagicPod に移行して」「Playwright のテストを MagicPod で作り直して」などで使う。
license: MIT
---

# Playwright → MagicPod 変換

PlaywrightのテストをMagicPodのブラウザテストケースとして作り直す。

**最重要ルール：不明点は推測で実装しない。** 変換方法が1つに決まらないものは、ユーザーに確認してから進める。

## 必要なもの

- MagicPod MCPサーバーに接続されていること
- 変換元のPlaywrightのコード
- 変換先のMagicPodの組織・プロジェクト（ブラウザのプロジェクト）

## 参照ファイル

| ファイル | いつ読むか |
|---|---|
| [references/command-mapping.md](references/command-mapping.md) | 手順3で、各操作を分類するとき |
| [references/locator-mapping.md](references/locator-mapping.md) | 手順3・5で、ロケーターを決めるとき |
| [references/shared-steps-and-variables.md](references/shared-steps-and-variables.md) | 手順4・5で、共有ステップ・データパターン・共有変数・作成順を決めるとき |
| [references/plan-template.md](references/plan-template.md) | 手順4で、変換計画を書くとき |
| [references/ui-handling.md](references/ui-handling.md) | 手順2・5で、共有UIを決める・取り込む・編集するとき |
| [references/mcp-notes.md](references/mcp-notes.md) | MagicPod MCPのエラーや思わぬ動きに当たったとき。ベースURLと言語を確かめるとき |
| [references/subagents.md](references/subagents.md) | 手順4でユーザーがサブエージェントを使うことを選んだとき |

## 手順

### 0. MagicPod MCPの接続を確認する

ほかの作業を始める前に、MagicPod MCPのツール（`list_organizations` など）が使えるかを確認する。

使えない場合は、そこで作業を止め、次のことをユーザーに伝える。

- 「MagicPod MCP Server が接続されていないようです。」と最初に伝える
- 使っているAIツールでの設定方法は、ヘルプセンターの [MagicPod MCPサーバー](https://support.magic-pod.com/hc/ja/articles/46186888063769) を参照してもらう
- 設定した後は、AIツールを再起動し、新しいセッションでもう一度依頼してもらう

APIトークンなどの認証情報は、チャットに貼ってもらったり、ファイルに書いたりしない。ユーザーから貼られても使わず、MCPの設定に入れてもらうよう伝える。

`list_organizations` は使えるが目的の組織やプロジェクトが出てこない場合は、権限がないか、生成AI機能が無効になっている可能性がある（生成AI機能が無効な組織・プロジェクトは一覧に出ない）。その旨をユーザーに伝えて確認してもらう。

### 1. 入力を確認する

次のことがわからなければユーザーに聞く。

- 変換するファイルとテスト（ファイル全体か、特定の `test()` か）
- 変換先の組織名・プロジェクト名（MagicPodのURLを貼ってもらえば取り出せる）
- 新しいテストケースを作るか、既存のテストケースに追加するか。**既存のテストケースは、許可なく書き換えない**
- 変換するテストの数。**1回の依頼で変換するのは20テストまで**（ループやデータで作られるテストは展開後の数）。超える場合は、どこで区切るかをユーザーに決めてもらう（推奨案はフォルダかファイル単位）
- 新しいテストケースを作るフォルダ。`list_test_cases` で一覧を示して選んでもらう（指定がなければルート）。新しいフォルダ名なら `manage_test_cases`（action=`create_folder`）で作る
- 使うテスト設定。`list_test_settings` で一覧を示して選んでもらう。以降の `manage_device`（action=`start`）の `test_settings_number` に必ずこの番号を指定する
  - テスト設定のベースURLと言語が、元のコードの `baseURL`・`locale` と合っているかは、最初のテストケースを作るときに実際に実行して確かめる（過去の実行の値は当てにしない）。やり方は [references/mcp-notes.md](references/mcp-notes.md) の「ベースURLと言語の確かめ方」

作業フォルダに、前の変換の進捗メモ・引き継ぎ用ファイル・報告書が残っていることがある。そこに書かれた値（ベースURL・言語・共有UIのID・テスト設定の番号など）はそのまま使わず、確かめ直す。

### 2. コードを読み、手順を展開する

テスト1件ごとに、実際に実行される操作を上から順に並べる。

- `beforeEach` / `afterEach` / `beforeAll` / `afterAll` は各テストの前後に展開する。ただし動きが違うものがあるので、command-mapping.md の「フック」に従って分類する
- Page Object と fixture は、呼ばれている部分だけを中身に展開する。Page Object の中の `if` は、渡している引数で実際に通る手順だけを残す
- `baseURL` からの相対パスは `${BASE_URL}/…` にする（テスト設定のベースURLから作られる組み込み変数。末尾の `/` に注意）
- Web API コマンド（`web_api`）のURLには、MCPからは `${BASE_URL}` を書けない。完全なURLで作り、画面で置き換える作業を報告で手作業として挙げる
- 次の箇所に印を付ける（手順4で提案するため）
  - 2つ以上のテストに出てくる同じ操作の並び（fixture、`beforeEach`、Page Object のメソッドなど）
  - 1つのテストの中で、値だけを変えて3回以上くり返す操作
  - 別々のテストが、同じ手順をデータだけ変えて実行している箇所
- テストどうしの順序の依存（`test.describe.serial` など）と、各テストがデータを作る・変える・消すのどれにあたるかを記録する
- 共有UIにする画面と、**どの状態で取り込むか**を決める。ヘッダーは、既存のヘッダー用の共有UIを探す（[references/ui-handling.md](references/ui-handling.md)）

### 3. 各操作を分類する

command-mapping.md を使って、各操作を `変換する` / `確認する` / `変換しない` に分ける。ロケーターは locator-mapping.md を見る。

- 対応表は目安。`start_session` の応答のコマンド一覧（Available commands）を正とする。食い違ったら一覧を優先する
- `変換しない` と判定する前に、一覧に使えるコマンドがないか確かめる。あれば `確認する` として提案する
- 対応表のコマンドが一覧にない場合は、そのコマンドを使わず `確認する` にする

コマンド一覧をまだ受け取っていなければ、既存のテストケースで `start_session` を呼んで取得してよい（そのテストケースは編集しない）。同じ会話ですでに受け取っていれば、呼ばない。

判断がページのHTMLの作りに左右される操作（`disabled` と `readonly`、`role` 属性の有無、名前がラベルから決まるか、操作の後で要素が現れるか、文言がブラウザ標準かサイト独自か、など）は、計画の前にページのHTMLとJSを取得して確かめる（例：`curl`）。取得できなければ推測せず `確認する` にする。

### 4. 変換計画を示して確認をもらう

ステップを作る前に、次の内容を示して確認をもらう。形式は plan-template.md に従う。

質問は一度にまとめる。決まった進め方があるもの（この Skill や対応表に書いてあるもの）や、違いが小さいものは「こう進める」に書く。質問するのは、本当に決まっていない点だけにする。推奨案がMagicPodの画面での作業を前提にしているときは、その項目が実際にあるかをヘルプセンター（`find_help_center_article`）で確かめてから示す。

1. 作成するテストケースの一覧（名前・作成先フォルダ・開始方法）と手順の概要
   - 名前：`describe名_test名`（入れ子なら外側から `_` でつなぐ）。意味のない名前（`test 1` など）や変数を含む名前は、案を出して確認する
   - 開始方法：「プロセス再起動」（`app_reinstall`）。前のテストの状態を引き継ぐ前提（`test.describe.serial` など）なら、どうするか確認する
2. 作成する順序（作る → 変える → 消す。shared-steps-and-variables.md の「投入の順序」）
3. `確認する` の項目：置き換えの案、**その案にした理由**（動きの違い、選ばなかった案とその理由）、**置き換えると確かめられなくなること**。承認されたら説明欄にも書く
4. `変換しない` の項目：ファイル名・行番号・理由
5. 共有ステップの提案（名前の案つき）。既存の共有ステップを使うなら中身を元のコードと比べる。URLの書き方（完全なURLと相対パス）が混ざっていれば、どちらにそろえるかを書く
6. データパターンの提案
7. 共有変数の突き合わせ結果（一致／表記揺れの疑い／未登録）。未登録は画面で登録してもらってから進む
8. 10件以上でサブエージェントに対応しているエージェントなら、サブエージェントを使うか。推奨案は決めず、時間・トークン・準備の違いを示して選んでもらう（[references/subagents.md](references/subagents.md)）

共有ステップとデータパターンは、**提案するだけで、承認なしには作らない。**

### 5. MagicPodでステップを作る

**作業の前と途中で確かめること（見落としが多いもの）**

- [ ] 計画の前に、既存のヘッダー用の共有UIを探したか
- [ ] 共有UIは、最初のテストケースのステップを作る前に、決めた状態でまとめて取り込み、要素の名前変更とロケーター追加を済ませたか
- [ ] 最初のテストケースで、ベースURLと言語を実際に実行して確かめたか
- [ ] `start_session` のたびに、そのセッションで `manage_device`（start）を呼んだか
- [ ] 変数やループのまとまりの前に、意図を書いたコメントを置いたか
- [ ] 否定の確認などは、前提の状態を変えて、一度失敗することを確かめたか
- [ ] 共有ステップの名前の接頭辞（`［画面名］`）は、画面内の操作だけに付けたか
- [ ] 次のセッションに移る前に、そのセッションの端末を `terminate` したか

手順4で合意した順序で、テストケースを1つずつ作る。共有UIの準備のしかたは [references/ui-handling.md](references/ui-handling.md) に従う。

新しくテストケースを作るときは、次の順で行う。

1. `manage_test_cases`（action=`create_test_case`、引数 `test_case_name`）で作成する。続けて何件も作るときは、1件ずつ順に呼ぶ（同時に呼ぶと、番号が作成順とずれるおそれがある）
2. `manage_test_cases`（action=`update_test_case`）で開始方法を設定する。説明欄には変換元だけを書いておいてもよい
3. `start_session` を呼んで、ステップを作り、確かめる（下の「画面単位のくり返し」）
4. 最後に、`read_test_case` で最終的なステップを読み直してから、説明欄を仕上げる（今の説明欄は `get_test_case_detail` で読む。ステップ番号を書くなら、読み直した番号を使う）
   - 変換元（例：`対応元: tests/login.spec.ts › ログインできる`）。まとめた場合はすべての変換元
   - 実機で調べて初めて決まったこと（ループの件数、確かめた属性の値など）
   - 元のコードにないステップを足した場合は、そのステップと理由
   - 言語で変わる文言を確認している場合は、前提にしているテスト設定の言語

テストケースごとに、画面単位で次をくり返す。

1. `start_session` → `read_test_case`。`ref` は `start_session` のたびに変わるので、編集の直前に取り直す。呼ぶ予定の共有ステップは、`search_shared_steps` で名前をそのまま検索しておく（単独で呼ぶ。mcp-notes.md）
2. `manage_device`（action=`start`、手順1で選んだテスト設定）で端末を起動する。端末はセッションごとに別で、前のセッションの画面・Cookie は引き継がれない
3. 対象の画面を開き、`capture_ui` で取り込む。同じ画面の共有UIがあれば、取り込まずにそれを使う
4. Playwrightのロケーターに対応する要素を特定する。要素の名前変更とロケーター追加は、ステップを作る前にまとめて済ませる
5. 使うコマンドの定義を `get_command_definition` で取得する（`shared_step` は取得できないので、`start_session` の応答の書式を使う）
6. `edit_steps` でステップを追加する
7. `execute_partial_steps` で実行する。失敗したら原因を調べて直す。変数に値を入れたら、実行ログで値を確かめる（command-mapping.md の「変数を使う確認」）
8. 次の画面に進んだら 3 に戻る

- 変数やループで組み立てたまとまりの前には、`comment` で1行のコメントを置く。元のコードとの対応と、何を確かめているかを書く（例：`// 商品が6件であること（6件目がある・7件目がない）を確認する（元のコード：toHaveCount(6)）`）
- ブラウザは数分で終了することがあるので、画面ごとにまとめて作り、まとめて実行する
- データパターンがあるテストケースは、作成中は `data_indexes` で1行だけを使い、最後に全行を通す
- 共有ステップは、承認を得たものだけを、テストケースの中に直接作って実機で通してから `create_shared_step` で切り出す（shared-steps-and-variables.md の「作り方」）
- 最後に、テストケース全体を最初から実行して通ることを確かめる。次のセッションに移る前に、`manage_device`（action=`terminate`）で端末を終了する

件数が多いとき（目安：10件以上）は、**進捗メモのファイル**を作り、作業のたびに更新する（共有UIと要素のID、共有ステップの番号、テスト設定の番号、ユーザーと決めたこと、終わったテストケース）。会話の文脈が要約された後も、これを読めば続けられる。サブエージェントを使う場合は [references/subagents.md](references/subagents.md) に従う。

MCPのエラーや思わぬ動き（端末が起動しない、保存が失敗する、共有ステップが呼べない、など）に当たったら、[references/mcp-notes.md](references/mcp-notes.md) を見る。

### 6. 結果を報告する

結果は、報告書のファイルに書き出す。チャットには全文を書かず、要点だけを返す。

- ファイル名：`playwright-to-magicpod_YYYY-MM-DD.md`（作業した日）。指定がなければ変換元のフォルダ（`playwright.config.ts` がある場所）に置く。進捗メモも同じ場所
- 同じ名前のファイルがあれば上書きせず、`_v2` のように番号を付ける。何回かに分けて変換した場合は、同じファイルに回ごとの見出しを付けて追記する
- チャットには、ファイルの場所、件数の内訳、人が手で行う作業、特に伝えたい点（3〜5個）だけを書く

報告書には次を書く。

- 作成・更新したテストケースのURLと変換元
- 作成した共有ステップと、それを呼んでいるテストケース
- 元のコードと順番を入れ替えた確認ステップ
- `変換しない` の項目と、確認を経て変換方法を変えた項目
- ユーザーが手で行う作業（アップロードするファイルの登録と選択、ウィンドウサイズ、画像差分の基準画像の承認、Web API のURLの置き換え、任意で共有UIの名前の変更など）
- 実行して確認できなかった範囲
- 画像差分の確認（`assert_no_visual_diff`）は「未検証」として挙げる（基準画像が承認されるまでは比較せずに成功するため）

## 注意

- 変換元のコードは、ユーザーの指示がない限り変更しない
- MagicPodのステップ名・コメント・共有ステップ名に、このSkillの中でしか使わない呼び名（判定ラベルなど）を書かない
- `assert_with_ai`（AIによる確認）は推奨案にしない。ほかの方法で同じ確認ができない場合に限り、選択肢の一つとして示してよい。示すときに伝えることは command-mapping.md の「AIによる確認」
- MagicPodは各ステップで要素が表示されるのを自動で待つ。Playwrightの明示的な待機は、必要なものだけを残す
- ツールの呼び出しが失敗したら、同じ呼び出しをくり返さない。同じ手順で3回失敗したら、エラー内容をユーザーに報告する（端末の空き待ちは例外。mcp-notes.md）
