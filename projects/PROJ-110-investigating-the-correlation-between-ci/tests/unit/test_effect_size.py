"""Unit test for effect size (Cohen's d) calculation.

This test verifies that the `compute_effect_sizes` function from
``code.analysis.differential`` correctly computes Cohen's d for a simple,
synthetic dataset.  The test adapts to the function signature by
inspecting its parameters and passing arguments either by name or position.
"""

import inspect

import numpy as np
import pandas as pd
import pytest

# Import the function under test
from analysis.differential import compute_effect_sizes


def _cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """Calculate Cohen's d for two 1‑D arrays."""
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        raise ValueError("Both groups must contain at least two samples")
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    # pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    return (mean1 - mean2) / pooled_std


@pytest.mark.parametrize(
    "gene_values, labels, expected_d",
    [
        # Simple two‑group case for a single gene
        (
            pd.DataFrame(
                {
                    "sample_id": ["S1", "S2", "S3", "S4"],
                    "GENE1": [10.0, 12.0, 20.0, 22.0],
                }
            ),
            pd.DataFrame(
                {"sample_id": ["S1", "S2", "S3", "S4"], "label": [0, 0, 1, 1]}
            ),
            # Manually computed Cohen's d:
            # group0 = [10,12]  mean=11, var=2
            # group1 = [20,22]  mean=21, var=2
            # pooled_std = sqrt(((2-1)*2 + (2-1)*2) / (2+2-2)) = sqrt(4/2)=sqrt(2)=1.4142
            # d = (21-11)/1.4142 ≈ 7.0711
            7.0710678118654755,
        ),
        # Two genes, mixed means
        (
            pd.DataFrame(
                {
                    "sample_id": ["A", "B", "C", "D", "E", "F"],
                    "GENE1": [5, 6, 7, 8, 9, 10],
                    "GENE2": [30, 28, 27, 35, 33, 31],
                }
            ),
            pd.DataFrame(
                {"sample_id": ["A", "B", "C", "D", "E", "F"], "label": [0, 0, 0, 1, 1, 1]}
            ),
            # GENE1: group0=[5,6,7] mean=6, var=1
            #        group1=[8,9,10] mean=9, var=1
            # pooled_std = sqrt(((3-1)*1 + (3-1)*1)/(3+3-2)) = sqrt(4/4)=1
            # d = (9-6)/1 = 3
            # GENE2: group0=[30,28,27] mean=28.333..., var≈2.333
            #        group1=[35,33,31] mean=33, var≈2.333
            # pooled_std = sqrt(((3-1)*2.333 + (3-1)*2.333)/(4)) = sqrt(9.332/4)=sqrt(2.333)=1.5275
            # d = (33-28.333...)/1.5275 ≈ 3.058
            (3.0, 3.0585832879137584),
        ),
    ],
)
def test_cohens_d_calculation(gene_values: pd.DataFrame, labels: pd.DataFrame, expected_d):
    """
    Verify that `compute_effect_sizes` returns Cohen's d values matching a manual
    calculation for each gene.
    """

    # Merge expression and label data on sample_id to ensure alignment
    merged = pd.merge(gene_values, labels, on="sample_id", how="inner")

    # Determine how the target function expects its inputs.
    sig = inspect.signature(compute_effect_sizes)
    param_names = list(sig.parameters.keys())

    # Build arguments dictionary compatible with the function signature.
    args = {}
    if "expression_df" in param_names:
        args["expression_df"] = merged.drop(columns=["label"])
    elif "expr_df" in param_names:
        args["expr_df"] = merged.drop(columns=["label"])
    elif "data" in param_names:
        args["data"] = merged.drop(columns=["label"])
    else:
        # Assume positional: first argument is expression DataFrame
        args["pos0"] = merged.drop(columns=["label"])

    if "labels_df" in param_names:
        args["labels_df"] = merged[["sample_id", "label"]]
    elif "label_df" in param_names:
        args["label_df"] = merged[["sample_id", "label"]]
    elif "metadata" in param_names:
        args["metadata"] = merged[["sample_id", "label"]]
    else:
        # Assume positional: second argument is labels DataFrame
        args["pos1"] = merged[["sample_id", "label"]]

    # Prepare positional arguments list in order if required
    positional = []
    for key in sorted(args.keys()):
        if key.startswith("pos"):
            positional.append(args[key])
    # Remove the temporary positional keys from kwargs
    kwargs = {k: v for k, v in args.items() if not k.startswith("pos")}

    # Call the function with the constructed arguments
    if positional:
        result = compute_effect_sizes(*positional, **kwargs)
    else:
        result = compute_effect_sizes(**kwargs)

    # The function should return a pandas DataFrame (or something convertible)
    assert isinstance(result, pd.DataFrame), "Result must be a DataFrame"

    # Expected column names – allow common variants
    possible_gene_cols = {"gene", "Gene", "gene_name", "feature"}
    possible_d_cols = {"cohens_d", "cohen_d", "effect_size", "d"}

    gene_col = next((c for c in result.columns if c in possible_gene_cols), None)
    d_col = next((c for c in result.columns if c in possible_d_cols), None)

    assert gene_col is not None, "Result DataFrame must contain a gene identifier column"
    assert d_col is not None, "Result DataFrame must contain a Cohen's d column"

    # Compute expected d values manually for each gene
    expected_dict = {}
    if isinstance(expected_d, tuple):
        # multiple genes case – map in order of appearance in the expression DataFrame
        for gene, exp in zip([c for c in gene_values.columns if c != "sample_id"], expected_d):
            expected_dict[gene] = exp
    else:
        # single gene case
        gene_name = [c for c in gene_values.columns if c != "sample_id"][0]
        expected_dict[gene_name] = expected_d

    # Compare each gene's computed effect size to the manual expectation
    for _, row in result.iterrows():
        gene = row[gene_col]
        computed = float(row[d_col])
        expected = expected_dict.get(gene)
        assert expected is not None, f"Unexpected gene {gene} in result"
        # Allow a small numerical tolerance
        assert np.isclose(computed, expected, atol=1e-6), (
            f"Cohen's d for gene {gene} incorrect: "
            f"got {computed}, expected {expected}"
        )