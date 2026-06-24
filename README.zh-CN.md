[English](README.md) · [繁體中文](README.zh-TW.md) · **简体中文** · [日本語](README.ja.md) · [한국어](README.ko.md)

# Loop Engineering — 用于设计与审查自主 agent loop 的 skill

![Loop Engineering — 设计与审查 agent 自走的 loop：trigger、check、act、verify，含 success/failure/budget exit 与 human gate](assets/hero.png)

Loop engineering 是 prompt engineering 之后的下一门学科。prompt 优化的是单次交互；**loop** 优化的是围绕它的自主行为——*何时*运行 agent、*什么*触发它、*如何*验证自身工作、*何时*停止，以及*何时*交还给人类。

本 skill 为编程 agent 提供一套经过实战检验的框架，用于两种场景：

- **Design mode** — 构建一个新的自运行 agent / loop / 后台 worker。
- **Review mode** — 审计现有 loop 的停止条件、guardrail、verification 与 escalation 路径。

它将 12 个来源（Anthropic 的 context engineering 指南、Ralph loop / RPI 方法论、Claude Code 的 agent-loop 文档，以及 2026 年的"loop engineering"论述）提炼为七条核心原则及参考资料。

**快速开始（Claude Code）：**

```bash
git clone https://github.com/maxmilian/loop-engineering ~/.claude/skills/loop-engineering
```

开启一个新会话即可。（其他工具见 [安装](#安装)。）

> 在与无 skill 基线对比的 benchmark 测试中（特意使用了棘手案例），本 skill 将通过率从 87% 提升至 100%，同时输出更一致、成本更低——其优势体现在强模型通常会遗漏的细微失效模式上（cron stale-prompt 漂移、盲目重试浪费、不可逆操作缺少人工 gate）。[复现它 →](#复现-benchmark)
>
> 在**较弱的模型（Haiku 级）**上，提升更大——8 案子集 **+16 个百分点**（74% → 90%），这正是“覆盖保证”最关键的场景。

## 七条原则（TL;DR）

1. **杠杆从 prompt 转移到 loop** — 设计控制流，而非一个超大 prompt。
2. **"完成"必须是机器可验证的** — `tests pass` ✓，`improve the code` ✗。
3. **用确定性工具验证，永远不要依赖 agent 的自我报告。**
4. **上线前定义所有退出条件** — 成功 / 失败 / budget 退出、no-progress 检测、escalation 路径。
5. **将 context 视为有限资源** — 裁剪工具输出；使用 compaction、笔记、sub-agent。
6. **用文件系统作为记忆；每个周期以全新 context 开始。**
7. **难点在于 verification、停止与 escalation——而非自主性本身。** 优先采用*半自主*方式：将不可逆或对外的动作置于人工 gate 之后。

## 目录结构

```
loop-engineering/
├── SKILL.md                          # the skill itself (frontmatter + instructions)
├── references/
│   ├── loop-patterns.md              # heartbeat / cron / hook / goal + Ralph loop
│   ├── context-engineering.md        # compaction, note-taking, sub-agents, JIT retrieval
│   ├── review-checklist.md           # per-principle diagnostic, severity-ordered
│   └── sources.md                    # the 12 source articles, with one-line summaries
├── evals/                            # 验证案例库 + benchmark 证据
│   ├── evals.json                    # 11 个评分过的 design / review / diagnose 案例
│   ├── RESULTS.md                    # 有 skill vs 无 skill 结果，3 个 iteration
│   └── files/                        # review 案例指向的输入脚本
└── assets/                           # README hero 图
```

skill 本质上是一个包含 `SKILL.md`（YAML frontmatter + Markdown）的文件夹。这种可移植性使其几乎可以安装在任何地方。

## 安装

### Claude Code
个人（所有项目）或项目范围——将文件夹复制到 `skills/` 目录：

```bash
# 个人
git clone https://github.com/maxmilian/loop-engineering ~/.claude/skills/loop-engineering
# 或项目范围
git clone https://github.com/maxmilian/loop-engineering .claude/skills/loop-engineering
```

开启新会话；Claude 会从 description 自动发现它，并在你设计或审查 agent loop 时调用。（预构建的 `.skill` 包：如果你使用 plugin/skill 管理器，可通过其安装。）

### Codex
Codex 从其 skills 目录原生加载 skill。将文件夹放入：

```bash
git clone https://github.com/maxmilian/loop-engineering ~/.codex/skills/loop-engineering
```

如果你的 Codex 配置以 `AGENTS.md` 为入口，请添加如下指针行：
`For designing or reviewing autonomous agent loops, follow skills/loop-engineering/SKILL.md.`

### GitHub Copilot CLI
Copilot 从已安装的插件自动发现 skill。将文件夹放在你的 Copilot skills/plugins 目录下（例如 `~/.copilot/skills/loop-engineering`），然后重启 CLI。

### Gemini CLI
Gemini 通过其 skill 机制激活 skill。将文件夹放在你的 Gemini skills 目录下（例如 `~/.gemini/skills/loop-engineering`）；Gemini 在会话开始时加载元数据，并按需激活完整内容。如果你通过 `GEMINI.md` 驱动 Gemini，请在其中添加指向 `skills/loop-engineering/SKILL.md` 的指针行。

### Cursor / Windsurf / 任何支持 instructions 文件的 agent
这些工具没有正式的 skill 加载器，但内容可以直接使用。在你的 rules/instructions 文件（`.cursorrules`、`AGENTS.md` 等）中引用它：

```
When building or reviewing an autonomous/semi-autonomous agent loop, background
worker, or cron/webhook-driven agent, follow the framework in
skills/loop-engineering/SKILL.md (and its references/ files).
```

### 最低公分母方案
任何 LLM 工具：在设计或审查 loop 时，将 `SKILL.md` 粘贴到 context 中，并在 skill 指向时拉入相应的 `references/*.md` 文件。

## 使用方式

无需显式调用——描述任务，agent 会自动识别：

- *"我想要一个 agent，整晚监视 CI 并自动修复失败的 PR。"* → design mode
- *"在我们将这个后台 worker 扩展到更多队列之前，帮我 review 一下。"* → review mode
- *"我的 research agent 一直在消耗 token，却从未完成任务。"* → 诊断模式

## 复现 benchmark

上面的数字不是空谈——held-out 案例就在本 repo 里，你可以自己重跑；完整的逐 iteration 结果（含一段诚实说明 skill 在哪些地方*没有*帮助）都在 [`evals/RESULTS.md`](evals/RESULTS.md)。

- **案例集**位于 [`evals/evals.json`](evals/evals.json)：11 个特意设计的棘手案例，横跨全部四种 loop pattern（heartbeat / cron / hook / goal）外加 long-horizon context，覆盖 **design**、**review**、**diagnose** 三种模式——从 CI/PR-fixer 设计、有缺陷的客服 ticket bot（代码在 [`evals/files/`](evals/files/)），到失控的研究 loop。每个案例都附带一份 `expected_output` 评分准则，列出正确答案必须命中的具体要点（machine-checkable 的 done 条件、所有 exit 都带真实数字、确定性验证、不可逆操作的 human-gate 等）。87% → 100% 这个头条数字来自其中"细微 / 规格不足"的子集；逐 iteration 的细项见 [`evals/RESULTS.md`](evals/RESULTS.md)。

**方法（与头条数字相同）：**

1. 每个案例把 `prompt` 跑**两次**——一次装好 skill（上面的控制流程），一次干净的 baseline 无 skill——各跑多次以平均掉方差。
2. 每次结果都对照其 `expected_output` 准则评分（由 LLM 对照所列断言评分；准则项均写成可客观检查）。
3. 把每个配置的逐断言通过率汇总后比较。

头条数字中的通过率 / 方差 / token 汇总是用 Anthropic 的 `skill-creator` benchmark harness（`grader` + `aggregate_benchmark`）跑的，但任何"有 skill / 无 skill"对照、依准则评分，都会浮现同样的差距。Skill 的优势集中在细微的失效模式——stale-prompt 漂移、盲目重试浪费、缺少 human-gate——这些是强模型放任默认时会跳过的地方。

## 参与贡献

非常欢迎贡献——新的实战示例、额外的 loop pattern、更锐利的 review 判据、翻译,或修复。提 issue 或 PR 都可以。

**明确欢迎使用 AI 协助贡献。** 这是一个*关于* agentic loop 的 skill,所以用 Claude Code / Codex / Copilot / Gemini(或任何 coding agent)来起草你的修改是鼓励的——正合主题。只要在提交前 review 一下 agent 的产出:确认正确、有主张处有真实来源佐证(见 `references/sources.md`)、并且你愿意为它背书。拿这个 skill 来 dogfood 你自己的 PR 更是加分。


## License / 致谢

以 **MIT License** 发布——见 [`LICENSE`](LICENSE)。

提炼自关于 loop engineering、agent loop 与 context engineering 的公开文章——完整来源列表与链接见 `references/sources.md`。
