---
name: sciskillhub
description: 当本地 agent 需要为当前任务选择合适 skill 时，使用 SciSkillHub 查询 API 先缩小 object、stage、tasks、domains，再获取候选 skill list。这个 skill 只提供查询 API 与查询方法；具体判断当前任务属于什么 object、stage、domains，是本地 agent 自己的职责。
metadata:
    skill-author: sciskillhub
    homepage: https://sciskillhub.org
---

# sciskillhub — Skill Routing API

SciSkillHub 是一个面向 AI agent 的技能分发平台。

这个 skill 的作用是：

- 提供 SciSkillHub 的查询 API 和查询顺序
- 告诉本地 agent 应该如何从 `object / stage / tasks / domains` 缩小范围
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
  -> 本地 agent 判断 object
  -> 本地 agent 判断 stage
  -> 本地 agent 判断 domains
  -> 用 object + stage + domains 查询 tasks
  -> 从 tasks 中挑出最贴近当前任务的多个tasks
  -> 用 object + stage + tasks + domains 查询 skills
  -> 从候选 skill list 中选择最合适的多个skills
```

推荐顺序：

1. 本地先判断 `object`
2. 本地再判断 `stage`
3. 本地再判断 `domains`
4. 再调用查询 API，不要一开始直接盲搜所有 skill

---

## 固定 Object 列表

`object` 是固定枚举，本地 agent 需要先从下面选择最接近的一项：

- `Concepts and Theory`
- `Research Capabilities`
- `Methods and Techniques`
- `Software and Tools`
- `Instruments and Equipment`
- `Data and Resources`
- `Workflows`
- `Standards and Guidelines`

判断原则：

- 先判断“当前用户要解决的问题，本体更像什么”
- 不要把这个判断步骤跳过
- 如果本地 agent 连 `object` 都没先判断清楚，就不要直接查 skill list

---

## 固定 Stage 列表

`stage` 也是固定枚举，本地 agent 需要先选最主要的一个阶段：

- `Problem Definition and Background Research`
- `Study Design`
- `Data / Sample Acquisition`
- `Data Analysis and Modeling`
- `Validation and Interpretation`
- `Writing and Publication`
- `Translation to Practice`
- `General Research Support`

判断原则：

- 只保留最主要阶段
- 不要因为一个任务覆盖多个环节，就同时传多个 stage
- 如果当前任务更偏“现在最需要做哪一步”，就按那一步选

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

## API 1：按 Object + Stage + Domains 查询 Tasks

用途：

- 先根据已经判断好的 `object + stage + domains` 缩小 `tasks`
- 不要直接跳过这一步

接口：

`GET /api/v1/agent/skills/tasks`

查询参数：

- `object`
- `stage`
- `domains`
- `page`
- `limit`

约束：

- 不提供 `q`
- `limit` 默认 `100`
- 返回必须包含 `total`

示例：

```http
GET /api/v1/agent/skills/tasks?object=Research%20Capabilities&stage=Study%20Design&domains=Life%20Sciences&page=1&limit=100
```

示例返回：

```json
{
  "object": "Research Capabilities",
  "stage": "Study Design",
  "domains": ["Life Sciences"],
  "page": 1,
  "limit": 100,
  "total": 3,
  "tasks": [
    {"name": "Hypothesis Building", "count": 12},
    {"name": "Problem Definition", "count": 9},
    {"name": "Experimental Design", "count": 7}
  ]
}
```

本地 agent 在这一步要做的事情：

- 不是把返回的 tasks 全部照单全收
- 而是结合用户当前问题，从里面挑 1-3 个最贴近当前意图的 task

---

## API 2：按 Object + Stage + Tasks + Domains 查询 Skills

用途：

- 用结构化条件获取候选 `skill list`
- 然后由本地 agent 继续判断具体该用哪个 skill

接口：

`GET /api/v1/agent/skills`

查询参数：

- `object`
- `stage`
- `tasks`
- `domains`
- `page`
- `limit`

约束：

- 不提供 `q`
- `limit` 默认 `100`
- 返回必须包含 `total`

示例：

```http
GET /api/v1/agent/skills?object=Research%20Capabilities&stage=Study%20Design&tasks=Hypothesis%20Building&tasks=Experimental%20Design&domains=Life%20Sciences&page=1&limit=100
```

示例返回：

```json
{
  "object": "Research Capabilities",
  "stage": "Study Design",
  "tasks": ["Hypothesis Building", "Experimental Design"],
  "domains": ["Life Sciences"],
  "page": 1,
  "limit": 100,
  "total": 27,
  "skills": [
    {
      "id": "open-source/FreedomIntelligence/OpenClaw-Medical-Skills/skills/hypothesis-generation",
      "name": "hypothesis-generation",
      "object": "Research Capabilities",
      "stage": "Study Design",
      "tasks": ["Hypothesis Building", "Experimental Design"],
      "domains": ["Life Sciences", "General Research"],
      "description": "Generate and refine scientific hypotheses from prior knowledge and evidence."
    }
  ]
}
```

本地 agent 在这一步要做的事情：

- 看返回 skill 是否和当前用户任务真正匹配
- 选择最合适的 1-3 个 skill
- 不要因为某个 skill 出现在结果里，就默认必须使用它

---

## API 3：读取 Taxonomy 枚举

接口：

`GET /api/v1/agent/skills/taxonomy`

用途：

- 读取标准 `object / stage / tasks / domains` 枚举
- 保证本地 agent 传参时使用平台认可的标准值

示例返回：

```json
{
  "object_options": ["Research Capabilities", "Methods and Techniques", "Software and Tools"],
  "stage_options": ["Study Design", "Data Analysis and Modeling", "Writing and Publication"],
  "task_options": ["Hypothesis Building", "Experimental Design", "Clustering"],
  "domain_options": ["Life Sciences", "Computational Sciences", "General Research"]
}
```

---

## 本地 Agent 的职责边界

在使用这个 skill 时，必须遵守下面的边界：

- 先判断 `object`
- 再判断 `stage`
- 再判断 `domains`
- 再查 `tasks`
- 最后再查 `skills`

不要把职责反过来：

- 不要先拿一堆 skill 再倒推 object/stage
- 不要把远端接口当成“自动分类器”
- 不要把“判断当前任务属于什么 object/stage/domains”的责任后置到查询之后

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

用户问题：

```text
我需要帮助设计一个假设生成流程，用于肿瘤单细胞研究
```

本地 agent 应先做：

- `object = Research Capabilities`
- `stage = Study Design`
- `domains = [Life Sciences, General Research]`

然后：

1. 查 `GET /api/v1/agent/skills/tasks`
2. 从返回里挑 `Hypothesis Building`、`Experimental Design`
3. 查 `GET /api/v1/agent/skills`
4. 从候选结果里选择最合适的 skill

---

## 最后原则

这个 skill 是“查询入口”，不是“分类裁判”。

本地 agent 先理解任务，再使用 API。
