---
name: infercnvpy-skill
description: scRNA-seq CNV analysis with infercnvpy. Infer copy number variation (CNV) from scRNA-seq data. Plays nicely with Scanpy and AnnData.
metadata:
    author: sciskillhub
    version: 0.1.4
---

# infercnvpy-skill

Use this skill for **general scRNA-seq CNV analysis** with `infercnvpy`, especially when:

- the data are already in `AnnData`
- cell annotations already exist in `adata.obs`
- normal reference cells must be inferred from annotation labels
- malignant candidates must be inferred from annotation labels
- the user wants an automatic tumor/normal or tumor-candidate labeling workflow

## What this skill does

This skill provides:

- an annotation-guided workflow for choosing `infercnv` reference cells
- heuristics for manually selecting normal baseline cell types and suspect malignant lineages from `adata.obs`
- a per-cell scoring workflow:
  - `cnv_score_cell`
  - `cnv_normal_distance`
  - `cnv_segment_score`
- a two-stage automatic labeling strategy
- default chromosome heatmap outputs for all cells
- a reusable script for arbitrary `.h5ad` input

## Input assumptions

- `AnnData` is already quality-controlled
- expression is normalized and log-transformed for `infercnvpy`
- a cell-annotation column exists in `adata.obs`

## Core workflow

1. Load a user-provided `.h5ad`.
2. Confirm the `infercnvpy` prerequisites:
   - normalized/log-transformed expression
   - genomic coordinates in `adata.var`
   - annotation column in `adata.obs`
   - inspect the preflight summary for annotation-column presence, available labels, genomic-position completeness, `X` dtype, value range, nonzero-per-cell counts, and normalization/log1p hints in `adata.uns` or `adata.layers`
3. If `chromosome`, `start`, or `end` are missing from `adata.var`, add genomic positions first:
   - prefer `infercnvpy.io.genomic_position_from_gtf`
   - fall back to `infercnvpy.io.genomic_position_from_biomart`
4. Inspect `adata.obs[annotation_col]` labels and their counts.
5. Choose normal reference categories explicitly from the observed labels.
6. Choose suspect malignant lineages explicitly from the observed labels.
   - if no suspect malignant categories can be justified from the user context and `adata.obs`, stop and ask for confirmation
   - do not continue CNV labeling until the suspect malignant lineages are explicitly confirmed
7. Run `cnv.tl.infercnv(...)` with explicit `--reference-cats` and `--suspect-cats`.
8. Compute per-cell CNV features:
   - per-cell CNV score (`cnv_score_cell`)
   - distance from normal baseline
   - contiguous abnormal segment score
9. Stage 1:
   - mark cells outside the normal baseline range as `tumor_like`
10. Stage 2:
   - restrict to suspect malignant lineages
   - use `cnv_segment_score` to promote high-confidence tumor cells
11. Save labels and scores back into `AnnData`.
12. Write standard plots:
   - per-cell CNV score and segment score distributions
   - expression-space embeddings if available
   - chromosome heatmaps for all cells grouped by automatic CNV status and by the input annotation column

## Why annotation-guided inference matters

For most scRNA-seq datasets, automatic CNV analysis is only as good as the normal reference set. Existing cell annotations usually contain enough information to build a reasonable first-pass reference:

- immune cells are usually safe normal references
- stromal cells are often safe normal references
- epithelial-lineage cells are often where malignant candidates live in carcinomas

The same annotation column should therefore drive both:

- baseline selection
- suspect lineage selection

In this skill, that decision is made by the agent after inspecting the actual labels in `adata.obs`. The bundled script does not do keyword-based auto-matching.

## Practical defaults

- Stage 1 per-cell CNV score threshold: `mean + 2*sd` on baseline normals
- Stage 1 normal-distance threshold: `q99` on baseline normals
- Stage 2 segment threshold: `mean + 2*sd` on baseline normals

These are defaults, not universal truths. Use stricter thresholds when false positives are more costly than false negatives.

## Recommended labels

The bundled workflow writes three automatic labels:

- `normal`
- `tumor_candidate`
- `tumor_high_cnv`

Interpretation:

- `normal`: not clearly outside the normal baseline
- `tumor_candidate`: abnormal but not yet high-confidence CNV tumor
- `tumor_high_cnv`: abnormal and supported by contiguous CNV segment structure in suspect malignant lineages

## Default plot outputs

The bundled script writes these standard figures into `--output-dir`:

- `01_global_baseline_distribution.png`
- `02_candidate_feature_scatter.png`
- `03_segment_score_distribution.png`
- `04_expression_umap_labels.png` when `X_umap` exists
- `05_expression_umap_scores.png` when `X_umap` exists
- `06_chromosome_heatmap_all_by_cnv_status.png`
- `07_chromosome_heatmap_all_by_annotation.png`

## Files

- Main script:
  - [scripts/run_infercnvpy.py](scripts/run_infercnvpy.py)
- Expression preflight script:
  - [scripts/check_preflight.py](scripts/check_preflight.py)
- References:
  - [references/genomic_positions.md](references/genomic_positions.md)
  - [references/annotation_heuristics.md](references/annotation_heuristics.md)
  - [references/feature_definitions.md](references/feature_definitions.md)

## When to read references

- Read `references/genomic_positions.md` when `adata.var` is missing genomic coordinates and positions must be added from GTF or Biomart.
- Read `references/annotation_heuristics.md` when deciding which labels should be normal references and which labels should be suspect malignant lineages.
- Read `references/feature_definitions.md` when tuning the automatic CNV features or justifying the method.

## Running the bundled script

Example:

```bash
python \
./scripts/check_preflight.py \
--input-h5ad /path/to/input.h5ad \
--annotation-col cell_type \
--check-mode warn

PYTHONPATH=/data20T/dev/agenticbioinfo/sciskillhub/infercnvpy/src \
python \
./scripts/run_infercnvpy.py \
--input-h5ad /path/to/input.h5ad \
--annotation-col cell_type \
--reference-cats "T cell CD4,T cell CD8,B cell,NK cell,Fibroblast,Endothelial cell" \
--suspect-cats "Epithelial cell,Ciliated" \
--output-dir /path/to/output_dir

# Optional: skip heatmaps for large datasets
python \
./scripts/run_infercnvpy.py \
--input-h5ad /path/to/input.h5ad \
--annotation-col cell_type \
--reference-cats "T cell CD4,T cell CD8,B cell,NK cell,Fibroblast,Endothelial cell" \
--suspect-cats "Epithelial cell,Ciliated" \
--output-dir /path/to/output_dir \
--skip-heatmaps
```

## Recommended usage pattern

First inspect `adata.obs[annotation_col]` directly, then choose categories explicitly and pass them to the script. The agent should not rely on keyword matching inside the script.

Use the separate preflight script first when checking a new dataset. It reports:

- whether `annotation_col` exists in `adata.obs`
- the available annotation labels and counts
- whether `adata.var` contains complete `chromosome/start/end` coordinates
- whether `X` looks more like normalized/log-transformed expression or suspicious raw/scaled input

The main infercnv script reuses the same preflight logic before CNV inference. If `X` looks like raw counts or scaled data, it will warn by default. Use `--expression-check-mode fail` when you want the run to stop on suspicious input.

Important reminder:
If no suspect malignant labels can be justified from the annotation column, stop and ask for explicit confirmation instead of silently continuing.

The main script now also writes whole-dataset `cnv.pl.chromosome_heatmap(...)` outputs. These heatmaps use all cells in the supplied `AnnData`, grouped by:

- `cnv_status_2stage`
- `annotation_col`

Use `--skip-heatmaps` when the dataset is large enough that full-cell heatmaps would be too slow or too large to inspect comfortably.

Override or refine the initial category choice when:

- the dataset uses nonstandard annotation names
- epithelial subtypes are mixed with clearly normal epithelial cells
- the user already knows the exact normal reference set

If no suspect malignant categories can be justified from `adata.obs`, stop and ask the user to confirm them explicitly before continuing. In scripted runs, fail fast and require both `--reference-cats` and `--suspect-cats`.

## Notes

- Prefer per-cell scoring over cluster-only scoring when cluster count is small.
- Do not treat the output as ground truth without checking whether the inferred normal references make biological sense.
- Segment-continuity remains the automatic quantitative readout for broad contiguous CNV structure, even though the default workflow now also saves whole-cell chromosome heatmaps for manual review.
