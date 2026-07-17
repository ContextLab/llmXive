import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path

from config import get_processed_path, get_random_seed
from analysis import (
    load_master_dataset,
    stratify_by_magnitude,
    stratify_by_region,
    run_robustness_analysis,
    run_sensitivity_analysis,
    benjamini_hochberg_fdr,
    apply_fdr_correction,
    interpret_effect_size
)
from utils.logging import get_logger

logger = get_logger(__name__)

def load_statistical_results() -> dict:
    """Load the statistical results from the previous analysis stage."""
    stats_path = get_processed_path() / "statistical_results.json"
    if not stats_path.exists():
        raise FileNotFoundError(f"Statistical results file not found at {stats_path}")
    
    with open(stats_path, 'r') as f:
        return json.load(f)

def run_robustness_sweep(dataset: pd.DataFrame) -> dict:
    """
    Run robustness analysis by stratifying the dataset.
    
    Returns a dictionary containing results for each subset:
    - magnitude_stratified: { "4.0-5.0": {...}, ">5.0": {...} }
    - region_stratified: { "Pacific Ring of Fire": {...}, "Other": {...} }
    """
    results = {
        "magnitude_stratified": {},
        "region_stratified": {}
    }
    
    # Stratify by magnitude
    magnitude_groups = stratify_by_magnitude(dataset)
    for label, group_df in magnitude_groups.items():
        logger.info(f"Running robustness analysis for magnitude group: {label}")
        subset_stats = run_robustness_analysis(group_df)
        results["magnitude_stratified"][label] = subset_stats
    
    # Stratify by region
    region_groups = stratify_by_region(dataset)
    for label, group_df in region_groups.items():
        logger.info(f"Running robustness analysis for region: {label}")
        subset_stats = run_robustness_analysis(group_df)
        results["region_stratified"][label] = subset_stats
    
    return results

def run_sensitivity_sweep(dataset: pd.DataFrame) -> dict:
    """
    Run sensitivity analysis by sweeping anomaly cutoffs.
    
    Returns a dictionary containing results for each cutoff multiplier.
    """
    logger.info("Running sensitivity analysis sweep...")
    return run_sensitivity_analysis(dataset)

def generate_robustness_report(
    base_results: dict,
    robustness_results: dict,
    sensitivity_results: dict
) -> dict:
    """
    Compile the final robustness report combining base statistics,
    stratified results, and sensitivity sweeps.
    """
    report = {
        "metadata": {
            "generated_from": "statistical_results.json",
            "analysis_type": "robustness_and_sensitivity",
            "description": "Pilot report containing p-values, effect sizes, and significance rates for all subsets and sensitivity sweeps"
        },
        "base_analysis": base_results,
        "robustness_analysis": robustness_results,
        "sensitivity_analysis": sensitivity_results
    }
    
    # Apply FDR correction to all p-values in the report
    # Collect all p-values from robustness and sensitivity results
    all_p_values = []
    p_value_map = {}
    counter = 0
    
    # Extract p-values from robustness results
    for category, groups in robustness_results.items():
        for group_label, stats in groups.items():
            if 'p_value' in stats:
                p_val = stats['p_value']
                all_p_values.append(p_val)
                key = f"{category}_{group_label}"
                p_value_map[key] = p_val
                counter += 1
    
    # Extract p-values from sensitivity results
    if 'cutoffs' in sensitivity_results:
        for cutoff_info in sensitivity_results['cutoffs']:
            if 'p_value' in cutoff_info:
                p_val = cutoff_info['p_value']
                all_p_values.append(p_val)
                key = f"sensitivity_cutoff_{cutoff_info.get('cutoff_multiplier', 'unknown')}"
                p_value_map[key] = p_val
    
    # Apply Benjamini-Hochberg FDR correction
    if all_p_values:
        corrected_p_values = benjamini_hochberg_fdr(all_p_values, alpha=0.05)
        
        # Map corrected p-values back to the report structure
        correction_map = {}
        for i, (key, _) in enumerate(p_value_map.items()):
            if i < len(corrected_p_values):
                correction_map[key] = corrected_p_values[i]
        
        report["fdr_correction"] = {
            "method": "Benjamini-Hochberg",
            "alpha": 0.05,
            "total_tests": len(all_p_values),
            "corrections": correction_map
        }
        
        # Update p-values in robustness results with corrected values
        for category, groups in report["robustness_analysis"].items():
            for group_label, stats in groups.items():
                key = f"{category}_{group_label}"
                if key in correction_map:
                    stats["p_value_corrected"] = correction_map[key]
                    stats["is_significant_after_fdr"] = correction_map[key] < 0.05
        
        # Update p-values in sensitivity results
        if 'cutoffs' in report["sensitivity_analysis"]:
            for i, cutoff_info in enumerate(report["sensitivity_analysis"]["cutoffs"]):
                key = f"sensitivity_cutoff_{cutoff_info.get('cutoff_multiplier', 'unknown')}"
                if key in correction_map:
                    cutoff_info["p_value_corrected"] = correction_map[key]
                    cutoff_info["is_significant_after_fdr"] = correction_map[key] < 0.05
    
    return report

def main():
    """Main entry point for generating the robustness report."""
    logger.info("Starting robustness report generation (T031)...")
    
    # Load base statistical results
    logger.info("Loading base statistical results...")
    base_results = load_statistical_results()
    
    # Load master dataset
    logger.info("Loading master dataset...")
    dataset = load_master_dataset()
    
    if dataset.empty:
        raise ValueError("Master dataset is empty. Cannot perform robustness analysis.")
    
    # Run robustness sweep
    logger.info("Running robustness sweep...")
    robustness_results = run_robustness_sweep(dataset)
    
    # Run sensitivity sweep
    logger.info("Running sensitivity sweep...")
    sensitivity_results = run_sensitivity_sweep(dataset)
    
    # Generate final report
    logger.info("Generating final robustness report...")
    report = generate_robustness_report(
        base_results,
        robustness_results,
        sensitivity_results
    )
    
    # Save report
    output_path = get_processed_path() / "robustness_report.json"
    logger.info(f"Saving robustness report to {output_path}")
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Robustness report successfully generated: {output_path}")
    return output_path

if __name__ == "__main__":
    main()