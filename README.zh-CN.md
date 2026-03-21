# sciskill

English version: [README.md](README.md)

`sciskill` 是 `sciskillhub` 下的一个独立仓库，用于收集公开 GitHub 仓库中符合要求的 `SKILL.md`，并将命中的上游仓库以 Git submodule 的方式纳入本仓库，同时输出结构化报告。

核心收集脚本是 [`scripts/collect_skills.py`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/scripts/collect_skills.py)，自动化流程定义在 [`.github/workflows/collect-skills.yml`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/.github/workflows/collect-skills.yml)。

### 仓库结构

- [`scripts/collect_skills.py`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/scripts/collect_skills.py)：发现并校验技能仓库的收集脚本
- [`config/topics.txt`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/config/topics.txt)：用于扩展搜索的 GitHub topic 列表
- [`open-source/`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/open-source)：已纳入的上游 submodule 仓库
- [`skill_report.json`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/skill_report.json)：最近一次收集结果报告
- [`requirements.txt`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/requirements.txt)：Python 依赖
- [`community/`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/community)：预留目录，目前未使用

### 收集器做什么

- 基于基础查询和配置的 topic 搜索 GitHub 仓库
- 扫描候选仓库中的 `SKILL.md`
- 校验其中的 YAML front matter
- 将新命中的仓库加入为 Git submodule
- 生成结构化 JSON 报告

当前校验规则要求：

- `SKILL.md` 包含可解析的 YAML front matter
- `name` 非空，且匹配 `[a-z0-9-]+`
- `description` 非空，且长度不少于 10 个字符

### 环境要求

- `python3`
- `git`
- 可用于 GitHub API 的 token
- 可选 SSH key；脚本优先使用 SSH，失败时回退到 HTTPS

### 自动化

GitHub Actions 工作流 [`.github/workflows/collect-skills.yml`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/.github/workflows/collect-skills.yml)：

- 支持手动触发
- 每天 `07:10 UTC` 定时运行
- 使用 `secrets.SKILL_COLLECTOR_TOKEN`
- 自动更新 `skill_report.json`、`.gitmodules` 和 `open-source/`

### 维护说明

- [`config/topics.txt`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/config/topics.txt) 每行一个 topic，空行和 `#` 注释会被忽略
- 已存在于 `open-source/` 或 [`.gitmodules`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/.gitmodules) 的仓库会被跳过
- [`skill_report.json`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/skill_report.json) 保存汇总信息和逐仓库状态
