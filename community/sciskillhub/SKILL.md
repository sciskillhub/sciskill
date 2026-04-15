---
name: sciskillhub
description: 为本地 agent 选择合适 skill 来执行任务/数据分析，当用户提出一个任务时，调用这个来帮助用户选择这个任务最合适的 skill
metadata:
    skill-author: sciskillhub
    homepage: https://sciskillhub.org
    version: 0.1.0
---

# sciskillhub — Skill Routing via CLI

SciSkillHub 是一个面向 AI agent 的技能分发平台。

这个 skill 的作用是：

- 提供 SciSkillHub CLI (`sciskill`) 的查询命令和调用顺序
- 告诉本地 agent 应该如何从 `object / stage / domains` 缩小范围
- 返回候选 skill list，供本地 agent 继续判断

以下判断应由本地 agent 结合用户当前问题先自行完成：

- 当前任务属于什么 `object`
- 当前任务主要处于什么 `stage`
- 当前任务涉及哪些 `domains`
- 哪些候选 `tasks` 最贴近当前意图

---

## 推荐调用流程

```text
用户自然语言输入
  -> 本地 agent 判断可能的 object 列表（2-3 个候选）
  -> 本地 agent 判断可能的 stage 列表（1-2 个候选）
  -> 本地 agent 判断 domains
  -> 本地 agent 将用户任务拆解为 2-3 个独立概念维度
  -> 路径 A：对每个 object+stage 组合查询 tasks（可并行）
  -> 路径 B：对每个概念维度并行做关键词查询（先通用后具体）
  -> 路径 A 中若出现贴切 tasks：继续用 object + stage + tasks + domains 查询 skills
  -> 路径 B 同时持续返回 query 命中的 skills
  -> 对所有返回结果做适用性判断（是否匹配用户的具体场景和数据类型）
  -> 汇总两条路径的 skill 结果，去重后选择最合适的多个 skills
```

推荐顺序：

1. 本地先列出可能的 `object`（不要只选一个，尝试 2-3 个相关候选）
2. 本地再列出可能的 `stage`（1-2 个）
3. 本地再判断 `domains`
4. 将用户任务拆解为 2-3 个独立概念维度，每个维度提取关键词
5. 对多个 object+stage 组合分别查询，扩大覆盖面
6. 与结构化查询并行，对每个概念维度做关键词查询，优先通用关键词
7. 对所有返回结果做适用性判断，筛除与用户具体场景不匹配的 skill
8. 汇总结果后再筛选，不要一开始就锁定单一组合

**重要：多组合尝试原则**

很多任务横跨多个 object 或 stage。例如"长读长测序数据分析"：

- `Methods and Techniques` + `Data Analysis and Modeling` → 分析方法
- `Software and Tools` + `Data Analysis and Modeling` → 分析软件
- `Data and Resources` + `Data Analysis and Modeling` → 数据资源

如果只选一个 object，会漏掉其他维度下的相关 skill。应该对 2-3 个最可能的组合都查询一遍，然后汇总去重。

**重要：任务维度拆解**

很多任务由多个独立概念组成。本地 agent 应将用户输入拆解为 2-3 个维度，分别作为关键词查询：

- "单细胞数据的 CNV 分析" → 维度 1: `单细胞 / single cell`，维度 2: `CNV / copy number`
- "肿瘤空间转录组细胞通讯" → 维度 1: `spatial transcriptomics`，维度 2: `cell communication`
- "长读长测序数据比对" → 维度 1: `long read / nanopore`，维度 2: `alignment`

拆解原则：

- 每个维度用 1-2 个短关键词表达
- 维度之间应相对独立（不是简单切分句子）
- 对每个维度分别查询，然后看交集和互补
- 拆解后还要做一轮**组合查询**（把两个维度关键词合并），捕捉同时覆盖多个维度的 skill

**重要：结构化路径与关键词路径并行**

- `tax --tasks` 是推荐入口，但不是唯一入口
- 某些任务下，返回的 tasks 可能过泛、明显不贴题，或者虽然有返回但不足以覆盖真实相关 skill
- 因此应默认并行做关键词查询，不是等结构化路径失败后再补做
- 最终应汇总 `tasks` 路径和 `query` 路径的结果，再去重和判断

---

## 固定 Object 列表

`object` 是固定枚举，本地 agent 需要从中选出 **2-3 个最可能的候选**：

- `Concepts and Theory`
- `Research Capabilities`
- `Methods and Techniques`
- `Software and Tools`
- `Instruments and Equipment`
- `Data and Resources`
- `Workflows`
- `Standards and Guidelines`

判断原则：

- 不要只选一个 object，很多任务横跨多个维度
- 例如"数据分析"相关的任务，通常同时涉及 `Methods and Techniques` 和 `Software and Tools`
- 例如"实验设计"相关的任务，可能同时涉及 `Research Capabilities` 和 `Workflows`
- 对每个候选 object 都执行查询，然后汇总结果去重

---

## 固定 Stage 列表

`stage` 也是固定枚举，本地 agent 需要选出 **1-2 个最相关的阶段**：

- `Problem Definition and Background Research`
- `Study Design`
- `Data / Sample Acquisition`
- `Data Analysis and Modeling`
- `Validation and Interpretation`
- `Writing and Publication`
- `Translation to Practice`
- `General Research Support`

判断原则：

- 选最主要阶段，必要时加 1 个次要阶段
- 例如"分析数据"偏 `Data Analysis and Modeling`，但如果涉及"如何设计分析方案"也覆盖 `Study Design`

---

## Domains 判断

`domains` 由本地 agent 根据用户输入先做归类。

常见原则：

- 生命科学、医学、组学、临床、生物信息分析，优先考虑 `Life Sciences` 或 `Medical and Health Sciences`
- 编程、建模、算法、系统、数据工程，优先考虑 `Computational Sciences`
- 通用科研能力、跨学科研究方法，可考虑 `General Research`

如果任务是跨学科的：

- 保留主要 domain
- 可以附带 1-2 个次级 domain
- 不要一次传太多 domain，避免把结果集冲散

---

## 命令 0：查看 Taxonomy 枚举

用途：

- 读取标准 `object / stage / domain` 枚举
- 保证本地 agent 传参时使用平台认可的标准值

命令：

```bash
sciskill tax
```

示例输出：

```
Object (--object-list)
  • Concepts and Theory
  • Research Capabilities
  • Methods and Techniques
  • Software and Tools
  • Instruments and Equipment
  • Data and Resources
  • Workflows
  • Standards and Guidelines

Stage (--stage-list)
  • Problem Definition and Background Research
  • Study Design
  • Data / Sample Acquisition
  • Data Analysis and Modeling
  • Validation and Interpretation
  • Writing and Publication
  • Translation to Practice
  • General Research Support

Domain (--domain-list)
  • Life Sciences
  • Computational Sciences
  • General Research
  • ...
```

选项：

- `sciskill tax --object-list` — 只看 object
- `sciskill tax --stage-list` — 只看 stage
- `sciskill tax --domain-list` — 只看 domain
- `sciskill tax --task-list` — 只看 task（默认不显示 task）
- `sciskill tax --refresh` — 强制刷新缓存
- `sciskill tax --json` — JSON 输出

---

## 命令 1：按 Object + Stage + Domains 查询 Tasks

用途：

- 先根据已经判断好的 `object + stage + domains` 缩小 `tasks`
- 这是推荐入口，但不是强制唯一入口

命令：

```bash
sciskill tax --tasks --object "Research Capabilities" --stage "Study Design" --domain "Life Sciences"
```

示例输出：

```
Tasks (3 total)
  Object: Research Capabilities
  Stage: Study Design
  Domains: Life Sciences

  • Hypothesis Building (12)
  • Problem Definition (9)
  • Experimental Design (7)
```

选项：

- `--object <value>` — 过滤 object
- `--stage <value>` — 过滤 stage
- `--domain <values...>` — 过滤 domain（可多个）
- `--limit <n>` — 返回数量，默认 100
- `--json` — JSON 输出

本地 agent 在这一步要做的事情：

- 不是把返回的 tasks 全部照单全收
- 而是结合用户当前问题，从里面挑 1-3 个最贴近当前意图的 task
- 如果没有明显贴切的 task，不要硬选
- 即使已经在查 task，也要同步保留“关键词并行查询”这一路，不要把 query 当成失败后的备用方案

---

## 命令 2：按 Object + Stage + Tasks + Domains 查询 Skills

用途：

- 用结构化条件获取候选 `skill list`
- 然后由本地 agent 继续判断具体该用哪个 skill

命令：

```bash
sciskill browse skills --object "Research Capabilities" --stage "Study Design" --task "Hypothesis Building" "Experimental Design" --domain "Life Sciences"
```

示例输出：

```
Found 27 skills:

  #  Name                      Object               Stage           Author         Path
  1. hypothesis-generation     Research Capabilities Study Design    FreedomIntell  hypothesis-generation
  ...

Install with: sciskill install <author>/<path>
```

选项：

- `--object <values...>` — 过滤 object
- `--stage <values...>` — 过滤 stage
- `--task <values...>` — 过滤 tasks（可多个）
- `--domain <values...>` — 过滤 domains（可多个）
- `-q, --query <text>` — 额外关键词过滤
- `--sort <field>` — 排序：name, stars, recent, score
- `--order <dir>` — 排序方向：asc, desc
- `-l, --limit <n>` — 返回数量，默认 20
- `--json` — JSON 输出

本地 agent 在这一步要做的事情：

- 看返回 skill 是否和当前用户任务真正匹配
- 选择最合适的 1-3 个 skill
- 不要因为某个 skill 出现在结果里，就默认必须使用它
- 如果 `task` 路径结果很弱，可以省略 `--task`，保留 `object + stage + domains`，再叠加 `-q`

---

## 命令 2B：并行关键词查询 Skills

用途：

- 与结构化路径默认并行执行
- 它不是失败后的补救步骤，而是常规检索路径之一
- 当 `tasks` 结果为空、过泛、或无法覆盖用户真实意图时，这一路通常会更快暴露相关 skill
- 关键词查询不是禁止使用；禁止的是完全跳过任务理解和结构化判断

### 关键词策略：先通用，后具体

关键词查询应按 **通用 → 具体** 的顺序组织，优先用覆盖面广的通用词：

**第一轮（通用关键词）**：用任务拆解出的每个维度的最通用表达

```bash
# “单细胞数据的CNV分析” 拆解为两个维度
# 维度 1: 单细胞
sciskill browse skills --object “Software and Tools” --object “Methods and Techniques” --stage “Data Analysis and Modeling” --domain “Life Sciences” -q “single cell”
# 维度 2: CNV
sciskill browse skills --object “Software and Tools” --object “Methods and Techniques” --stage “Data Analysis and Modeling” --domain “Life Sciences” -q “cnv”
sciskill browse skills --object “Software and Tools” --object “Methods and Techniques” --stage “Data Analysis and Modeling” --domain “Life Sciences” -q “copy number”
```

**第二轮（组合 + 具体关键词）**：在通用词之后，补充具体工具/方法名

```bash
# 组合两个维度
sciskill browse skills --object “Software and Tools” --object “Methods and Techniques” --stage “Data Analysis and Modeling” --domain “Life Sciences” -q “single cell cnv”
# 具体工具名（如果用户提到或你已知）
sciskill browse skills --object “Software and Tools” --object “Methods and Techniques” --stage “Data Analysis and Modeling” --domain “Life Sciences” -q “infercnv”
sciskill browse skills --object “Software and Tools” --object “Methods and Techniques” --stage “Data Analysis and Modeling” --domain “Life Sciences” -q “copykat”
```

### 关键词选择原则

- **先通用后具体**：先用 `single cell`、`cnv` 等通用词扩大覆盖面，再用 `infercnv`、`copykat` 等具体工具名查漏
- **不要只查一个长短语**：优先拆成多个短 query 并行查
  - 好：`cnv`、`copy number`、`single cell`（分别并行查）
  - 差：`single cell CNV analysis for tumor data`（一句话塞进去）
- **按维度组织**：每个拆解出的维度独立查询，再做一轮组合查询
- **关键词要短**：1-3 个词最佳，避免把整句自然语言原样塞进去
- **优先用领域词、方法词、工具词**，不用虚词和停用词

### 什么时候优先启用这一支路

- `tax --tasks` 返回的 task 不相关
- `tax --tasks` 返回的 task 太泛，无法支撑精确筛选
- 用户任务由多个独立概念组成（如”单细胞 + CNV”），结构化路径可能无法同时覆盖
- 你怀疑 metadata 不完整，结构化过滤会漏掉技能
- 某类技能通常靠名称/描述更容易命中，而不是靠 task 枚举

---

## 适用性判断

查询返回的 skill 列表不是最终答案。本地 agent 必须对每个候选 skill 做**适用性判断**，检查它是否真正匹配用户的具体场景。

### 判断步骤

1. **读 skill 描述和 use_cases**：用 `--json` 获取完整信息，关注 `description`、`use_cases`、`workflows` 字段
2. **比对数据类型**：用户说的是 scRNA-Seq、WES、WGS、ATAC-Seq 还是 bulk RNA-Seq？skill 支持的输入是什么？
3. **比对分析目标**：用户要做的是 calling、annotation、visualization 还是 integration？skill 覆盖哪个环节？
4. **主动标记不匹配**：如果 skill 明确针对另一种数据类型或场景，应直接排除并告知用户

### 常见适用性陷阱

| 陷阱 | 说明 | 应对 |
|------|------|------|
| bulk vs single-cell | 同一个分析任务（如 CNV）在 bulk 和 single-cell 下用的是完全不同的工具 | 检查 skill 描述中的数据类型，区分 "sequencing data" 和 "single-cell RNA-seq" |
| WES vs WGS vs Panel | CNVkit、GATK CNV 等工具针对特定测序类型 | 确认 skill 适用范围 |
| calling vs annotation vs visualization | 一个分析流程的上下游环节用不同工具 | 确认用户要的是哪个环节 |
| 人类 vs 模式生物 | 某些工具只支持特定物种的基因组 | 检查物种支持 |

### 适用性判断示例

用户任务："单细胞数据的 CNV 分析"

返回的 skill 列表：

- `cnv-caller-agent` — "从测序数据检测 CNV，用于癌症基因组学"
- `bio-copy-number-cnvkit-analysis` — "从靶向/外显子测序检测 CNV，基于 CNVkit"
- `bio-copy-number-gatk-cnv` — "GATK CNV calling"

适用性判断：

- `cnv-caller-agent`：描述为"sequencing data"，未提及 single-cell → **可能不适用，需进一步确认**
- `bio-copy-number-cnvkit-analysis`：明确写"靶向/外显子测序" → **不适用于 scRNA-Seq**
- `bio-copy-number-gatk-cnv`：GATK CNV 是 bulk WES 工具 → **不适用于 scRNA-Seq**

结论：当前结果**没有适用于 scRNA-Seq CNV 推断的 skill**，应如实告知用户，并建议替代方案（如安装 scanpy skill 后手动编写 inferCNV/CopyKAT 分析流程）。

### 判断原则

- 不要因为 skill 出现在搜索结果中，就默认它适用
- 不要假设通用描述一定覆盖你的具体场景
- 对结果做**主动排除**比**被动接受**更重要
- 如果所有结果都不适用，**明确告知用户"没有找到直接匹配的 skill"**，而不是强行推荐不合适的
- 告知用户时，说明**为什么**不适用（数据类型、分析环节、物种等），帮助用户理解缺口

---

## 命令 3：安装 Skill

找到合适的 skill 后，安装到本地：

```bash
sciskill install <author>/<path> --agent claude
```

---

## 本地 Agent 的职责边界

在使用这个 skill 时，必须遵守下面的边界：

- 先判断 `object`
- 再判断 `stage`
- 再判断 `domains`
- 将用户任务拆解为 2-3 个独立概念维度
- 然后默认并行执行：
  `sciskill tax --tasks`（结构化路径）
  和
  `sciskill browse skills ... -q <通用关键词>`（关键词路径，按维度并行）
- 对所有返回结果做适用性判断
- 最后汇总两路结果，筛选出真正适用的 skill

不要把职责反过来：

- **不要使用 `sciskill search`** 代替任务理解
- 不要在完全不判断 `object/stage/domains` 的情况下盲搜
- 不要先拿一堆 skill 再倒推 object/stage
- 不要把 CLI 当成”自动分类器”
- 不要把”判断当前任务属于什么 object/stage/domains”的责任后置到查询之后
- 不要跳过适用性判断，把查询结果直接当推荐结果

简化成一句话：

当前用户任务属于什么 `object / stage / domains`，应先由本地 agent 判断；拆解概念维度后并行走”结构化路径 + 关键词路径”；最后对结果做适用性判断，筛除不匹配的 skill。

---

## 何时使用这个 Skill

在这些情况下优先使用：

- 你需要为当前任务动态选择 skill
- 你已经知道当前任务的大致 `object / stage / domains`
- 你想先缩小 `tasks`，再拿候选 skill list

在这些情况下不要优先使用：

- 你已经明确知道要调用哪个具体 skill
- 当前任务只是普通闲聊，不涉及专业 skill routing
- 你还没有对当前问题做基本任务理解和分类

---

## 最小示例

### 示例 1：假设生成流程

用户问题：

```text
我需要帮助设计一个假设生成流程，用于肿瘤单细胞研究
```

本地 agent 应先判断多组候选：

- `object = [Research Capabilities, Methods and Techniques]`
- `stage = [Study Design]`
- `domains = [Life Sciences, General Research]`
- 概念维度：`hypothesis`、`单细胞 / single cell`

然后（并行查询）：

1. **结构化路径**：
   - `sciskill tax --tasks --object "Research Capabilities" --stage "Study Design" --domain "Life Sciences" "General Research"`
   - `sciskill tax --tasks --object "Methods and Techniques" --stage "Study Design" --domain "Life Sciences" "General Research"`
2. **关键词路径（通用）**：
   - `sciskill browse skills --object "Research Capabilities" --object "Methods and Techniques" --stage "Study Design" --domain "Life Sciences" -q "hypothesis"`
   - `sciskill browse skills --object "Research Capabilities" --object "Methods and Techniques" --stage "Study Design" --domain "Life Sciences" -q "single cell"`
3. 汇总 tasks，挑出 `Hypothesis Building`、`Experimental Design`
4. `sciskill browse skills --object "Research Capabilities" --stage "Study Design" --task "Hypothesis Building" "Experimental Design" --domain "Life Sciences" "General Research"`
5. `sciskill browse skills --object "Methods and Techniques" --stage "Study Design" --task "Hypothesis Building" "Experimental Design" --domain "Life Sciences" "General Research"`
6. **适用性判断**：检查候选 skill 是否支持肿瘤/单细胞场景
7. 汇总去重，选择最合适的 skill
8. `sciskill install <author>/<path> --agent claude`

### 示例 2：长读长测序数据分析

用户问题：

```text
帮我分析 Nanopore 长读长测序数据
```

本地 agent 应判断：

- `object = [Methods and Techniques, Software and Tools, Data and Resources]`
- `stage = [Data Analysis and Modeling]`
- `domains = [Life Sciences]`
- 概念维度：`nanopore / long read`、`alignment / analysis`

然后（并行查询）：

1. **结构化路径**：
   - `sciskill tax --tasks --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences"`
   - `sciskill tax --tasks --object "Software and Tools" --stage "Data Analysis and Modeling" --domain "Life Sciences"`
2. **关键词路径（通用）**：
   - `sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "nanopore"`
   - `sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "long read"`
3. 汇总 tasks，挑出 `Quality Control`、`Alignment`、`Quantification`
4. `sciskill browse skills --object "Methods and Techniques" --stage "Data Analysis and Modeling" --task "Quality Control" "Alignment" "Quantification" --domain "Life Sciences"`
5. `sciskill browse skills --object "Software and Tools" --stage "Data Analysis and Modeling" --task "Quality Control" "Alignment" "Quantification" --domain "Life Sciences"`
6. **适用性判断**：确认 skill 支持长读长数据（而非仅短读长）
7. 汇总去重，选择最合适的 skill
8. `sciskill install <author>/<path> --agent claude`

### 示例 3：单细胞 CNV 分析（跨维度任务）

用户问题：

```text
单细胞数据的CNV分析
```

本地 agent 应判断：

- `object = [Methods and Techniques, Software and Tools]`
- `stage = [Data Analysis and Modeling]`
- `domains = [Life Sciences]`
- 概念维度：**维度 1 = `single cell / 单细胞`**，**维度 2 = `CNV / copy number`**

然后（并行查询）：

1. **结构化路径**：
   - `sciskill tax --tasks --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences"`
   - `sciskill tax --tasks --object "Software and Tools" --stage "Data Analysis and Modeling" --domain "Life Sciences"`
2. **关键词路径（第一轮：通用，按维度并行）**：
   - `sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "single cell"`
   - `sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "cnv"`
   - `sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "copy number"`
3. **关键词路径（第二轮：组合 + 具体）**：
   - `sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "single cell cnv"`
   - `sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "infercnv"`
   - `sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "copykat"`
4. 汇总结构化路径找到的 task `copy number variation`
5. `sciskill browse skills --object "Software and Tools" --stage "Data Analysis and Modeling" --task "copy number variation" --domain "Life Sciences"`
6. **适用性判断**（关键步骤）：
   - `cnv-caller-agent`：描述为"从测序数据检测 CNV"→ 未提及 single-cell → **可能不适用**
   - `bio-copy-number-cnvkit-analysis`：明确写"靶向/外显子测序" → **不适用于 scRNA-Seq**
   - `bio-copy-number-gatk-cnv`：GATK CNV 是 bulk WES 工具 → **不适用于 scRNA-Seq**
7. **结论**：当前没有直接适用于 scRNA-Seq CNV 推断的 skill，告知用户并建议替代方案
8. 如果用户接受替代方案：`sciskill install <scanpy skill> --agent claude`

---

## 最后原则

这个 skill 是"查询入口"，不是"分类裁判"。

本地 agent 先理解任务，拆解维度，再使用 CLI，最后对结果做适用性判断。
