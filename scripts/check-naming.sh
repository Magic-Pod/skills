#!/usr/bin/env bash
#
# スキルの名前とフォルダの決まりを確認する（CONTRIBUTING.md の "Naming rules"）。
#
#   - スキルは skills/<スキル名>/SKILL.md に置く
#   - スキル名は magicpod- で始まり、小文字・数字・ハイフンだけを使う
#   - SKILL.md の name はフォルダ名と同じにする
#
#   bash scripts/check-naming.sh
set -uo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."

FAILED=0
fail() {
  echo "$1" >&2
  FAILED=1
}

# skills/ の外に SKILL.md がないか
while IFS= read -r path; do
  case "$path" in
    skills/*/SKILL.md) ;;
    *) fail "SKILL.md は skills/<スキル名>/SKILL.md に置いてください: $path" ;;
  esac
done < <(git ls-files --cached --others --exclude-standard | grep -E '(^|/)SKILL\.md$')

for dir in skills/*/; do
  dir="${dir%/}"
  folder="$(basename "$dir")"

  if [ ! -f "$dir/SKILL.md" ]; then
    fail "SKILL.md がありません: $dir"
    continue
  fi

  if ! [[ "$folder" =~ ^magicpod-[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
    fail "スキル名（フォルダ名）は magicpod- で始め、小文字・数字・ハイフンだけにしてください: $folder"
  fi

  # frontmatter の name を取り出す
  name="$(awk 'NR==1 && $0!="---"{exit} NR>1 && $0=="---"{exit} NR>1 && /^name:/{sub(/^name:[[:space:]]*/,""); gsub(/["'\'']/,""); print; exit}' "$dir/SKILL.md")"
  if [ "$name" != "$folder" ]; then
    fail "SKILL.md の name（${name:-なし}）をフォルダ名（$folder）と同じにしてください: $dir/SKILL.md"
  fi
done

if [ "$FAILED" -ne 0 ]; then
  exit 1
fi
echo "スキルの名前とフォルダは決まりどおりです。"
