#!/usr/bin/env bash
# テスト用 Redmine を Docker で起動し、magicpod-to-redmine を試せる状態にする。
#   - REST API 有効化 / テキスト書式 Markdown（5.0以降はCommonMark）または Textile
#   - 日本語の初期データ（トラッカー・ステータス・優先度）を投入
#   - プロジェクト「QA自動テスト (qa-automation)」を作成
#   - admin の APIキーを表示
# 使い方: bash setup.sh   （環境変数 NAME / PORT / IMAGE / TEXT_FORMAT で上書き可）
#   例: IMAGE=redmine:4.2 NAME=redmine-42 PORT=3042 TEXT_FORMAT=textile bash setup.sh
#   ※ バージョンを変えるときは NAME も変える（同じ名前のコンテナがあると、それを起動し直すだけになる）
set -euo pipefail

NAME="${NAME:-redmine-test}"
PORT="${PORT:-3000}"
IMAGE="${IMAGE:-redmine:6.0}"
PROJECT="${PROJECT:-qa-automation}"
TEXT_FORMAT="${TEXT_FORMAT:-markdown}"

case "$TEXT_FORMAT" in
  markdown|textile) ;;
  *) echo "TEXT_FORMAT は markdown か textile を指定してください（指定値: $TEXT_FORMAT）" >&2; exit 1 ;;
esac

if ! docker info >/dev/null 2>&1; then
  echo "Docker が起動していません。Docker（Docker Desktop など）を起動してから再実行してください。" >&2
  exit 1
fi

if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then
  CURRENT_IMAGE="$(docker inspect -f '{{.Config.Image}}' "$NAME")"
  echo "コンテナ $NAME は既にあります（$CURRENT_IMAGE）。起動します。"
  if [ "$CURRENT_IMAGE" != "$IMAGE" ]; then
    echo "注意: 指定された IMAGE=$IMAGE ではなく、既存の $CURRENT_IMAGE を使います。" >&2
    echo "      別のバージョンを試すには NAME を変えてください（例: NAME=redmine-42）。" >&2
  fi
  docker start "$NAME" >/dev/null
else
  echo "Redmine ($IMAGE) を起動します（初回はイメージ取得に数分かかります）..."
  # admin / admin のままなので、外部から接続できないよう 127.0.0.1 にだけ公開する
  docker run -d --name "$NAME" -p "127.0.0.1:$PORT:3000" "$IMAGE" >/dev/null
fi

echo -n "起動を待っています"
for _ in $(seq 1 90); do
  if curl -fs -o /dev/null "http://localhost:$PORT/"; then echo " OK"; break; fi
  echo -n "."; sleep 2
done
curl -fs -o /dev/null "http://localhost:$PORT/" || { echo; echo "起動しませんでした: docker logs $NAME を確認してください" >&2; exit 1; }

echo "初期データを投入します..."
TRACKERS="$(docker exec -u redmine "$NAME" bundle exec rails runner -e production 'print Tracker.count' 2>/dev/null | tail -n1)"
if [ "${TRACKERS:-0}" = "0" ]; then
  docker exec -u redmine -e RAILS_ENV=production -e REDMINE_LANG=ja "$NAME" \
    bundle exec rake redmine:load_default_data
else
  echo "（初期データは投入済みのためスキップ）"
fi

echo "API・プロジェクトを設定します..."
docker exec -i -u redmine "$NAME" bash -c "cat > /tmp/setup_magicpod.rb" <<RUBY
Setting.rest_api_enabled = "1"
# CommonMark は Redmine 5.0 以降のみ。古い版では Markdown（redcarpet）を使う（どちらもスクリプトの markdown 書式で表示できる）
formats = Redmine::WikiFormatting.format_names
Setting.text_formatting =
  if "$TEXT_FORMAT" == "textile" then "textile"
  elsif formats.include?("common_mark") then "common_mark"
  else "markdown"
  end
admin = User.find_by_login("admin")
admin.must_change_passwd = false
admin.save!
abort "ERROR: トラッカーがありません。初期データの投入に失敗しています。" if Tracker.count.zero?
project = Project.find_by(identifier: "$PROJECT") ||
  Project.create!(name: "QA自動テスト", identifier: "$PROJECT",
                  enabled_module_names: %w[issue_tracking])
# 既存プロジェクト（トラッカー未設定のまま作られた場合を含む）にも全トラッカーを割り当てる
project.tracker_ids = Tracker.pluck(:id)
project.enabled_module_names = (project.enabled_module_names | %w[issue_tracking])
project.save!
bug = Tracker.find_by(name: "バグ") || Tracker.first
puts "API_KEY=#{admin.api_key}"
puts "TRACKER_ID=#{bug.id}"
puts "TEXT_FORMATTING=#{Setting.text_formatting}"
RUBY
if ! docker exec -u redmine "$NAME" test -s /tmp/setup_magicpod.rb; then
  echo "設定スクリプトをコンテナに書き込めませんでした。" >&2
  exit 1
fi
OUT="$(docker exec -u redmine "$NAME" bundle exec rails runner -e production /tmp/setup_magicpod.rb 2>&1)" || true
API_KEY="$(echo "$OUT" | sed -n 's/^API_KEY=//p')"
TRACKER_ID="$(echo "$OUT" | sed -n 's/^TRACKER_ID=//p')"
TEXT_FORMATTING="$(echo "$OUT" | sed -n 's/^TEXT_FORMATTING=//p')"
if [ -z "$API_KEY" ] || [ -z "$TRACKER_ID" ]; then
  echo "設定に失敗しました。以下の出力を確認してください:" >&2
  echo "$OUT" >&2
  exit 1
fi

cat <<EOF

==================== 完了 ====================
Redmine:   http://localhost:$PORT   （ログイン: admin / admin。このPCからのみ接続できます）
プロジェクト: http://localhost:$PORT/projects/$PROJECT/issues
テキスト書式: ${TEXT_FORMATTING:-不明}（スクリプトは $TEXT_FORMAT として扱います）

次の内容をターミナルで実行してから、Claude に連携を依頼してください:

export REDMINE_URL="http://localhost:$PORT"
export REDMINE_API_KEY="$API_KEY"
export REDMINE_PROJECT_ID="$PROJECT"
export REDMINE_TRACKER_ID=$TRACKER_ID
export REDMINE_TEXT_FORMAT=$TEXT_FORMAT

後片付け: docker rm -f $NAME
==============================================
EOF
