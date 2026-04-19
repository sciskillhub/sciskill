# Genomic Positions

Before running `infercnv`, check whether `adata.var` already contains genomic coordinates:

- `chromosome`
- `start`
- `end`

If any of these are missing, add them before CNV analysis.

## Preferred order

1. Prefer `infercnvpy.io.genomic_position_from_gtf`
2. Fall back to `infercnvpy.io.genomic_position_from_biomart`

Use the GTF route first whenever a matching annotation file is available. It is the more reproducible path and avoids network dependence.

## `genomic_position_from_gtf`

API:

`infercnvpy.io.genomic_position_from_gtf(gtf_file, adata=None, *, gtf_gene_id='gene_name', adata_gene_id=None, inplace=True)`

Key notes:

- the GTF must match the genome annotation used for the dataset
- currently only tested with GENCODE GTFs
- if `adata_gene_id` is not set, matching uses `adata.var_names`
- if `inplace=True`, genomic coordinates are added directly into `adata.var`

Typical usage:

```python
cnv.io.genomic_position_from_gtf(
    gtf_file="path/to/genes.gtf",
    adata=adata,
    gtf_gene_id="gene_name",
    adata_gene_id=None,
    inplace=True,
)
```

## `genomic_position_from_biomart`

API:

`infercnvpy.io.genomic_position_from_biomart(adata=None, *, adata_gene_id=None, biomart_gene_id='ensembl_gene_id', species='hsapiens', inplace=True, **kwargs)`

Key notes:

- use this when no suitable GTF is available
- gene identifiers between `adata` and Biomart must match
- default `biomart_gene_id` is `ensembl_gene_id`, but symbol-based matching can also work when configured correctly
- this route depends on Biomart availability and network access

Typical usage:

```python
cnv.io.genomic_position_from_biomart(
    adata=adata,
    adata_gene_id=None,
    biomart_gene_id="ensembl_gene_id",
    species="hsapiens",
    inplace=True,
)
```

## Recommended check

Use this check before CNV analysis:

```python
required = {"chromosome", "start", "end"}
missing = required.difference(adata.var.columns)
```

If `missing` is non-empty:

- first try `genomic_position_from_gtf`
- otherwise use `genomic_position_from_biomart`
