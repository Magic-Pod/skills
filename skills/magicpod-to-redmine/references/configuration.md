# 設定

## 環境変数

| 変数 | 必須 | 説明 | 例 |
|---|---|---|---|
| `REDMINE_URL` | ✔ | RedmineのベースURL（末尾 `/` なし） | `https://redmine.example.com` |
| `REDMINE_API_KEY` | ✔ | APIアクセスキー（個人設定 → APIアクセスキー） | `0123abcd...` |
| `REDMINE_PROJECT_ID` | ✔ | 起票先プロジェクトの識別子または数値ID | `qa-automation` |
| `REDMINE_TRACKER_ID` | | トラッカーID（未指定なら config.json → プロジェクト既定） | `1`（バグ） |
| `REDMINE_PRIORITY_ID` | | 優先度ID | `2` |
| `REDMINE_ASSIGNED_TO_ID` | | 担当者（ユーザー/グループ）ID | `5` |
| `REDMINE_CATEGORY_ID` | | カテゴリID | `3` |
| `REDMINE_TEXT_FORMAT` | 実質必須 | `textile` または `markdown`（CommonMark も含む）。未設定時は `markdown` として扱い、警告を出す | `textile` |
| `MAGICPOD_REDMINE_TEMPLATE_DIR` | | テンプレートフォルダ（`customization.md` 参照） | `~/qa/templates` |
| `REDMINE_VERIFY_TLS` | | `0` で証明書検証を無効化（社内の自己署名証明書向け。通常は使わない） | `1` |

トラッカー・優先度・担当者・カテゴリ・カスタムフィールドは、テンプレートフォルダの `config.json` でも設定できる（環境変数が優先）。

IDが分からない場合は `python3 scripts/redmine_sync.py meta` で一覧を取得できる。

`REDMINE_TEXT_FORMAT` は Redmine の 管理 → 設定 → 全般 → 「テキスト書式」に合わせる。
合っていないと、チケット本文のリンクや見出しが崩れて表示される。
この設定は Redmine の REST API では読み取れないため、`check` が成功しても書式が合っているとは限らない。
古い Redmine や社内サーバーの Redmine は Textile のことが多い。

## Redmine側の準備

1. 管理 → 設定 → API → 「RESTによるWebサービスを有効にする」をオン
2. 連携用ユーザー（ボットユーザー推奨）を作成し、対象プロジェクトに次の権限を持つロールで参加させる
   - 必須: 「チケットの閲覧」「チケットの追加」「注記の追加」
   - 任意: 「関連するチケットの管理」（同じテストの完了済みチケットと新しいチケットを紐付けるため。なくても起票は動きます）
   - 「チケットの編集」は不要です（権限を最小限にしておくと、情報システム部門の承認を得やすくなります）
3. そのユーザーでログインし、個人設定 → APIアクセスキー を発行

## 設定例

```bash
export REDMINE_URL="https://redmine.example.com"
export REDMINE_API_KEY="xxxxxxxxxxxxxxxx"
export REDMINE_PROJECT_ID="qa-automation"
export REDMINE_TRACKER_ID=1
```
