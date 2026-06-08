---
name: sciskillhub
description: Use when a user needs to find the right skill for a research task, especially when the task can be mapped to Concepts and Theory, Research Capabilities, Methods and Techniques, Software and Tools, Instruments and Equipment, Data and Resources, Workflows, or Standards and Guidelines, or when the research stage belongs to Study Design, Data / Sample Acquisition, Data PreProcessing, Data Analysis and Modeling, Validation and Interpretation, Visualization and Publication, Writing and Publication, or Reproducibility, Collaboration and Management. Use this skill to query SciSkillHub for the most appropriate skill. Supports multi-value object and stage queries.
metadata:
    skill-author: sciskillhub
    homepage: https://sciskillhub.org
    version: 0.1.0
---

# sciskillhub - Skill Routing via CLI

SciSkillHub is a skill distribution platform for AI agents.

This skill is used to:

- Provide SciSkillHub CLI (`sciskill`) query commands and the recommended call sequence
- Tell local agents how to narrow the search space by `object / stage / domains` because object and stage fields support multiple values
- Return candidate skill lists for the local agent to evaluate further

Use this skill first in these situations:

- The user explicitly asks to "find a suitable skill / workflow / method / tool"
- The user's question is essentially asking "which SciSkillHub skill should be used for this requirement?"
- The current user task can be classified into one of these object types:
  `Concepts and Theory`, `Research Capabilities`, `Methods and Techniques`, `Software and Tools`, `Instruments and Equipment`, `Data and Resources`, `Workflows`, `Standards and Guidelines`
- The current user task mainly belongs to one of these research stages:
  `Study Design`, `Data / Sample Acquisition`, `Data PreProcessing`, `Data Analysis and Modeling`, `Validation and Interpretation`, `Visualization and Presentation`, `Writing and Publication`, `Reproducibility, Collaboration and Management`

The local agent must make these judgments first from the current user request:

- Which `object` the task belongs to
- Which `stage` the task mainly belongs to
- Which `domains` the task involves
- Which candidate `tasks` best match the current intent

---

## Recommended Call Flow

```text
User natural-language input
  -> Local agent identifies possible object values (2-3 candidates)
  -> Local agent identifies possible stage values (1-2 candidates)
  -> Local agent identifies domains
  -> Local agent decomposes the user task into 2-3 independent conceptual dimensions
  -> Path A: query tasks for each object+stage combination (can run in parallel)
  -> Path B: run keyword queries for each conceptual dimension in parallel (general terms before specific terms)
  -> If Path A returns relevant tasks: query skills with object + stage + tasks + domains
  -> Path B continues returning query-matched skills
  -> Evaluate applicability for all returned results (fit to the user's specific scenario and data type)
  -> Combine skill results from both paths, deduplicate them, and choose the best matching skills
```

Recommended order:

1. First list possible `object` values locally. Do not choose only one; try 2-3 relevant candidates.
2. Then list possible `stage` values locally, usually 1-2 candidates.
3. Then identify `domains`.
4. Decompose the user task into 2-3 independent conceptual dimensions and extract keywords for each dimension.
5. Query multiple object+stage combinations to improve coverage.
6. In parallel with the structured query path, query each conceptual dimension by keyword, starting with broad keywords.
7. Evaluate all returned results and filter out skills that do not fit the user's concrete scenario.
8. Combine results before final filtering. Do not lock onto a single combination at the start.

**Important: try multiple combinations**

Many tasks span multiple objects or stages. For example, "long-read sequencing data analysis":

- `Methods and Techniques` + `Data Analysis and Modeling` -> analysis methods
- `Software and Tools` + `Data Analysis and Modeling` -> analysis software
- `Data and Resources` + `Data Analysis and Modeling` -> data resources

If only one object is selected, relevant skills from other dimensions may be missed. Query the 2-3 most plausible combinations, then combine and deduplicate the results.

**Important: decompose task dimensions**

Many tasks contain several independent concepts. The local agent should decompose the user input into 2-3 dimensions and query each as keywords:

- "single-cell data CNV analysis" -> dimension 1: `single cell`, dimension 2: `CNV / copy number`
- "tumor spatial transcriptomics cell communication" -> dimension 1: `spatial transcriptomics`, dimension 2: `cell communication`
- "long-read sequencing data alignment" -> dimension 1: `long read / nanopore`, dimension 2: `alignment`

Decomposition rules:

- Express each dimension with 1-2 short keywords.
- Dimensions should be relatively independent, not just sentence fragments.
- Query each dimension separately, then inspect both overlap and complementarity.
- After decomposition, also run one **combined query** by joining the dimension keywords to capture skills that cover multiple dimensions at once.

**Important: run structured and keyword paths in parallel**

- `tax --tasks` is the recommended entry point, but it is not the only entry point.
- For some tasks, returned tasks may be too broad, clearly off target, or insufficient even when results exist.
- Therefore, keyword queries should run in parallel by default, not only after the structured path fails.
- The final decision should combine results from the `tasks` path and the `query` path, then deduplicate and evaluate them.

---

## Fixed Object List

`object` is a fixed enumeration. The local agent should select **2-3 most likely candidates**:

- `Concepts and Theory`
- `Research Capabilities`
- `Methods and Techniques`
- `Software and Tools`
- `Instruments and Equipment`
- `Data and Resources`
- `Workflows`
- `Standards and Guidelines`

Decision rules:

- Do not select only one object; many tasks span multiple dimensions.
- Tasks related to "data analysis" usually involve both `Methods and Techniques` and `Software and Tools`.
- Tasks related to "experimental design" may involve both `Research Capabilities` and `Workflows`.
- Query each candidate object, then combine and deduplicate the results.

---

## Fixed Stage List

`stage` is also a fixed enumeration. The local agent should select the **1-2 most relevant stages**:

- `Study Design`
- `Data / Sample Acquisition`
- `Data PreProcessing`
- `Data Analysis and Modeling`
- `Validation and Interpretation`
- `Visualization and Presentation`
- `Writing and Publication`
- `Reproducibility, Collaboration and Management`

Decision rules:

- Select the primary stage and add one secondary stage when needed.
- "Analyze data" usually maps to `Data Analysis and Modeling`.
- Upstream cleaning, alignment, and preprocessing usually map to `Data PreProcessing`.
- Plotting, reporting, and result presentation usually map to `Visualization and Presentation`.
- Versioning, workflow reproducibility, collaboration, and delivery usually map to `Reproducibility, Collaboration and Management`.

---

## Domain Selection

The local agent should classify `domains` from the user input first.

Common rules:

- Life science, medicine, omics, clinical work, and bioinformatics analysis should usually include `Life Sciences` or `Medical and Health Sciences`.
- Programming, modeling, algorithms, systems, and data engineering should usually include `Computational Sciences`.
- General research capabilities and cross-disciplinary research methods may include `General Research`.

For interdisciplinary tasks:

- Keep the primary domain.
- Add 1-2 secondary domains when useful.
- Do not pass too many domains at once, because this can fragment the result set.

---

## Command 0: View Taxonomy Enumerations

Purpose:

- Read the standard `object / stage / domain` enumerations.
- Ensure that local agents use platform-approved values when passing arguments.

Command:

```bash
sciskill tax
```

Example output:

```text
Object (--object-list)
  * Concepts and Theory
  * Research Capabilities
  * Methods and Techniques
  * Software and Tools
  * Instruments and Equipment
  * Data and Resources
  * Workflows
  * Standards and Guidelines

Stage (--stage-list)
  * Study Design
  * Data / Sample Acquisition
  * Data PreProcessing
  * Data Analysis and Modeling
  * Validation and Interpretation
  * Visualization and Presentation
  * Writing and Publication
  * Reproducibility, Collaboration and Management

Domain (--domain-list)
  * Life Sciences
  * Computational Sciences
  * General Research
  * ...
```

Options:

- `sciskill tax --object-list` - show only objects
- `sciskill tax --stage-list` - show only stages
- `sciskill tax --domain-list` - show only domains
- `sciskill tax --task-list` - show only tasks; tasks are hidden by default
- `sciskill tax --refresh` - force refresh the cache
- `sciskill tax --json` - output JSON

---

## Command 1: Query Tasks by Object + Stage + Domains

Purpose:

- Narrow `tasks` using the already inferred `object + stage + domains`.
- This is the recommended entry point, but it is not the only allowed entry point.

Command:

```bash
sciskill tax --tasks --object "Research Capabilities" --object "Methods and Techniques" --stage "Study Design" --domain "Life Sciences"
```

Example output:

```text
Tasks (3 total)
  Object(s): Research Capabilities, Methods and Techniques
  Stage(s): Study Design
  Domains: Life Sciences

  * Hypothesis Building (12)
  * Problem Definition (9)
  * Experimental Design (7)
```

Options:

- `--object <values...>` - filter by object; can be passed multiple times
- `--stage <values...>` - filter by stage; can be passed multiple times
- `--domain <values...>` - filter by domain; can be passed multiple times
- `--limit <n>` - number of results to return; default 100
- `--json` - output JSON

What the local agent should do at this step:

- Do not accept every returned task blindly.
- Select 1-3 tasks that best match the current user intent.
- If no task is clearly relevant, do not force one.
- Even while querying tasks, keep the parallel keyword-query path active. Do not treat keyword query as a fallback that only runs after failure.

---

## Command 2: Query Skills by Object + Stage + Tasks + Domains

Purpose:

- Retrieve candidate `skill list` entries using structured filters.
- Let the local agent decide which specific skill should actually be used.

Command:

```bash
sciskill browse skills --object "Research Capabilities" --stage "Study Design" --task "Hypothesis Building" "Experimental Design" --domain "Life Sciences"
```

Example output:

```text
Found 27 skills:

  #  Name                      Objects                           Stages                          Author         Path
  1. hypothesis-generation     Research Capabilities Study Design    FreedomIntell  hypothesis-generation
  ...

Install with: sciskill install <author>/<path>
```

Options:

- `--object <values...>` - filter by object
- `--stage <values...>` - filter by stage
- `--task <values...>` - filter by tasks; can pass multiple values
- `--domain <values...>` - filter by domains; can pass multiple values
- `-q, --query <text>` - additional keyword filter
- `--sort <field>` - sort by name, stars, recent, or score
- `--order <dir>` - sort direction: asc or desc
- `-l, --limit <n>` - number of results to return; default 20
- `--json` - output JSON

What the local agent should do at this step:

- Check whether each returned skill truly matches the current user task. Prefer checking the multi-value `objects` and `stages` fields.
- Select the best 1-3 skills.
- Do not assume a skill must be used just because it appears in the result list.
- If the `task` path produces weak results, omit `--task`, keep `object + stage + domains`, and add `-q`.

---

## Command 2B: Parallel Keyword Skill Queries

Purpose:

- Run in parallel with the structured path by default.
- This is a normal retrieval path, not a recovery step after failure.
- When `tasks` results are empty, too broad, or unable to cover the user's real intent, this path often surfaces relevant skills faster.
- Keyword queries are allowed. What is not allowed is skipping task understanding and structured judgment entirely.

### Keyword Strategy: General Before Specific

Organize keyword queries from **general -> specific**. Start with broad terms that maximize coverage.

**Round 1 (general keywords)**: use the broadest expression for each decomposed task dimension.

```bash
# "single-cell data CNV analysis" decomposed into two dimensions
# Dimension 1: single cell
sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "single cell"
# Dimension 2: CNV
sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "cnv"
sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "copy number"
```

**Round 2 (combined + specific keywords)**: after broad terms, add specific tool or method names.

```bash
# Combine two dimensions
sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "single cell cnv"
# Specific tool names, if the user mentioned them or you already know them
sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "infercnv"
sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "copykat"
```

### Keyword Selection Rules

- **General before specific**: use broad terms such as `single cell` and `cnv` first, then specific tool names such as `infercnv` and `copykat` to catch misses.
- **Do not search only one long phrase**: split into several short queries and run them in parallel.
  - Good: `cnv`, `copy number`, `single cell` queried separately in parallel.
  - Bad: `single cell CNV analysis for tumor data` stuffed into one query.
- **Organize by dimension**: query each decomposed dimension independently, then run one combined query.
- **Keep keywords short**: 1-3 words is best. Avoid passing the whole natural-language sentence directly.
- **Prefer domain terms, method terms, and tool terms**. Avoid filler words and stop words.

### When to Prioritize This Path

- `tax --tasks` returns irrelevant tasks.
- `tax --tasks` returns tasks that are too broad to support precise filtering.
- The user task contains multiple independent concepts, such as "single-cell + CNV", and the structured path may not cover both at once.
- You suspect metadata is incomplete and structured filters may miss skills.
- A skill type is usually easier to find by name or description than by task enumeration.

---

## Applicability Evaluation

The returned skill list is not the final answer. The local agent must evaluate each candidate skill for **applicability** and check whether it truly matches the user's concrete scenario.

### Evaluation Steps

1. **Read the skill description and use cases**: use `--json` to get full information, especially `description`, `use_cases`, and `workflows`.
2. **Compare data type**: is the user asking about scRNA-seq, WES, WGS, ATAC-seq, or bulk RNA-seq? What input does the skill support?
3. **Compare analysis goal**: does the user need calling, annotation, visualization, or integration? Which step does the skill cover?
4. **Actively mark mismatches**: if a skill clearly targets another data type or scenario, exclude it directly and tell the user why.

### Common Applicability Pitfalls

| Pitfall | Explanation | Response |
|---|---|---|
| bulk vs single-cell | The same analysis task, such as CNV, often uses completely different tools for bulk and single-cell data | Check the data type in the skill description and distinguish "sequencing data" from "single-cell RNA-seq" |
| WES vs WGS vs panel | Tools such as CNVkit and GATK CNV target specific sequencing types | Confirm the skill's scope |
| calling vs annotation vs visualization | Upstream and downstream steps of one workflow use different tools | Confirm which step the user needs |
| human vs model organism | Some tools only support specific species or genomes | Check species support |

### Applicability Example

User task: "single-cell data CNV analysis"

Returned skill list:

- `cnv-caller-agent` - "detect CNVs from sequencing data for cancer genomics"
- `bio-copy-number-cnvkit-analysis` - "detect CNVs from targeted/exome sequencing using CNVkit"
- `bio-copy-number-gatk-cnv` - "GATK CNV calling"

Applicability evaluation:

- `cnv-caller-agent`: described as "sequencing data" and does not mention single-cell -> **possibly not applicable; needs further confirmation**
- `bio-copy-number-cnvkit-analysis`: explicitly says "targeted/exome sequencing" -> **not applicable to scRNA-seq**
- `bio-copy-number-gatk-cnv`: GATK CNV is a bulk WES tool -> **not applicable to scRNA-seq**

Conclusion: the current results contain **no skill directly applicable to scRNA-seq CNV inference**. Tell the user this clearly and suggest an alternative, such as installing a Scanpy skill and manually writing an inferCNV/CopyKAT analysis workflow.

### Evaluation Principles

- Do not assume a skill is applicable just because it appears in search results.
- Do not assume a generic description covers the user's specific scenario.
- **Active exclusion** is more important than **passive acceptance**.
- If all results are inapplicable, **clearly say that no directly matching skill was found** instead of forcing an unsuitable recommendation.
- When telling the user, explain **why** the results are inapplicable, such as data type, analysis step, or species mismatch.

---

## Command 3: Install a Skill

After finding a suitable skill, install it locally:

```bash
sciskill install <author>/<path> --agent claude
```

---

## Local Agent Responsibility Boundary

When using this skill, follow these boundaries:

- First identify `object`.
- Then identify `stage`.
- Then identify `domains`.
- Decompose the user task into 2-3 independent conceptual dimensions.
- Then run these paths in parallel by default:
  `sciskill tax --tasks` (structured path)
  and
  `sciskill browse skills ... -q <general keyword>` (keyword path, parallel by dimension)
- Evaluate applicability for all returned results.
- Finally combine both paths and select only truly applicable skills.

Do not reverse these responsibilities:

- **Do not use `sciskill search`** as a replacement for task understanding.
- Do not blindly search without judging `object/stage/domains`.
- Do not retrieve a pile of skills first and infer object/stage afterward.
- Do not treat the CLI as an "automatic classifier".
- Do not postpone the responsibility of classifying the current task's object/stage/domains until after querying.
- Do not skip applicability evaluation and treat query results as final recommendations.

One-sentence summary:

The local agent should first decide which `object / stage / domains` the current user task belongs to, then decompose the conceptual dimensions, run the **structured path + keyword path** in parallel, and finally evaluate applicability to filter out mismatched skills.

---

## When to Use This Skill

Use it first when:

- You need to dynamically select a skill for the current task.
- You already know the approximate `object / stage / domains` for the current task.
- You want to narrow `tasks` first, then retrieve a candidate skill list.

Do not prioritize it when:

- You already know the exact specific skill to invoke.
- The current task is just ordinary conversation and does not involve professional skill routing.
- You have not yet done basic task understanding and classification for the current request.

---

## Minimal Examples

### Example 1: Hypothesis Generation Workflow

User question:

```text
I need help designing a hypothesis-generation workflow for tumor single-cell research.
```

The local agent should first identify multiple candidate groups:

- `object = [Research Capabilities, Methods and Techniques]`
- `stage = [Study Design]`
- `domains = [Life Sciences, General Research]`
- Conceptual dimensions: `hypothesis`, `single cell`

Then run queries in parallel:

1. **Structured path**:
   - `sciskill tax --tasks --object "Research Capabilities" --stage "Study Design" --domain "Life Sciences" "General Research"`
   - `sciskill tax --tasks --object "Methods and Techniques" --stage "Study Design" --domain "Life Sciences" "General Research"`
2. **Keyword path (general)**:
   - `sciskill browse skills --object "Research Capabilities" --object "Methods and Techniques" --stage "Study Design" --domain "Life Sciences" -q "hypothesis"`
   - `sciskill browse skills --object "Research Capabilities" --object "Methods and Techniques" --stage "Study Design" --domain "Life Sciences" -q "single cell"`
3. Combine tasks and select `Hypothesis Building` and `Experimental Design`.
4. `sciskill browse skills --object "Research Capabilities" --object "Methods and Techniques" --stage "Study Design" --task "Hypothesis Building" "Experimental Design" --domain "Life Sciences" "General Research"`
5. `sciskill browse skills --object "Research Capabilities" --object "Methods and Techniques" --stage "Study Design" --task "Hypothesis Building" "Experimental Design" --domain "Life Sciences" "General Research"`
6. **Applicability evaluation**: check whether candidate skills support tumor and single-cell scenarios.
7. Combine and deduplicate, then choose the best skill.
8. `sciskill install <author>/<path> --agent claude`

### Example 2: Long-Read Sequencing Data Analysis

User question:

```text
Help me analyze Nanopore long-read sequencing data.
```

The local agent should identify:

- `object = [Methods and Techniques, Software and Tools, Data and Resources]`
- `stage = [Data Analysis and Modeling]`
- `domains = [Life Sciences]`
- Conceptual dimensions: `nanopore / long read`, `alignment / analysis`

Then run queries in parallel:

1. **Structured path**:
   - `sciskill tax --tasks --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences"`
   - `sciskill tax --tasks --object "Software and Tools" --stage "Data Analysis and Modeling" --domain "Life Sciences"`
2. **Keyword path (general)**:
   - `sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "nanopore"`
   - `sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "long read"`
3. Combine tasks and select `Quality Control`, `Alignment`, and `Quantification`.
4. `sciskill browse skills --object "Methods and Techniques" --object "Software and Tools" --stage "Data Analysis and Modeling" --task "Quality Control" "Alignment" "Quantification" --domain "Life Sciences"`
5. `sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --task "Quality Control" "Alignment" "Quantification" --domain "Life Sciences"`
6. **Applicability evaluation**: confirm that the skill supports long-read data rather than only short-read data.
7. Combine and deduplicate, then choose the best skill.
8. `sciskill install <author>/<path> --agent claude`

### Example 3: Single-Cell CNV Analysis Across Dimensions

User question:

```text
Single-cell data CNV analysis.
```

The local agent should identify:

- `object = [Methods and Techniques, Software and Tools]`
- `stage = [Data Analysis and Modeling]`
- `domains = [Life Sciences]`
- Conceptual dimensions: **dimension 1 = `single cell`**, **dimension 2 = `CNV / copy number`**

Then run queries in parallel:

1. **Structured path**:
   - `sciskill tax --tasks --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences"`
   - `sciskill tax --tasks --object "Software and Tools" --stage "Data Analysis and Modeling" --domain "Life Sciences"`
2. **Keyword path (round 1: general, parallel by dimension)**:
   - `sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "single cell"`
   - `sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "cnv"`
   - `sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "copy number"`
3. **Keyword path (round 2: combined + specific)**:
   - `sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "single cell cnv"`
   - `sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "infercnv"`
   - `sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --domain "Life Sciences" -q "copykat"`
4. Combine the structured-path task `copy number variation`.
5. `sciskill browse skills --object "Software and Tools" --object "Methods and Techniques" --stage "Data Analysis and Modeling" --task "copy number variation" --domain "Life Sciences"`
6. **Applicability evaluation** (critical step):
   - `cnv-caller-agent`: described as "detect CNVs from sequencing data" -> does not mention single-cell -> **possibly not applicable**
   - `bio-copy-number-cnvkit-analysis`: explicitly says "targeted/exome sequencing" -> **not applicable to scRNA-seq**
   - `bio-copy-number-gatk-cnv`: GATK CNV is a bulk WES tool -> **not applicable to scRNA-seq**
7. **Conclusion**: there is currently no skill directly applicable to scRNA-seq CNV inference. Tell the user and suggest an alternative.
8. If the user accepts the alternative: `sciskill install <scanpy skill> --agent claude`

---

## Final Principle

This skill is a "query entry point", not a "classification judge".

The local agent should first understand the task, decompose dimensions, use the CLI, and then evaluate applicability.
