import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

logger = logging.getLogger(__name__)

# Existing public functions (preserved)
def determine_correlation_methods(
    phenotype_df: pd.DataFrame,
    expression_df: pd.DataFrame,
    alpha: float = 0.05,
) -> Dict[Tuple[str, str], str]:
    """
    Determine whether to use Pearson or Spearman correlation for each gene‑trait pair
    based on normality of the two variables (Shapiro‑Wilk test).

    Returns
    -------
    dict
        Mapping of (gene, trait) -> method name ('pearson' or 'spearman')
    """
    from scipy.stats import shapiro

    methods = {}
    for gene in expression_df.columns:
        gene_vals = expression_df[gene].dropna()
        # Test normality of gene expression
        _, p_gene = shapiro(gene_vals) if len(gene_vals) >= 3 else (np.nan, 1.0)

        for trait in phenotype_df.columns:
            trait_vals = phenotype_df[trait].dropna()
            # Test normality of trait
            _, p_trait = shapiro(trait_vals) if len(trait_vals) >= 3 else (np.nan, 1.0)

            # If both are ~normal, use Pearson; otherwise Spearman
            if p_gene > alpha and p_trait > alpha:
                methods[(gene, trait)] = "pearson"
            else:
                methods[(gene, trait)] = "spearman"
    # Persist the decision map for downstream inspection
    method_path = Path("data/processed/correlation_method_flags.json")
    method_path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(
        {f"{gene}|{trait}": meth for (gene, trait), meth in methods.items()},
        open(method_path, "w"),
        indent=2,
    )
    logger.info(f"Correlation methods written to {method_path}")
    return methods

def generate_correlation_analysis(
    phenotype_df: pd.DataFrame,
    expression_df: pd.DataFrame,
    methods: Optional[Dict[Tuple[str, str], str]] = None,
) -> pd.DataFrame:
    """
    Compute correlation coefficients and raw p‑values for each gene‑trait pair.

    Parameters
    ----------
    phenotype_df : pd.DataFrame
        Continuous clinical traits (e.g., BMI, Glucose, TG, HDL, BP).
    expression_df : pd.DataFrame
        Log2‑transformed expression matrix for core circadian genes.
    methods : dict, optional
        Mapping from (gene, trait) to correlation method. If None,
        ``determine_correlation_methods`` will be called internally.

    Returns
    -------
    pd.DataFrame
        Columns: ['gene', 'trait', 'r', 'p_raw']
    """
    from scipy.stats import pearsonr, spearmanr

    if methods is None:
        methods = determine_correlation_methods(phenotype_df, expression_df)

    rows = []
    for gene in expression_df.columns:
        gene_vals = expression_df[gene]
        for trait in phenotype_df.columns:
            trait_vals = phenotype_df[trait]
            # Align non‑missing samples
            valid_idx = gene_vals.notna() & trait_vals.notna()
            if valid_idx.sum() < 3:
                # Not enough data to compute a correlation
                continue
            x = gene_vals[valid_idx]
            y = trait_vals[valid_idx]
            method = methods.get((gene, trait), "spearman")
            if method == "pearson":
                r, p = pearsonr(x, y)
            else:
                r, p = spearmanr(x, y)
            rows.append({"gene": gene, "trait": trait, "r": r, "p_raw": p})

    corr_df = pd.DataFrame(rows)
    out_path = Path("data/processed/raw_correlation_results.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    corr_df.to_csv(out_path, index=False)
    logger.info(f"Raw correlation results written to {out_path}")
    return corr_df

def apply_correlation_fdr(
    correlation_df: Optional[pd.DataFrame] = None,
    input_path: str = "data/processed/raw_correlation_results.csv",
    output_path: str = "data/processed/correlation_fdr.csv",
) -> pd.DataFrame:
    """
    Apply a global Benjamini‑Hochberg FDR correction to the raw p‑values
    from the correlation analysis.

    Parameters
    ----------
    correlation_df : pd.DataFrame, optional
        DataFrame containing at least the columns ``['gene', 'trait', 'p_raw']``.
        If ``None``, the function will load the table from ``input_path``.
    input_path : str, default ``'data/processed/raw_correlation_results.csv'``
        Path to the CSV file containing raw correlation results.
    output_path : str, default ``'data/processed/correlation_fdr.csv'``
        Destination CSV where the DataFrame with adjusted p‑values will be saved.

    Returns
    -------
    pd.DataFrame
        The original correlation DataFrame with an additional column ``p_adj``
        containing the FDR‑adjusted p‑values.
    """
    # Load the raw results if they are not supplied directly
    if correlation_df is None:
        corr_path = Path(input_path)
        if not corr_path.is_file():
            raise FileNotFoundError(f"Correlation results not found at {corr_path}")
        correlation_df = pd.read_csv(corr_path)

    if "p_raw" not in correlation_df.columns:
        raise ValueError("Input DataFrame must contain a 'p_raw' column with raw p‑values.")

    # Perform the Benjamini‑Hochberg correction on the entire set of p‑values
    raw_pvals = correlation_df["p_raw"].values
    _, p_adj, _, _ = multipletests(raw_pvals, method="fdr_bh")

    # Attach adjusted p‑values to the DataFrame
    correlation_df = correlation_df.copy()
    correlation_df["p_adj"] = p_adj

    # Persist the results
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    correlation_df.to_csv(out_path, index=False)
    logger.info(f"FDR‑adjusted correlation results written to {out_path}")

    return correlation_df

# Exported symbols (the module's public API)
__all__ = [
    "determine_correlation_methods",
    "generate_correlation_analysis",
    "apply_correlation_fdr",
]
