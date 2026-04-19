#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import scipy.sparse as sp

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import infercnvpy as cnv
import scanpy as sc
from check_preflight import enforce_expression_preflight, enforce_input_structure_preflight


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run annotation-guided infercnvpy analysis on an h5ad dataset.")
    parser.add_argument("--input-h5ad", type=Path, required=True, help="Input AnnData file.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for outputs.")
    parser.add_argument("--annotation-col", default="cell_type", help="obs column containing cell annotations.")
    parser.add_argument("--window-size", type=int, default=250, help="Window size for infercnv.")
    parser.add_argument(
        "--reference-cats",
        default="",
        help="Comma-separated normal reference categories selected explicitly from adata.obs[annotation_col].",
    )
    parser.add_argument(
        "--suspect-cats",
        default="",
        help="Comma-separated suspect malignant lineage categories selected explicitly from adata.obs[annotation_col].",
    )
    parser.add_argument("--stage1-mode", choices=["mean+2sd", "mean+3sd", "q95", "q99"], default="mean+2sd")
    parser.add_argument("--distance-mode", choices=["mean+2sd", "mean+3sd", "q95", "q99"], default="q99")
    parser.add_argument("--segment-mode", choices=["mean+2sd", "mean+3sd", "q95", "q99"], default="mean+2sd")
    parser.add_argument("--segment-z-threshold", type=float, default=2.5)
    parser.add_argument("--segment-min-run", type=int, default=5)
    parser.add_argument(
        "--expression-check-mode",
        choices=["warn", "fail", "off"],
        default="warn",
        help="How to handle suspicious expression matrices during preflight validation.",
    )
    parser.add_argument(
        "--skip-heatmaps",
        action="store_true",
        help="Skip chromosome heatmap outputs. Useful for very large datasets or headless batch runs.",
    )
    return parser.parse_args()


def choose_threshold(base_scores: pd.Series, mode: str) -> float:
    if mode == "mean+2sd":
        return float(base_scores.mean() + 2 * base_scores.std())
    if mode == "mean+3sd":
        return float(base_scores.mean() + 3 * base_scores.std())
    if mode == "q95":
        return float(base_scores.quantile(0.95))
    if mode == "q99":
        return float(base_scores.quantile(0.99))
    raise ValueError(mode)


def parse_categories_arg(raw_value: str, flag_name: str) -> list[str]:
    categories = [x.strip() for x in raw_value.split(",") if x.strip()]
    if not categories:
        raise ValueError(f"{flag_name} must contain at least one category.")
    return categories


def format_available_annotations(labels: pd.Series) -> str:
    counts = labels.astype(str).value_counts()
    return ", ".join(f"{label} (n={count})" for label, count in counts.items())


def fail_missing_category_args(labels: pd.Series, annotation_col: str, missing_flags: list[str]) -> None:
    available = format_available_annotations(labels)
    message = (
        "Missing required category arguments.\n"
        f"Annotation column: {annotation_col}\n"
        f"Missing flags: {', '.join(missing_flags)}\n"
        f"Available annotations: {available}\n"
        "Inspect the labels above and rerun with explicit comma-separated category lists."
    )
    print(message, file=sys.stderr)
    raise ValueError(message)


def validate_selected_categories(
    labels: pd.Series,
    annotation_col: str,
    reference_cats: list[str],
    suspect_cats: list[str],
) -> None:
    available = set(labels.astype(str).unique())
    missing_reference = sorted(set(reference_cats).difference(available))
    missing_suspect = sorted(set(suspect_cats).difference(available))
    overlap = sorted(set(reference_cats).intersection(suspect_cats))

    if not missing_reference and not missing_suspect and not overlap:
        return

    available = format_available_annotations(labels)
    parts = [f"Annotation column: {annotation_col}", f"Available annotations: {available}"]
    if missing_reference:
        parts.append(f"Unknown --reference-cats labels: {missing_reference}")
    if missing_suspect:
        parts.append(f"Unknown --suspect-cats labels: {missing_suspect}")
    if overlap:
        parts.append(f"Overlapping reference and suspect labels are not allowed: {overlap}")
    message = "Invalid category selection.\n" + "\n".join(parts)
    print(message, file=sys.stderr)
    raise ValueError(message)


def get_dense_cnv_matrix(adata) -> np.ndarray:
    x_cnv = adata.obsm["X_cnv"]
    if sp.issparse(x_cnv):
        return x_cnv.toarray()
    return np.asarray(x_cnv)


def compute_normal_distance(x_cnv: np.ndarray, baseline_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    normal_centroid = x_cnv[baseline_mask].mean(axis=0)
    centered_centroid = normal_centroid - normal_centroid.mean()
    centroid_norm = np.linalg.norm(centered_centroid)
    centered_cells = x_cnv - x_cnv.mean(axis=1, keepdims=True)
    cell_norm = np.linalg.norm(centered_cells, axis=1)
    denom = cell_norm * centroid_norm
    corr = np.divide(centered_cells @ centered_centroid, denom, out=np.zeros(x_cnv.shape[0]), where=denom > 0)
    return 1.0 - corr, normal_centroid


def _segment_fraction_from_z(z_row: np.ndarray, z_threshold: float, min_run: int) -> tuple[float, float]:
    active = np.abs(z_row) >= z_threshold
    signs = np.sign(z_row)
    qualifying_bins = 0
    longest_run = 0
    current_run = 0
    current_sign = 0.0
    for is_active, sign in zip(active, signs):
        if is_active and sign != 0:
            if current_run > 0 and sign == current_sign:
                current_run += 1
            else:
                if current_run >= min_run:
                    qualifying_bins += current_run
                    longest_run = max(longest_run, current_run)
                current_run = 1
                current_sign = sign
        else:
            if current_run >= min_run:
                qualifying_bins += current_run
                longest_run = max(longest_run, current_run)
            current_run = 0
            current_sign = 0.0
    if current_run >= min_run:
        qualifying_bins += current_run
        longest_run = max(longest_run, current_run)
    return qualifying_bins / z_row.shape[0], longest_run / z_row.shape[0]


def compute_segment_scores(x_cnv: np.ndarray, baseline_mask: np.ndarray, z_threshold: float, min_run: int) -> tuple[np.ndarray, np.ndarray]:
    base_mean = x_cnv[baseline_mask].mean(axis=0)
    base_std = x_cnv[baseline_mask].std(axis=0)
    base_std = np.where(base_std < 1e-6, 1e-6, base_std)
    z = (x_cnv - base_mean) / base_std
    segment_fraction = np.zeros(x_cnv.shape[0], dtype=float)
    longest_fraction = np.zeros(x_cnv.shape[0], dtype=float)
    for idx, row in enumerate(z):
        segment_fraction[idx], longest_fraction[idx] = _segment_fraction_from_z(row, z_threshold, min_run)
    return segment_fraction, longest_fraction


def ordered_categories_from_obs(series: pd.Series) -> list[str]:
    if isinstance(series.dtype, pd.CategoricalDtype):
        return [str(x) for x in series.cat.categories if pd.notna(x)]
    return list(series.astype(str).value_counts().index)


def build_output_files(has_umap: bool, skip_heatmaps: bool) -> list[str]:
    output_files = [
        "annotated_infercnvpy_labels.h5ad",
        "summary.json",
        "01_global_baseline_distribution.png",
        "02_candidate_feature_scatter.png",
        "03_segment_score_distribution.png",
    ]
    if has_umap:
        output_files.extend(
            [
                "04_expression_umap_labels.png",
                "05_expression_umap_scores.png",
            ]
        )
    if not skip_heatmaps:
        output_files.extend(
            [
                "06_chromosome_heatmap_all_by_cnv_status.png",
                "07_chromosome_heatmap_all_by_annotation.png",
            ]
        )
    return output_files


def write_chromosome_heatmaps(output_dir: Path, adata, annotation_col: str) -> list[str]:
    written_files = []
    try:
        adata.obs["_cnv_status_plot"] = pd.Categorical(
            adata.obs["cnv_status_2stage"].astype(str),
            categories=["normal", "tumor_candidate", "tumor_high_cnv"],
            ordered=True,
        )
        adata.obs["_annotation_plot"] = pd.Categorical(
            adata.obs[annotation_col].astype(str),
            categories=ordered_categories_from_obs(adata.obs[annotation_col]),
            ordered=True,
        )

        cnv.pl.chromosome_heatmap(
            adata,
            groupby="_cnv_status_plot",
            figsize=(18, 10),
            show=False,
            cmap="bwr",
        )
        plt.savefig(output_dir / "06_chromosome_heatmap_all_by_cnv_status.png", dpi=200, bbox_inches="tight")
        written_files.append("06_chromosome_heatmap_all_by_cnv_status.png")
        plt.close("all")

        cnv.pl.chromosome_heatmap(
            adata,
            groupby="_annotation_plot",
            figsize=(18, 10),
            show=False,
            cmap="bwr",
        )
        plt.savefig(output_dir / "07_chromosome_heatmap_all_by_annotation.png", dpi=200, bbox_inches="tight")
        written_files.append("07_chromosome_heatmap_all_by_annotation.png")
        plt.close("all")
    finally:
        adata.obs.drop(columns=["_cnv_status_plot", "_annotation_plot"], inplace=True, errors="ignore")
    return written_files


def write_plots(
    output_dir: Path,
    adata,
    annotation_col: str,
    skip_heatmaps: bool,
    baseline_scores: pd.Series,
    candidate_df: pd.DataFrame,
    score_threshold: float,
    distance_threshold: float,
    segment_threshold: float,
) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written_files = []

    bins = np.linspace(0, max(adata.obs["cnv_score_cell"].max(), 0.065), 80)
    non_base = adata.obs.loc[~adata.obs["is_normal_baseline"], "cnv_score_cell"]

    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    ax.hist(baseline_scores, bins=bins, alpha=0.65, color="#4C78A8", density=True, label="baseline")
    ax.hist(non_base, bins=bins, alpha=0.55, color="#E45756", density=True, label="non-baseline")
    ax.axvline(score_threshold, color="#2ca02c", linestyle="--", linewidth=1.8, label=f"score={score_threshold:.4f}")
    ax.set_xlabel("cnv_score_cell")
    ax.set_ylabel("density")
    ax.set_title("Per-cell CNV score distribution")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_dir / "01_global_baseline_distribution.png", bbox_inches="tight")
    written_files.append("01_global_baseline_distribution.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    ax.scatter(candidate_df["cnv_score_cell"], candidate_df["cnv_normal_distance"], s=16, alpha=0.65)
    ax.axvline(score_threshold, color="#2ca02c", linestyle="--", linewidth=1.5)
    ax.axhline(distance_threshold, color="#d62728", linestyle="--", linewidth=1.5)
    ax.set_xlabel("cnv_score_cell")
    ax.set_ylabel("cnv_normal_distance")
    ax.set_title("Candidate cells: per-cell CNV score vs normal distance")
    fig.tight_layout()
    fig.savefig(output_dir / "02_candidate_feature_scatter.png", bbox_inches="tight")
    written_files.append("02_candidate_feature_scatter.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    seg_bins = np.linspace(0, max(0.01, candidate_df["cnv_segment_score"].max() * 1.05), 50)
    ax.hist(
        adata.obs.loc[adata.obs["is_normal_baseline"], "cnv_segment_score"],
        bins=seg_bins,
        alpha=0.65,
        density=True,
        color="#4C78A8",
        label="baseline",
    )
    ax.hist(candidate_df["cnv_segment_score"], bins=seg_bins, alpha=0.55, density=True, color="#72B7B2", label="candidates")
    ax.axvline(segment_threshold, color="#d62728", linestyle="--", linewidth=1.8, label=f"segment={segment_threshold:.4f}")
    ax.set_xlabel("cnv_segment_score")
    ax.set_ylabel("density")
    ax.set_title("Segment-continuity score")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_dir / "03_segment_score_distribution.png", bbox_inches="tight")
    written_files.append("03_segment_score_distribution.png")
    plt.close(fig)

    if "X_umap" in adata.obsm:
        fig = sc.pl.umap(
            adata,
            color=["cnv_status_2stage", annotation_col],
            wspace=0.35,
            return_fig=True,
            show=False,
        )
        fig.savefig(output_dir / "04_expression_umap_labels.png", bbox_inches="tight", dpi=150)
        written_files.append("04_expression_umap_labels.png")
        plt.close(fig)

        fig = sc.pl.umap(
            adata,
            color=["cnv_score_cell", "cnv_normal_distance", "cnv_segment_score"],
            color_map="viridis",
            wspace=0.35,
            return_fig=True,
            show=False,
        )
        fig.savefig(output_dir / "05_expression_umap_scores.png", bbox_inches="tight", dpi=150)
        written_files.append("05_expression_umap_scores.png")
        plt.close(fig)

    if not skip_heatmaps:
        written_files.extend(write_chromosome_heatmaps(output_dir, adata, annotation_col))
    return written_files


def build_cluster_summary(adata, annotation_col: str) -> pd.DataFrame:
    return (
        adata.obs.groupby("cnv_leiden")
        .agg(
            n=("cnv_score_cell", "size"),
            cnv_score_cluster=("cnv_score", "first"),
            cnv_score_cell_mean=("cnv_score_cell", "mean"),
            cnv_normal_distance_mean=("cnv_normal_distance", "mean"),
            cnv_segment_score_mean=("cnv_segment_score", "mean"),
            tumor_candidate_frac=("cnv_status_2stage", lambda x: (x == "tumor_candidate").mean()),
            tumor_high_cnv_frac=("cnv_status_2stage", lambda x: (x == "tumor_high_cnv").mean()),
            major_annotation=(annotation_col, lambda x: x.value_counts().idxmax()),
        )
        .sort_values("cnv_score_cluster", ascending=False)
        .reset_index()
    )


def main() -> None:
    args = parse_args()
    adata = sc.read_h5ad(args.input_h5ad)
    input_structure_preflight = enforce_input_structure_preflight(adata, args.annotation_col)
    expression_preflight = enforce_expression_preflight(adata, args.expression_check_mode)

    labels = adata.obs[args.annotation_col].astype(str)
    missing_flags = []
    if not args.reference_cats.strip():
        missing_flags.append("--reference-cats")
    if not args.suspect_cats.strip():
        missing_flags.append("--suspect-cats")
    if missing_flags:
        fail_missing_category_args(labels, args.annotation_col, missing_flags)

    reference_cats = parse_categories_arg(args.reference_cats, "--reference-cats")
    suspect_cats = parse_categories_arg(args.suspect_cats, "--suspect-cats")
    validate_selected_categories(labels, args.annotation_col, reference_cats, suspect_cats)

    cnv.tl.infercnv(
        adata,
        reference_key=args.annotation_col,
        reference_cat=reference_cats,
        window_size=args.window_size,
    )
    cnv.tl.pca(adata)
    cnv.pp.neighbors(adata)
    cnv.tl.leiden(adata)
    cnv.tl.cnv_score(adata)

    x_cnv = get_dense_cnv_matrix(adata)
    adata.obs["is_normal_baseline"] = adata.obs[args.annotation_col].isin(reference_cats)
    baseline_mask = adata.obs["is_normal_baseline"].to_numpy()

    adata.obs["cnv_score_cell"] = np.abs(x_cnv).mean(axis=1)
    adata.obs["cnv_normal_distance"], _ = compute_normal_distance(x_cnv, baseline_mask)
    adata.obs["cnv_segment_score"], adata.obs["cnv_segment_longest"] = compute_segment_scores(
        x_cnv,
        baseline_mask,
        z_threshold=args.segment_z_threshold,
        min_run=args.segment_min_run,
    )

    base_score = adata.obs.loc[adata.obs["is_normal_baseline"], "cnv_score_cell"]
    base_distance = adata.obs.loc[adata.obs["is_normal_baseline"], "cnv_normal_distance"]
    base_segment = adata.obs.loc[adata.obs["is_normal_baseline"], "cnv_segment_score"]

    score_threshold = choose_threshold(base_score, args.stage1_mode)
    distance_threshold = choose_threshold(base_distance, args.distance_mode)
    segment_threshold = choose_threshold(base_segment, args.segment_mode)

    stage1_candidate = (adata.obs["cnv_score_cell"] > score_threshold) | (
        adata.obs["cnv_normal_distance"] > distance_threshold
    )
    adata.obs["stage1_status"] = np.where(stage1_candidate, "tumor_like", "normal_like")

    candidate_mask = (adata.obs["stage1_status"] == "tumor_like") & (adata.obs[args.annotation_col].isin(suspect_cats))
    candidates = adata.obs.loc[
        candidate_mask,
        [args.annotation_col, "cnv_score_cell", "cnv_normal_distance", "cnv_segment_score", "cnv_segment_longest"],
    ].copy()

    if candidates.empty:
        raise ValueError("No candidate cells remained after stage 1. Adjust thresholds or suspect categories.")

    adata.obs["cnv_status_2stage"] = "normal"
    adata.obs.loc[candidate_mask, "cnv_status_2stage"] = "tumor_candidate"
    candidate_index = candidates.index.to_numpy()
    high_conf_mask = candidates["cnv_segment_score"].to_numpy() > segment_threshold
    adata.obs.loc[candidate_index[high_conf_mask], "cnv_status_2stage"] = "tumor_high_cnv"

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_plots(
        args.output_dir,
        adata,
        args.annotation_col,
        args.skip_heatmaps,
        base_score,
        candidates,
        score_threshold,
        distance_threshold,
        segment_threshold,
    )
    output_files = build_output_files("X_umap" in adata.obsm, args.skip_heatmaps)
    adata.write_h5ad(args.output_dir / "annotated_infercnvpy_labels.h5ad")

    summary = {
        "input_h5ad": str(args.input_h5ad),
        "annotation_col": args.annotation_col,
        "input_structure_preflight": input_structure_preflight,
        "expression_preflight": expression_preflight,
        "reference_cats": reference_cats,
        "suspect_cats": suspect_cats,
        "n_cells": int(adata.n_obs),
        "n_cnv_bins": int(adata.obsm["X_cnv"].shape[1]),
        "stage1_threshold_cnv_score_cell": score_threshold,
        "stage1_threshold_distance": distance_threshold,
        "stage2_segment_threshold": segment_threshold,
        "status_2stage_counts": adata.obs["cnv_status_2stage"].value_counts().to_dict(),
        "baseline_cnv_score_cell_summary": base_score.describe().to_dict(),
        "baseline_distance_summary": base_distance.describe().to_dict(),
        "baseline_segment_summary": base_segment.describe().to_dict(),
        "candidate_annotation_counts": candidates[args.annotation_col].value_counts().to_dict(),
        "cluster_summary_top": build_cluster_summary(adata, args.annotation_col).to_dict(orient="records"),
        "heatmaps_enabled": not args.skip_heatmaps,
        "output_files": output_files,
    }

    with open(args.output_dir / "summary.json", "w") as handle:
        json.dump(summary, handle, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
