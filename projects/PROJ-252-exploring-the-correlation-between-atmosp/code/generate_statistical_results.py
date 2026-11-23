"""
Task T026: Generate statistical_results.json with p-values, effect sizes, and associational framing.

This script loads the master dataset, performs the statistical analysis (KS test, permutation test),
calculates effect sizes, and saves the results to a JSON file with explicit associational framing
as required by FR-005.
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from existing project modules
from config import get_processed_path, get_random_seed
from analysis import (
    load_master_dataset,
    perform_ks_test,
    perform_permutation_test,
    calculate_p_value_permutation,
    calculate_cohen_d,
    stratify_by_magnitude,
    stratify_by_region,
    interpret_effect_size,
    save_results
)
from utils.logging import get_logger

# Set up logger
logger = get_logger(__name__)

def generate_statistical_results(output_path: Path) -> Dict[str, Any]:
    """
    Perform statistical analysis on the master dataset and generate results.

    Args:
        output_path: Path to save the statistical results JSON.

    Returns:
        Dictionary containing p-values, effect sizes, and associational framing.
    """
    logger.info(f"Loading master dataset from {output_path.parent}")
    df = load_master_dataset()

    if df is None or df.empty:
        logger.error("Master dataset is empty or could not be loaded.")
        raise ValueError("Master dataset is empty or could not be loaded.")

    # Separate event and control windows
    event_df = df[df['is_event_window'] == True]
    control_df = df[df['is_event_window'] == False]

    if event_df.empty or control_df.empty:
        logger.error("Cannot perform analysis: missing event or control windows.")
        raise ValueError("Cannot perform analysis: missing event or control windows.")

    event_anomalies = event_df['pressure_anomaly'].values
    control_anomalies = control_df['pressure_anomaly'].values

    logger.info(f"Performing KS test: {len(event_anomalies)} event, {len(control_anomalies)} control samples")
    ks_stat, ks_pvalue = perform_ks_test(event_anomalies, control_anomalies)

    logger.info(f"Performing permutation test")
    # Use a reasonable number of permutations for the pilot (can be adjusted in config)
    n_permutations = 1000
    permuted_stats = perform_permutation_test(event_anomalies, control_anomalies, n_permutations)
    p_value_perm = calculate_p_value_permutation(ks_stat, permuted_stats)

    logger.info(f"Calculating effect size (Cohen's d)")
    cohens_d = calculate_cohen_d(event_anomalies, control_anomalies)
    effect_size_interpretation = interpret_effect_size(cohens_d)

    # Stratify by magnitude
    magnitude_groups = stratify_by_magnitude(df)
    magnitude_results = {}
    for mag_range, group_df in magnitude_groups.items():
        event_g = group_df[group_df['is_event_window'] == True]['pressure_anomaly'].values
        control_g = group_df[group_df['is_event_window'] == False]['pressure_anomaly'].values
        if len(event_g) > 0 and len(control_g) > 0:
            ks_stat_g, ks_p_g = perform_ks_test(event_g, control_g)
            perm_stats_g = perform_permutation_test(event_g, control_g, n_permutations)
            p_val_g = calculate_p_value_permutation(ks_stat_g, perm_stats_g)
            d_g = calculate_cohen_d(event_g, control_g)
            magnitude_results[mag_range] = {
                "ks_statistic": float(ks_stat_g),
                "ks_p_value": float(ks_p_g),
                "perm_p_value": float(p_val_g),
                "cohens_d": float(d_g),
                "n_event": len(event_g),
                "n_control": len(control_g)
            }

    # Stratify by region
    region_groups = stratify_by_region(df)
    region_results = {}
    for region, group_df in region_groups.items():
        event_g = group_df[group_df['is_event_window'] == True]['pressure_anomaly'].values
        control_g = group_df[group_df['is_event_window'] == False]['pressure_anomaly'].values
        if len(event_g) > 0 and len(control_g) > 0:
            ks_stat_g, ks_p_g = perform_ks_test(event_g, control_g)
            perm_stats_g = perform_permutation_test(event_g, control_g, n_permutations)
            p_val_g = calculate_p_value_permutation(ks_stat_g, perm_stats_g)
            d_g = calculate_cohen_d(event_g, control_g)
            region_results[region] = {
                "ks_statistic": float(ks_stat_g),
                "ks_p_value": float(ks_p_g),
                "perm_p_value": float(p_val_g),
                "cohens_d": float(d_g),
                "n_event": len(event_g),
                "n_control": len(control_g)
            }

    # Construct results dictionary with explicit associational framing
    results = {
        "metadata": {
            "task_id": "T026",
            "description": "Statistical Association Analysis Results",
            "fr_005_framing": "associational",
            "note": "These results represent statistical associations between pressure anomalies and earthquake events. Causality is not implied.",
            "timestamp": pd.Timestamp.now().isoformat(),
            "n_total_events": len(df[df['is_event_window'] == True]),
            "n_total_controls": len(df[df['is_event_window'] == False])
        },
        "primary_analysis": {
            "test_type": "Kolmogorov-Smirnov and Permutation Test",
            "ks_statistic": float(ks_stat),
            "ks_p_value": float(ks_pvalue),
            "permutation_p_value": float(p_value_perm),
            "n_permutations": n_permutations,
            "cohens_d": float(cohens_d),
            "effect_size_interpretation": effect_size_interpretation,
            "is_significant_perm": p_value_perm < 0.05
        },
        "stratified_by_magnitude": magnitude_results,
        "stratified_by_region": region_results,
        "framing_statement": (
            "The results presented here are strictly associational. "
            "A statistically significant p-value indicates that the distribution of pressure anomalies "
            "in the pre-earthquake window differs from the control window distribution. "
            "This does not imply a causal relationship between atmospheric pressure and earthquake occurrence. "
            "Further research is required to establish causality."
        )
    }

    # Save to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Statistical results saved to {output_path}")
    return results

def main():
    """Main entry point for T026."""
    output_path = get_processed_path() / "statistical_results.json"
    try:
        results = generate_statistical_results(output_path)
        logger.info("T026 completed successfully.")
    except Exception as e:
        logger.error(f"T026 failed: {e}")
        raise

if __name__ == "__main__":
    main()