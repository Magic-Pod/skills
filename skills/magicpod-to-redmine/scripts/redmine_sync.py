#!/usr/bin/env python3
"""MagicPod の失敗情報を Redmine に連携するスクリプト（標準ライブラリのみ）。

使い方:
  python redmine_sync.py check                      # 接続・権限確認
  python redmine_sync.py meta                       # トラッカー/優先度/カスタムフィールド等のID一覧
  python redmine_sync.py init [--dir DIR]           # カスタマイズ用にテンプレートをコピー
  python redmine_sync.py preview --input failures.json   # Redmineに接続せずチケット内容を表示
  python redmine_sync.py sync --input failures.json [--dry-run] [--always-create]
                             [--pattern-mode merge|split] [--data-pattern-mode merge|split]
  python redmine_sync.py set-pattern-mode merge|split [--dir DIR]        # 複数の実行パターンで失敗したときの扱いを保存
  python redmine_sync.py set-data-pattern-mode merge|split [--dir DIR]   # 複数のデータパターンで失敗したときの扱いを保存

接続設定は環境変数、チケットの内容はテンプレート（references/customization.md 参照）で決める。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MAX_TEXT = 2000
SKILL_DIR = Path(__file__).resolve().parent.parent
BUNDLED_TEMPLATES = SKILL_DIR / "assets" / "templates"
DEFAULT_USER_DIR = ".magicpod-redmine"
FIELD_KEYS = ("tracker_id", "priority_id", "assigned_to_id", "category_id")
PATTERN_MODES = ("merge", "split")
# 同じテストケースが複数の「実行パターン」（ブラウザ・端末）／「データパターン」で失敗したときの扱い。
# merge: 1件のチケットにまとめて注記で追記 / split: パターンごとに別チケット。
# 未設定（null）のときの動き（従来の動きに合わせる）: 実行パターンは merge、データパターンは split。
MODE_KEYS = {"pattern_mode": "merge", "data_pattern_mode": "split"}


def fail(msg: str, code: int = 1):
    print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False, indent=2))
    sys.exit(code)


def _int_or_none(v, name=""):
    if v in (None, ""):
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        fail(f"{name} に数値ではない値が指定されています: {v}")


# ---------------------------------------------------------------- templates
def template_dirs(explicit: str | None) -> list[Path]:
    """テンプレートを探す順番。先に見つかったファイルを使い、無いファイルは同梱の既定を使う。"""
    dirs = []
    for d in (explicit,
              os.environ.get("MAGICPOD_REDMINE_TEMPLATE_DIR"),
              DEFAULT_USER_DIR,
              str(Path.home() / ".config" / "magicpod-redmine")):
        if d and Path(d).expanduser().is_dir():
            p = Path(d).expanduser().resolve()
            if p not in dirs:
                dirs.append(p)
    dirs.append(BUNDLED_TEMPLATES)
    return dirs


def find_file(dirs: list[Path], name: str) -> Path:
    for d in dirs:
        if (d / name).is_file():
            return d / name
    fail(f"テンプレート {name} が見つかりません（探した場所: {', '.join(map(str, dirs))}）")


BLOCK_RE = re.compile(r"^[ \t]*\{\{#(\w+)\}\}[ \t]*\n(.*?)^[ \t]*\{\{/\1\}\}[ \t]*(?:\n|\Z)", re.M | re.S)
INLINE_BLOCK_RE = re.compile(r"\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}", re.S)
VAR_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def render(template: str, values: dict, unknown: set) -> str:
    """{{name}} を置換し、{{#name}}...{{/name}} は値が空なら丸ごと消す（ミニMustache）。"""
    out = _render(template, values, unknown)
    return re.sub(r"\n{3,}", "\n\n", out).strip() + "\n"


def _render(template: str, values: dict, unknown: set) -> str:
    def block(m):
        return _render(m.group(2), values, unknown) if values.get(m.group(1)) not in (None, "", []) else ""
    prev = None
    while prev != template:  # 入れ子に対応
        prev = template
        template = BLOCK_RE.sub(block, template)
        template = INLINE_BLOCK_RE.sub(block, template)

    def var(m):
        k = m.group(1)
        if k not in values:
            unknown.add(k)
            return ""
        v = values[k]
        return "" if v is None else str(v)
    return VAR_RE.sub(var, template)


# ---------------------------------------------------------------- config
class Config:
    def __init__(self, tdirs: list[Path]) -> None:
        self.url = os.environ.get("REDMINE_URL", "").rstrip("/")
        self.api_key = os.environ.get("REDMINE_API_KEY", "")
        self.project_id = os.environ.get("REDMINE_PROJECT_ID", "")
        self.text_format_explicit = bool(os.environ.get("REDMINE_TEXT_FORMAT"))
        self.text_format = (os.environ.get("REDMINE_TEXT_FORMAT") or "markdown").lower()
        self.verify_tls = os.environ.get("REDMINE_VERIFY_TLS", "1") != "0"
        self.config_path = find_file(tdirs, "config.json")
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            fail(f"{self.config_path} のJSONが不正です: {e}")
        self.fields = {k: _int_or_none(data.get(k), k) for k in FIELD_KEYS}
        for k in FIELD_KEYS:  # 環境変数があれば config.json より優先
            env = os.environ.get(f"REDMINE_{k.upper()}")
            if env:
                self.fields[k] = _int_or_none(env, f"REDMINE_{k.upper()}")
        self.custom_fields = data.get("custom_fields") or []
        self.modes = {}
        for k in MODE_KEYS:
            v = data.get(k) or None
            if v not in (None, *PATTERN_MODES):
                fail(f"{self.config_path} の {k} は merge か split を指定してください: {v}")
            self.modes[k] = v
        if self.text_format not in ("markdown", "textile"):
            fail("REDMINE_TEXT_FORMAT は markdown か textile を指定してください")

    def warnings(self) -> list[str]:
        w = []
        if not self.text_format_explicit:
            w.append("REDMINE_TEXT_FORMAT が未設定のため markdown として扱っています。"
                     "Redmine の「管理 → 設定 → 全般 → テキスト書式」が Textile の場合はチケットの表示が崩れるので、"
                     "設定に合わせて REDMINE_TEXT_FORMAT=textile または markdown を指定してください"
                     "（この設定は Redmine の API では読み取れないため、checkでは判定できません）。")
        return w

    def require(self) -> None:
        missing = [n for n, v in (("REDMINE_URL", self.url),
                                  ("REDMINE_API_KEY", self.api_key),
                                  ("REDMINE_PROJECT_ID", self.project_id)) if not v]
        if missing:
            fail(f"環境変数が未設定です: {', '.join(missing)}")


# ---------------------------------------------------------------- http
CLAUDE_BLOCK_MSG = (
    "Redmineに届く前に、Claudeの実行環境のネットワーク制限（許可リスト）で接続が遮断されました。"
    "Redmine側の設定の問題ではありません。"
    "Claudeアプリ（Cowork / claude.ai）で実行している場合は、組織の管理者に"
    "「設定 → Capabilities」でRedmineのドメインへのネットワークアクセスを許可してもらってください。"
    "社内ネットワーク内にしかないRedmineはこの方法では届かないため、社内PCのClaude Codeから実行してください。"
)
PROXY_BLOCK_MSG = (
    "Redmineに届く前に、途中のプロキシで接続が拒否されました（Redmine側の設定の問題ではありません）。"
    "考えられる原因は2つあります。"
    "(1) Claudeアプリ（Cowork / claude.ai）で実行している場合: Claudeのネットワーク制限です。"
    "組織の管理者に「設定 → Capabilities」でRedmineのドメインへのアクセスを許可してもらってください。"
    "(2) 社内PCのClaude Codeなどで実行している場合: 会社のプロキシがRedmineへの接続を止めています。"
    "社内のRedmineならプロキシを経由しないよう環境変数 NO_PROXY にRedmineのホスト名を追加するか、"
    "社内のネットワーク担当者にプロキシ設定を確認してください。"
)
# Claude の許可リストが返す応答（Redmine自身の403と区別するため）
_CLAUDE_BLOCK_PATTERNS = ("blocked by network allowlist", "not in allowlist", "host_not_allowed")
# 会社のプロキシでも Claude の環境でも起こり得る応答
_PROXY_BLOCK_PATTERNS = ("tunnel connection failed: 403", "tunnel connection failed: 407")


def network_block_message(text: str) -> str | None:
    t = (text or "").lower()
    if any(p in t for p in _CLAUDE_BLOCK_PATTERNS):
        return CLAUDE_BLOCK_MSG
    if any(p in t for p in _PROXY_BLOCK_PATTERNS):
        return PROXY_BLOCK_MSG
    return None


class Redmine:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.ctx = None
        if not cfg.verify_tls:
            import ssl
            self.ctx = ssl._create_unverified_context()  # 社内の自己署名証明書向け

    def request(self, method: str, path: str, params=None, body=None):
        url = f"{self.cfg.url}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params, doseq=True)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("X-Redmine-API-Key", self.cfg.api_key)
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req, context=self.ctx, timeout=30) as res:
                raw = res.read()
                return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            msg = network_block_message(detail)
            if msg:
                raise RuntimeError(msg + f"（{method} {url}: HTTP {e.code} {detail.strip()}）") from None
            hint = {401: "（APIキーが誤っています）",
                    403: "（REST APIが無効か、権限がありません）",
                    404: "（プロジェクトIDやURLが誤っています）",
                    422: "（入力内容が不正です。トラッカー・カスタムフィールドの必須項目などを確認）"}.get(e.code, "")
            raise RuntimeError(f"HTTP {e.code}{hint} {method} {path}: {detail}") from None
        except urllib.error.URLError as e:
            msg = network_block_message(str(e.reason))
            if msg:
                raise RuntimeError(msg + f"（{url}: {e.reason}）") from None
            raise RuntimeError(f"接続できません ({url}): {e.reason}") from None

    def get(self, path, params=None):
        return self.request("GET", path, params=params)

    def paged(self, path, key, params=None):
        params = dict(params or {})
        offset, out = 0, []
        while True:
            params.update({"offset": offset, "limit": 100})
            res = self.get(path, params)
            items = res.get(key, [])
            out.extend(items)
            offset += len(items)
            if not items or offset >= res.get("total_count", 0):
                return out


# ---------------------------------------------------------------- issue building
def pattern_label(f: dict) -> str:
    """重複判定キーに使う実行パターン名。短い pattern_name（例: 日本語Chrome）を優先する。"""
    name = str(f.get("pattern_name") or f.get("pattern") or "").strip()
    return re.sub(r"[\[\]]", "", name)  # ] があるとキーの終わりと誤認するため除く


def effective_mode(modes: dict | None, k: str) -> str:
    return (modes or {}).get(k) or MODE_KEYS[k]


def base_key(project: str, tc) -> str:
    """同じテストケースのチケットに共通するキーの先頭部分（末尾の ] や -P・@ は含まない）。"""
    return f"[MagicPod:{project}#{tc}"


def issue_key(project: str, f: dict, modes: dict | None = None) -> str:
    key = base_key(project, f["test_case_number"])
    if f.get("data_pattern_number") and effective_mode(modes, "data_pattern_mode") == "split":
        key += f"-P{f['data_pattern_number']}"
    if effective_mode(modes, "pattern_mode") == "split" and pattern_label(f):
        key += f"@{pattern_label(f)}"
    return key + "]"


def same_test_case(key: str, base: str) -> bool:
    """key が base と同じテストケースのキーか（#1 と #10 を取り違えないよう、続く1文字で判定）。"""
    return key.startswith(base) and key[len(base):len(base) + 1] in ("]", "-", "@")


def multi_pattern_failures(failures: list) -> list:
    """同じテストケース（データパターン）が2つ以上の実行パターンで失敗しているもの。"""
    groups: dict = {}
    for f in failures:
        k = (f["test_case_number"], f.get("data_pattern_number"))
        groups.setdefault(k, [])
        label = pattern_label(f)
        if label and label not in groups[k]:
            groups[k].append(label)
    out = []
    for (tc, dp), labels in groups.items():
        if len(labels) >= 2:
            name = next((f.get("test_case_name") for f in failures if f["test_case_number"] == tc), None)
            out.append({"test_case_number": tc, "test_case_name": name,
                        **({"data_pattern_number": dp} if dp else {}), "patterns": labels})
    return out


def multi_data_pattern_failures(failures: list) -> list:
    """同じテストケースが2つ以上のデータパターンで失敗しているもの。"""
    groups: dict = {}
    for f in failures:
        dp = f.get("data_pattern_number")
        if dp:
            g = groups.setdefault(f["test_case_number"], {"name": f.get("test_case_name"), "dps": []})
            if dp not in g["dps"]:
                g["dps"].append(dp)
    return [{"test_case_number": tc, "test_case_name": g["name"], "data_patterns": sorted(g["dps"])}
            for tc, g in groups.items() if len(g["dps"]) >= 2]


def pattern_mode_info(cfg, failures: list, modes: dict) -> dict:
    """複数パターン失敗時の扱いが未決定なら、利用者に確認するための情報を返す。
    決定済みなら何も出さない（出力が「未決定」に見えて紛らわしいため）。"""
    info: dict = {}
    if not modes.get("pattern_mode"):
        multi = multi_pattern_failures(failures)
        if multi:
            info.update({
                "pattern_mode_undecided": True,
                "multi_pattern_failures": multi,
                "pattern_mode_question": (
                    "同じテストケースが複数の実行パターン（ブラウザ・端末など）で失敗しています。"
                    "merge: チケットは1件にまとめ、他のパターンは注記で追記する / "
                    "split: 実行パターンごとに別のチケットにする。"
                    "未設定のため merge として扱っています。"
                    "決めたら set-pattern-mode merge|split で保存してください。")})
    if not modes.get("data_pattern_mode"):
        multi = multi_data_pattern_failures(failures)
        if multi:
            info.update({
                "data_pattern_mode_undecided": True,
                "multi_data_pattern_failures": multi,
                "data_pattern_mode_question": (
                    "データ駆動テストが複数のデータパターンで失敗しています。"
                    "merge: チケットは1件にまとめ、他のデータパターンは注記で追記する / "
                    "split: データパターンごとに別のチケットにする。"
                    "未設定のため split として扱っています。"
                    "決めたら set-data-pattern-mode merge|split で保存してください。")})
    if info:
        info["modes_in_effect"] = {k: effective_mode(modes, k) for k in MODE_KEYS}
    return info


def run_id(project: str, f: dict, run: dict) -> str:
    """1回のテスト実行を表すID。注記の二重追加を防ぐために本文に埋め込む。
    （「#2」のように書くと Redmine がチケット番号へのリンクに変換するので # は使わない）"""
    rid = f"{project}/tc{f['test_case_number']}"
    if f.get("data_pattern_number"):
        rid += f"-p{f['data_pattern_number']}"
    if f.get("test_run_number"):
        rid += f"/run{f['test_run_number']}"
    else:
        rid += f"/batch{run.get('batch_run_number', '')}"
    return rid


def run_marker(rid: str) -> str:
    return f"MagicPod run ID: {rid}"


def has_marker(text: str, rid: str) -> bool:
    return re.search(re.escape(run_marker(rid)) + r"(?![\w-])", text or "") is not None


def clip(v):
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        v = "\n".join(map(str, v))
    elif isinstance(v, dict):
        v = json.dumps(v, ensure_ascii=False)
    text = str(v).strip()
    if len(text) > MAX_TEXT:
        return text[:MAX_TEXT] + f"\n…（{len(text) - MAX_TEXT}文字省略）"
    return text


def link(label: str, url: str, fmt: str) -> str:
    if not url:
        return label
    return f'"{label}":{url}' if fmt == "textile" else f"[{label}]({url})"


def build_values(run: dict, f: dict, project: str, fmt: str, modes: dict | None = None) -> dict:
    """テンプレートで使える値。入力JSONのキーはすべてそのまま使え、さらに *_link 等を追加する。"""
    v = {}
    for k, val in run.items():
        if k in ("failures",):
            continue
        if k == "summary" and isinstance(val, dict):
            for sk, sv in val.items():
                v[f"summary_{sk}"] = sv
            continue
        v[k] = ", ".join(map(str, val)) if k == "condition_labels" and isinstance(val, list) else clip(val)
    v.update({k: clip(val) for k, val in f.items()})
    dpv = f.get("data_pattern_values")
    if isinstance(dpv, dict):  # {"dp_url": "https://..."} → 1行1変数
        v["data_pattern_values"] = clip([f"{k} = {val}" for k, val in dpv.items()])
    v.setdefault("status", "failed")
    if not v.get("pattern"):
        v["pattern"] = v.get("condition_labels", "")
    if not v.get("started_at"):
        v["started_at"] = clip(run.get("started_at"))
    v["key"] = issue_key(project, f, modes)
    v["run_id"] = run_id(project, f, run)
    tc_label = f"#{f['test_case_number']} {f.get('test_case_name', '')}".strip()
    v["test_case_link"] = link(tc_label, f.get("test_case_url", ""), fmt)
    v["test_run_link"] = link(f"#{f.get('test_run_number', '')}", f.get("test_run_url", ""), fmt)
    v["batch_run_link"] = link(f"#{run.get('batch_run_number', '')}", run.get("batch_run_url", ""), fmt)
    v.setdefault("test_case_name", f"テストケース #{f['test_case_number']}")
    return v


class Builder:
    def __init__(self, cfg: Config, tdirs: list[Path]):
        ext = "textile" if cfg.text_format == "textile" else "md"
        self.cfg = cfg
        self.paths = {
            "subject": find_file(tdirs, "subject.txt"),
            "description": find_file(tdirs, f"description.{ext}"),
            "note": find_file(tdirs, f"note.{ext}"),
        }
        self.tpl = {k: p.read_text(encoding="utf-8") for k, p in self.paths.items()}
        self.unknown: set[str] = set()

    def subject(self, values):
        body = render(self.tpl["subject"], values, self.unknown).strip().replace("\n", " ")
        # 重複判定キーは必ず先頭に付ける（テンプレートで消されないように）
        body = body.replace(values["key"], "").strip()
        return f"{values['key']} {body}"[:255]

    @staticmethod
    def _with_marker(body, values):
        # テンプレートが編集されても重複判定が壊れないよう、実行IDの行を必ず末尾に付ける
        if has_marker(body, values["run_id"]):
            return body
        return body.rstrip() + "\n\n" + run_marker(values["run_id"]) + "\n"

    def description(self, values):
        return self._with_marker(render(self.tpl["description"], values, self.unknown), values)

    def note(self, values):
        return self._with_marker(render(self.tpl["note"], values, self.unknown), values)

    def custom_fields(self, values):
        out = []
        for cf in self.cfg.custom_fields:
            if "id" not in cf:
                fail(f"custom_fields の要素に id がありません: {cf}")
            val = cf.get("value", "")
            if isinstance(val, str):
                val = render(val, values, self.unknown).strip()
            elif isinstance(val, list):
                val = [render(x, values, self.unknown).strip() if isinstance(x, str) else x for x in val]
            out.append({"id": cf["id"], "value": val})
        return out

    def issue(self, project_id, values):
        issue = {"project_id": project_id,
                 "subject": self.subject(values),
                 "description": self.description(values)}
        for k, v in self.cfg.fields.items():
            if v is not None:
                issue[k] = v
        cfs = self.custom_fields(values)
        if cfs:
            issue["custom_fields"] = cfs
        return issue

    def info(self):
        return {"templates": {k: str(p) for k, p in self.paths.items()},
                "config": str(self.cfg.config_path),
                **({"unknown_placeholders": sorted(self.unknown)} if self.unknown else {})}


def load_input(path: str):
    try:
        with open(path, encoding="utf-8") as fp:
            run = json.load(fp)
    except (OSError, json.JSONDecodeError) as e:
        fail(f"入力ファイルを読めません: {e}")
    if not run.get("project"):
        fail("入力JSONに project がありません")
    for i, f in enumerate(run.get("failures", [])):
        if "test_case_number" not in f:
            fail(f"failures[{i}] に test_case_number がありません")
    return run


# ---------------------------------------------------------------- commands
def cmd_check(rm: Redmine, cfg: Config, b: Builder):
    try:
        user = rm.get("/users/current.json").get("user", {})
        proj = rm.get(f"/projects/{urllib.parse.quote(str(cfg.project_id))}.json").get("project", {})
    except RuntimeError as e:
        fail(str(e))
    print(json.dumps({
        "ok": True,
        "user": user.get("login"),
        "project": {"id": proj.get("id"), "identifier": proj.get("identifier"), "name": proj.get("name")},
        "text_format": cfg.text_format,
        "fields": {k: v for k, v in cfg.fields.items() if v is not None},
        **b.info(),
        **({"warnings": cfg.warnings()} if cfg.warnings() else {}),
    }, ensure_ascii=False, indent=2))


def cmd_meta(rm: Redmine, cfg: Config):
    out = {}
    pid = urllib.parse.quote(str(cfg.project_id))
    for key, path, pick in [
        ("trackers", "/trackers.json", "trackers"),
        ("issue_statuses", "/issue_statuses.json", "issue_statuses"),
        ("priorities", "/enumerations/issue_priorities.json", "issue_priorities"),
        ("categories", f"/projects/{pid}/issue_categories.json", "issue_categories"),
        ("members", f"/projects/{pid}/memberships.json", "memberships"),
        ("custom_fields", "/custom_fields.json", "custom_fields"),
    ]:
        try:
            items = rm.get(path).get(pick, [])
        except RuntimeError as e:
            out[key] = {"error": str(e) + (" ※カスタムフィールド一覧は管理者のAPIキーが必要" if key == "custom_fields" else "")}
            continue
        if key == "members":
            items = [m.get("user") or m.get("group") for m in items]
        if key == "custom_fields":
            items = [c for c in items if c.get("customized_type") == "issue"]
            out[key] = [{"id": c["id"], "name": c.get("name"), "format": c.get("field_format"),
                         "required": c.get("is_required", False),
                         **({"values": [pv.get("value") for pv in c.get("possible_values", [])]}
                            if c.get("possible_values") else {})} for c in items]
            continue
        out[key] = [{"id": i.get("id"), "name": i.get("name"),
                     **({"is_closed": i["is_closed"]} if "is_closed" in i else {})} for i in items if i]
    print(json.dumps({"ok": True, **out}, ensure_ascii=False, indent=2))


def cmd_set_mode(config_key: str, mode: str, target: str | None, tdirs: list[Path]):
    """config.json に pattern_mode / data_pattern_mode を保存する。利用者用の config.json があればそれを、なければ作って書き込む。"""
    if target:
        path = Path(target).expanduser() / "config.json"
    else:
        path = next((d / "config.json" for d in tdirs
                     if d != BUNDLED_TEMPLATES and (d / "config.json").is_file()),
                    Path(DEFAULT_USER_DIR) / "config.json")
    if path.resolve().parent == BUNDLED_TEMPLATES.resolve():
        fail("スキル同梱のテンプレートは書き換えません。--dir で保存先を指定してください")
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            fail(f"{path} のJSONが不正です: {e}")
    else:
        data = json.loads((BUNDLED_TEMPLATES / "config.json").read_text(encoding="utf-8"))
        path.parent.mkdir(parents=True, exist_ok=True)
    before = data.get(config_key)
    data[config_key] = mode
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out = {"ok": True, "config": str(path.resolve()), config_key: mode, "previous": before}
    if (before or MODE_KEYS[config_key]) != mode:
        out["note"] = ("扱いを変えたため、変更前に作ったチケットとは重複判定のキーが変わります。"
                       "未完了の旧チケットは自動では閉じないので、必要に応じて手動で完了にしてください。")
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_init(target: str, force: bool):
    dst = Path(target).expanduser()
    dst.mkdir(parents=True, exist_ok=True)
    copied, skipped = [], []
    for src in sorted(BUNDLED_TEMPLATES.iterdir()):
        if not src.is_file():
            continue
        to = dst / src.name
        if to.exists() and not force:
            skipped.append(str(to))
            continue
        shutil.copy2(src, to)
        copied.append(str(to))
    print(json.dumps({"ok": True, "dir": str(dst.resolve()), "copied": copied,
                      "skipped_existing": skipped}, ensure_ascii=False, indent=2))


def cmd_preview(cfg: Config, b: Builder, input_path: str, limit: int, modes: dict):
    run = load_input(input_path)
    project = run["project"]
    previews = []
    for f in run.get("failures", [])[:limit]:
        values = build_values(run, f, project, cfg.text_format, modes)
        previews.append({"issue": b.issue(cfg.project_id or "(REDMINE_PROJECT_ID)", values),
                         "note_when_existing": b.note(values)})
    print(json.dumps({"ok": True, "count": len(run.get("failures", [])),
                      "text_format": cfg.text_format,
                      "previews": previews, **b.info(),
                      **pattern_mode_info(cfg, run.get("failures", []), modes),
                      **({"warnings": cfg.warnings()} if cfg.warnings() else {})},
                     ensure_ascii=False, indent=2))


def _key_of(subject: str) -> str | None:
    if subject.startswith("[MagicPod:") and "]" in subject:
        return subject.split("]", 1)[0] + "]"
    return None


def cmd_sync(rm: Redmine, cfg: Config, b: Builder, input_path: str, dry_run: bool, always_create: bool,
             modes: dict):
    run = load_input(input_path)
    project = run["project"]
    failures = run.get("failures", [])
    warnings = list(cfg.warnings())

    open_by_key, closed_by_key = {}, {}
    if failures:
        base = {"project_id": cfg.project_id,
                # 件名で絞り込み（未対応の古いRedmineでも下のローカル判定で正しく動く）
                "subject": "~[MagicPod:", "sort": "id:desc"}
        try:
            if not always_create:
                for iss in rm.paged("/issues.json", "issues", {**base, "status_id": "open"}):
                    k = _key_of(iss.get("subject", ""))
                    if k:
                        open_by_key.setdefault(k, iss)   # 新しいチケットを優先
            for iss in rm.paged("/issues.json", "issues", {**base, "status_id": "closed"}):
                k = _key_of(iss.get("subject", ""))
                if k:
                    closed_by_key.setdefault(k, iss)
        except RuntimeError as e:
            fail(f"既存チケットの取得に失敗: {e}")

    issue_texts: dict = {}   # チケットID -> 本文＋注記（既に記録済みの実行IDを探すため）

    def recorded_text(issue_id):
        if issue_id not in issue_texts:
            data = rm.get(f"/issues/{issue_id}.json", {"include": "journals"}).get("issue", {})
            issue_texts[issue_id] = "\n".join(
                [data.get("description") or ""] + [j.get("notes") or "" for j in data.get("journals", [])])
        return issue_texts[issue_id]

    handled_runs = set()
    created_keys = set()   # この実行で新規作成（予定）したチケットのキー
    # 今回の入力で使うキー。これに一致する既存チケットは「今回の連携先」なので孤立扱いしない
    current_keys = {issue_key(project, f, modes) for f in failures}
    results = []

    def other_open_tickets(key, tc):
        """同じテストケースで、キーの付け方だけが違う未完了チケット（設定変更前のチケットなど）。"""
        base = base_key(project, tc)
        return [{"id": iss.get("id"), "key": k, "subject": iss.get("subject"),
                 "url": f"{cfg.url}/issues/{iss.get('id')}"}
                for k, iss in open_by_key.items()
                if k not in current_keys and k not in created_keys and not iss.get("_pending") and same_test_case(k, base)]

    for f in failures:
        values = build_values(run, f, project, cfg.text_format, modes)
        key, rid = values["key"], values["run_id"]
        hit = open_by_key.get(key)
        entry = {"key": key, "run_id": rid, "test_case_number": f["test_case_number"],
                 "test_case_name": f.get("test_case_name"), "pattern": values.get("pattern") or None}
        try:
            if rid in handled_runs:
                entry.update(action="skip", reason="入力JSON内で同じテスト実行が重複しています")
            elif hit and hit.get("_pending"):
                # dry-run で、この実行中に新規作成する予定のチケットへの注記
                entry.update(action="update", issue_id=None, subject=hit["subject"],
                             note="この実行で新規作成する予定のチケットに追記します")
            elif hit:
                entry.update(issue_id=hit["id"], subject=hit.get("subject"))
                if has_marker(recorded_text(hit["id"]), rid):
                    entry.update(action="skip", reason="このテスト実行の結果は記録済みです")
                else:
                    entry["action"] = "update"
                    note = b.note(values)
                    if not dry_run:
                        rm.request("PUT", f"/issues/{hit['id']}.json", body={"issue": {"notes": note}})
                    issue_texts[hit["id"]] = recorded_text(hit["id"]) + "\n" + note
            else:
                issue = b.issue(cfg.project_id, values)
                entry.update(action="create", subject=issue["subject"])
                others = [] if always_create else other_open_tickets(key, f["test_case_number"])
                if others:
                    entry["other_open_tickets"] = others
                created_keys.add(key)
                prev = closed_by_key.get(key)
                if prev:
                    entry["related_to"] = prev["id"]
                if dry_run:
                    open_by_key[key] = {"_pending": True, "subject": issue["subject"]}
                else:
                    created = rm.request("POST", "/issues.json", body={"issue": issue}).get("issue", {})
                    entry["issue_id"] = created.get("id")
                    open_by_key[key] = {"id": entry["issue_id"], "subject": issue["subject"]}
                    issue_texts[entry["issue_id"]] = issue["description"]
                    if prev and entry["issue_id"]:
                        try:  # 過去に完了したチケットと「関連する」で紐付け（再発が分かるように）
                            rm.request("POST", f"/issues/{entry['issue_id']}/relations.json",
                                       body={"relation": {"issue_to_id": prev["id"], "relation_type": "relates"}})
                        except RuntimeError as e:
                            entry["warning"] = (f"完了済みチケット #{prev['id']} との関連付けに失敗しました"
                                                f"（「関連するチケットの管理」権限が必要です）: {e}")
            if entry.get("issue_id"):
                entry["url"] = f"{cfg.url}/issues/{entry['issue_id']}"
            if entry.get("related_to"):
                entry["related_url"] = f"{cfg.url}/issues/{entry['related_to']}"
            entry["ok"] = True
            if entry["action"] != "skip":
                handled_runs.add(rid)
        except RuntimeError as e:
            entry.update(ok=False, error=str(e))
        results.append(entry)

    ok_results = [r for r in results if r["ok"]]
    orphan_ids = sorted({o["id"] for r in results for o in r.get("other_open_tickets", [])})
    if orphan_ids:
        warnings.append(
            "同じテストケースの未完了チケットが、キーの付け方が違うため一致しませんでした: "
            + ", ".join(f"#{i}" for i in orphan_ids)
            + "（データ駆動化や pattern_mode / data_pattern_mode の変更前に作られたチケットの可能性）。"
              "このまま新規起票すると同じテストのチケットが複数になるので、利用者に扱いを確認してください。")
    summary = {
        "ok": len(ok_results) == len(results),
        "dry_run": dry_run,
        "batch_run_number": run.get("batch_run_number"),
        "batch_run_url": run.get("batch_run_url"),
        "text_format": cfg.text_format,
        "created": sum(1 for r in ok_results if r["action"] == "create"),
        "updated": sum(1 for r in ok_results if r["action"] == "update"),
        "skipped": sum(1 for r in ok_results if r["action"] == "skip"),
        "errors": len(results) - len(ok_results),
        "results": results,
        **b.info(),
        **pattern_mode_info(cfg, failures, modes),
        **({"warnings": warnings} if warnings else {}),
    }
    if dry_run and failures:
        summary["preview_description"] = b.description(build_values(run, failures[0], project, cfg.text_format, modes))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    sys.exit(0 if summary["ok"] else 2)


def main():
    p = argparse.ArgumentParser(description="MagicPod の失敗を Redmine に連携")
    p.add_argument("--template-dir", help="テンプレートのフォルダ（既定: ./.magicpod-redmine → ~/.config/magicpod-redmine → 同梱）")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="接続確認")
    sub.add_parser("meta", help="トラッカー等のID一覧")
    i = sub.add_parser("init", help="カスタマイズ用テンプレートをコピー")
    i.add_argument("--dir", default=DEFAULT_USER_DIR, help=f"コピー先（既定: ./{DEFAULT_USER_DIR}）")
    i.add_argument("--force", action="store_true", help="既存ファイルを上書き")
    pv = sub.add_parser("preview", help="Redmineに接続せずチケット内容を表示")
    pv.add_argument("--input", required=True)
    pv.add_argument("--limit", type=int, default=1, help="表示する件数（既定1）")
    pv.add_argument("--pattern-mode", choices=PATTERN_MODES, help="config.json の pattern_mode をこの回だけ上書き")
    pv.add_argument("--data-pattern-mode", choices=PATTERN_MODES, help="config.json の data_pattern_mode をこの回だけ上書き")
    s = sub.add_parser("sync", help="失敗をチケット化")
    s.add_argument("--input", required=True, help="failures.json のパス")
    s.add_argument("--dry-run", action="store_true", help="書き込まずに結果を表示")
    s.add_argument("--always-create", action="store_true",
                   help="既存の未完了チケットを無視して新規起票（同じ実行内で同じキーの2件目以降は、作ったチケットに追記）")
    s.add_argument("--pattern-mode", choices=PATTERN_MODES, help="config.json の pattern_mode をこの回だけ上書き")
    s.add_argument("--data-pattern-mode", choices=PATTERN_MODES, help="config.json の data_pattern_mode をこの回だけ上書き")
    for cmd, label in (("set-pattern-mode", "実行パターン（ブラウザ・端末）"), ("set-data-pattern-mode", "データパターン")):
        pm = sub.add_parser(cmd, help=f"複数の{label}で失敗したときの扱いを config.json に保存")
        pm.add_argument("mode", choices=PATTERN_MODES, help="merge: 1件にまとめて注記で追記 / split: パターンごとに別チケット")
        pm.add_argument("--dir", help=f"保存先のテンプレートフォルダ（既定: 既存の利用者用 config.json、なければ ./{DEFAULT_USER_DIR}）")
    a = p.parse_args()

    if a.cmd == "init":
        return cmd_init(a.dir, a.force)

    tdirs = template_dirs(a.template_dir)
    if a.cmd in ("set-pattern-mode", "set-data-pattern-mode"):
        return cmd_set_mode(a.cmd[4:].replace("-", "_"), a.mode, a.dir, tdirs)
    cfg = Config(tdirs)
    b = Builder(cfg, tdirs)
    modes = {"pattern_mode": getattr(a, "pattern_mode", None) or cfg.modes["pattern_mode"],
             "data_pattern_mode": getattr(a, "data_pattern_mode", None) or cfg.modes["data_pattern_mode"]}
    if a.cmd == "preview":
        return cmd_preview(cfg, b, a.input, a.limit, modes)
    cfg.require()
    rm = Redmine(cfg)
    if a.cmd == "check":
        cmd_check(rm, cfg, b)
    elif a.cmd == "meta":
        cmd_meta(rm, cfg)
    else:
        cmd_sync(rm, cfg, b, a.input, a.dry_run, a.always_create, modes)


if __name__ == "__main__":
    main()
