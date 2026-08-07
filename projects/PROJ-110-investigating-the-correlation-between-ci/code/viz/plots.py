"""Visualization utilities for the project.

This module provides functions to generate plots required by the analysis
pipeline, including scatter plots for significant gene‑trait correlations
and a heatmap of gene expression patterns across MetS/Control groups.
"""

import logging
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)

def plot_scatter_significant(
    correlation_fdr_path: Path = Path("data/processed/correlation_fdr.csv"),
    expression_path: Path = Path("data/processed/core_genes_log2_matrix.csv"),
    phenotype_path: Path = Path("data/processed/filtered_phenotype.csv"),
    output_dir: Path = Path("docs"),
    pvalue_threshold: float = 0.05,
) -> None:
    """Generate scatter plots for gene‑trait pairs that show significant correlations.

    The function reads the FDR‑adjusted correlation results, filters for
    significance, merges the log‑transformed gene expression matrix with the
    phenotype data, and creates a scatter plot for each significant pair.

    Parameters
    ----------
    correlation_fdr_path: Path
        CSV containing at least the columns ``gene``, ``trait``, ``r``,
        ``p_raw`` and an adjusted‑p‑value column (named ``p_adj`` or
        ``adjusted_p``).
    expression_path: Path
        CSV with log2‑transformed TPM values. The first column must be a
        sample identifier; remaining columns are gene names.
    phenotype_path: Path
        CSV with clinical traits. The first column must be the same sample
        identifier as in ``expression_path``.
    output_dir: Path
        Directory where PNG files will be written.
    pvalue_threshold: float
        Adjusted p‑value cutoff for significance (default 0.05).
    """
    logger.info("Generating scatter plots for significant correlations")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load correlation results
    corr_df = pd.read_csv(correlation_fdr_path)
    # Normalise column name for adjusted p‑value
    if "p_adj" not in corr_df.columns:
        if "adjusted_p" in corr_df.columns:
            corr_df = corr_df.rename(columns={"adjusted_p": "p_adj"})
        else:
            raise KeyError(
                "Adjusted p‑value column not found in correlation results"
            )

    # Keep only significant pairs
    sig_df = corr_df[corr_df["p_adj"] < pvalue_threshold]
    if sig_df.empty:
        logger.warning(
            "No significant correlations found (adjusted p < %s)", pvalue_threshold
        )
        return

    # Load expression and phenotype tables
    expr_df = pd.read_csv(expression_path)
    pheno_df = pd.read_csv(phenotype_path)

    # Standardise the sample identifier column name
    sample_id_col = expr_df.columns[0]
    expr_df = expr_df.rename(columns={sample_id_col: "sample_id"})
    pheno_df = pheno_df.rename(columns={pheno_df.columns[0]: "sample_id"})

    for _, row in sig_df.iterrows():
        gene = row["gene"]
        trait = row["trait"]
        r_val = row["r"]
        p_adj = row["p_adj"]

        if gene not in expr_df.columns:
            logger.warning("Gene %s not found in expression matrix", gene)
            continue
        if trait not in pheno_df.columns:
            logger.warning("Trait %s not found in phenotype data", trait)
            continue

        # Merge expression of the gene with the clinical trait
        merged = pd.merge(
            expr_df[["sample_id", gene]],
            pheno_df[["sample_id", trait]],
            on="sample_id",
        ).dropna()

        if merged.empty:
            logger.warning(
                "No overlapping samples for gene %s and trait %s", gene, trait
            )
            continue

        plt.figure(figsize=(6, 4))
        plt.scatter(merged[trait], merged[gene], alpha=0.7)
        plt.xlabel(trait)
        plt.ylabel(f"{gene} (log2 TPM)")
        plt.title(f"{gene} vs {trait}\\n r={r_val:.3f}, adj p={p_adj:.3e}")
        plt.tight_layout()

        # Sanitize filenames
        safe_gene = "".join(c if c.isalnum() else "_" for c in gene)
        safe_trait = "".join(c if c.isalnum() else "_" for c in trait)
        out_path = output_dir / f"correlation_scatter_{safe_gene}_{safe_trait}.png"
        plt.savefig(out_path)
        plt.close()
        logger.info("Saved scatter plot %s", out_path)


def generate_heatmap(
    expression_path: Path = Path("data/processed/core_genes_log2_matrix.csv"),
    phenotype_path: Path = Path("data/processed/filtered_phenotype.csv"),
    output_path: Path = Path("docs/heatmap.png"),
    group_column: str = "label",
    cmap: str = "vlag",
    figsize: tuple = (10, 8),
) -> None:
    """Generate a heatmap visualising expression patterns of core circadian genes.

    The heatmap displays the mean log2‑TPM expression of each core circadian gene
    within the MetS and Control groups (or any categorical grouping provided
    via ``group_column``). The resulting figure is saved to ``output_path``.

    Parameters
    ----------
    expression_path: Path
        CSV containing log2‑transformed TPM values. The first column must be a
        sample identifier; remaining columns are gene names.
    phenotype_path: Path
        CSV containing at least the sample identifier column and a categorical
        column (default ``label``) indicating MetS vs Control status.
    output_path: Path
        Destination file for the heatmap PNG.
    group_column: str, optional
        Column name in the phenotype file that defines the groups to compare.
        Defaults to ``label`` which is created by ``classify_metabolic_status``.
    cmap: str, optional
        Matplotlib colormap name for the heatmap. Defaults to ``vlag`` (a diverging
        palette suitable for centered data).
    figsize: tuple, optional
        Figure size in inches. Defaults to (10, 8).
    """
    logger.info("Generating heatmap of core circadian gene expression")
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load data
    expr_df = pd.read_csv(expression_path)
    pheno_df = pd.read_csv(phenotype_path)

    # Standardise sample identifier column names
    sample_id_col_expr = expr_df.columns[0]
    expr_df = expr_df.rename(columns={sample_id_col_expr: "sample_id"})
    sample_id_col_pheno = pheno_df.columns[0]
    pheno_df = pheno_df.rename(columns={sample_id_col_pheno: "sample_id"})

    # Verify grouping column exists
    if group_column not in pheno_df.columns:
        raise KeyError(f"Grouping column '{group_column}' not found in phenotype data")

    # Merge expression with phenotype
    merged_df = pd.merge(expr_df, pheno_df[["sample_id", group_column]], on="sample_id", how="inner")
    if merged_df.empty:
        raise ValueError("No overlapping samples between expression matrix and phenotype data")

    # Compute mean expression per gene per group
    gene_cols = [col for col in expr_df.columns if col != "sample_id"]
    group_means = (
        merged_df.groupby(group_column)[gene_cols]
        .mean()
        .transpose()
    )  # genes x groups

    # Plot heatmap
    plt.figure(figsize=figsize)
    sns.heatmap(
        group_means,
        cmap=cmap,
        linewidths=0.5,
        linecolor="gray",
        cbar_kws={"label": "Mean log2 TPM"},
    )
    plt.title("Mean Log2 TPM of Core Circadian Genes by Group")
    plt.ylabel("Gene")
    plt.xlabel("Group")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logger.info("Heatmap saved to %s", output_path)