#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

import anndata as ad
import numpy as np
import scipy.sparse as sp


NORMALIZATION_HINTS = [
    "log1p",
    "normalize",
    "normalized",
    "norm",
    "scran",
    "sctransform",
    "size_factor",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether an AnnData object is ready for infercnvpy input.")
    parser.add_argument("--input-h5ad", type=Path, required=True, help="Input AnnData file.")
    parser.add_argument("--annotation-col", default="cell_type", help="obs column containing cell annotations.")
    parser.add_argument(
        "--check-mode",
        choices=["warn", "fail", "off"],
        default="warn",
        help="How to handle suspicious expression matrices.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional path to write the preflight summary as JSON.",
    )
    return parser.parse_args()


def _sample_nonzero_values(matrix, sample_size: int = 100000) -> np.ndarray:
    if sp.issparse(matrix):
        data = np.asarray(matrix.data, dtype=float)
        if data.size <= sample_size:
            return data
        return data[:sample_size]

    sample_parts = []
    remaining = sample_size
    for row in np.asarray(matrix):
        row = np.asarray(row).ravel()
        nz = row[row != 0]
        if nz.size == 0:
            continue
        take = min(remaining, nz.size)
        sample_parts.append(np.asarray(nz[:take], dtype=float))
        remaining -= take
        if remaining == 0:
            break
    if not sample_parts:
        return np.array([], dtype=float)
    return np.concatenate(sample_parts)


def _find_normalization_hints(keys: list[str]) -> list[str]:
    return sorted({key for key in keys if any(hint in key.lower() for hint in NORMALIZATION_HINTS)})


def format_available_annotations(labels) -> str:
    counts = labels.astype(str).value_counts()
    return ", ".join(f"{label} (n={count})" for label, count in counts.items())


def summarize_input_structure(adata, annotation_col: str) -> dict:
    required_var = ["chromosome", "start", "end"]
    missing_var_columns = [column for column in required_var if column not in adata.var.columns]
    genomic_position_missing_counts = {}
    if not missing_var_columns:
        for column in required_var:
            series = adata.var[column]
            if series.dtype == object:
                missing_mask = series.isna() | (series.astype(str).str.strip() == "")
            else:
                missing_mask = series.isna()
            genomic_position_missing_counts[column] = int(missing_mask.sum())

    annotation_exists = annotation_col in adata.obs.columns
    annotation_counts = format_available_annotations(adata.obs[annotation_col]) if annotation_exists else ""

    errors = []
    if not annotation_exists:
        errors.append(f"{annotation_col!r} not found in adata.obs.")
    if missing_var_columns:
        errors.append(f"Missing genomic position columns in adata.var: {missing_var_columns}")
    incomplete_position_columns = [column for column, count in genomic_position_missing_counts.items() if count > 0]
    if incomplete_position_columns:
        details = ", ".join(f"{column}={genomic_position_missing_counts[column]}" for column in incomplete_position_columns)
        errors.append(f"Found genes with missing genomic positions: {details}")

    return {
        "annotation_col": annotation_col,
        "annotation_col_exists": annotation_exists,
        "obs_columns": sorted(str(column) for column in adata.obs.columns),
        "annotation_counts": annotation_counts,
        "var_columns": sorted(str(column) for column in adata.var.columns),
        "required_genomic_position_columns": required_var,
        "missing_genomic_position_columns": missing_var_columns,
        "genomic_position_missing_counts": genomic_position_missing_counts,
        "errors": errors,
    }


def format_input_structure_preflight(summary: dict) -> str:
    lines = [
        "Input structure preflight:",
        f"Annotation column: {summary['annotation_col']} | exists: {summary['annotation_col_exists']}",
        f"Required genomic position columns: {summary['required_genomic_position_columns']}",
        f"Missing genomic position columns: {summary['missing_genomic_position_columns']}",
    ]
    if summary["genomic_position_missing_counts"]:
        lines.append(f"Genomic position missing counts: {summary['genomic_position_missing_counts']}")
    if summary["annotation_counts"]:
        lines.append(f"Available annotations: {summary['annotation_counts']}")
    return "\n".join(lines)


def enforce_input_structure_preflight(adata, annotation_col: str) -> dict:
    summary = summarize_input_structure(adata, annotation_col)
    print(format_input_structure_preflight(summary), file=sys.stderr)
    if summary["errors"]:
        raise ValueError("Input structure preflight failed:\n- " + "\n- ".join(summary["errors"]))
    return summary


def summarize_expression_matrix(adata) -> dict:
    x = adata.X
    is_sparse = sp.issparse(x)
    nnz_per_cell = np.asarray(x.getnnz(axis=1)).ravel() if is_sparse else np.count_nonzero(np.asarray(x), axis=1)
    nonzero_sample = _sample_nonzero_values(x)
    integer_like_fraction = (
        float(np.mean(np.isclose(nonzero_sample, np.round(nonzero_sample), atol=1e-6))) if nonzero_sample.size else 0.0
    )

    uns_keys = sorted(str(key) for key in adata.uns.keys())
    layer_keys = sorted(str(key) for key in adata.layers.keys())
    log1p_uns_present = "log1p" in adata.uns
    normalized_uns_hints = _find_normalization_hints(uns_keys)
    normalized_layer_hints = _find_normalization_hints(layer_keys)

    suspicious_reasons = []
    if np.issubdtype(x.dtype, np.integer):
        suspicious_reasons.append("X uses an integer dtype, which is more consistent with raw counts than log-normalized expression.")
    if float(x.min()) < 0:
        suspicious_reasons.append("X contains negative values, which suggests scaled or centered expression rather than log-normalized expression.")
    if integer_like_fraction >= 0.99 and float(x.max()) >= 20:
        suspicious_reasons.append("Nonzero X values are almost entirely integer-like and the maximum value is large, which strongly suggests raw counts.")
    if integer_like_fraction >= 0.99 and not (log1p_uns_present or normalized_uns_hints or normalized_layer_hints):
        suspicious_reasons.append("Nonzero X values are almost entirely integer-like and no log1p/normalized metadata was found in adata.uns or adata.layers.")

    return {
        "x_dtype": str(x.dtype),
        "x_is_sparse": bool(is_sparse),
        "x_shape": [int(adata.n_obs), int(adata.n_vars)],
        "x_min": float(x.min()),
        "x_max": float(x.max()),
        "nnz_per_cell_min": int(nnz_per_cell.min()) if nnz_per_cell.size else 0,
        "nnz_per_cell_median": float(np.median(nnz_per_cell)) if nnz_per_cell.size else 0.0,
        "nnz_per_cell_mean": float(np.mean(nnz_per_cell)) if nnz_per_cell.size else 0.0,
        "nnz_per_cell_max": int(nnz_per_cell.max()) if nnz_per_cell.size else 0,
        "nonzero_sample_size": int(nonzero_sample.size),
        "nonzero_integer_like_fraction": integer_like_fraction,
        "log1p_uns_present": bool(log1p_uns_present),
        "normalized_uns_hints": normalized_uns_hints,
        "normalized_layer_hints": normalized_layer_hints,
        "uns_keys": uns_keys,
        "layer_keys": layer_keys,
        "raw_present": bool(adata.raw is not None),
        "suspicious_reasons": suspicious_reasons,
    }


def format_expression_preflight(summary: dict) -> str:
    return (
        "Expression preflight:\n"
        f"X dtype: {summary['x_dtype']} | sparse: {summary['x_is_sparse']} | shape: {tuple(summary['x_shape'])}\n"
        f"X range: min={summary['x_min']:.4f}, max={summary['x_max']:.4f}\n"
        "Nonzero genes per cell: "
        f"min={summary['nnz_per_cell_min']}, median={summary['nnz_per_cell_median']:.1f}, "
        f"mean={summary['nnz_per_cell_mean']:.1f}, max={summary['nnz_per_cell_max']}\n"
        "Metadata hints: "
        f"log1p_uns_present={summary['log1p_uns_present']}, "
        f"normalized_uns_hints={summary['normalized_uns_hints']}, "
        f"normalized_layer_hints={summary['normalized_layer_hints']}, "
        f"raw_present={summary['raw_present']}\n"
        f"Integer-like nonzero fraction (sample): {summary['nonzero_integer_like_fraction']:.3f}"
    )


def enforce_expression_preflight(adata, mode: str) -> dict:
    summary = summarize_expression_matrix(adata)
    print(format_expression_preflight(summary), file=sys.stderr)

    if not summary["suspicious_reasons"] or mode == "off":
        return summary

    suspicious_message = "Suspicious expression matrix detected:\n- " + "\n- ".join(summary["suspicious_reasons"])
    if mode == "fail":
        raise ValueError(suspicious_message)
    print(suspicious_message, file=sys.stderr)
    return summary


def main() -> None:
    args = parse_args()
    adata = ad.read_h5ad(args.input_h5ad)
    input_structure = enforce_input_structure_preflight(adata, args.annotation_col)
    expression = enforce_expression_preflight(adata, args.check_mode)
    summary = {
        "input_h5ad": str(args.input_h5ad),
        "input_structure_preflight": input_structure,
        "expression_preflight": expression,
    }
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.json_out, "w") as handle:
            json.dump(summary, handle, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
