"""
Unit tests for the correlation method selection logic.

These tests verify that the `determine_correlation_methods` function
selects Pearson correlation when the Shapiro‑Wilk test indicates normality
(p > 0.05) and selects Spearman correlation otherwise.
"""

import numpy as np
import pandas as pd
from analysis.correlation import determine_correlation_methods
import inspect

def _call_determine_correlation_methods(expr_df: pd.DataFrame, phen_df: pd.DataFrame):
    """
    Helper that calls ``determine_correlation_methods`` with the correct
    signature, handling possible variations in the function definition.
    """
    sig = inspect.signature(determine_correlation_methods)
    params = list(sig.parameters)

    # Most common signature: (expression_df, phenotype_df)
    if len(params) == 2:
        return determine_correlation_methods(expr_df, phen_df)

    # Alternative signature that also expects explicit gene/trait lists
    if len(params) >= 4:
        # Assume order: expression_df, phenotype_df, genes, traits
        genes = list(expr_df.columns)
        traits = list(phen_df.columns)
        return determine_correlation_methods(expr_df, phen_df, genes, traits)

    # Fallback – try calling with only the two dataframes; let any error surface.
    return determine_correlation_methods(expr_df, phen_df)

def test_method_selection_normal_data():
    """
    Verify that Pearson is chosen when both gene expression and trait are
    drawn from a normal distribution (Shapiro‑Wilk p > 0.05).
    """
    np.random.seed(0)
    n_samples = 200

    # Generate normally distributed synthetic data
    gene_vals = np.random.normal(loc=0.0, scale=1.0, size=n_samples)
    trait_vals = np.random.normal(loc=5.0, scale=2.0, size=n_samples)

    expr_df = pd.DataFrame({"GENE1": gene_vals})
    phen_df = pd.DataFrame({"TRAIT1": trait_vals})

    methods = _call_determine_correlation_methods(expr_df, phen_df)

    # The function should return a dict mapping each (gene, trait) pair to a method name.
    assert isinstance(methods, dict), "Expected a dict from determine_correlation_methods"
    # Accept either tuple keys or concatenated string keys.
    possible_keys = [("GENE1", "TRAIT1"), "GENE1_TRAIT1"]
    key = next((k for k in possible_keys if k in methods), None)
    assert key is not None, f"Result dict missing expected key for GENE1‑TRAIT1: {methods.keys()}"

    method = methods[key]
    assert method == "pearson", f"Expected 'pearson' for normal data, got '{method}'"

def test_method_selection_nonnormal_data():
    """
    Verify that Spearman is chosen when the data are clearly non‑normal
    (Shapiro‑Wilk p ≤ 0.05).  Here we use an exponential distribution for the
    trait which is positively skewed.
    """
    np.random.seed(1)
    n_samples = 200

    # Gene remains normal; trait is exponential (non‑normal)
    gene_vals = np.random.normal(loc=0.0, scale=1.0, size=n_samples)
    trait_vals = np.random.exponential(scale=1.0, size=n_samples)

    expr_df = pd.DataFrame({"GENE1": gene_vals})
    phen_df = pd.DataFrame({"TRAIT1": trait_vals})

    methods = _call_determine_correlation_methods(expr_df, phen_df)

    assert isinstance(methods, dict), "Expected a dict from determine_correlation_methods"
    possible_keys = [("GENE1", "TRAIT1"), "GENE1_TRAIT1"]
    key = next((k for k in possible_keys if k in methods), None)
    assert key is not None, f"Result dict missing expected key for GENE1‑TRAIT1: {methods.keys()}"

    method = methods[key]
    assert method == "spearman", f"Expected 'spearman' for non‑normal data, got '{method}'"