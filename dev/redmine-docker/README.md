# テスト用 Redmine（Docker）

本番の Redmine を使わずに `magicpod-to-redmine` を試すための、テスト用 Redmine の起動手順です。
手元の PC の Docker 上に Redmine を起動し、スキルを試せる状態まで自動で設定します。

すでに試用できる Redmine がある場合は、この手順は不要です。

> [!CAUTION]
> テスト専用です。管理者のログインは `admin` / `admin` のままで、データも保護されていません。
> Redmine はこの PC（`127.0.0.1`）からのみ接続できるように起動しますが、
> 本番環境や共有サーバーでは使わないでください。

## 必要なもの

| もの | 備考 |
|---|---|
| Docker | Docker Desktop は、一定規模以上の企業での業務利用に有料のサブスクリプションが必要です（詳しくは Docker の利用規約を確認してください）。Rancher Desktop や colima などでも動く見込みですが、未検証です |
| `curl`・`bash` | Mac / Linux には標準で入っています。Windows では WSL などで実行してください |
| Python 3.8 以上 | 同梱スクリプトの実行に使います |
| PC 上で動く AI エージェント | Claude Code など。クラウド上で動くエージェント（Claude アプリなど）からは、この PC の `localhost` に接続できません |

## 手順

### 1. Redmine を起動して設定する

```bash
cd dev/redmine-docker
bash setup.sh
```

スクリプトは次のことを自動で行います。何度実行しても問題ありません。

- `redmine:6.0` イメージの起動（データは SQLite、ポート 3000）
- REST API の有効化と、テキスト書式の設定（既定は Markdown。Redmine 5.0 以降は CommonMark）
- 日本語の初期データ（トラッカー「バグ」など）の投入
- プロジェクト「QA自動テスト」（識別子 `qa-automation`）の作成
- 最後に、設定用の `export` コマンドを表示

初回はイメージの取得に数分かかります。

#### バージョンや書式を変えて試す

環境変数で、起動する Redmine のバージョンやテキスト書式を変えられます。お使いの Redmine に近い構成で試すと、チケットの見た目を事前に確認できます。

| 変数 | 既定 | 内容 |
|---|---|---|
| `IMAGE` | `redmine:6.0` | Docker イメージ（例: `redmine:5.1`, `redmine:5.0`, `redmine:4.2`） |
| `NAME` | `redmine-test` | コンテナ名 |
| `PORT` | `3000` | PC 側のポート |
| `TEXT_FORMAT` | `markdown` | `markdown` か `textile`。最後に表示される `export REDMINE_TEXT_FORMAT=...` もこれに合わせて変わる |

```bash
# Redmine 4.2 + Textile
IMAGE=redmine:4.2 NAME=redmine-42 PORT=3042 TEXT_FORMAT=textile bash setup.sh
# Redmine 5.1 + CommonMark
IMAGE=redmine:5.1 NAME=redmine-51 PORT=3051 bash setup.sh
```

> [!NOTE]
> バージョンを変えるときは `NAME` も変えてください。同じ名前のコンテナがすでにあると、
> `IMAGE` を指定してもそのコンテナを起動し直すだけになります（その場合は警告が出ます）。
> 複数を同時に動かすときは `PORT` も分けてください。
>
> 既存のコンテナの書式だけを変えたいときは、同じ `NAME` で `TEXT_FORMAT` を変えて再実行すれば切り替わります。
> 切り替える前に作ったチケットは、元の書式のまま残ります。

### 2. 環境変数を設定する

スクリプトの最後に表示された `export` で始まる5行を、**まとめてコピーして**同じターミナルに貼り付けます。

- 一部だけ貼ると、設定が空になってエラーになります。
- ターミナルを開き直すと設定は消えます。その場合は `bash setup.sh` をもう一度実行して、表示された5行を貼り直してください。
- エージェントは、`export` したのと同じターミナルから起動してください（Claude Code なら `claude`）。VS Code の拡張機能から使う場合など、ターミナルの設定が届かないときは、[docs/magicpod-to-redmine.md](../../docs/magicpod-to-redmine.md) の「設定」にある方法で値を渡してください。

### 3. 接続を確認する

```bash
python3 ../../skills/magicpod-to-redmine/scripts/redmine_sync.py check
```

`"ok": true` とプロジェクト名「QA自動テスト」が表示されれば準備完了です。

### 4. サンプルデータで試す（MagicPod 不要）

同梱の `sample-failures.json` で、起票と重複防止の動きを確認できます。MagicPod の接続は要りません。

```bash
S=../../skills/magicpod-to-redmine/scripts/redmine_sync.py
python3 $S preview --input sample-failures.json --limit 2   # チケットの見た目を確認（Redmine には書き込まない）
python3 $S sync --input sample-failures.json --dry-run      # 起票・追記の予定を確認
python3 $S sync --input sample-failures.json                # 起票（2件）
python3 $S sync --input sample-failures.json                # もう一度 → 記録済みなのでスキップされる
```

起票されたチケットは http://localhost:3000/projects/qa-automation/issues で確認できます（ログイン: `admin` / `admin`）。

> サンプルデータは架空の組織（`acme`）のものなので、チケット内の MagicPod へのリンクは開けません。

### 5. 自分の MagicPod の結果で試す

MagicPod MCP サーバーを接続したエージェントに、次のように頼みます。

```
MagicPod の <組織名> / <プロジェクト名> の一括実行 #<番号> で失敗したテストを Redmine に起票して
```

失敗を含む一括実行を指定してください。同じ依頼をもう一度すると、新しいチケットは作られず、記録済みとしてスキップされます。

## 後片付け

```bash
docker rm -f redmine-test
```

バージョン違いを起動した場合は、それぞれの `NAME` も削除してください（例: `docker rm -f redmine-42`）。

## うまくいかないとき

| 症状 | 対処 |
|---|---|
| `Docker が起動していません` | Docker を起動してから再実行する |
| 起動待ちのまま終わる | `docker logs redmine-test` でエラーを確認する。ポート 3000 が使用中なら `PORT=3100 bash setup.sh` のように変える |
| `設定に失敗しました` で止まる | 表示された出力を確認する。古いイメージでは初期データの投入に失敗することがある |
| `環境変数が未設定です` | `export` の5行が貼られていない。`bash setup.sh` を再実行して、5行をまとめて貼る |
| `接続できません (http://localhost:/...)` | URL のポート番号が空。`setup.sh` が表示した5行を貼り直す |
| `check` が `HTTP 403` | REST API が無効。`bash setup.sh` を再実行する |
| `check` が `HTTP 404` | `REDMINE_PROJECT_ID` が誤っている |
| `ネットワーク制限（許可リスト）で接続が遮断されました` | クラウド上で動くエージェントから実行している。PC 上で動くエージェント（Claude Code など）を使う |
| `can't open file '.../check'` | 変数 `S` が空。手順4の `S=...` の行を実行し直す |
