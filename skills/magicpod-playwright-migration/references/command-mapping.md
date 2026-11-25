# Playwright → MagicPod コマンド対応表

## 判定

| 判定 | 意味 | エージェントがすること |
|---|---|---|
| `変換する` | 対応するコマンドがある | そのまま変換する |
| `確認する` | 置き換えはできるが、意味が少し変わる、または人の作業が要る | **推測で変換しない。**置き換え案を示し、ユーザーの承認を得てから変換する |
| `変換しない` | MagicPodのテストステップでは表現できない | 変換せず、ファイル名・行番号・理由を報告する |

## この表の位置づけ

- この表は**判断の目安**であり、MagicPodで使えるコマンドの正式な一覧ではない。
- 正式な一覧は、`start_session` の応答に含まれるコマンド一覧（Available commands）。この表と食い違う場合は、**コマンド一覧を優先する**。
- 表で `変換しない` になっている操作でも、判定する前にコマンド一覧を確認し、使えるコマンドが追加されていないか調べる。見つかった場合は `確認する` として扱い、ユーザーに提案する。
- 表に載っているコマンドが一覧にない場合（削除・名前の変更）は、そのコマンドを使わず `確認する` として扱う。
- コマンド名は `get_command_definition` で使う ID。ステップを作る前に、使うコマンドの定義を必ず `get_command_definition` で取得する（パラメータはこの表に書かない。MagicPod側の変更に追従するため）。ただし `shared_step` は `get_command_definition` で取得できない（エラーになる）ので、`start_session` の応答にある書式を使う。

> 確認日：2026-11-20

## ページ操作・ナビゲーション

| Playwright | 判定 | MagicPod | 注意 |
|---|---|---|---|
| `page.goto(url)` | `変換する` | `navigate_to_url` | `baseURL` からの相対パスは `${BASE_URL}/…` にする（`${BASE_URL}` はテスト実行設定のベースURLから作られる組み込み変数）。実行設定のベースURLが元の `baseURL` と同じかを確認する |
| `page.goBack()` / `goForward()` / `reload()` | `変換する` | `back` / `forward` / `reload` | |
| `page.waitForLoadState()` | `変換する` | （通常は不要）/ `wait_whole_rendered` | MagicPodは各ステップで自動で待つ。明示が必要なときだけ入れる |
| `page.waitForTimeout(ms)` | `変換する` | `wait_fixed_time` | |
| `page.waitForURL(url)` | `確認する` | `assert_contains_url` など | URLを待つコマンドはない。待機と確認の違いをユーザーに伝える。後ろに見出しなどの表示確認があれば、その後ろに URL の確認を置く（表示確認は自動で待つので安定する。「操作の直後の否定の確認」の行と同じ考え方） |
| 待つことが目的の `expect`（例：`expect(locator).not.toHaveValue('')`） | `変換する` | コメント → 待機系のコマンド（例：`wait_not_equals_value`） | Playwrightの `expect` は「条件を満たすまで待ち、時間内に満たさなければ失敗する」。MagicPodの待機系のコマンドも同じ動きをするので、待機コマンド1つで元のコードと同じになる。待機の `limit` は、**元のコードの待ち時間に合わせる。ユーザーに聞かずに、次の値を既定にする**（Playwrightの `expect` の既定値は5秒。`playwright.config.ts` の `expect.timeout` や、`expect(…, { timeout })` で変えていればその値）。MagicPodに詳しくない人にも意図が伝わるよう、待機の前に、元のコードとの対応と「時間内に条件を満たさなければ失敗する」ことを書いたコメントを置く（例：`// 数量に値が入るまで待つ。5秒以内に入らなければ失敗する（元のコード：expect(…).not.toHaveValue('')）`） |

## 要素の操作

| Playwright | 判定 | MagicPod | 注意 |
|---|---|---|---|
| `click()` | `変換する` | `click` | |
| `dblclick()` | `変換する` | `double_click` | |
| `click({ button: 'right' })` | `変換する` | `right_click` | |
| `click({ modifiers })` | `変換する` | `click_with_special_key` | |
| `click({ position })` | `変換する` | `click_specified_position` | 座標は要素に対する割合（%）に換算する |
| `fill(value)` | `変換する` | `input` | |
| `pressSequentially()` / `type()` | `変換する` | `input` | 1文字ずつのキーイベントが必要か確認してもよい |
| `press('Enter')` / `keyboard.press()` | `変換する` | `input_key_browser` | |
| codegen が `fill()` の直前に入れる `click()` | `変換する` | （省略） | 入力欄へのフォーカス目的なら省く |
| `check()` / `uncheck()` | `変換する` | `check` / `uncheck` | |
| `selectOption(label)` | `変換する` | `select` | 値（value）指定の場合は、画面に表示される文字列に読み替える |
| `hover()` | `変換する` | `hover` | |
| `dragTo()` | `変換する` | `drag_and_drop` | |
| `scrollIntoViewIfNeeded()` | `変換する` | `scroll_parent_target_to` | |
| `setInputFiles(path)` | `確認する` | `upload_file` | ファイルはMagicPodに事前登録が必要。MCPからはファイルを選べない（`file` は `{}` で作る）ので、**ステップ作成後に人が画面で選ぶ**と伝える。ファイルが選ばれるまでそのステップは実行できないので、確認の実行は**アップロードの直前まで**にし、残りは結果の報告で手作業として挙げる。`upload_fixture_image` は画像の確認コマンド用の画像を登録するもので、アップロード用のファイルとは別物なので使わない |
| `setInputFiles({ buffer })` | `確認する` | `upload_file` | メモリ上のデータは使えない。元のコードのデータ（base64 など）から同じ内容のファイルを作り、ユーザーに渡して登録してもらう案を示す。作ったファイルは報告書と同じ場所に置き、人が手で行う作業の一覧にフルパスで書く（ユーザーが登録するときに探さなくて済むように） |

## アサーション（`expect`）

| Playwright | 判定 | MagicPod | 注意 |
|---|---|---|---|
| `toBeVisible()` | `変換する` | `assert_visible` | 要素がテキストで指定されている場合（`getByText(x)`）は次の行 |
| `getByText(x).toBeVisible()` | `変換する` | `assert_contains_value`（`exact: true` なら `assert_equals_value`） | 文字が表示されていることの確認なので、値の確認系を使う。対象は `x` を含む要素 |
| `toBeHidden()` / `not.toBeVisible()` | `変換する` | `assert_invisible` | `assert_invisible` は、要素がDOMにない場合も成功するため、`toBeHidden()` は `assert_invisible` でよい。要素がDOMから消えることまで確かめたいなら `assert_not_exists` |
| `toHaveText(text)` | `変換する` | `assert_equals_value` | ロケーターが複数の要素に当たりうる場合は、locator-mapping.md の「複数の要素に当たるロケーター（strict mode）」に従う（1件目の確認と、2件目がないことの確認に分ける） |
| `toHaveText([…])` / `toContainText([…])`（配列） | `変換する` | 1件ずつ `assert_equals_value` / `assert_contains_value` → n+1件目の非存在の確認 | 配列の長さ（件数）も確かめているので、`toHaveCount(n)` と同じ組み立てで n+1件目がないことも確かめる。locator-mapping.md の「複数の要素に当たるロケーター（strict mode）」 |
| `toContainText(text)` | `変換する` | `assert_contains_value` | `page.locator('main')` のような大きな範囲が対象のときは、確認する要素を絞るか確認 |
| `toHaveText(/…/)` / `toContainText(/…/)` / `toHaveValue(/…/)`（正規表現） | `変換する` | `store_value_to_variable` → `store_reg_exp_match_to_variable` → `assert_contains_variable` | 下の「正規表現の確認」の組み立てで変換する。中身が普通の文字だけの正規表現なら `assert_contains_value` でよい。`toHaveText(/…/)` は要素の文字全体ではなく一部に合えば成功する（`^`/`$` がない場合）ので、`toContainText` と同じ組み立てでよい。`toHaveValue(/…/)` も入力欄の今の値を `store_value_to_variable` で読んで同じように組み立てる |
| `toHaveValue(v)` | `変換する` | `assert_equals_value` | 入力欄の**今の値**を確認する。`assert_attribute`（value）は使わない（下の「入力欄の値」）。ページのJSが値を入れる入力欄（初期値が自動で入る日付など）では、確認コマンドだと値が入る前に評価されて失敗するおそれがあるので、待機コマンド（`wait_equals_value`、上限はPlaywrightの `expect` のタイムアウト。既定5秒）にする。隠し項目（`type="hidden"`）は例外で、`value` 属性で読む（下の「入力欄の値」） |
| `toHaveAttribute(name, '文字列')` | `変換する` | `assert_attribute` | 属性は書かれたままの値で読む（`href` なら `./detail.html?item-id=9` のまま。完全なURLにはならない）ので、元のコードの値で完全一致にできる |
| `toHaveClass(/文字列/)` / `not.toHaveClass(/文字列/)`（`^` `$` や記号がない正規表現） | `変換する` | `assert_attribute`（`class`、operator: `contains` / `not_contains`） | 部分一致と同じ。記号を含む正規表現なら、`store_attribute_to_variable`（class）から「正規表現の確認」の組み立て。`toHaveClass('a b')`（文字列）は class 属性全体の完全一致なので `equal_to`。否定の確認は「わざと失敗させて確かめる」 |
| `toHaveAttribute(name, /文字列/)`（`^` `$` や記号がなく、`i` もない） | `変換する` | `assert_attribute`（operator: `contains`） | 部分一致と同じ。`assert_attribute` の operator には `equal_to` / `not_equal_to` / `contains` / `not_contains` / `exists` / `not_exists` がある |
| `toHaveAttribute(name, /…/)`（記号を含む正規表現。`i` なし） | `変換する` | `store_attribute_to_variable` → `store_reg_exp_match_to_variable` → `assert_contains_variable` | 下の「正規表現の確認」の組み立てで変換する |
| `toHaveAttribute(name, /…/i)` / `toHaveTitle(/…/i)` / `toHaveURL(/…/i)`（大文字・小文字を区別しない） | `変換する` | 「正規表現の確認」の組み立て | `i` フラグは使えないので、英字を1文字ずつ `[uU][tT][fF]-8` のように大文字・小文字の両方を並べた正規表現に書き換える（下の「正規表現の確認」） |
| `toBeEnabled()` / `toBeDisabled()` | `変換する` | `assert_enabled` / `assert_disabled` | |
| `toBeChecked()` | `変換する` | `assert_selected` / `assert_not_selected` | |
| `toBeEditable()` | `確認する` | `assert_enabled` ＋ `assert_attribute`（`readonly` が `not_exists`） | 編集できるかを直接確かめるコマンドはない。「無効になっていない」と「読み取り専用でない」の2つで代わりにしてよいか確認する（`contenteditable` の要素は対象外） |
| `not.toBeEditable()` | `確認する` | `assert_disabled` または `assert_attribute`（`readonly` が `exists`） | 「編集できない」は「無効 または 読み取り専用」だが、MagicPodでは「または」を1ステップで書けない。ページのHTMLを見て、どちらで編集を止めているかを確かめ、その一方にする。もう一方の作りに変わると、Playwrightは通るのにMagicPodだけが失敗することを「確かめられなくなること」に書く。`assert_disabled` は、親が `d-none` などで表示されていない要素にも成功する |
| `toHaveRole(role)`（`role` 属性が書かれている要素） | `変換する` | `assert_attribute`（`role` が `role` の値と一致） |  |
| `toHaveRole(role)`（タグから決まる役割。`<a href>` はリンク、`<button>` はボタン、など） | `確認する` | ロケーターでタグと条件を保証 ＋ `assert_attribute`（`role` が `not_exists`） | 役割を計算して確かめるコマンドはない。タグから決まる役割になる条件は「そのタグであること（`a` なら `href` があること）」と「`role` 属性で上書きされていないこと」なので、前者をロケーター（例：`a[href="…"]`）で、後者を `role` の `not_exists` で確かめる。タグが変わると「要素が見つからない」で失敗するので、ステップの前に意図を書いたコメントを置く。`role="link"` のように同じ役割が明示されている場合は、Playwrightでは成功するがこの組み立てでは失敗することを説明欄に書く。ロケーターの作り方は locator-mapping.md の「`getByRole` の注意」 |
| `toHaveAccessibleName(name)` | `確認する` | `assert_attribute`（`aria-label` など）／ラベルの確認（下の注意） | 読み上げ用の名前を計算して確かめるコマンドはない。名前が `aria-label` 属性で付いている要素なら属性の確認で代わりにできる。名前が `<label for>` から決まる入力欄は、次の3つで代わりにする：①ラベル（`//label[@for='…']`）の文字を `assert_equals_value` で確かめる、②入力欄に `aria-label` がない（`not_exists`）、③入力欄に `aria-labelledby` がない（`not_exists`）。②③は、ラベルより優先される属性で名前が上書きされていないことの確認。それ以外（ボタンの文字など）から決まる名前は、`assert_equals_value` などで代わりにしてよいか確認する |
| 操作の直後の否定の確認（`not.toHaveURL`、`toBeHidden` など） | `変換する` | 対応する否定の確認コマンド | 画面の切り替えや表示の変化が遅いと、変化の前に評価されてしまう。対策①直後にエラーメッセージの表示など肯定の確認があれば、その後ろに置くことを提案する。対策②待機コマンドの追加を提案する |
| `toHaveCount(0)` | `変換する` | `assert_not_exists` | 0以外の件数は下の `toHaveCount(n)` の行 |
| `count()` が 0 より大きい（`toBeGreaterThan(0)`） | `変換する` | 1件目を位置指定した要素（例：`xpath=(//head/link[@rel='stylesheet'])[1]`）に `assert_exists`（画面に表示される要素なら `assert_visible`） | 「1件目がある」と意味は同じ |
| `toHaveCount(n)` | `変換する` | n件目の存在の確認 → n+1件目の非存在の確認 | 位置で指定したロケーター（`(…)[n]` と `(…)[n+1]`）で、n件目があり、n+1件目がないことを確かめる。表示されているかで数える場合は `assert_visible` / `assert_invisible`、DOMにあるかで数える場合は `assert_exists` / `assert_not_exists` を使う。要素は「I件目」（`xpath=(…)[${I}]`）を1つだけ用意し、`store_fixed_value_to_variable` で `I` に n、n+1 を入れて確認してよい。n件目・n+1件目の要素を別々に作らなくて済む。参考：[一覧画面などのテーブルのテスト](https://support.magic-pod.com/hc/ja/articles/55867425645721) |
| `toHaveTitle('文字列')` | `変換する` | `assert_title` | 完全一致 |
| `toHaveTitle(/文字列/)` | `変換する` | `assert_contains_title` | `^` や `$` がなく、中身が普通の文字だけの正規表現は部分一致と同じ |
| `toHaveTitle(/^文字列$/)` | `変換する` | `assert_title` | 中身が普通の文字だけなら完全一致と同じ |
| `toHaveTitle(/…/)` / `toHaveURL(/…/)`（記号を含む正規表現） | `変換する` | `store_title_to_variable` / `store_url_to_variable` → `store_reg_exp_match_to_variable` → `assert_contains_variable` | 下の「正規表現の確認」の組み立てで変換する |
| `toHaveURL(…)` | `toHaveTitle` と同じ | `assert_url` / `assert_contains_url` | `toHaveTitle` と同じ考え方で判定する。値には `${BASE_URL}/…` を書ける（MCPから書けない `web_api` のURLとは違う）。`.html` の `.` のように、エスケープされた記号（`\.`）は普通の文字として扱う |
| `not.toHaveURL()` / `not.toHaveTitle()` | `変換する` | `assert_not_contains_url` など | 操作の直後に置くと、画面が切り替わる前に評価されて成功してしまうことがある（上の「操作の直後の否定の確認」の行を参照） |
| `toHaveScreenshot()` | `確認する` | `assert_no_visual_diff` | `setting` は `baseline_id: null` と、ほかと重ならない `supplemental_update_id` で作る。基準画像は最初の部分実行で作られる。ウィンドウサイズを固定する必要がある。`fullPage`・`maxDiffPixelRatio` などのオプションはステップでは指定できないので、基準画像の確認とあわせて手作業として報告する。**基準画像を画面で承認するまでは、比較せずに成功する**（実行ログに「基準画像がまだ登録されていない」という内容が出る）。結果の報告では「未検証」として挙げる。`baseline_id: null` で作っても、追加した直後に数値のIDに置き換わる |
| `toMatchAriaSnapshot()` | `変換しない` | — | `assert_no_accessibility_issue` はWCAG違反の検査で、別物 |
| `expect.poll()` / `expect(配列や変数)` | `確認する` | `assert_*_variable` | 値が変数に入れられる場合のみ |
| ブラウザ標準のバリデーションメッセージ | `確認する` | `assert_contains_value` など | 元のコードに忠実にするため、まず**元のコードと同じ文言で確認する案**を出す（Playwrightの `getByText` で見つかっているなら、文言はページの中にあるので確認できる）。文言はブラウザの言語で変わる場合があるため、実行設定の言語（`device_language`）を確認し、元のコードの `locale` と合っているかを確かめる。実行して一致しなかった場合に限り、表示されていることだけの確認に切り替える案を出す。前提にした言語は説明欄に書く |

## 分岐・繰り返し・変数・計算

| Playwright | 判定 | MagicPod | 注意 |
|---|---|---|---|
| `if (await x.isVisible())` | `変換する` | `if_visible` … `statement_end` | `else` は `otherwise`（`just_under_else_parts`）。変換したら、どちらの分岐を通ったかが元のコードと同じかを確かめる（下の「条件分岐」） |
| `inputValue()` / `textContent()` で値を読む | `変換する` | `store_value_to_variable` | 以降は `${変数名}` で参照。入力欄でも `store_attribute_to_variable`（value）は使わない（下の「入力欄の値」） |
| `getAttribute(name)` で属性を読む | `変換する` | `store_attribute_to_variable` | |
| 日付の計算 | `変換する` | `date_calculation` | 加算する単位は1つだけ（例：7日後）。書式は date-fns 形式。タイムゾーンは日本を基準とする。タイムゾーンに依存する確認は、そのことを説明欄に書く |
| 四則演算 | `変換する` | `arithmetic_operation` | 小数は丸められない（0.5−1 は `-0.5`、15.99−15.49 は `0.5`、1÷3 は `0.3333333333`（10桁）。7.99−29.99 は `-22` と表示され、末尾の0は省かれる） |
| 2つの変数の大小を比べる（`expect(a).toBeGreaterThanOrEqual(b)` など） | `変換する` | `arithmetic_operation`（差を計算）→ `assert_numerical_comparison_variable`（差を 0 と比べる） | `assert_numerical_comparison_variable` の比較値（`value`）は数値だけで、`${PREV}` のような変数は書けない。`DIFF = ${CUR} − ${PREV}` を作り、`DIFF` が 0 以上かを確かめる。計画でステップ数を見積もるときも、この形（比べるたびに2ステップ）で数える |
| `Math.random()` などの乱数 | `確認する` | `store_current_second_based_unique_value_to_variable` | 時刻ベースの一意な値で代用してよいか確認 |
| `Date.now()` で一意な値を作る（`user-${Date.now()}@example.com` など） | `変換する` | `store_current_second_based_unique_value_to_variable` → `${変数}` で使う | ミリ秒が秒になる。テストケースごとに別の実行になるので、ぶつかることはまずない。秒になったことを説明欄に書く。日時の計算に使っている場合は `date_calculation` の行 |
| `for` で件数分くり返す（`locator.nth(i)` を順に確認する、など） | `変換する` | 番号用の変数 → `repeat_until_not_exists` … `end_repeat` | 下の「ループ」の組み立てで変換する。件数が変わっても全件を確認できる |
| テストデータの配列で同じ手順を回す | `確認する` | データパターン（`edit_data_pattern`） | 作る前にユーザーに提案して承認をもらう |
| 並び順の確認（`allTextContents()` で取った配列を `sort()` した結果と比べる）：**数値**（価格など） | `変換する` | 下の「ループ」の組み立てで、I件目と I+1件目の値を読み、差を計算して 0 と比べる | 上の「2つの変数の大小を比べる」の行の形にする。値に `$` などの記号が付いている場合は、`store_replacement_to_variable` で数字以外を消してから計算する |
| 並び順の確認：**文字列**（名前順など。`localeCompare` で並べ替えて比べる） | `確認する` | 期待する並びを固定値で1件ずつ `assert_equals_value` → n+1件目の非存在の確認 | 文字列の大小を比べるコマンドがないので、ループでは変換できない。今の画面の並びを元のコードの規則（`localeCompare` など）で並べた期待値を作り、1件目から順に完全一致で確かめ、最後に n+1件目がないことを確かめる（`toHaveCount(n)` と同じ組み立て）。件数や商品が変わると追従しないことを「確かめられなくなること」に書く。これを推奨案にする。`assert_with_ai` は選択肢の一つとして示してよいが、推奨にはしない（伝えることは下の「AIによる確認」） |
| 並び順の確認：**日付・日時**（`new Date()` などで比べて並べ替える） | `変換する`（形式による） | 日付を数に直してから、数値の並び順と同じ組み立て（差を計算して 0 と比べる） | 日付の文字を読み込むコマンドはない（`date_calculation` は今の日時からの計算だけ）ので、正規表現と計算で数に直す。①年→月→日の順で月・日が2桁（`2026/11/05`、`2026-11-05 09:30`）：`store_replacement_to_variable`（正規表現 `\D` を空に置き換え）で `20261105`・`202611050930` にする。②月・日が1桁のことがある、または順番が違う（`2026/11/5`、`11/5/2026`）：年・月・日を後読みなどで1つずつ取り出し（例：月は `(?<=^\d{4}/)\d{1,2}`）、`arithmetic_operation` で `年×10000＋月×100＋日` を計算する（取り出した `05` は `5` として計算される）。③月の名前（`Nov 5`）、和暦、「3日前」などの相対表示：数に直すのが重いので `確認する` にし、文字列の並び順と同じく固定値で1件ずつ確かめる案を示す。元のコードが `new Date()` で比べている場合は、タイムゾーンの扱いが変わりうることを説明欄に書く |
| `test.step(name)` | `変換する` | `comment` | |
| `console.log()` | `変換する` | `output_to_log` | |

## AIによる確認（`assert_with_ai`）

推奨案にしない。ほかのコマンドでは元のコードと同じ確認ができない場合（文字列の並び順など）に限り、`確認する` の項目で**選択肢の一つ**として示してよい。ユーザーが選んだ場合だけ使う。示すときは次を伝え、使った場合は説明欄にも書く。

- 実行のたびに使用回数の上限やAIクレジットを消費する場合がある。条件はヘルプセンター [AIアサーション](https://support.magic-pod.com/hc/ja/articles/51882271299609) を案内する
- 判定に使うのは、実行した時点で**画面に表示されている範囲**だけ。スクロールしないと見えない部分は判定されない（見るならスクロールと `assert_with_ai` を何回か置く。[一覧画面などのテーブルのテスト](https://support.magic-pod.com/hc/ja/articles/55867425645721)）
- 判定の規則がAI任せになり、元のコードと同じ規則（`localeCompare` など）の保証はない
- 失敗してもテストは止まらず、失敗扱いで続く（ヘルプセンターで今の仕様を確かめる）

## ウィンドウ・ダイアログ・ブラウザの状態

| Playwright | 判定 | MagicPod | 注意 |
|---|---|---|---|
| `waitForEvent('popup')` → 新しいタブを操作 | `変換する` | `select_new_window` | |
| 新しいタブを閉じて元に戻る | `変換する` | `close_window` → `select_previous_window`（必ず2つ続けて置く） | `close_window` はタブを閉じるだけで、操作の対象は元のタブに戻らない。続けて `select_previous_window` を置く |
| `page.on('dialog')` → `accept()` / `dismiss()` | `変換する` | `close_alert`（ok / cancel） | 操作の**後に**置く。メッセージの確認は `assert_contains_alert_message`。`page.on('dialog')` は**その後に出るすべてのダイアログ**に効くので、1回の操作で複数のダイアログが続けて出る場合（例：確認ダイアログの後に完了のダイアログ）は、その数だけ `close_alert` を置く（下の「ダイアログ」） |
| `page.on('dialog')` → `accept('文字')`（`prompt()` に文字を入力して OK） | `確認する` | — | `prompt()` に文字を入力するコマンドは、MCP のコマンド一覧にない。文字を入れずに閉じる（`close_alert`）だけでよいか、変換しないかを確認する。判定の前に、コマンド一覧に入力できるコマンドが追加されていないかを確かめる |
| Cookie の設定・取得・削除 | `変換する` | `set_cookie` / `store_cookie_value` / `clear_cookies` | |
| `localStorage` / `sessionStorage` の操作（`evaluate` 内） | `変換する` | `set_value_to_local_storage` / `clear_local_storage` など | `evaluate` の中身が storage 操作だけの場合 |
| `context.grantPermissions` + `setGeolocation` | `変換する` | `set_geolocation` | |
| `test.use({ viewport })` | `確認する` | テスト実行設定のウィンドウサイズ | テストケースではなく実行設定で指定する。ユーザーに設定を依頼する |
| `test.use({ locale })` | `確認する` | テスト実行設定の言語（`device_language`） | テストケースではなく実行設定で指定する。`viewport` と同じく、ユーザーに設定を依頼する。今の値は `get_test_run`（`settings`）で確かめる |
| `test.use({ timezoneId })` | `確認する` | — | **ブラウザのテスト設定にはタイムゾーンの項目がない**（設定できるのはスマートフォンのテスト設定だけ。`get_test_run` の `settings` には `time_zone` が出るが、ブラウザでは変えられない）。クラウドで実行する場合は、元のタイムゾーンで確かめられなくなることを「確かめられなくなること」に書く。確かめたい場合は、そのタイムゾーンのPCでローカルPC実行してもらう（`Default` はPCのタイムゾーンになる） |
| `storageState`（ログイン状態の保存と再利用） | `確認する` | Cookie の保存 → `reset_browser` → 書き戻し | 下の「ログイン状態の保存と再利用」の組み立てを第一案にする。毎回ログインする形は第二案 |
| `page.evaluate()`（上記以外） | `変換しない` | — | MagicPodの「TypeScriptコードを実行」はDOMにアクセスできず（ヘルプセンター [TypeScriptコードを実行コマンド](https://support.magic-pod.com/hc/ja/articles/54908846655513) の「制限事項」）、MCPのコマンド一覧にもない |

## フック（`beforeEach` など）

MagicPodには、テストケースの前後に動く処理（フック）も、失敗しても必ず動く後処理もない。フックの中身は各テストケースのステップとして展開するので、Playwrightと動きが変わるものがある。

| Playwright | 判定 | MagicPod | 注意 |
|---|---|---|---|
| `beforeEach` | `変換する` | 各テストケースの先頭に展開する | Playwrightと同じく、毎回動く。2つ以上のテストに出てくるなら共有ステップの候補（shared-steps-and-variables.md） |
| `afterEach`（ブラウザの中の状態だけを戻す。ログアウト、Cookie・storage の削除など） | `変換する` | 各テストケースの最後に展開する（または省く） | Playwrightはテストが失敗しても動くが、MagicPodは失敗したステップで止まるので動かない。開始方法が「プロセス再起動」なら次のテストケースはまっさらなブラウザで始まるので、影響はない。計画の「こう進める」に書く |
| `afterEach`（サーバーに残るデータを消す、など） | `確認する` | 各テストケースの最後に展開する＋下の案 | 失敗すると後片付けが動かず、データが残って次のテストケースに影響しうる。「確かめられなくなること」に挙げ、扱いを聞く。案：①次のテストケースの最初で状態を整える（例：残っていれば消す。`if_visible` などの分岐を使う）、②後片付けを別のテストケースに分け、一括実行の最後に動かす（テストケースどうしの順番に依存する）、③そのままにする（失敗したときは人が片付ける）。　確認ステップを「失敗扱いとして続ける」（`failure_behavior`: `mark_as_failure_and_continue`）にしても、最後までたどり着く保証にはならない。続けた先の操作が失敗すれば、そこで止まる（例：データがないとき、そのデータの確認は失敗扱いで続いても、そのデータをクリックする操作で止まる）。そのため、これは案にしない |
| `beforeAll`（何回動いても結果が同じ処理。ログイン、画面を開く、など） | `変換する` | 各テストケースの先頭に展開する | Playwrightでは describe（ワーカー）ごとに1回だけだが、MagicPodでは毎回動く。動く回数が増えることを説明欄に書く |
| `beforeAll`（データを作るなど、毎回動くと困る処理） | `確認する` | 下の案 | そのまま展開すると、同じデータを何度も作るなどの問題が出る。案：①準備用のテストケースに分け、一括実行の最初に動かす（テストケースどうしの順番に依存する）、②一意な値（`store_current_second_based_unique_value_to_variable`）を使って、各テストケースで別々のデータを作る（元のコードと違い、テストケースごとにデータが増える） |
| `afterAll` | `確認する` | 下の案 | Playwrightでは最後に1回だけ、失敗しても動く。案：①後片付け用のテストケースに分け、一括実行の最後に動かす（順番に依存する。前のテストケースが失敗しても動く）、②変換しない（後片付けを人が行う）。中身がブラウザの中の状態だけなら、開始方法が「プロセス再起動」であれば不要なので、変換しない（`変換しない` ではなく「不要」として計画の「こう進める」に書く） |

`describe.serial` などで複数のテストを1つのテストケースにまとめたときは、`beforeAll`・各テスト・`afterAll` の区切りに `comment` を置き、元のどのテストかを書く（例：`// 2件目：注文画面の氏名に登録した氏名が入る（元のコード：test('注文画面の氏名に…')）`）。

## ログイン状態の保存と再利用

Playwrightの `storageState` は、ログイン状態（Cookie と localStorage）をファイルに保存し、別のブラウザ状態に復元する。MagicPodでは次の組み立てで再現できる。

```
（ログインする）
Cookieの値を変数に保存（store_cookie_value）：session → SESSION
ブラウザをリセット（reset_browser）
同じドメインのページを開く（navigate_to_url）   ← set_cookie は今開いているページのドメインに設定するため
Cookieを設定（set_cookie）：session = ${SESSION}
（保存した状態でページを開いて確認する）
```

- 何を書き戻すかは、元のコードが保存した状態ファイル（例：`.auth/user.json`）を読んで決める。Cookie の名前と、localStorage に値があるかを確かめる。localStorage があれば `store_local_storage_value` / `set_value_to_local_storage` で同じように書き戻す
- Playwrightの `storageState` は sessionStorage を保存しないので、書き戻さなくてよい
- `set_cookie` は名前と値しか指定できない。path・有効期限・SameSite などは元と同じにならないことを「確かめられなくなること」に書く
- 状態ファイルが手元にない場合は、推測せずユーザーに確認する

## ループ

`for` で要素を順に確認するコードは、ロケーターの中で変数を使って番号を指定し、繰り返しコマンドで再現する。

```ts
for (let i = 0; i < count; i++) {
  await expect(items.nth(i)).toHaveAttribute('href', /detail\.html\?item-id=\d+/);
}
```

```
固定値を変数に保存（store_fixed_value_to_variable）：I = 1
繰り返し（repeat_until_not_exists、interval: 1）：対象 xpath=(//a[normalize-space()='詳細を見る'])[${I}]
    （繰り返しの中で、同じ要素に対する確認を置く）
    四則演算（arithmetic_operation）：${I} + 1 を I に保存
繰り返しの終わり（end_repeat）
```

- ロケーターの `${I}` は、繰り返しのたびに新しい値で評価される
- 繰り返しの条件（I件目が存在しない）は、**中身を実行する前に**判定される。I件目がなくなったところで抜ける
- `interval`（1回ごとの待ち時間、秒）の既定値は5秒。0は指定できない（エラーになる）ので `1` にする。7件の確認で、既定値では約40秒、`1` では約12秒だった
- `timeout`（繰り返し全体の上限、秒）の既定値は600秒
- 元のコードが「1件以上あること」も確認している場合（`count()` が0より大きい、など）は、繰り返しの前に1件目の存在の確認を置く。繰り返しは、1件もないと中身を1回も実行せずに成功してしまうため
- `edit_steps` で繰り返しの開始だけを置き換えることはできない（`end_repeat` までまとめて置き換える）

要素と関係なく決まった回数だけくり返すコード（例：「次へ」を5回押す `for (let i = 0; i < 5; i++)`）は、番号用の変数と、変数の値で判定する繰り返し（`repeat_until_numerical_comparison_variable`：`I` が5より大きくなるまで）で組み立てる。作ったら実行して、回数が合っているかを実行ログで確かめる。参考：[一覧画面などのテーブルのテスト](https://support.magic-pod.com/hc/ja/articles/55867425645721)

## 正規表現の確認

MagicPodの確認コマンドは正規表現を使えないが、「正規表現に合う部分を変数に保存」（`store_reg_exp_match_to_variable`）で代用できる。

```
値を変数に読む（store_attribute_to_variable など）：HREF
正規表現に合う部分を変数に保存：対象 ${HREF}、正規表現 detail\.html\?item-id=\d+、保存先 MATCHED
MATCHED が「detail.html?item-id=」を含むことを確認する（assert_contains_variable）
```

- 正規表現に合わなければ、変数は空になる。そのため、合ったときに必ず含まれる文字列を含むかを確認すれば、「正規表現に合うこと」の確認になる
- 確認に使う文字列は、正規表現のうち記号を含まない部分（上の例なら `detail.html?item-id=`）にする
- **待てない点に注意：**Playwrightの `expect` は文字が正規表現に合うまで待つが、この組み立ては変数に読んだ時点の文字で判定する。対象の文字がページのJSで後から入る・変わる場合（一覧の2件目以降を後から読み込む、など）は、読み込みが遅いと失敗しうる。説明欄にそのことを書き、安定させる待機（例：最後の要素が表示されるまで待つ）を足すかはユーザーに確認する
- 記号を含まない部分がない正規表現（例：`/^\d+$/`）は、「変数が空でないこと」を確認する。`assert_not_equals_variable` で、値を空のままにする（2026-11-20 実機で確認：`12345` では成功、`12a45` では「Variable "NUM_NG" (value: "") is equal to ""」で失敗）

```
正規表現に合う部分を変数に保存：対象 ${VALUE}、正規表現 ^\d+$、保存先 MATCHED
MATCHED が「」（空）と一致しないことを確認する（assert_not_equals_variable、値は空）
```

正規表現の扱い：

| 項目 | 動作 | 変換のしかた |
|---|---|---|
| 文法 | JavaScript（ECMAScript 2021）の正規表現 | Playwrightの正規表現をほぼそのまま使える |
| 合わなかったとき | 変数は空になる | 上の確認方法がそのまま使える |
| キャプチャグループ `( )` | グループの中身ではなく、**合った部分全体**が保存される（`item-id=(\d+)` に対して `item-id=42`）。ヘルプセンターも、正規表現を作るときはキャプチャグループを使わないよう案内している | 合うかどうかの確認なら、グループはそのまま書いてよい。グループの中身だけを後のステップで使っているコード（`match()[1]` など）は `確認する` として扱い、次の案を示す。第一案：先読み・後読みで、取り出したい部分だけに合う正規表現に書き換える（例：`(?<=item-id=)\d+`。ヘルプセンターの「条件に一致する部分を抜き出して変数に保存する」の例と同じ形）。第二案：`store_replacement_to_variable` で、グループより前（例：`^.*item-id=`）と後ろを空に置き換える（2026-11-20 実機で `4` が取れた） |
| `^` と `$` | **文字列全体の**先頭・末尾 | Playwrightの既定と同じなので、そのまま使える |
| フラグ（`i` `m` `s` など） | 指定する欄がない。式の中に書く `(?i)` は「Invalid regular expression」のエラーになる | `i` は下の書き換えで代わりにできる。`m` `s` は `確認する` として扱う |
| 大文字・小文字を区別しない（`i`） | `[uU][tT][fF]-8` のように書けば同じ意味になる | 英字を1文字ずつ `[小文字大文字]` に書き換える。確認に使う文字列は、英字を含まない部分（例：`-8`）にする |

JavaScript（Playwright）の正規表現から書き換えるときの違い：

| Playwright | MagicPodに書くとき |
|---|---|
| `/detail\.html/` のようなリテラル | 前後の `/` とフラグを外し、中身だけを書く（`detail\.html`） |
| `new RegExp('a\\.b')` のような文字列からの生成 | JavaScriptの文字列のエスケープを外した、実際の正規表現（`a\.b`）を書く |
| 先読み・後読み（`(?=…)` `(?<=…)` など。ES2018） | 使える。ヘルプセンターの例（`(?<=金額は).*(?=円)` など）にもあり、2026-11-25 に実機でも後読みで取り出せた |
| 名前付きグループ（`(?<name>…)`。ES2018） | ECMAScript 2021 の範囲なので使える見込み（未確認。使う場合は実行して確かめる）。保存されるのは合った部分全体で、名前で取り出すことはできない |
| ES2022以降の機能（`d` `v` フラグ、`(?i:…)` などの部分的な修飾子、同じ名前のグループの重複） | ECMAScript 2021 にはないので使えない。`確認する` として扱う |
| `g` フラグ | 不要。最初に合った部分だけが保存される |
| `y` `u` フラグ | 指定する欄がない。`確認する` として扱う |


## 条件分岐

条件分岐（`if (await x.isVisible())` など）は、ロケーターしだいで、元のコードと**違う分岐を通っても**テストは成功してしまう。
条件分岐を変換したら、次を行う。

1. `execute_partial_steps` で実行し、実行ログ（`get_test_run` の `log_search`）で、どちらの分岐を通ったかを確かめる
2. 元のコードでどちらの分岐を通るかを調べる。ユーザーに聞く前に、次の方法を試す
   - 変換元のフォルダに `node_modules` があり、ユーザーが手元での実行を認めていれば、元のテストだけを実行して `console.log` の出力を見る（例：`npx playwright test <ファイル> -g "<テスト名>" --reporter=list`）。実行してよいかは、変換計画の「こう進めるもの」に書いて確認しておく
   - 対象のページのHTMLを取得して（例：`curl`）、要素の `role` などの属性を確かめる
   - どちらもできないときは、ユーザーに確認する
3. 食い違っていたら、推測で直さず、事実をユーザーに伝えて対応を相談する。元のコードの条件そのものが意図どおりでない可能性もある

## 変数を使う確認

変数を使う確認は、変数が空でも成功してしまうことがある。たとえば `assert_contains_value` で `${NIGHTS}泊` を確認すると、`NIGHTS` が空なら「泊」だけを含めば成功する。

`store_*_to_variable` で変数に値を入れたら、`execute_partial_steps` で実行し、実行ログ（`get_test_run` の `log_search`）で、変数に期待どおりの値が入っていることを確かめる。

### わざと失敗させて確かめる

次のような確認は、条件が成り立っていなくても成功してしまうことがある。作ったら一度だけ、条件を崩して**失敗すること**を確かめる（例：Cookie の書き戻しを飛ばすと、ログイン後の画面の確認が失敗する）。確かめた後は元に戻し、確かめたことを説明欄に書く。
確認が共有ステップの中にある場合は、共有ステップは編集しない（ほかのテストケースにも影響するため）。テストケースに同じ確認を一時的に足し、条件を崩した状態で実行して失敗することを確かめ、足したステップを消す。

- 状態の復元（Cookie・storage の書き戻し）
- 否定の確認（`assert_not_*`、`assert_invisible` など）
- 変数を使う確認（変数が空でも成功しうるもの）

それ以外の確認では行わない（実行の回数とトークンが増えるため）。

条件の崩し方は、**前提の状態を変える**のを基本にする。属性の確認なら、`set_attribute` で属性を一時的に付ける・変えると手早い（例：`readonly`・`aria-label`・`role`・`href`）（例：「リンクが有効」を確かめるなら、リンクが無効なユーザーでログインして失敗することを見る）。確認の演算子を逆にする（`not_contains` を `contains` にする、など）だけでは、値が空で読めていない場合も失敗するので、確認が正しく働いている証拠にならない。

## 入力欄の値

- 入力欄の値は、値の確認系のコマンド（`store_value_to_variable`、`assert_equals_value`、`assert_contains_value`）で読む・確かめる。Playwright の `inputValue()` / `toHaveValue()` と同じく、入力やスクリプトで変わった後の**今の値**が取れる
- `value` **属性**（`store_attribute_to_variable` / `assert_attribute`）は使わない。ページを読み込んだときの最初の値なので、今の値と食い違う
- ページの JS が値を入れる入力欄は、確認ではなく待機（`wait_equals_value` など）にする
- **例外：隠し項目（`type="hidden"`）**は、値の確認系では空になる。`value` 属性（`store_attribute_to_variable` / `wait_attribute` / `assert_attribute`）で読む。JS が入れた後の値が取れるので、実行ログで値を確かめる

## ダイアログ

ここでの「ダイアログ」は、JavaScript の `alert()` / `confirm()` / `prompt()` で出るブラウザ標準のダイアログ（Playwright の `page.on('dialog')`）。ページが HTML で作るダイアログ（モーダル、`<dialog>` 要素など）は普通の要素なので、`click` や `assert_visible` などで扱う。

- 1回の操作で、ダイアログが続けて出ることがある。Playwrightの `page.on('dialog')` はそのすべてを処理するが、MagicPodでは1つずつ `close_alert` が必要になる
- ダイアログを閉じるステップを作ったら、`execute_partial_steps` で実行し、**別のダイアログが残っていないか**を確認する。残っていれば、その分の `close_alert` を足す
- ダイアログが残っているかどうかは、`capture_ui` が「アラートが表示されている」という内容のエラーで失敗することでわかる
- 特にテストの最後のステップの後は見落としやすい。ダイアログが残ったままだと、次の操作や画面の取り込みが止まる（実例：取り込みがタイムアウトした）
- 元のコードが特定のダイアログのメッセージだけを確認している場合（`messages[0]` など）は、そのダイアログにだけ `assert_contains_alert_message` を置き、ほかは閉じるだけにする

## 変換できないもの（`変換しない`）

「代わりの案」がある行は、推奨案を決めずに「代わりの案で変換する／変換しない」の2択として示し、ユーザーに選んでもらう。代わりの案は元のコードと別物の確認なので、どちらがよいかはユーザーの考え方に合わせる。代わりの案で変換した場合は、別物であることを説明欄に書く。ただし、代わりの案がその環境では実現できない場合（例：`page.route()` の「モック環境のURLに向ける」で、対象のサイトにモック環境がない）は、2択にせず「変換しない」とし、代わりの案が使えない理由を書く。

| Playwright | 理由 | 代わりの案（提示のみ） |
|---|---|---|
| `page.route()`（通信の遮断・モック） | 通信に介入するコマンドがない | モック環境のURLに向ける |
| `page.on('request' / 'response' / 'requestfailed')` | 通信を監視するコマンドがない | リンク切れの確認だけなら `assert_links_are_valid`（意味は別物） |
| `page.goto()` の戻り値でHTTPステータスを確認 | 画面遷移の結果を取れない | `web_api`（GET）で同じURLにリクエストし、`response_status_expectation` で確認する。**別のリクエストになる**ので、置き換えてよいかを確認する |
| `request.get()` などのAPIテスト | — | `web_api` で一部可能。JSON以外の本文の確認はできない |
| `page.on('console' / 'pageerror')` | コンソールを監視するコマンドがない | — |
| `context.setOffline()` | ネットワーク状態を変えるコマンドがない | — |
| `colorScheme` のエミュレーション | 実行環境の設定に当たる項目がない | — |
| `toMatchAriaSnapshot()` | 対応する確認コマンドがない | — |
| `toHaveCSS(name, value)` | 実際に効いているCSSの値（色・大きさなど）を確かめるコマンドがない。「UI要素の属性を確認」で見られるのはHTMLに書かれた属性だけで、CSSの変更や読み込みの失敗で値が変わっても成功する | ヘルプセンター [文字や画像の色を確認したい](https://support.magic-pod.com/hc/ja/articles/48882093257369) へのリンクを示す（AIで確認・画像差分の除外領域・属性の確認。どれも厳密な置き換えではない）。**例外：**`toHaveCSS('display', 'none')` や `toHaveCSS('visibility', 'hidden')` などは「表示されていないこと」の確認なので、`確認する` として `assert_invisible` / `assert_visible` の案を示す |
| `toBeFocused()` | フォーカスを確かめるコマンドがない | — |
| `toBeInViewport()` | 画面の表示範囲に入っているかを確かめるコマンドがない。「TypeScriptコードを実行」は DOM にアクセスできない（`getBoundingClientRect()` を使えない）ので、それでも代わりにできない | `assert_visible` は表示範囲の外でも成功するので別物 |

`web_api` で置き換えるときの書き方（URLには、MCPからは `${BASE_URL}` などの変数を書けない。完全なURLで作り、画面での置き換えを手作業として報告する）：

| 元のコード | `web_api` での書き方 |
|---|---|
| `res.ok()` | `response_status_expectation: ["200-299"]` |
| `status()` が特定の値 | `response_status_expectation: ["404"]` など |
| レスポンスヘッダーの確認（`headers()['content-type']` など） | `result.params` で `responseHeaders["content-type"]`（ヘッダー名は小文字）を変数に入れ、`assert_contains_variable` で確認する |

## `<head>` 内の要素

| Playwright | 判定 | MagicPod | 注意 |
|---|---|---|---|
| `<meta>` / `<link>` の属性確認（`toHaveAttribute`） | `変換する` | `assert_attribute` / `store_attribute_to_variable` | ロケーターの用意のしかたは下の説明を参照 |
| `<head>` 内の要素の存在確認 | `変換する` | `assert_exists` | 画面に表示されないので `assert_visible` は使わない |

`capture_ui` は `<head>` 内の要素を取り込まない。ロケーターの用意のしかたは [locator-mapping.md](locator-mapping.md) の「取り込まれない要素の扱い」に従う。
