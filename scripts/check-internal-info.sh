#!/usr/bin/env bash
#
# 公開してはいけない社内情報（社内リポジトリ・社内ツールへのリンク、社内チャンネル名など）が
# 含まれていないかを確認する。見つかったら該当箇所を表示して失敗する。
#
#   bash scripts/check-internal-info.sh
set -uo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."

# 1行に1つ、拡張正規表現（grep -E、大文字小文字は区別しない）
PATTERNS=(
  'magicpod-internal'              # 社内 GitHub リポジトリ
  'dev\.app\.magicpod\.com'        # 開発環境
  '[a-z0-9-]+\.slack\.com'         # Slack のリンク
  'app\.hubspot\.com'              # HubSpot
  'notion\.(so|site)|app\.notion\.com'  # Notion
  '(docs|drive)\.google\.com'      # Google Drive / Docs
  'productboard\.com'              # Productboard
  'zendesk\.com/(agent|hc/.*/requests)'  # Zendesk の管理画面・問い合わせ
  '(^|[^a-z0-9&])#(cs|sales|support|dev|eng|meeting|help)-[a-z0-9-]+'  # 社内 Slack チャンネル名
)

# このスクリプト自体と .git は対象外
FILES=$(git ls-files --cached --others --exclude-standard | grep -v '^scripts/check-internal-info\.sh$')

FOUND=0
for pattern in "${PATTERNS[@]}"; do
  # shellcheck disable=SC2086
  hits=$(printf '%s\n' $FILES | xargs grep -nIiE -- "$pattern" 2>/dev/null)
  if [ -n "$hits" ]; then
    echo "社内情報の可能性があるもの（パターン: $pattern）:" >&2
    echo "$hits" >&2
    echo >&2
    FOUND=1
  fi
done

if [ "$FOUND" -ne 0 ]; then
  echo "公開リポジトリに社内情報を含めないでください。問題ない場合はパターンを見直してください。" >&2
  exit 1
fi
echo "社内情報は見つかりませんでした。"
