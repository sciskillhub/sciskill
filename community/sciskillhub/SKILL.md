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
  -> 对每个 object+stage 组合，查询 tasks（可并行）
  -> 汇总所有 tasks，挑出最贴近当前任务的多个 tasks
  -> 用 object + stage + tasks + domains 查询 skills（可对多个 object 组合并行查询）
  -> 汇总候选 skill list，选择最合适的多个 skills
```

推荐顺序：

1. 本地先列出可能的 `object`（不要只选一个，尝试 2-3 个相关候选）
2. 本地再列出可能的 `stage`（1-2 个）
3. 本地再判断 `domains`
4. 对多个 object+stage 组合分别查询，扩大覆盖面
5. 汇总结果后再筛选，不要一开始就锁定单一组合

**重要：多组合尝试原则**

很多任务横跨多个 object 或 stage。例如"长读长测序数据分析"：

- `Methods and Techniques` + `Data Analysis and Modeling` → 分析方法
- `Software and Tools` + `Data Analysis and Modeling` → 分析软件
- `Data and Resources` + `Data Analysis and Modeling` → 数据资源

如果只选一个 object，会漏掉其他维度下的相关 skill。应该对 2-3 个最可能的组合都查询一遍，然后汇总去重。

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
- 不要直接跳过这一步

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
- 再查 `tasks`（`sciskill tax --tasks`）
- 最后再查 `skills`（`sciskill browse skills`）

不要把职责反过来：

- **不要使用 `sciskill search`**，这不是本 skill 的推荐流程。应通过 `tax --tasks` → `browse skills` 的结构化查询路径逐步缩小范围
- 不要先拿一堆 skill 再倒推 object/stage
- 不要把 CLI 当成"自动分类器"
- 不要把"判断当前任务属于什么 object/stage/domains"的责任后置到查询之后

简化成一句话：

当前用户任务属于什么 `object / stage / domains`，应先由本地 agent 判断，再进入后续查询步骤。

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

然后（并行查询）：

1. `sciskill tax --tasks --object "Research Capabilities" --stage "Study Design" --domain "Life Sciences" "General Research"`
2. `sciskill tax --tasks --object "Methods and Techniques" --stage "Study Design" --domain "Life Sciences" "General Research"`
3. 汇总 tasks，挑出 `Hypothesis Building`、`Experimental Design`
4. `sciskill browse skills --object "Research Capabilities" --stage "Study Design" --task "Hypothesis Building" "Experimental Design" --domain "Life Sciences"`
5. `sciskill browse skills --object "Methods and Techniques" --stage "Study Design" --task "Hypothesis Building" "Experimental Design" --domain "Life Sciences"`
6. 汇总去重，选择最合适的 skill
7. `sciskill install <author>/<path> --agent claude`

### 示例 2：长读长测序数据分析

用户问题：

```text
帮我分析 Nanopore 长读长测序数据
```

本地 agent 应判断：

- `object = [Methods and Techniques, Software and Tools, Data and Resources]`
- `stage = [Data Analysis and Modeling]`
- `domains = [Life Sciences]`

然后（并行查询）：

1. `sciskill tax --tasks --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences"`
2. `sciskill tax --tasks --object "Software and Tools" --stage "Data Analysis and Modeling" --domain "Life Sciences"`
3. 汇总 tasks，挑出 `Quality Control`、`Alignment`、`Quantification`
4. `sciskill browse skills --object "Methods and Techniques" --stage "Data Analysis and Modeling" --task "Quality Control" "Alignment" "Quantification" --domain "Life Sciences"`
5. `sciskill browse skills --object "Software and Tools" --stage "Data Analysis and Modeling" --task "Quality Control" "Alignment" "Quantification" --domain "Life Sciences"`
6. 汇总去重，选择最合适的 skill
7. `sciskill install <author>/<path> --agent claude`

---

## 最后原则

这个 skill 是"查询入口"，不是"分类裁判"。

本地 agent 先理解任务，再使用 CLI。
