"""
Report template generation for the Structure-Only Surrogate Model.

This module provides the Markdown template structure for the final feature
importance report. It defines the static headers, disclaimers, and table
skeletons required by T027c.
"""

from typing import List, Dict, Any, Optional

REPORT_TEMPLATE = """
# Feature Importance Report: Structure-Only Surrogate Model

**Project**: PROJ-169-predicting-the-elastic-moduli-of-2d-mate
**Task**: T027c (Report Generation)
**Generated**: {generated_date}

## Executive Summary

This report details the statistical correlations identified by the surrogate model
regarding the structural descriptors that influence predicted elastic moduli in 2D materials.
The model is a **Structure-Only Surrogate** trained on pre-computed DFT data.

> **CRITICAL DISCLAIMER**: The identified descriptors are statistical correlations learned
> by the surrogate model from DFT data, not fundamental quantum mechanical variables derived
> from the Hamiltonian. This model interpolates existing DFT results; it does NOT solve
> the Schrödinger equation.

## Methodology

Feature importance was assessed using two complementary methods:
1. **SHAP Interaction Values**: To measure the contribution of each descriptor to the model's output.
2. **Permutation Importance**: To evaluate the performance drop when a descriptor's values are shuffled.

Statistical significance was determined via p-values calculated from the distribution of
importance scores across the test set.

## Significant Descriptors (p < 0.05)

The following table lists descriptors that demonstrated statistical significance
(p-value < 0.05) in influencing the predicted elastic moduli.

| Descriptor | Importance Score | p-value | Description |
| :--- | :--- | :--- | :--- |
{table_rows}

## Ablation Study Results

To understand the contribution of structural topology versus composition, a baseline
composition-only model was compared against the full Graph Neural Network.

- **Full GNN MAPE**: {full_gnn_mape:.4f}
- **Composition-Only Baseline MAPE**: {baseline_mape:.4f}
- **Performance Delta (Improvement)**: {ablation_delta:.4f}

*Note: A positive delta indicates the full GNN (with topology) outperformed the composition-only baseline.*

## Failure Mode Analysis

{failure_message}

---
**End of Report**
"""

FAILURE_TEMPLATE = """
**SC-005 Failure: Fewer than 3 significant descriptors found**

The analysis identified fewer than 3 descriptors with a p-value < 0.05.
This suggests the model may not have learned distinct structural correlations,
or the dataset lacks sufficient variance in the tested descriptors.

**Top 3 Non-Significant Descriptors:**
{non_significant_list}
"""

def generate_markdown_table_rows(significant_descriptors: List[Dict[str, Any]]) -> str:
    """
    Generates the Markdown table rows for significant descriptors.

    Args:
        significant_descriptors: List of dicts containing 'descriptor', 'score', 'p_value', 'description'.

    Returns:
        A string containing the formatted table rows.
    """
    if not significant_descriptors:
        return "No significant descriptors found (p < 0.05)."

    rows = []
    for item in significant_descriptors:
        # Format p-value to avoid scientific notation if small, or standard float
        p_val = item.get('p_value', 0.0)
        score = item.get('score', 0.0)
        desc = item.get('description', 'N/A')
        name = item.get('descriptor', 'Unknown')

        # Ensure p-value is formatted reasonably
        if p_val < 0.001:
            p_str = f"{p_val:.2e}"
        else:
            p_str = f"{p_val:.4f}"

        rows.append(f"| {name} | {score:.4f} | {p_str} | {desc} |")

    return "\n".join(rows)

def generate_failure_message(non_significant_descriptors: List[Dict[str, Any]]) -> str:
    """
    Generates the failure message if fewer than 3 significant descriptors are found.

    Args:
        non_significant_descriptors: List of top non-significant descriptors.

    Returns:
        A formatted string explaining the failure.
    """
    if not non_significant_descriptors:
        return "No failure conditions met."

    list_items = []
    for i, item in enumerate(non_significant_descriptors[:3], 1):
        name = item.get('descriptor', 'Unknown')
        p_val = item.get('p_value', 0.0)
        list_items.append(f"{i}. **{name}** (p-value: {p_val:.4f})")

    non_significant_str = "\n".join(list_items)
    return FAILURE_TEMPLATE.format(non_significant_list=non_significant_str)

def render_report(
    generated_date: str,
    significant_descriptors: List[Dict[str, Any]],
    full_gnn_mape: float,
    baseline_mape: float,
    non_significant_descriptors: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Renders the full Markdown report string.

    Args:
        generated_date: ISO format date string.
        significant_descriptors: List of significant descriptor dicts.
        full_gnn_mape: MAPE of the full GNN model.
        baseline_mape: MAPE of the composition-only baseline.
        non_significant_descriptors: Optional list of non-significant descriptors for failure report.

    Returns:
        The complete Markdown report string.
    """
    table_rows = generate_markdown_table_rows(significant_descriptors)
    ablation_delta = full_gnn_mape - baseline_mape

    # Determine failure message
    if len(significant_descriptors) < 3:
        # Use provided non-significant list or fallback to empty
        failure_msg = generate_failure_message(
            non_significant_descriptors or []
        )
    else:
        failure_msg = "No failure conditions met. At least 3 significant descriptors found."

    return REPORT_TEMPLATE.format(
        generated_date=generated_date,
        table_rows=table_rows,
        full_gnn_mape=full_gnn_mape,
        baseline_mape=baseline_mape,
        ablation_delta=ablation_delta,
        failure_message=failure_msg
    )