# sciskill

Chinese version: [README.zh-CN.md](README.zh-CN.md)

`sciskill` is a standalone repository under `sciskillhub` for collecting public GitHub repositories that contain valid `SKILL.md` files. This repo stores registry metadata plus a markdown index of collected GitHub repositories.

### Repository Layout

- [`open-source-skills.md`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/open-source-skills.md): markdown index of collected GitHub repositories
- [`community/`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/community): reserved directory, currently unused

### What This Repository Tracks

- Searches GitHub repositories from a base query plus domain-topic × qualifier-topic combinations
- Scans candidate repositories for `SKILL.md`
- Validates YAML front matter in each matched file
- Adds newly accepted repositories into `skill-manifest.json`
- Regenerates `open-source-skills.md`
- Writes a structured JSON report

Current validation requires:

- a parseable YAML front matter block
- a non-empty `name` matching `[a-z0-9-]+`
- a non-empty `description` with at least 10 characters

### Automation

The GitHub Actions workflow [`.github/workflows/collect-skills.yml`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/.github/workflows/collect-skills.yml):

- runs on manual dispatch
- runs daily at `07:10 UTC`
- uses `secrets.SKILL_COLLECTOR_TOKEN`
- updates `skill-manifest.json` and `open-source-skills.md`

### Notes

- The collector uses AND semantics across two topic dimensions: one domain topic and one qualifier topic
- Effective queries are generated as the Cartesian product `M × N`, for example:
  - `archived:false is:public topic:clinical-research topic:ai-agents`
- repositories already present in [`skill-manifest.json`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/skill-manifest.json) are skipped
- this repository is intended to track collected GitHub repositories and their metadata
