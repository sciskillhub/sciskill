# Feature Definitions

## `cnv_score_cell`

Per-cell CNV score:

`mean(abs(X_cnv_i))`

Interpretation:

- high values mean strong overall CNV deviation
- useful for first-pass abnormality screening

## `cnv_normal_distance`

Distance from the normal-baseline centroid.

Procedure:

1. compute a baseline centroid from normal reference cells in `X_cnv`
2. compute similarity of each cell to the centroid
3. convert similarity into a distance-like score

Interpretation:

- high values mean the cell profile does not look like normal baseline cells
- complements the per-cell CNV score

## `cnv_segment_score`

Automatic proxy for “broad, contiguous CNV blocks” seen in chromosome heatmaps.

Procedure:

1. z-score each CNV bin using the baseline normal cells
2. mark bins where `abs(z) >= z_threshold`
3. keep only same-sign runs of length `>= min_run`
4. compute the fraction of bins belonging to valid runs

Interpretation:

- low score: fragmented or noise-like deviation
- high score: segment-like CNV structure

This is the most important feature for replacing manual heatmap inspection in automated pipelines.
