# MagicPod Agent Skills

MagicPod 公式の [Agent Skills](https://agentskills.io/) です。
[MagicPod MCP Server](https://support.magic-pod.com/hc/articles/46186888063769) と組み合わせて、Claude Code などの AI エージェントから MagicPod のテスト作成を進められます。

## 含まれるスキル

| スキル | できること |
|---|---|
| `magicpod-smoke` | アプリの核心機能を確かめるスモークテストを対話的に設計し、MagicPod にテストケースとして登録します |

## 前提

- MagicPod のアカウント
- MagicPod MCP Server のセットアップ（手順は次のヘルプページを参照）

https://support.magic-pod.com/hc/articles/46186888063769

## インストール

### Claude Code

```
/plugin marketplace add Magic-Pod/skills
/plugin install magicpod@magicpod
```

### その他のエージェント（Cursor、Codex など）

```bash
npx skills add Magic-Pod/skills
```

## 使い方

インストール後、AI エージェントに次のように頼んでください。

```
このアプリのスモークテストを MagicPod に作って
```

## 更新

Claude Code では、`/plugin` の画面からマーケットプレイスを更新すると最新版が入ります。

## お問い合わせ

このリポジトリでは Issue を受け付けていません。ご質問・ご要望は MagicPod サポートまでお問い合わせください。

https://support.magic-pod.com/

## ライセンス

[MIT](LICENSE)
