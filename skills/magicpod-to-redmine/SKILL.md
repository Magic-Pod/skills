---
name: magicpod-to-redmine
description: Files the failed tests of a MagicPod batch run as Redmine issues, adding a note instead of a duplicate when an open issue for the same test case exists, and showing a dry run before writing. Also changes the issue subject, body, tracker, and custom fields via templates. Needs the Redmine REST API and connection environment variables. Use when asked to file MagicPod failures in Redmine (e.g., "send this batch run's failures to Redmine"), when a MagicPod batch run and Redmine come up together, or to change the Redmine issue format. To find the cause of failures, use magicpod-failure-investigation instead. / MagicPodの一括実行で失敗したテストをRedmineのチケットとして起票する。同じテストケースの未完了チケットがあれば注記で追記し、書き込む前にdry-runを見せる。件名・本文・トラッカー・カスタムフィールドはテンプレートで変更できる。RedmineのREST APIと接続情報（環境変数）が必要。「失敗をRedmineに起票」「この一括実行の失敗を Redmine へ」などの依頼や、一括実行とRedmineが同時に話題に出たとき、チケットの書式を変えたいときに使う。失敗の原因を調べたいだけなら magicpod-failure-investigation を使う。
license: MIT
---

# MagicPod → Redmine 失敗連携

MagicPodの一括実行結果から失敗したテストを集め、Redmineにチケットとして登録する。
MagicPodのデータは **MagicPod MCPコネクタ** で取得し、Redmineへの書き込みは同梱の　`scripts/redmine_sync.py`（Redmine REST API、Python標準ライブラリのみ）で行う。

同じテストケースが失敗し続けるたびにチケットが増えると、Redmine側が重複チケットで埋まり運用が破綻する。そのためスクリプトは「同じテストケースの未完了チケットがあれば注記を追記、なければ新規起票」という動きをする。

## 前提

- MagicPod MCP コネクタが接続されていること（`list_batch_runs` などが呼べる）
- 環境変数（詳細は `references/configuration.md`）
  - 必須: `REDMINE_URL`, `REDMINE_API_KEY`, `REDMINE_PROJECT_ID`
  - 任意: `REDMINE_TEXT_FORMAT`(markdown|textile)、`REDMINE_TRACKER_ID` など
- チケットの件名・本文・項目はテンプレートで決まる（`references/customization.md`）。
  ユーザーがカスタマイズしていれば `./.magicpod-redmine/` などにあり、スクリプトが自動で使う。
  作業フォルダに `./.magicpod-redmine/` が無ければ `~/.config/magicpod-redmine/`（全プロジェクト共通）、
  それも無ければスキル同梱の既定を使う。どれが使われたかは `check` / `preview` の出力で分かるので、
  設定の出どころを聞かれたらそれを示す。

環境変数が無い場合は、ユーザーに値を尋ねる。APIキーをチャットに貼らせるより、
ユーザー自身にシェルで `export` してもらう方が安全なので、まずそれを提案する。

**テキスト書式は最初に必ず確認する。** `REDMINE_TEXT_FORMAT` が未設定なら、起票の前にユーザーに
「Redmine の 管理 → 設定 → 全般 → テキスト書式 は Textile と Markdown/CommonMark のどちらか」を尋ね、
答えに合わせて `REDMINE_TEXT_FORMAT=textile` か `markdown` を設定してもらう。
この設定は Redmine の API では読み取れず、`check` が成功しても書式が合っているとは限らない。
合っていないと、見出しやリンクが記号のまま表示されて全チケットの見た目が崩れる。
古いRedmineや社内サーバーのRedmineは Textile のことが多い。分からない場合は管理者に確認してもらう。

## スクリプトの実行方法

この文書と `references/` に出てくる `python3 scripts/redmine_sync.py ...` は、**このSKILL.mdがあるフォルダを基準にしたパス**である。
実行するときは次の2点を守る（エージェントによって作業フォルダの扱いが違うため）:

- `scripts/redmine_sync.py` は、このSKILL.mdと同じフォルダにある `scripts/` の**絶対パス**に置き換えて実行する
  （例: `python3 /path/to/skills/magicpod-to-redmine/scripts/redmine_sync.py check`）。
- 作業フォルダは**ユーザーの作業フォルダのまま**にし、スキルのフォルダへ `cd` しない。
  入力JSONやカスタマイズ用の `./.magicpod-redmine/` は作業フォルダを基準に読み書きするため、`cd` すると見つからなくなる。

`python3` が無い環境（Windowsなど）では `python` または `py` を使う。Python 3.8以上が必要。

## 手順

### 1. 対象の一括実行を特定する

- ユーザーがURLを渡した場合: `https://app.magicpod.com/{organization}/{project}/batch-run/{番号}/` から
  組織名・プロジェクト名・番号を読み取る。
- 一覧ページのURL（`https://app.magicpod.com/{organization}/{project}/batch-runs/`、複数形で番号なし）の場合は、
  組織名・プロジェクト名だけを読み取り、番号の指定がないものとして扱う。
- 番号の指定がない場合: `list_batch_runs`（`count: 5` 程度）で最新を確認し、
  「最新の #N（実行日時・ステータス）を対象にしてよいか」をユーザーに確認する。
- 組織名やプロジェクト名が不明なら `list_organizations` / `list_projects` で候補を出す。
- URLで番号が分かっている場合も、`list_batch_runs` を `cursor: {番号}`, `count: 1` で1回呼ぶ。
  テスト設定名・実行条件・ブランチ・開始/終了日時はここからしか取れない（入力JSONの `test_setting_name` /
  `condition_labels` / `branch` / `started_at` / `ended_at`）。

### 2. 失敗したテストを集める

1. `list_batch_run_test_runs` で一括実行内の全テスト結果を取得する。
2. `status_name` が `failed` のものを連携対象にする。`aborted`（中断）や `unresolved` を含めるかは
   ユーザーの指示に従う（指示がなければ `failed` のみ）。
3. データ駆動テスト（`data_pattern_result` がある）は、失敗したデータパターンごとに `failures` の1要素にする
   （チケットを分けるかまとめるかは `data_pattern_mode` で決まる。手順4参照）。
   `summary` は**テスト実行単位**で数える（MagicPodの一括実行画面と同じ数え方。データパターンが2つ失敗しても `failed` は1）。
   `list_batch_run_test_runs` は実行パターン（ブラウザ・端末など）ごとにグループ分けして返す
   （例: `Pattern 1: 日本語Chrome | Browser: Chrome 157 | Environment: Cloud`）。各失敗には
   見出し全体（`Pattern N:` を除く）を `pattern` に、先頭の名前（例: `日本語Chrome`）を `pattern_name` に入れる。
   名前が無い見出しなら `pattern_name` は省略する。
4. 各失敗について `get_test_run` を呼び、`include` に次の2つを指定する。
   データ駆動なら**データパターンごとに別の呼び出しにし**、各項目に `data_pattern_number` を指定する:
   - `{"kind":"failure_analysis"}`
   - `{"kind":"log_search","log_type":"test_run_log","pattern":"\\[[\\d.]+\\] |Error:"}`

   `{"kind":"result"}` は最初は指定しない。失敗時の画面の要素一覧（数百件になる）とスクリーンショットが
   付いてきて応答が非常に大きくなり、必要な情報はたいていログで足りるため。次の場合だけ追加で呼ぶ:
   - ログに `Error:` 行が無い、または失敗したステップをログから特定できない
     （このときは `result.failed_lines[]` の `step_number` と `message` を使う）
   - ユーザーが「失敗したUI要素」も載せてほしいと言っている
     （`failed_lines[].expected_ui_ids` に一致する `failure_ui.ui_elements` の `name` だけを `failure_ui` に入れる。
     `expected_ui_ids` は空のことが多く、その場合は `failure_ui` を省略する）
5. 失敗したテストケースごとに `get_test_case_detail` を1回呼ぶ（`branch_name` は一括実行のブランチ）。
   同じテストケースが複数のパターンで失敗していても1回でよい。
   `human_readable_steps` には、ステップが1行1ステップで並び（`//` のコメント行も1ステップ）、
   データ駆動ならその前にデータパターンの表（`|dp_url|` のようなMarkdownの表。1行目が見出し、
   3行目以降がデータパターン1, 2, …）が入っている。
6. 取得結果を次のように読み替える:
   - **失敗したステップの番号:** 実行ログには `09:28:40  [8] click([領域(45)], {})` のように
     `[ステップ番号] コマンド` が出る（`[0]` はブラウザ/アプリ起動）。最初の `Error:` 行の直前にある `[N]` 行が失敗したステップ。
   - **`failed_step`:** 次の条件を両方満たすときは、`human_readable_steps` のN行目（表と空行を除いて数える）を使い、
     ログのコマンドを括弧で添える。例: `ステップ 8: Click 領域(45)(xpath=//a[text()='Yahoo! JAPAN'])（ログ: click([領域(45)], {})）`
     （2026-11 時点で、ログの `[N]` と `human_readable_steps` のN行目が対応することを確認済み）
     - 表と空行を除いた行数が `step_count` と一致する
     - ステップ番号に `.` が無い（`[8.2]` のような共有ステップ内部の番号は1行と対応しない）

     満たさないときはログのコマンドだけを使う（`ステップ 8.2: click([...], {})`）。
     開発者が読むので、対応が確かなときだけ読みやすい形にし、推測で行を当てはめない。
   - **`error_message`:** ログの `Error: ...` 行（`result` を呼んだ場合は `failed_lines[].message` も。同じ内容なら1つでよい）。
   - **`data_pattern_values`:** データ駆動なら、表のN番目のデータ行を `{"dp_url": "https://..."}` のように
     変数名と値の組で入れる。ログには `navigateToUrl(${dp_url}, {})` と変数名しか出ないため、
     どのデータで失敗したかを開発者が知る唯一の手がかりになる。
     表は**現在の**テストケースの内容なので、`get_test_case_detail` の `updated_at` がテスト実行より後なら、
     実行時と値が違う可能性があることを報告で添える。
   - **`failure_analysis`:** MagicPod の AI 失敗分析で、**ユーザーが MagicPod 上で明示的に実行したときだけ存在する**
     （AIクレジットを消費する機能）。実行していなければ `result` は `null` になるのが正常で、その場合は省略する。
     `get_test_run` での取得は既存の分析を読むだけで、分析を実行したりクレジットを使ったりはしない。
     分析が無いことをユーザーに伝えたり、分析の実行を勧めたりする必要はない。
     データ駆動のとき hint に「the analysis lives on a specific data pattern」と出るが、
     `data_pattern_number` を指定済みなら気にしなくてよい。
   - `get_test_case_detail` などが返す `url` は内部ホスト名のことがあるので使わず、下記の形式で組み立てる。
   - テンプレートが `{{test_steps}}` を使っている場合（既定では使っていない）は、`human_readable_steps` を `test_steps` に入れる。
     テンプレートが求める値だけを集めればよい。

失敗が多い場合（目安10件以上）、サブエージェントを使える環境なら、失敗ごとの取得（手順4〜6）を任せ、
`failures` の1要素分の値だけを返させるとよい。MagicPod の応答をそのまま会話に溜めずに済む。

失敗が0件なら、Redmineには何もせず「失敗なし」と報告して終了する。

### 3. 入力JSONを作る

`references/input-format.md` の形式でJSONファイル（例: `failures.json`）を作業ディレクトリに書き出す。
MagicPodのURLは次の形式で組み立てる（Redmineのチケットから元の結果にすぐ飛べることが重要）:

- 一括実行: `https://app.magicpod.com/{org}/{project}/batch-run/{batch_run_number}/`
- テスト実行: `https://app.magicpod.com/{org}/{project}/{test_case_number}/test-run/{test_case_run_number}/`

エラーメッセージや失敗分析は要約せずそのまま入れる。開発者が原因調査に使う一次情報だからである。
長すぎる場合（目安2,000文字超）はスクリプトが自動で末尾を省略する。

JSONを書いたら `python3 scripts/redmine_sync.py preview --input failures.json` を実行する（Redmineには接続しない）。
出力に `unknown_placeholders` があれば、テンプレートが求めているのにJSONに無い値なので、
MagicPodから取得してJSONに追加し、もう一度 `preview` する。

### 4. 接続確認とプレビュー（dry-run）

```bash
python3 scripts/redmine_sync.py check
python3 scripts/redmine_sync.py sync --input failures.json --dry-run
```

`check` が失敗したら、エラーの種類で伝える内容を分ける:

- 「Claudeの実行環境のネットワーク制限（許可リスト）で接続が遮断されました」: Redmineには届いていない。
  Redmineの設定を疑わせないこと。組織の管理者にRedmineのドメインへのネットワークアクセスを許可してもらう必要がある。
  Redmineが社内ネットワークにしかない場合はこの方法では届かないので、社内PCのClaude Codeでの実行を案内する。
- 「途中のプロキシで接続が拒否されました」: Claudeの制限か会社のプロキシかは、どこで動いているかで決まる。
  今の実行環境が Claude Code（ユーザーのPC）なら会社のプロキシ設定（`NO_PROXY` など）の確認を、
  Claudeアプリならネットワーク許可の設定を案内する。両方を並べて伝えるだけにしない。
- `HTTP 401` / `403` / `404` など: Redmineまでは届いている。URL・APIキー・プロジェクトID・REST API有効化
  （Redmine管理画面 → 設定 → API）を確認するようユーザーに伝える。
- 「接続できません」: URLの誤りか、Redmineが起動していない／ネットワーク的に到達できない。
トラッカーや優先度のIDが分からないときは `python3 scripts/redmine_sync.py meta` で一覧を出す。

`check` や `sync` の出力に `warnings` があれば、内容をユーザーに伝える（特にテキスト書式の警告）。

dry-runの出力は長い（`preview_description` を含む）ので、判定だけ見るなら次のように絞るとよい:

```bash
python3 scripts/redmine_sync.py sync --input failures.json --dry-run | python3 -c "import json,sys; d=json.load(sys.stdin); [print(r['action'], r['key'], r['run_id'], r.get('issue_id') or '', r.get('note') or r.get('reason') or '', r.get('other_open_tickets') or '') for r in d['results']]; print({k: d[k] for k in d if k.endswith('_undecided') or k.startswith('multi_') or k == 'warnings'})"
```

**キーの違う未完了チケット:** `results[].other_open_tickets` があれば、同じテストケースの未完了チケットが
あるのに、キーの付け方が違うため一致しなかったということ（テストをデータ駆動にした、`pattern_mode` /
`data_pattern_mode` を変えた、など）。このまま進めると同じテストのチケットが複数並ぶので、
該当チケットの番号と件名を示してユーザーに選んでもらう:
- 今の設定どおり新規起票する（古いチケットは手動で完了にしてもらう）
- 古いチケットにまとめたい → そのキーになる設定（例: 古いキーが `[MagicPod:test#1]` なら両方 merge）に合わせる。
  その回だけなら `--pattern-mode` / `--data-pattern-mode` で上書きして dry-run し直す。

**複数の実行パターンでの失敗:** 出力に `pattern_mode_undecided: true` があれば、同じテストケースが
複数の実行パターン（例: 日本語Chrome と 英語Edge）で失敗していて、その扱いがまだ決まっていない。
書き込む前に、`multi_pattern_failures` の中身（テストケースと失敗したパターン）を示してユーザーに選んでもらう:

- **まとめる（merge）:** チケットは1件。2つ目以降のパターンの失敗はそのチケットへの注記になる。
  ブラウザに関係なく同じ原因で落ちていることが多い場合に向く。
- **パターンごとに分ける（split）:** パターンごとに別のチケットにする（件名のキーが `[MagicPod:test#1@日本語Chrome]` のようになる）。
  ブラウザごとに担当や対応が分かれる場合に向く。

答えを `python3 scripts/redmine_sync.py set-pattern-mode merge`（または `split`）で保存し、もう一度 dry-run する。
ただし、選ばれた扱いが dry-run 時に使った値（出力の `modes_in_effect`）と同じなら、結果は変わらないので
dry-run のやり直しは省いてよい。その場合は「扱いの選択」と「実行してよいか」を1回の質問でまとめて聞いてよい。
保存先はユーザー用の `config.json`（無ければ `./.magicpod-redmine/config.json` を作る）なので、次回からは聞かれない。
ユーザーが後から変えたいと言ったら同じコマンドで変える。その場合、出力の `note` にあるとおり、
変更前に作った未完了チケットは重複判定のキーが合わなくなる（自動では閉じない）ことを伝える。
定期実行などで確認できない場合は、未設定のまま merge で進め、報告の最後に「扱いが未設定なので決めてほしい」と添える。

**複数のデータパターンでの失敗:** 出力に `data_pattern_mode_undecided: true` があれば、データ駆動テストが
複数のデータパターンで失敗していて、その扱いがまだ決まっていない。`multi_data_pattern_failures` を示して同じように選んでもらう:

- **まとめる（merge）:** テストケースごとにチケットは1件。他のデータパターンの失敗は注記になる。
- **データパターンごとに分ける（split）:** 件名のキーが `[MagicPod:test#1-P2]` のようになる。

`set-data-pattern-mode merge|split` で保存する。未設定のときは split として動く（従来どおり）。
実行パターンとデータパターンの扱いは別々に決まる。両方 merge ならテストケースごとに1件、両方 split なら
「データパターン×実行パターン」ごとに1件になる。どちらでも、同じテスト実行・同じデータパターンの結果は二重に記録されない。

dry-runの結果（新規起票○件・追記○件・スキップ○件と各件名）をユーザーに見せ、実行してよいか確認する。
- merge の場合、同じテストケースの2つ目以降のパターンは、そのチケットへの追記になる。
  dry-runでは「この実行で新規作成する予定のチケットに追記します」と表示される。
- `skip` は、そのテスト実行の結果がすでにチケットに記録済み（同じ一括実行を再度連携した）という意味で、正常な動き。
- `related_to` があれば、同じテストの完了済みチケットがあり、新しいチケットを「関連するチケット」として紐付ける（再発の可能性）。
Redmineへの書き込みは他のメンバーにも通知が飛ぶため、確認を挟む。
ユーザーが最初から「確認不要」と言っている場合や定期実行の場合は確認を省略してよい。

### 5. 実行と報告

```bash
python3 scripts/redmine_sync.py sync --input failures.json
```

スクリプトの出力（JSON）をもとに、次を簡潔に報告する。チケットのURLは `results[].url`、
紐付けた完了済みチケットのURLは `results[].related_url`、`other_open_tickets` の各要素にも `url` が入っている:

- 対象の一括実行（番号・日時・成功/失敗件数）
- 新規起票したチケット（番号とURL。過去の完了済みチケットに紐付けた場合はその番号も）
- 追記したチケット（番号とURL）
- スキップしたもの（記録済みのため。件数だけでよい）
- エラーや警告（`warning`）があれば理由

## チケット内容を変えたいと言われたら

「チケットに再現手順も書いて」「件名を【自動テスト】で始めて」「カスタムフィールドの検出工程に“結合テスト”を入れて」
のような依頼は、その場限りでなく今後もずっと反映してほしいことが多い。テンプレートを編集して対応する。

1. ユーザー用のテンプレートフォルダがなければ `python3 scripts/redmine_sync.py init` で作る
   （既定は作業フォルダの `./.magicpod-redmine/`。全プロジェクト共通にしたいと言われたら `--dir ~/.config/magicpod-redmine`）。
   スキル同梱の `assets/templates/` は直接編集しない。スキルを更新したときに変更が消えるため。
2. `references/customization.md` の書式に従い、`subject.txt` / `description.md`（Textileなら `.textile`） /
   `note.md` / `config.json` を編集する。本文を変えたら、追記用の `note` も合わせるか検討する。
3. カスタムフィールドやトラッカーのIDが分からなければ `meta` で調べる。
4. 手元に `failures.json` があれば `preview` で変更後の見た目をユーザーに見せる。

その回だけの変更（「今回だけ担当者を田中さんに」など）なら、テンプレートは変えずに `failures.json` の値で対応するか、
`--template-dir` で一時的なテンプレートを使う。どちらにするか迷ったら、今後も同じにするかユーザーに確認する。

## 重複判定のしくみ

チケットの件名先頭に `[MagicPod:{project}#{test_case_number}]`（データ駆動なら `-P{パターン番号}`、
`pattern_mode` が split なら `@{実行パターン名}` 付き）というキーを入れ、未完了（open）チケットの中から同じキーを探す。見つかれば注記として今回の失敗を追記し、
見つからなければ新規起票する。チケットを完了にすれば、次に失敗したときは新しいチケットになり、
完了済みのチケットとは「関連する」で紐付く（「関連するチケットの管理」権限がない場合は紐付けだけ省略される）。

本文と注記の末尾には `MagicPod run ID: {project}/tc{番号}/run{実行番号}` という行が自動で付く。
同じテスト実行の結果をもう一度連携しようとすると、この行を見つけてスキップするので、注記が二重に付かない。
テンプレートを編集してもこの行は自動で付くので、消さないよう説明しなくてよい。

`--always-create` は「既存の未完了チケットを無視して新規起票する」オプション。正確には:
- 既存の未完了チケットとは照合しない（追記しない。`other_open_tickets` の検出もしない）。
- ただし同じ実行の中で同じキーの失敗が続いたときは、最初に作ったチケットに追記する（失敗ごとに1件ではない）。
- 同じキーの完了済みチケットがあれば、従来どおり「関連する」で紐付ける。
「未完了のチケットはあるが、今回の失敗は新しいチケットにしてほしい」と言われたときに使う。

## 参照ファイル

- `references/configuration.md` — 環境変数とRedmine側の準備
- `references/input-format.md` — `failures.json` の形式と例
- `references/customization.md` — テンプレートと config.json の書き方、使える値の一覧
