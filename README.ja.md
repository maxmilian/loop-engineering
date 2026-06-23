<!-- LANG-SWITCH --> [English](README.md) · [繁體中文](README.zh-TW.md) · [简体中文](README.zh-CN.md) · **日本語** · [한국어](README.ko.md)

# Loop Engineering — 自律型 agent loop の設計・レビュー用 skill

Loop engineering は、prompt engineering の次にくる規律です。prompt が単一のインタラクションを最適化するのに対し、**loop** はそれを取り巻く自律的な振る舞い全体を最適化します — agent が *いつ* 動くか、*何が* それをトリガーするか、*どのように* 自分の成果を検証するか、*いつ* 止まるか、*いつ* 人間に戻すか。

この skill は、coding agent に実戦で鍛えられたフレームワークを提供し、次の2つの用途に対応します:

- **Design mode** — 新しい自己実行型 agent / loop / バックグラウンドワーカーを構築する。
- **Review mode** — 既存の loop の停止条件・guardrail・verification・escalation パスを監査する。

Anthropic の context engineering ガイダンス、Ralph loop / RPI メソドロジー、Claude Code の agent-loop ドキュメント、2026年の「loop engineering」に関する文書など、12のソースを7つの核心原則と参考資料に凝縮しています。

> 意図的にトリッキーなケースを使ったベンチマークテストで、skill なしのベースラインと比較したところ、合格率が 87% → 100% に向上し、より一貫した低コストな回答を生成しました — その強みは、強力なモデルでも見落としがちな細かい失敗パターン（cron の stale-prompt ドリフト、無駄な blind-retry、取り消し不可能なアクションに対する human-gate の欠如）で発揮されます。

## 7つの原則（TL;DR）

1. **レバレッジは prompt から loop へ移った** — 一つの巨大 prompt ではなく、control flow を設計する。
2. **「完了」は機械的に検証可能でなければならない** — `tests pass` ✓、`improve the code` ✗。
3. **検証は決定論的ツールで行う。agent の自己申告に頼らない。**
4. **稼働前にすべての終了条件を定義する** — 成功・失敗・budget 終了、no-progress 検知、escalation パス。
5. **context は有限リソースとして扱う** — ツール出力をトリミングし、compaction・メモ書き・sub-agent を活用する。
6. **ファイルシステムをメモリとして使い、各サイクルは新鮮な context からスタートする。**
7. **難所は verification・停止・escalation であり、自律性ではない。** *semi-autonomous* を優先: 取り消し不可能・外部向けのアクションは人間の確認を挟む。

## 構成

```
loop-engineering/
├── SKILL.md                          # the skill itself (frontmatter + instructions)
└── references/
    ├── loop-patterns.md              # heartbeat / cron / hook / goal + Ralph loop
    ├── context-engineering.md        # compaction, note-taking, sub-agents, JIT retrieval
    ├── review-checklist.md           # per-principle diagnostic, severity-ordered
    └── sources.md                    # the 12 source articles, with one-line summaries
```

skill とは `SKILL.md`（YAML frontmatter + Markdown）を含むフォルダに過ぎません。その可搬性ゆえに、ほぼどこにでもインストールできます。

## インストール

### Claude Code
個人用（全プロジェクト共通）またはプロジェクト単位 — `skills/` ディレクトリにフォルダをコピーします:

```bash
# personal
git clone <this-repo> ~/.claude/skills/loop-engineering
# or project-scoped
git clone <this-repo> .claude/skills/loop-engineering
```

新しいセッションを開始すると、Claude が `description` から自動検出し、agent loop の設計またはレビュー時に自動的に呼び出します。（ビルド済み `.skill` バンドル: plugin/skill マネージャーを使っている場合はそこからインストールしてください。）

### Codex
Codex はスキルディレクトリから skill をネイティブに読み込みます。フォルダをここに配置します:

```bash
git clone <this-repo> ~/.codex/skills/loop-engineering
```

Codex の設定が `AGENTS.md` を参照する場合は、以下のようなポインター行を追加します:
`For designing or reviewing autonomous agent loops, follow skills/loop-engineering/SKILL.md.`

### GitHub Copilot CLI
Copilot はインストール済みプラグインから skill を自動検出します。Copilot の skills/plugins ディレクトリ（例: `~/.copilot/skills/loop-engineering`）にフォルダを配置し、CLI を再起動してください。

### Gemini CLI
Gemini は skill メカニズム経由で skill を有効化します。Gemini の skills ディレクトリ（例: `~/.gemini/skills/loop-engineering`）にフォルダを配置すると、Gemini がセッション開始時にメタデータを読み込み、必要に応じて全コンテンツを有効化します。`GEMINI.md` 経由で Gemini を操作する場合は、`skills/loop-engineering/SKILL.md` へのポインター行を追加してください。

### Cursor / Windsurf / instructions ファイルを持つ任意の agent
これらには正式な skill ローダーがありませんが、コンテンツはそのまま使えます。rules/instructions ファイル（`.cursorrules`、`AGENTS.md` など）から参照してください:

```
When building or reviewing an autonomous/semi-autonomous agent loop, background
worker, or cron/webhook-driven agent, follow the framework in
skills/loop-engineering/SKILL.md (and its references/ files).
```

### 最小構成（共通分母）
どんな LLM ツールでも: loop の設計またはレビュー時に `SKILL.md` を context にペーストし、skill が参照している場合は `references/*.md` のファイルも取り込んでください。

## 使い方

明示的に呼び出す必要はありません — タスクを説明すれば agent が自動的に判断します:

- *「CI を夜通し監視して、失敗した PR を自動修正する agent が欲しい。」* → design mode
- *「このバックグラウンドワーカーをより多くのキューにスケールする前にレビューしてほしい。」* → review mode
- *「私の research agent がトークンを消費し続けて、いつまでも終わらない。」* → diagnosis

## SKILL.md の description について

SKILL.md の description フィールドおよび skill 本文は**英語のまま**にしてください。これらはモデルが処理するメタデータであり、翻訳すると自動検出や呼び出しトリガーの精度が下がります。README のような人間が読むドキュメントのみ多言語化の対象です。

## ライセンス / 出典

loop engineering、agent loops、context engineering に関する公開文書を凝縮したものです — 全ソースリストとリンクは `references/sources.md` を参照してください。
