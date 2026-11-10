# MagicPod Agent Skills

[English](#english) | [日本語](#日本語)

---

## English

Official [Agent Skills](https://agentskills.io/) for MagicPod.
Use them with the [MagicPod MCP Server](https://support.magic-pod.com/hc/en-us/articles/46186888063769) to create MagicPod tests from AI agents such as Claude Code.

### Skills

| Skill | What it does |
|---|---|
| `magicpod-smoke` | Designs smoke tests for the core features of your app through a short conversation, and registers them as test cases in MagicPod |

### Requirements

- A MagicPod account
- MagicPod MCP Server set up (see the help page below)

https://support.magic-pod.com/hc/en-us/articles/46186888063769

### Install

#### Claude Code

```
/plugin marketplace add Magic-Pod/skills
/plugin install magicpod-skills@magicpod
```

#### Claude Desktop / Web (Chat, Cowork)

1. Go to **Customize > Plugins**, choose to add a marketplace, and enter `Magic-Pod/skills`
2. Install the "MagicPod Skills" plugin
3. If you have not connected the MagicPod MCP Server yet, search for "MagicPod" in **Customize > Connectors** and connect it (on Team / Enterprise plans, an organization owner needs to add the connector first)

Skills require a paid Claude plan.

#### Other agents (Cursor, Codex, etc.)

```bash
npx skills add Magic-Pod/skills
```

### Usage

After installing, ask your AI agent something like:

```
Create smoke tests for this app in MagicPod
```

### Update

In Claude Code, update the marketplace from the `/plugin` screen to get the latest version.

### Contact

This repository does not accept issues. For questions or requests, please contact MagicPod support.

https://support.magic-pod.com/

### License

[MIT](LICENSE)

---

## 日本語

MagicPod 公式の [Agent Skills](https://agentskills.io/) です。
[MagicPod MCP Server](https://support.magic-pod.com/hc/ja/articles/46186888063769) と組み合わせて、Claude Code などの AI エージェントから MagicPod のテスト作成を進められます。

### 含まれるスキル

| スキル | できること |
|---|---|
| `magicpod-smoke` | アプリの核心機能を確かめるスモークテストを対話的に設計し、MagicPod にテストケースとして登録します |

### 前提

- MagicPod のアカウント
- MagicPod MCP Server のセットアップ（手順は次のヘルプページを参照）

https://support.magic-pod.com/hc/ja/articles/46186888063769

### インストール

#### Claude Code

```
/plugin marketplace add Magic-Pod/skills
/plugin install magicpod-skills@magicpod
```

#### Claude Desktop / Web（チャット・Cowork）

1. **カスタマイズ > プラグイン** から追加を選び、マーケットプレイスとして `Magic-Pod/skills` を追加します
2. 表示された「MagicPod Skills」プラグインをインストールします
3. MagicPod MCP Server をまだ接続していない場合は、**カスタマイズ > コネクタ** で「MagicPod」を検索して接続します（Team / Enterprise プランでは、先に組織のオーナーがコネクタを追加する必要があります）

スキルの利用には Claude の有料プランが必要です。

#### その他のエージェント（Cursor、Codex など）

```bash
npx skills add Magic-Pod/skills
```

### 使い方

インストール後、AI エージェントに次のように頼んでください。

```
このアプリのスモークテストを MagicPod に作って
```

### 更新

Claude Code では、`/plugin` の画面からマーケットプレイスを更新すると最新版が入ります。

### お問い合わせ

このリポジトリでは Issue を受け付けていません。ご質問・ご要望は MagicPod サポートまでお問い合わせください。

https://support.magic-pod.com/

### ライセンス

[MIT](LICENSE)
