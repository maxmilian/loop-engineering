[English](README.md) · **繁體中文** · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

# Loop Engineering — 設計與審查自主 agent loop 的 skill

![Loop Engineering — 設計與審查 agent 自走的 loop：trigger、check、act、verify，含 success/failure/budget exit 與 human gate](assets/hero.png)

Loop engineering 是接在 prompt engineering 之後的工程學科。一個 prompt 優化的是「單次互動」;一個 **loop** 優化的是「圍繞它的自主行為」——agent 何時跑、什麼觸發它、怎麼驗證自己的成果、何時停、何時把球交回給人。

這個 skill 給 coding agent 一套實戰框架,做兩件事:

- **設計模式(Design mode)** — 從零打造一個自走的 agent / loop / 背景 worker。
- **審查模式(Review mode)** — 稽核既有 loop 的停手條件、護欄、驗證機制與升級路徑。

它把 12 篇來源(Anthropic 的 context engineering、Ralph loop / RPI 方法論、Claude Code 的 agent-loop 文件,以及 2026 年的「loop engineering」寫作)收斂成七條核心原則加參考資料。

**快速開始(Claude Code):**

```bash
git clone https://github.com/maxmilian/loop-engineering ~/.claude/skills/loop-engineering
```

開一個新 session 就好。(其他工具見 [安裝](#安裝)。)

> 在 benchmark 中對照「無 skill」的 baseline,於刻意設計的刁鑽案例上,這個 skill 把通過率從 87% 拉到 100%,同時答案更一致、更省 token——它的優勢出現在強模型原本會漏掉的隱晦失效模式(cron stale-prompt 腐壞、盲目重試浪費、不可逆動作缺人工閘)。[重現它 →](#重現-benchmark)
>
> 在**較弱的模型(Haiku 級)**上,增益更大——8 案子集 **+16 個百分點**(74% → 90%),這正是「覆蓋保證」最關鍵的場景。

## 七條核心原則(TL;DR)

1. **槓桿已從 prompt 移到 loop** — 設計控制流,而非一個巨型 prompt。
2. **「Done」必須機器可驗** — `tests pass` ✓、`improve the code` ✗。
3. **用確定性工具驗證,絕不靠 agent 自報。**
4. **上線前定義所有 exit** — success / failure / budget 三類 exit、no-progress 偵測、escalation 升級路徑。
5. **把 context 當有限資源** — 修剪工具輸出;用 compaction、note-taking、sub-agent。
6. **用檔案系統當記憶;每個 cycle 從 fresh context 開始。**
7. **難的不是自主,是 verification、stopping、escalation。** 偏好**半自主**:把不可逆 / 對外動作擋在人工閘之後。

## 內容結構

```
loop-engineering/
├── SKILL.md                          # skill 本體(frontmatter + 指令)
├── references/
│   ├── loop-patterns.md              # heartbeat / cron / hook / goal + Ralph loop
│   ├── context-engineering.md        # compaction、note-taking、sub-agent、JIT retrieval
│   ├── review-checklist.md           # 逐原則診斷清單,依嚴重性排序
│   └── sources.md                    # 12 篇來源文章 + 一句話摘要
├── evals/                            # 驗證案例庫 + benchmark 證據
│   ├── evals.json                    # 11 個評分過的 design / review / diagnose 案例
│   ├── RESULTS.md                    # 有 skill vs 無 skill 結果,3 個 iteration
│   └── files/                        # review 案例指向的輸入腳本
└── assets/                           # README hero 圖
```

一個 skill 就是一個含 `SKILL.md`(YAML frontmatter + Markdown)的資料夾。正因如此,它幾乎能裝在任何地方。

## 安裝

### Claude Code
個人層級(所有專案)或專案層級——把資料夾複製進 `skills/` 目錄:

```bash
# 個人層級
git clone https://github.com/maxmilian/loop-engineering ~/.claude/skills/loop-engineering
# 或專案層級
git clone https://github.com/maxmilian/loop-engineering .claude/skills/loop-engineering
```

開新 session,Claude 會依 `description` 自動發現它,並在你設計或審查 agent loop 時叫起來。(預先打包的 `.skill` bundle:若你用 plugin / skill 管理器,直接安裝即可。)

### Codex
Codex 原生從它的 skills 目錄載入 skill,把資料夾放進去:

```bash
git clone https://github.com/maxmilian/loop-engineering ~/.codex/skills/loop-engineering
```

若你的 Codex 是吃 `AGENTS.md`,加一行指引即可:
`For designing or reviewing autonomous agent loops, follow skills/loop-engineering/SKILL.md.`

### GitHub Copilot CLI
Copilot 從已安裝的 plugin 自動發現 skill。把資料夾放到你的 Copilot skills / plugins 目錄(例如 `~/.copilot/skills/loop-engineering`),重啟 CLI。

### Gemini CLI
Gemini 透過它的 skill 機制啟用。把資料夾放進 Gemini skills 目錄(例如 `~/.gemini/skills/loop-engineering`);Gemini 在 session 啟動時載入 metadata、按需啟用完整內容。若你用 `GEMINI.md` 驅動 Gemini,加一行指向 `skills/loop-engineering/SKILL.md`。

### Cursor / Windsurf / 任何有 instructions 檔的 agent
這些沒有正式的 skill loader,但內容照樣可用。在你的規則 / 指令檔(`.cursorrules`、`AGENTS.md` 等)引用它:

```
當你要打造或審查自主 / 半自主 agent loop、背景 worker、或 cron / webhook 驅動的 agent 時,
依循 skills/loop-engineering/SKILL.md(及其 references/ 檔案)的框架。
```

### 最低共識做法
任何 LLM 工具:設計 / 審查 loop 時,把 `SKILL.md` 貼進 context;當 skill 指示時,再拉進對應的 `references/*.md`。

## 怎麼用

你不需要明確呼叫它——描述任務,agent 就會接手:

- *「我想要一個 agent 整晚盯著 CI,自動修好失敗的 PR。」* → 設計模式
- *「在我們把這支背景 worker 擴到更多 queue 之前,幫我 review 一下。」* → 審查模式
- *「我的研究 agent 一直燒 token、永遠不收尾。」* → 診斷
- *「設計一個跑到目標達成才停的 loop,別讓它失控。」* → 設計模式

## 重現 benchmark

上面的數字不是空口說白話——held-out 案例就在這個 repo 裡,你可以自己重跑;完整的逐 iteration 結果(含一段誠實說明 skill 在哪裡*沒有*幫助)都在 [`evals/RESULTS.md`](evals/RESULTS.md)。

- **案例集**在 [`evals/evals.json`](evals/evals.json):11 個刻意刁鑽的案例,橫跨全部四種 loop pattern(heartbeat / cron / hook / goal)外加 long-horizon context,涵蓋 **design**、**review**、**diagnose** 三種模式——從 CI/PR-fixer 設計、有瑕疵的客服 ticket bot(程式碼在 [`evals/files/`](evals/files/)),到失控的研究 loop。每個案例都附一份 `expected_output` 評分準則,列出正確答案必須命中的具體要點(machine-checkable 的 done 條件、所有 exit 都帶實際數字、確定性驗證、不可逆動作的 human-gate 等)。87% → 100% 這個頭條數字來自其中「隱晦 / 規格不足」的子集;逐 iteration 的細項見 [`evals/RESULTS.md`](evals/RESULTS.md)。

**方法(與頭條數字相同):**

1. 每個案例把 `prompt` 跑**兩次**——一次裝了 skill(上面的控制流程),一次乾淨的 baseline 無 skill——各跑數次以平均掉變異。
2. 每次的結果都對照它的 `expected_output` 準則評分(由 LLM 對照所列斷言評分;準則項目都寫成可客觀檢查)。
3. 把每個配置的逐斷言通過率加總後比較。

頭條數字的通過率 / 變異 / token 加總是用 Anthropic 的 `skill-creator` benchmark harness(`grader` + `aggregate_benchmark`)跑的,但任何「有 skill / 無 skill」對照、依準則評分,都會浮現同樣的落差。Skill 的優勢集中在隱晦的失效模式——stale-prompt 腐壞、盲目重試浪費、缺少 human-gate——這些是強模型放任預設時會跳過的地方。

## 參與貢獻

非常歡迎貢獻——新的實戰範例、額外的 loop pattern、更銳利的 review 判準、翻譯,或修正。開 issue 或 PR 都可以。

**明確歡迎使用 AI 協助貢獻。** 這是一個*關於* agentic loop 的 skill,所以用 Claude Code / Codex / Copilot / Gemini(或任何 coding agent)來起草你的修改是鼓勵的——正合主題。只要在送出前 review 一下 agent 的產出:確認正確、有主張處有真實來源佐證(見 `references/sources.md`)、而且你願意為它背書。拿這個 skill 來 dogfood 你自己的 PR 更是加分。


## 授權 / 出處

以 **MIT License** 釋出——見 [`LICENSE`](LICENSE)。

萃取自關於 loop engineering、agent loop、context engineering 的公開寫作——完整來源清單與連結見 `references/sources.md`。
