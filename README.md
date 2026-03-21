# sciskill

Chinese version: [README.zh-CN.md](README.zh-CN.md)

`sciskill` is a standalone repository under `sciskillhub` for collecting public GitHub repositories that contain valid `SKILL.md` files. Matching upstream repositories are tracked here as Git submodules, and the collection results are written to a report file.

The main collector is [`scripts/collect_skills.py`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/scripts/collect_skills.py). Scheduled automation is defined in [`.github/workflows/collect-skills.yml`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/.github/workflows/collect-skills.yml).

### Repository Layout

- [`scripts/collect_skills.py`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/scripts/collect_skills.py): collector for discovering and validating skill repositories
- [`config/domain_topics.txt`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/config/domain_topics.txt): domain topics such as `clinical-research`
- [`config/qualifier_topics.txt`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/config/qualifier_topics.txt): skill or agent qualifier topics such as `ai-agents`
- [`open-source/`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/open-source): imported upstream repositories as submodules
- [`skill_report.json`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/skill_report.json): latest collection report
- [`requirements.txt`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/requirements.txt): Python dependencies
- [`community/`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/community): reserved directory, currently unused

### What The Collector Does

- Searches GitHub repositories from a base query plus domain-topic × qualifier-topic combinations
- Scans candidate repositories for `SKILL.md`
- Validates YAML front matter in each matched file
- Adds newly accepted repositories as Git submodules
- Writes a structured JSON report

Current validation requires:

- a parseable YAML front matter block
- a non-empty `name` matching `[a-z0-9-]+`
- a non-empty `description` with at least 10 characters

### Requirements

- `python3`
- `git`
- a GitHub token for API access
- optional SSH key support; the collector prefers SSH and falls back to HTTPS

### Automation

The GitHub Actions workflow [`.github/workflows/collect-skills.yml`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/.github/workflows/collect-skills.yml):

- runs on manual dispatch
- runs daily at `07:10 UTC`
- uses `secrets.SKILL_COLLECTOR_TOKEN`
- updates `skill_report.json`, `.gitmodules`, and `open-source/`

### Notes

- The collector now uses AND semantics across two topic dimensions:
  - one domain topic from [`config/domain_topics.txt`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/config/domain_topics.txt)
  - one qualifier topic from [`config/qualifier_topics.txt`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/config/qualifier_topics.txt)
- Effective queries are generated as the Cartesian product `M × N`, for example:
  - `archived:false is:public topic:clinical-research topic:ai-agents`
- Each topic file uses one topic per line; blank lines and `#` comments are ignored
- repositories already present in `open-source/` or [`.gitmodules`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/.gitmodules) are skipped
- [`skill_report.json`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/skill_report.json) stores summary metadata plus per-repository result statuses
