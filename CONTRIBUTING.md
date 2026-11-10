# メンテナンスのルール

このリポジトリは公開されています。ファイルだけでなく、コミットメッセージ・PR のタイトルと本文・ブランチ名も誰でも見られます。

## 書かないもの

- お客様の社名・担当者名、お客様から聞いた内容
- テストで使ったサイトやアプリの具体的な名前・URL・画面（スキルの例は、どのアプリにも当てはまる一般的な書き方にする）
- 社内のリンク（社内 GitHub リポジトリ、Slack、Notion、HubSpot、Google Drive、Productboard など）
- 社内の Slack チャンネル名、社内の呼び方・プロジェクト名
- API キー、トークン、パスワード
- 個人の MagicPod 組織名・プロジェクト名などの既定値

## 変更の流れ

1. ブランチを作って変更する
2. 手元で `bash scripts/validate.sh` を実行し、すべて通ることを確認する
3. PR を作る（タイトル・本文にも上の「書かないもの」を入れない）
4. GitHub Actions の `validate` が通ったらマージする

## 自動チェック（`validate`）

PR を作ったときと main が更新されたときに、次を確認します。

1. Agent Skills の規格（SKILL.md の `name` / `description` など）
2. Claude Code のプラグイン定義（`.claude-plugin/plugin.json` / `marketplace.json`）
3. スキルが見つかるか（フォルダを動かしてインストールできなくなっていないか）
4. 社内情報が含まれていないか（`scripts/check-internal-info.sh`。PR のタイトル・本文も確認）

4 は決まった形の文字列だけを見ています。社名やお客様の話などは機械では見つけられないため、PR を出す前に自分の目でも確認してください。

## リリース

1. `.claude-plugin/plugin.json` の `version` を上げる
2. main にマージしたあと、GitHub Release を作る
