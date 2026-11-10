#!/usr/bin/env bash
#
# スキルやプラグイン定義を変えたときに、plugin.json の version が上がっているかを確認する。
# version が上がっていないと、インストール済みのお客様に新しい版が届かない。
#
# 比べる相手は BASE_REF（既定は origin/main）。BASE_REF が手元にない場合は確認を飛ばす。
#
#   bash scripts/check-version.sh
#   BASE_REF=origin/main bash scripts/check-version.sh
set -uo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."

BASE_REF="${BASE_REF:-origin/main}"
PLUGIN_JSON=".claude-plugin/plugin.json"

if ! git rev-parse --verify --quiet "$BASE_REF" >/dev/null; then
  echo "比べる相手（$BASE_REF）が手元にないため、確認を飛ばします。"
  exit 0
fi

# お客様に届く中身（スキルとプラグイン定義）が変わったか
changed=$( { git diff --name-only "$BASE_REF"...HEAD; git diff --name-only HEAD; git ls-files --others --exclude-standard; } \
  | grep -E '^(skills/|\.claude-plugin/)' | sort -u)
if [ -z "$changed" ]; then
  echo "スキルとプラグイン定義は変わっていないため、version の確認は不要です。"
  exit 0
fi

read_version() {
  python3 -c 'import json,sys; print(json.load(sys.stdin)["version"])'
}

head_version=$(read_version < "$PLUGIN_JSON") || { echo "$PLUGIN_JSON の version を読めません。" >&2; exit 1; }
base_version=$(git show "$BASE_REF:$PLUGIN_JSON" | read_version) || { echo "$BASE_REF の version を読めません。" >&2; exit 1; }

# x.y.z を比べる（head > base なら 0）
if python3 - "$head_version" "$base_version" <<'EOF'
import re, sys
def parse(v):
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", v)
    if not m:
        sys.exit(f"version は x.y.z の形にしてください: {v}")
    return tuple(int(x) for x in m.groups())
sys.exit(0 if parse(sys.argv[1]) > parse(sys.argv[2]) else 1)
EOF
then
  echo "version が上がっています（$base_version → $head_version）。"
  exit 0
fi

echo "スキルまたはプラグイン定義が変わっていますが、$PLUGIN_JSON の version が上がっていません（$BASE_REF: $base_version、この変更: $head_version）。" >&2
echo "変わったファイル:" >&2
echo "$changed" | sed 's/^/  /' >&2
exit 1
