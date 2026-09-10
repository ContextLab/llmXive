"""
Visualization utilities for the GTEx circadian-metabolic project.

This module provides functions to generate:
- Scatter plots for significant gene‑trait correlations.
- A heatmap of core circadian gene expression stratified by MetS status.
- An ROC curve visualising logistic‑regression model performance.
"""

import logging
from pathlib import Path
from typing import Optional, Union

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import auc, roc_curve

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Scatter plot for significant correlations
# ----------------------------------------------------------------------
def plot_scatter_significant(
    correlation_df: pd.DataFrame,
    expression_df: pd.DataFrame,
    phenotype_df: pd.DataFrame,
    significance_level: float = 0.05,
    output_dir: Union[str, Path] = "docs",
) -> None:
    """
    Generate scatter plots for each gene‑trait pair that passes a
    significance threshold.

    Parameters
    ----------
    correlation_df : pd.DataFrame
        DataFrame containing at least the columns ``gene``, ``trait``,
        ``r`` (correlation coefficient) and ``p_adj`` (FDR‑adjusted p‑value).
    expression_df : pd.DataFrame
        Gene‑expression matrix where rows are genes and columns are sample IDs.
    phenotype_df : pd.DataFrame
        Clinical phenotype table indexed by the same sample IDs as ``expression_df``.
    significance_level : float, optional
        Maximum adjusted p‑value to consider a correlation significant.
    output_dir : str or Path, optional
        Directory where the PNG files will be written.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Filter for significant correlations
    sig_mask = correlation_df["p_adj"] <= significance_level
    sig_pairs = correlation_df[sig_mask]

    if sig_pairs.empty:
        logger.info("No significant gene‑trait pairs found (p_adj <= %s).", significance_level)
        return

    for _, row in sig_pairs.iterrows():
        gene = row["gene"]
        trait = row["trait"]
        r_val = row["r"]
        p_adj = row["p_adj"]

        # Extract expression for the gene and phenotype for the trait
        if gene not in expression_df.index:
            logger.warning("Gene %s not found in expression matrix; skipping.", gene)
            continue
        if trait not in phenotype_df.columns:
            logger.warning("Trait %s not found in phenotype table; skipping.", trait)
            continue

        expr_series = expression_df.loc[gene]
        trait_series = phenotype_df[trait]

        # Align the two series on sample identifiers
        common_idx = expr_series.dropna().index.intersection(trait_series.dropna().index)
        if common_idx.empty:
            logger.warning(
                "No overlapping samples for gene %s and trait %s; skipping.", gene, trait
            )
            continue

        x = expr_series.loc[common_idx]
        y = trait_series.loc[common_idx]

        plt.figure(figsize=(6, 4))
        sns.regplot(x=x, y=y, scatter_kws={"s": 20}, line_kws={"color": "red"})
        plt.title(f"{gene} vs {trait}\nPearson r={r_val:.3f}, FDR‑adj p={p_adj:.3e}")
        plt.xlabel("Expression (log2 TPM)")
        plt.ylabel(trait.replace("_", " ").title())

        fname = output_path / f"scatter_{gene}_{trait}.png"
        plt.tight_layout()
        plt.savefig(fname, dpi=150)
        plt.close()
        logger.info("Saved scatter plot for %s‑%s to %s", gene, trait, fname)

# ----------------------------------------------------------------------
# Heatmap of core circadian gene expression by MetS status
# ----------------------------------------------------------------------
def generate_heatmap(
    expression_df: pd.DataFrame,
    label_df: pd.DataFrame,
    output_path: Union[str, Path] = "docs/heatmap.png",
    cmap: str = "viridis",
) -> None:
    """
    Create a clustered heatmap of core circadian gene expression,
    annotated by MetS / Control status.

    Parameters
    ----------
    expression_df : pd.DataFrame
        Gene‑expression matrix (genes × samples). Rows must be genes,
        columns must be sample identifiers.
    label_df : pd.DataFrame
        DataFrame with at least a column ``label`` containing the strings
        ``MetS`` or ``Control``. Index must match the sample identifiers
        of ``expression_df``.
    output_path : str or Path, optional
        File path where the PNG image will be saved.
    cmap : str, optional
        Matplotlib colormap name.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Align expression matrix and labels
    common_samples = expression_df.columns.intersection(label_df.index)
    if common_samples.empty:
        raise ValueError("No overlapping samples between expression matrix and label table.")

    expr_aligned = expression_df[common_samples]
    labels_aligned = label_df.loc[common_samples, "label"]

    # Create a colour bar for the phenotype
    phenotype_palette = {"MetS": "#d73027", "Control": "#1a9850"}
    col_colors = labels_aligned.map(phenotype_palette)

    # Generate clustered heatmap
    sns.clustermap(
        expr_aligned,
        cmap=cmap,
        figsize=(10, 12),
        row_cluster=True,
        col_cluster=True,
        col_colors=col_colors,
        xticklabels=False,
        yticklabels=True,
    )
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info("Heatmap saved to %s", output_path)

# ----------------------------------------------------------------------
# ROC curve for logistic‑regression model performance
# ----------------------------------------------------------------------
def plot_roc_curve(
    y_true: Union[pd.Series, str, Path],
    y_score: Union[pd.Series, str, Path],
    output_path: Union[str, Path] = "docs/roc_curve.png",
    pos_label: int = 1,
) -> None:
    """
    Plot an ROC curve given true binary labels and predicted scores.

    The function accepts either raw pandas Series objects or file paths
    (CSV/TSV) that contain a single column of values. When a path is
    supplied, the file is read with ``pandas.read_csv``; the column name
    is inferred automatically.

    Parameters
    ----------
    y_true : pandas.Series or str or pathlib.Path
        Ground‑truth binary labels (0/1 or ``Control``/``MetS``). If a
        string/Path is supplied, the file is loaded.
    y_score : pandas.Series or str or pathlib.Path
        Predicted probability (or any continuous score) for the positive
        class. If a string/Path is supplied, the file is loaded.
    output_path : str or Path, optional
        Destination PNG file for the ROC plot.
    pos_label : int, optional
        The label considered the positive class (default ``1``). If the
        labels are strings, they will be mapped to ``0``/``1`` based on
        ``pos_label`` after conversion.
    """
    # Helper to load a Series from a path or Series
    def _load_series(data):
        if isinstance(data, pd.Series):
            return data
        path = Path(data)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        df = pd.read_csv(path)
        if df.shape[1] != 1:
            raise ValueError(f"Expected a single‑column file at {path}, got {df.shape[1]} columns.")
        return df.iloc[:, 0]

    y_true_series = _load_series(y_true)
    y_score_series = _load_series(y_score)

    # Align indexes if they exist
    if hasattr(y_true_series, "index") and hasattr(y_score_series, "index"):
        common_idx = y_true_series.dropna().index.intersection(y_score_series.dropna().index)
        if common_idx.empty:
            raise ValueError("No overlapping indices between y_true and y_score.")
        y_true_series = y_true_series.loc[common_idx]
        y_score_series = y_score_series.loc[common_idx]

    # Convert string labels to binary if necessary
    if y_true_series.dtype.kind in {"O", "U"}:
        # Assume values are "MetS"/"Control" or similar
        unique_vals = sorted(y_true_series.dropna().unique())
        if len(unique_vals) != 2:
            raise ValueError(f"Expected exactly two distinct label values, got {unique_vals}")
        mapping = {unique_vals[0]: 0, unique_vals[1]: 1}
        y_true_binary = y_true_series.map(mapping)
    else:
        y_true_binary = y_true_series.astype(int)

    # Compute ROC curve
    fpr, tpr, _ = roc_curve(y_true_binary, y_score_series, pos_label=pos_label)
    roc_auc = auc(fpr, tpr)

    # Plot
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(6, 6))
    plt.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (AUC = {roc_auc:.3f})")
    plt.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Receiver Operating Characteristic")
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info("ROC curve saved to %s (AUC = %.3f)", output_path, roc_auc)

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
__all__ = [
    "plot_scatter_significant",
    "generate_heatmap",
    "plot_roc_curve",
]