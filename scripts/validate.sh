#!/usr/bin/env bash
#
# スキルとプラグイン定義を検証する。CI (.github/workflows/validate.yml) と手元で共用。
# 参考: https://github.com/microcmsio/skills の scripts/validate.sh
#
#   bash scripts/validate.sh
set -uo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."

SKILLS_REF_VERSION="0.1.5"
SKILLS_VERSION="1.5.23"

FAILED=0

run() {
  local label="$1"; shift
  echo "==> $label"
  if "$@"; then
    echo "    OK"
  else
    echo "    FAILED: $label" >&2
    FAILED=1
  fi
  echo
}

skip() {
  echo "==> $1"
  echo "    SKIP: $2"
  echo
}

# 1. Agent Skills 規格（SKILL.md の name / description など）
for skill_dir in ./skills/*/; do
  run "Agent Skills 規格の検証 ($(basename "$skill_dir"))" \
    npx -y "skills-ref@${SKILLS_REF_VERSION}" validate "$skill_dir"
done

# 2. Claude Code のプラグイン定義（plugin.json / marketplace.json）
if command -v claude >/dev/null 2>&1; then
  run "プラグイン定義の検証 (claude plugin validate)" \
    claude plugin validate . --strict
else
  skip "プラグイン定義の検証 (claude plugin validate)" "claude CLI が見つかりません"
fi

# 3. フォルダを動かしたときにインストールできなくなる事故を検出する
run "発見可能性の確認 (skills add --list)" \
  npx -y "skills@${SKILLS_VERSION}" add . --list --full-depth

# 4. 社内情報が含まれていないか
run "社内情報のチェック" \
  bash scripts/check-internal-info.sh

if [ "$FAILED" -ne 0 ]; then
  echo "検証に失敗した項目があります。" >&2
  exit 1
fi
echo "すべての検証を通過しました。"
