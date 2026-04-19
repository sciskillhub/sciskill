# Annotation Heuristics

## Goal

Infer two sets from existing cell annotations:

- **normal baseline categories**
- **suspect malignant lineage categories**

These heuristics are for the agent reading `adata.obs` labels. They are not script-side keyword rules.

## Normal baseline labels

Usually safe to include:

- T cells
- B cells
- NK cells
- monocytes
- macrophages
- mast cells
- dendritic cells
- plasma cells
- fibroblasts
- endothelial cells
- pericytes
- smooth muscle cells
- generic stromal labels

Typical label families to look for:

- `t cell`
- `b cell`
- `nk`
- `monocyte`
- `macrophage`
- `mast`
- `dc`
- `dendritic`
- `plasma`
- `fibro`
- `endothelial`
- `pericyte`
- `smooth muscle`
- `stromal`
- `immune`

## Suspect malignant lineage labels

These are not automatically tumor. They are just the cell populations where tumor cells are more plausible and where refinement should happen.

Common examples:

- epithelial
- tumor
- malignant
- cancer
- neoplastic
- carcinoma
- alveolar
- ciliated
- club
- basal
- secretory

Typical label families to look for:

- `epithelial`
- `tumor`
- `malignant`
- `cancer`
- `neoplastic`
- `carcinoma`

## Important caution

- In carcinoma-style datasets, epithelial and related lineages are often the primary tumor-search space and should usually be considered first when choosing `suspect-cats`.
- Even in that setting, keep these labels as `suspect` input categories for CNV inference rather than pre-labeling every cell in the lineage as malignant before analysis.
- High-CNV cells are strong tumor candidates, but final malignant interpretation should still consider annotation context, sample context, and downstream validation where available.
- Treat these heuristics as a first-pass decision aid for choosing `reference-cats` and `suspect-cats`, and allow user override whenever annotation naming is unusual.
- If no suspect malignant labels can be justified from the annotation column, stop and ask for explicit confirmation instead of silently continuing.
