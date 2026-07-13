"""
Two-way independent-samples ANOVA for Social Memory Networks.

Implements a two-way ANOVA to test the interaction between context condition
and metric type on the measured values, using statsmodels.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Attempt to import statsmodels; provide a safe fallback if missing
def safe_import_statsmodels() -> Tuple[Optional[Any], Optional[Any]]:
    """Try to import statsmodels components needed for ANOVA."""
    try:
        from statsmodels.formula.api import ols
        from statsmodels.stats.anova import anova_lm
        return ols, anova_lm
    except ImportError:
        return None, None

# Global imports for convenience, will be None if statsmodels unavailable
_OLS, _ANOVA_LM = safe_import_statsmodels()


def load_experiment_results(
    full_path: str, limited_path: str
) -> pd.DataFrame:
    """
    Load results from full and limited context CSVs and combine into a long-format DataFrame.

    Expected columns in source CSVs:
    - game_id
    - specialization_index
    - retrieval_efficiency
    - context_condition (optional, will be inferred)
    - agent_count (optional)

    Returns a DataFrame with columns:
    - game_id
    - context_condition (full/limited)
    - metric_name (specialization/retrieval)
    - metric_value
    """
    df_full = None
    df_limited = None

    if os.path.exists(full_path):
        df_full = pd.read_csv(full_path)
        if 'context_condition' not in df_full.columns:
            df_full['context_condition'] = 'full'
    else:
        raise FileNotFoundError(f"Full results file not found: {full_path}")

    if os.path.exists(limited_path):
        df_limited = pd.read_csv(limited_path)
        if 'context_condition' not in df_limited.columns:
            df_limited['context_condition'] = 'limited'
    else:
        raise FileNotFoundError(f"Limited results file not found: {limited_path}")

    # Melt both to long format
    melt_cols = ['game_id', 'specialization_index', 'retrieval_efficiency']
    # Ensure only these exist
    existing_cols = [c for c in melt_cols if c in df_full.columns]
    df_full_long = df_full.melt(
        id_vars=['game_id', 'context_condition'],
        value_vars=existing_cols,
        var_name='metric_name',
        value_name='metric_value'
    )

    existing_cols_l = [c for c in melt_cols if c in df_limited.columns]
    df_limited_long = df_limited.melt(
        id_vars=['game_id', 'context_condition'],
        value_vars=existing_cols_l,
        var_name='metric_name',
        value_name='metric_value'
    )

    combined = pd.concat([df_full_long, df_limited_long], ignore_index=True)
    return combined


def prepare_data_for_anova(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and prepare data for ANOVA.
    - Drop rows with NaN metric_value
    - Ensure context_condition and metric_name are categorical
    """
    df_clean = df.dropna(subset=['metric_value'])
    df_clean['context_condition'] = pd.Categorical(df_clean['context_condition'])
    df_clean['metric_name'] = pd.Categorical(df_clean['metric_name'])
    return df_clean


def compute_two_way_anova(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Compute two-way ANOVA: metric_value ~ C(context_condition) * C(metric_name).

    Returns the ANOVA table as a DataFrame if successful, None otherwise.
    """
    if _OLS is None or _ANOVA_LM is None:
        print("Error: statsmodels not installed. Cannot run ANOVA.")
        return None

    try:
        # Fit the model
        model = _OLS(
            'metric_value ~ C(context_condition) * C(metric_name)',
            data=df
        ).fit()

        # Generate ANOVA table
        anova_table = _ANOVA_LM(model)
        return anova_table
    except Exception as e:
        print(f"Error computing ANOVA: {e}")
        return None


def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    Returns adjusted p-values, capped at 1.0.
    """
    n = len(p_values)
    if n == 0:
        return []
    adjusted = [min(p * n, 1.0) for p in p_values]
    return adjusted


def compute_effect_size_etasquared(anova_table: pd.DataFrame) -> Dict[str, float]:
    """
    Compute Eta-squared effect sizes from ANOVA table.
    Eta-squared = SS_effect / SS_total
    """
    if anova_table is None or 'sum_sq' not in anova_table.columns:
        return {}

    total_ss = anova_table['sum_sq'].sum()
    if total_ss == 0:
        return {}

    etasq = {}
    for idx, row in anova_table.iterrows():
        term = str(idx)
        ss = row['sum_sq']
        etasq[term] = ss / total_ss

    return etasq


def run_anova_analysis(
    full_path: str,
    limited_path: str,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the full two-way ANOVA pipeline.

    Returns a dictionary containing:
    - anova_table: DataFrame
    - interaction_p_value: float
    - effect_sizes: dict
    - bonferroni_adjusted: list
    """
    # Load and prepare data
    df = load_experiment_results(full_path, limited_path)
    df_clean = prepare_data_for_anova(df)

    # Compute ANOVA
    anova_table = compute_two_way_anova(df_clean)

    result = {
        "status": "error",
        "message": "ANOVA computation failed or statsmodels missing",
        "anova_table": None,
        "interaction_p_value": None,
        "effect_sizes": {},
        "bonferroni_adjusted": []
    }

    if anova_table is not None:
        # Extract interaction p-value
        # The interaction term is usually named 'C(context_condition):C(metric_name)'
        interaction_row = anova_table[
            anova_table.index.str.contains(':')
        ]

        interaction_p = None
        if not interaction_row.empty:
            interaction_p = float(interaction_row['PR(>F)'].iloc[0])

        # Effect sizes
        effect_sizes = compute_effect_size_etasquared(anova_table)

        # Bonferroni (for all p-values in the table)
        p_vals = [float(p) for p in anova_table['PR(>F)']]
        bonf_adj = apply_bonferroni_correction(p_vals)

        result = {
            "status": "success",
            "message": "ANOVA completed successfully",
            "anova_table": anova_table.to_dict(),
            "interaction_p_value": interaction_p,
            "effect_sizes": effect_sizes,
            "bonferroni_adjusted": bonf_adj
        }

    # Write output if path provided
    if output_path and result["status"] == "success":
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run two-way ANOVA on social memory experiment results."
    )
    parser.add_argument(
        "--full",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/results_full.csv",
        help="Path to full context results CSV"
    )
    parser.add_argument(
        "--limited",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/results_limited.csv",
        help="Path to limited context results CSV"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/anova_results.json",
        help="Path to output JSON file"
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    print(f"Loading full results from: {args.full}")
    print(f"Loading limited results from: {args.limited}")

    result = run_anova_analysis(args.full, args.limited, args.output)

    if result["status"] == "success":
        print("ANOVA completed successfully.")
        print(f"Interaction p-value: {result['interaction_p_value']}")
        if result['interaction_p_value'] is not None:
            if result['interaction_p_value'] < 0.05:
                print("Result: Significant interaction (p < 0.05)")
            else:
                print("Result: No significant interaction (p >= 0.05)")
        print(f"Output written to: {args.output}")
    else:
        print(f"ANOVA failed: {result['message']}")
        sys.exit(1)


if __name__ == "__main__":
    main()