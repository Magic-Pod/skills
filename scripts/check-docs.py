#!/usr/bin/env python3
"""
スキルの書き方の決まりを確認する（CONTRIBUTING.md の Language / Adding a skill）。

  - README の English と日本語の両方の表に、すべてのスキルが載っているか
  - SKILL.md の description が「英語 / 日本語」の形になっているか

  python3 scripts/check-docs.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JA_CHARS = re.compile(r"[぀-ヿ㐀-鿿＀-￯]")
LATIN = re.compile(r"[A-Za-z]")

errors = []


def read_description(skill_md: Path):
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("description:"):
            return line[len("description:"):].strip().strip("'\"")
    return None


skills = sorted(p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md"))

# README
readme = (ROOT / "README.md").read_text(encoding="utf-8")
if "## English" not in readme or "## 日本語" not in readme:
    errors.append("README.md に「## English」と「## 日本語」の見出しが必要です。")
else:
    ja_start = readme.index("## 日本語")
    en_start = readme.index("## English")
    sections = {
        "English": readme[en_start:ja_start] if en_start < ja_start else readme[en_start:],
        "日本語": readme[ja_start:en_start] if ja_start < en_start else readme[ja_start:],
    }
    for skill in skills:
        for label, text in sections.items():
            if not re.search(rf"^\|\s*`{re.escape(skill)}`\s*\|", text, re.MULTILINE):
                errors.append(f"README.md の {label} のスキル一覧の表に `{skill}` がありません。")

# description
for skill in skills:
    path = ROOT / "skills" / skill / "SKILL.md"
    desc = read_description(path)
    if desc is None:
        errors.append(f"{path.relative_to(ROOT)}: 1行の description が見つかりません。")
        continue
    if " / " not in desc:
        errors.append(f"{path.relative_to(ROOT)}: description は「英語 / 日本語」の形にしてください（「 / 」で区切る）。")
        continue
    en, ja = desc.split(" / ", 1)
    if JA_CHARS.search(en) or not LATIN.search(en):
        errors.append(f"{path.relative_to(ROOT)}: description の「 / 」より前は英語だけにしてください。")
    if not JA_CHARS.search(ja):
        errors.append(f"{path.relative_to(ROOT)}: description の「 / 」より後ろに日本語を書いてください。")

if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
print(f"README とスキルの description は決まりどおりです（スキル {len(skills)} 個）。")
