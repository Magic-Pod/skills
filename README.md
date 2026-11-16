# MagicPod Agent Skills

[English](#english) | [日本語](#日本語)

---

## English

Official [Agent Skills](https://agentskills.io/) for MagicPod.
Use them with the [MagicPod MCP Server](https://support.magic-pod.com/hc/en-us/articles/46186888063769) to create MagicPod tests from AI agents such as Claude Code.

### Skills

| Skill | What it does |
|---|---|
| `magicpod-smoke` | Designs smoke tests for the core features of your app through a short conversation, creates them as test cases in MagicPod, and checks that they run |
| `magicpod-test-review` | Reviews your test cases against 10 criteria (purpose, stability, readability, and maintainability) and writes a report. If you want, it fixes the findings in a new branch |

### Requirements

- A MagicPod account
- MagicPod MCP Server set up

References:

- [MagicPod MCP Server](https://support.magic-pod.com/hc/en-us/articles/46186888063769)
- [Setting Up MagicPod MCP Server](https://support.magic-pod.com/hc/en-us/articles/62605396709273)

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

New skills and updates are not always added to your AI agent automatically. If a skill in the list above is not available, update with the steps below, then start a new conversation (session).

#### Claude Code

```bash
claude plugin marketplace update magicpod
claude plugin update magicpod-skills@magicpod
```

Then restart Claude Code.

To get updates automatically, turn on auto-update for the `magicpod` marketplace in the **Marketplaces** tab of `/plugin`.

#### Claude Desktop / Web (Chat, Cowork)

In **Customize > Plugins**, open the "…" menu of the "MagicPod Skills" plugin and choose **Check for updates**.

#### Other agents (Cursor, Codex, etc.)

```bash
npx skills update
```

To only check whether updates are available, run `npx skills check`.

If you added the skills by asking your AI agent, ask it again, for example: "Install the latest skills from Magic-Pod/skills". If the new skill does not appear, restart the app.

#### Tip: update on a schedule

If your AI agent can run scheduled tasks, add a task like "Every Monday, check Magic-Pod/skills and add or update the skills". You will always have the latest skills.

### Contact

This repository does not accept issues. For questions or requests, please use the [MagicPod contact form](https://magicpod.com/en/contact/).

### License

[MIT](LICENSE)

---

## 日本語

MagicPod 公式の [Agent Skills](https://agentskills.io/) です。
[MagicPod MCP Server](https://support.magic-pod.com/hc/ja/articles/46186888063769) と組み合わせて、Claude Code などの AI エージェントから MagicPod のテスト作成を進められます。

### 含まれるスキル

| スキル | できること |
|---|---|
| `magicpod-smoke` | アプリの核心機能を確かめるスモークテストを対話的に設計し、MagicPod にテストケースとして作成して動作確認します |
| `magicpod-test-review` | テストケースを10の観点（目的・安定性・可読性・メンテナンス性）でレビューし、レポートにまとめます。希望すれば、指摘の修正を新しいブランチ上で行います |

### 前提

- MagicPod のアカウント
- MagicPod MCP Server のセットアップ

参考：

- [MagicPod MCPサーバー](https://support.magic-pod.com/hc/ja/articles/46186888063769)
- [MagicPod MCPサーバーのセットアップ手順](https://support.magic-pod.com/hc/ja/articles/62605396709273)

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

スキルの追加や更新は、AI エージェントに自動で反映されないことがあります。上の一覧にあるスキルが使えない場合は、次の手順で更新してから、新しい会話（セッション）を始めてください。

#### Claude Code

```bash
claude plugin marketplace update magicpod
claude plugin update magicpod-skills@magicpod
```

続けて Claude Code を再起動します。

自動で更新したい場合は、`/plugin` の **Marketplaces** タブで `magicpod` マーケットプレイスの自動更新をオンにしてください。

#### Claude Desktop / Web（チャット・Cowork）

**カスタマイズ > プラグイン** で「MagicPod Skills」プラグインの「…」メニューを開き、**アップデートを確認** を選びます。

#### その他のエージェント（Cursor、Codex など）

```bash
npx skills update
```

更新があるかだけ確認したい場合は `npx skills check` を実行します。

AI エージェントに頼んでスキルを入れた場合は、「Magic-Pod/skills から最新のスキルを入れて」のように、もう一度頼んでください。新しいスキルが表示されない場合は、アプリを再起動します。

#### ヒント：定期的に更新する

AI エージェントに定期実行の機能がある場合は、「毎週月曜に Magic-Pod/skills を確認して、スキルを追加・更新する」といったタスクを登録しておくと、常に最新のスキルを使えます。

### お問い合わせ

このリポジトリでは Issue を受け付けていません。ご質問・ご要望は [MagicPod お問い合わせフォーム](https://magicpod.com/contact/) からお問い合わせください。

### ライセンス

[MIT](LICENSE)
