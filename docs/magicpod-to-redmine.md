# magicpod-to-redmine

[MagicPod](https://magicpod.com/) の一括実行で失敗したテストを、AI エージェントが Redmine のチケットとして起票・追記するための **Agent Skill** です。

```
MagicPod の最新の一括実行で失敗したテストを Redmine に起票して
```

と頼むだけで、エージェントが MagicPod から失敗の内容を集め、プレビューを見せたうえで Redmine にチケットを登録します。

```
MagicPod ──(MagicPod MCP サーバー)──▶ AI エージェント ──(同梱スクリプト / REST API)──▶ Redmine
```

## 特長

- **重複チケットを作らない** — 同じテストケースの未完了チケットがあれば、新規起票せずに注記として追記します。同じ一括実行を2回連携しても、二重には書き込みません。
- **再発が分かる** — 完了済みのチケットがあるテストが再び失敗したときは、新しいチケットを「関連するチケット」として紐付けます。
- **調査に必要な情報をそのまま載せる** — テストケース・テスト実行・一括実行へのリンク、実行パターン（ブラウザ・端末）、失敗したステップ、エラーメッセージ、データ駆動テストのデータの値などを、要約せずに記載します。
- **書き込む前に確認できる** — 起票・追記の予定を dry-run で表示し、確認してから書き込みます。
- **チケットの書式を自由に変えられる** — 件名・本文・トラッカー・カスタムフィールドなどをテンプレートで変更できます。エージェントに「件名を【自動テスト】から始めて」と頼むこともできます。
- **Textile / Markdown（CommonMark）の両方に対応**

## 起票されるチケットの例

件名:

```
[MagicPod:web_regression#17] ログイン後にマイページが表示される が失敗
```

本文（Markdown の場合）:

```markdown
### 概要
* テストケース: [#17 ログイン後にマイページが表示される](https://app.magicpod.com/...)
* テスト実行: [#311](https://app.magicpod.com/...)
* 一括実行: [#128](https://app.magicpod.com/...)
* 実行パターン: 日本語Chrome | Browser: Chrome 157 | Environment: Cloud
* ブランチ: main

### 失敗ステップ
ステップ 7: Assert 「マイページ」が表示されている（ログ: assertElementPresent([マイページ見出し], {})）

### エラーメッセージ
UI element "マイページ見出し" is not found
```

件名の先頭の `[MagicPod:プロジェクト#テストケース番号]` は、重複を判定するためのキーです。

## 動作環境

| 必要なもの | 備考 |
|---|---|
| Agent Skills に対応した AI エージェント | Claude Code と Claude アプリ（Cowork / claude.ai）で動作を確認しています。他のエージェントでも動く見込みですが未検証です（下の「インストール」参照） |
| MagicPod MCP サーバーの接続 | 設定方法は [MagicPod MCPサーバーのセットアップ手順](https://support.magic-pod.com/hc/ja/articles/62605396709273) を参照してください |
| シェルと Python 3.8 以上 | 同梱のスクリプトは標準ライブラリだけで動きます（追加のインストールは不要） |
| Redmine | REST API が有効で、エージェントを動かす環境から接続できること。Redmine 4.2 / 6.0 で動作を確認しています |

## Redmine 側の準備

1. **REST API を有効にする** — 管理 → 設定 → API → 「RESTによるWebサービスを有効にする」をオンにします。
2. **連携用のユーザーを用意する** — ボット用のユーザーを作るのがおすすめです。対象のプロジェクトに、次の権限を持つロールで参加させます。
   - 必須: 「チケットの閲覧」「チケットの追加」「注記の追加」
   - 任意: 「関連するチケットの管理」（完了済みチケットとの紐付けに使います。無くても起票はできます）
   - 「チケットの編集」は不要です。
3. **API アクセスキーを発行する** — 連携用ユーザーでログインし、個人設定 → APIアクセスキー から発行します。
4. **テキスト書式を確認する** — 管理 → 設定 → 全般 → 「テキスト書式」が Textile か Markdown / CommonMark かを確認しておきます（下の `REDMINE_TEXT_FORMAT` に使います）。

## インストール

`magicpod-to-redmine` は MagicPod Skills プラグインに含まれています。[README](../README.md#インストール) の手順でインストールしてください。すでにインストール済みの場合は、[README](../README.md#更新) の手順で更新してください。

### Claude Desktop / Web（チャット・Cowork）で使う場合

Claude アプリでは、スクリプトがクラウド上の環境で動きます。そのため、次の **3つをすべて満たす** 場合にだけ Redmine に接続できます。

1. Redmine がインターネットから接続できる（IP アドレスで接続元を制限していない）
2. Redmine の REST API が有効になっている
3. Claude の組織設定で、Redmine のドメインへのネットワークアクセスが許可されている（組織の管理者が設定します）

社内ネットワークの中にしかない Redmine には接続できません。その場合は、社内の PC で Claude Code を使ってください。

### 他のエージェント（Cursor、Codex など）で使う場合

Claude Code と Claude アプリ以外のエージェントでは動作を確認していません。次の点にご注意ください。

- MagicPod MCP サーバーを、そのエージェントに接続しておく必要があります。
- エージェントがシェルコマンドを実行でき、Redmine へのネットワーク接続が許可されている必要があります。初期設定でネットワークを止めているエージェントもあります。
- 接続エラー時のメッセージは、Claude の環境を前提にした案内になっている箇所があります。

## 設定

接続情報は環境変数で渡します。

```bash
export REDMINE_URL="https://redmine.example.com"   # 末尾の / は不要
export REDMINE_API_KEY="xxxxxxxxxxxxxxxx"           # 連携用ユーザーの APIアクセスキー
export REDMINE_PROJECT_ID="qa-automation"           # 起票先プロジェクトの識別子
export REDMINE_TEXT_FORMAT=textile                  # textile または markdown（CommonMark も markdown）
export REDMINE_TRACKER_ID=1                         # 任意: 起票するトラッカーの ID
```

> [!IMPORTANT]
> `REDMINE_TEXT_FORMAT` は Redmine のテキスト書式に必ず合わせてください。合っていないと、チケットの見出しやリンクが記号のまま表示されます。この設定は API では読み取れないため、接続確認が成功しても合っているとは限りません。

Claude Code を VS Code から使う場合など、ターミナルで `export` した値が届かないときは、作業フォルダの `.claude/settings.local.json` に書いておけます。

```json
{
  "env": {
    "REDMINE_URL": "https://redmine.example.com",
    "REDMINE_API_KEY": "xxxxxxxxxxxxxxxx",
    "REDMINE_PROJECT_ID": "qa-automation",
    "REDMINE_TEXT_FORMAT": "textile"
  }
}
```

> [!WARNING]
> API キーを含むファイルは、Git にコミットしたり他の人に渡したりしないでください。API キーをエージェントとのチャットに直接貼り付けるのも避けてください。

優先度・担当者・カテゴリなど、その他の設定は [`configuration.md`](../skills/magicpod-to-redmine/references/configuration.md) を参照してください。

## 使い方

エージェントに次のように頼みます。

```
MagicPod の最新の一括実行で失敗したテストを Redmine に起票して
```

```
https://app.magicpod.com/acme/web_regression/batch-run/128/ の失敗を Redmine に連携して。中断したものも含めて
```

エージェントは次の流れで進めます。

1. 対象の一括実行を確認します（番号の指定がなければ、最新のものでよいか確認します）。
2. MagicPod から失敗したテストの情報（失敗したステップ、エラー、データの値、AI 失敗分析など）を集めます。
3. Redmine への接続を確認し、起票・追記の予定（dry-run）を表示します。
4. 確認がとれたら書き込み、作成・追記したチケットの URL を報告します。

AI 失敗分析は、MagicPod 上で実行済みの場合だけチケットに載ります。このスキルが分析を実行することはありません（AI クレジットは消費しません）。

### 同じテストが複数のパターンで失敗したとき

1回の一括実行の中で、同じテストケースが複数の実行パターン（例: Chrome と Edge）や、データ駆動テストの複数のデータパターンで失敗することがあります。そのときに **1件のチケットにまとめるか、パターンごとに分けるか** を、最初に該当したときにエージェントが確認し、設定として保存します。次回からは同じ扱いになります。

| 設定 | merge（まとめる） | split（分ける） | 未設定のとき |
|---|---|---|---|
| 実行パターン（`pattern_mode`） | 1件にまとめ、他のパターンは注記で追記 | パターンごとに別チケット | merge として動き、確認を求める |
| データパターン（`data_pattern_mode`） | 1件にまとめ、他のデータは注記で追記 | データパターンごとに別チケット | split として動き、確認を求める |

あとから「ブラウザごとにチケットを分けて」のように頼めば変更できます。

## チケットの内容を変える

件名・本文・追記の内容・トラッカー・カスタムフィールドなどは、テンプレートで変更できます。エージェントに頼むのがいちばん簡単です。

```
Redmine のチケットに再現手順も書くようにして
件名は【自動テスト失敗】から始めて
カスタムフィールド「検出工程」に“結合テスト”を入れて
```

エージェントがテンプレートを作成・編集し、変更後のチケットの見た目をプレビューで見せます。

自分で編集する場合は、次のコマンドでテンプレートの雛形をコピーします。

```bash
python3 <スキルのフォルダ>/scripts/redmine_sync.py init   # ./.magicpod-redmine/ にコピー
```

| ファイル | 内容 |
|---|---|
| `subject.txt` | 件名 |
| `description.md` / `description.textile` | 新規チケットの本文 |
| `note.md` / `note.textile` | 同じテストが再び失敗したときに追記する注記 |
| `config.json` | トラッカー・優先度・担当者・カスタムフィールド、複数パターン失敗時の扱い |

テンプレートは次の順に探されます。作業フォルダの `./.magicpod-redmine/` → `~/.config/magicpod-redmine/`（全プロジェクト共通）→ スキル同梱の既定。スキル本体のファイルは書き換えないので、スキルを更新してもカスタマイズは消えません。

書き方や使える値の一覧は [`customization.md`](../skills/magicpod-to-redmine/references/customization.md) を参照してください。

## テスト用の Redmine で試す

本番の Redmine を使わずに試したい場合は、Docker で手元にテスト用の Redmine を起動できます。

このリポジトリを取得したフォルダで実行します。

```bash
cd dev/redmine-docker
bash setup.sh                                                       # Redmine 6.0 + Markdown
IMAGE=redmine:4.2 NAME=redmine-42 PORT=3042 TEXT_FORMAT=textile bash setup.sh   # 4.2 + Textile
```

REST API の有効化やプロジェクトの作成まで自動で行い、最後に設定用の `export` コマンドを表示します。同梱のサンプルデータを使えば、MagicPod に接続せずに起票や重複防止の動きを確認できます。

手元の `localhost` に起動するため、Claude Code など、PC 上で動くエージェントから使ってください。管理者のログインが `admin` / `admin` のままのテスト専用環境なので、本番環境や共有サーバーでは使わないでください。詳しくは [`dev/redmine-docker/README.md`](../dev/redmine-docker/README.md) を参照してください。

## スクリプトを直接使う

エージェントを介さずに、CI などから同梱のスクリプトを直接使うこともできます（このリポジトリを取得したフォルダで実行します）。MagicPod の結果は、[`input-format.md`](../skills/magicpod-to-redmine/references/input-format.md) の形式の JSON（`failures.json`）にして渡します。

```bash
S=skills/magicpod-to-redmine/scripts/redmine_sync.py
python3 $S check                                          # 接続と権限の確認
python3 $S meta                                           # トラッカー・優先度・カスタムフィールドなどの ID 一覧
python3 $S preview --input failures.json                  # チケットの見た目を確認（Redmine には接続しない）
python3 $S sync --input failures.json --dry-run           # 起票・追記の予定を確認
python3 $S sync --input failures.json                     # 実行
python3 $S set-pattern-mode merge|split                   # 複数の実行パターンで失敗したときの扱いを保存
python3 $S set-data-pattern-mode merge|split              # 複数のデータパターンで失敗したときの扱いを保存
```

出力はすべて JSON です。

## うまくいかないとき

| 症状 | 対処 |
|---|---|
| `環境変数が未設定です` | `REDMINE_URL` / `REDMINE_API_KEY` / `REDMINE_PROJECT_ID` を設定する |
| `HTTP 401` | API キーが誤っている |
| `HTTP 403` | REST API が無効か、連携用ユーザーの権限が足りない |
| `HTTP 404` | `REDMINE_URL` か `REDMINE_PROJECT_ID` が誤っている、またはユーザーがプロジェクトに参加していない |
| `HTTP 422` | Redmine 側で必須のカスタムフィールドに値が入っていない。`config.json` で値を設定する |
| `ネットワーク制限（許可リスト）で接続が遮断されました` | Redmine ではなく、エージェントの実行環境のネットワーク設定で止められている。許可設定を確認するか、社内の PC で実行する |
| `途中のプロキシで接続が拒否されました` | 会社のプロキシ（`NO_PROXY` に Redmine のホスト名を追加するなど）か、エージェントの実行環境のネットワーク設定を確認する |
| 見出しやリンクが `###` や `[...](...)`、`h3.` のまま表示される | `REDMINE_TEXT_FORMAT` が Redmine のテキスト書式と合っていない |
| Mac で `xcode-select: note: No developer tools were found` | 表示されたダイアログで Command Line Tools をインストールするか、`xcode-select --install` を実行する |
