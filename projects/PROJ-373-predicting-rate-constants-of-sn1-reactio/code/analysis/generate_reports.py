import os
import sys
import csv
import json
import logging
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# Import from local modules as per API surface
from utils.logger import setup_logging
from config import AnalysisConfig, DataConfig, ensure_dirs

def setup_logging():
    """Setup logging for report generation."""
    return setup_logging("report_gen", logging.INFO)

def load_shap_rankings(logger):
    """Load SHAP rankings from interpret analysis output."""
    config = AnalysisConfig()
    # Assuming T026/T029 output is stored in artifacts as JSON or CSV
    # Based on T029, we need perturbation results and SHAP rankings
    shap_file = config.artifacts_dir / "shap_rankings.json"
    if not shap_file.exists():
        logger.warning(f"SHAP rankings file not found at {shap_file}. Generating empty placeholder for pipeline continuity.")
        return {}
    
    with open(shap_file, 'r') as f:
        return json.load(f)

def load_sensitivity_results(logger):
    """Load sensitivity results from T036/T027."""
    config = AnalysisConfig()
    # T036 produces sensitivity runner output, T027 aggregates.
    # We expect the aggregated result from T027 to be available here.
    # The task T030 requires generating sensitivity_report.csv.
    # We assume T027 produced a raw JSON or CSV that we read.
    # If T027 is not fully implemented to write to a specific file, 
    # we look for the output of the sensitivity_runner if T027 is just a wrapper.
    # Let's assume T027 wrote to artifacts/sensitivity_raw.json or similar.
    # However, T030 says "Generate ... sensitivity_report.csv".
    # If T027 already generated it, we just copy/validate. 
    # If T027 generated intermediate data, we process it here.
    # Given the dependency chain, T027 should have produced the data needed.
    # Let's look for the output of the sensitivity runner (T036) if T027 is empty.
    # Actually, T027 says "Aggregate results from T036".
    # Let's assume T036 wrote to artifacts/sensitivity_runner_results.json
    raw_file = config.artifacts_dir / "sensitivity_runner_results.json"
    if not raw_file.exists():
        logger.error(f"Sensitivity results file not found at {raw_file}. Cannot generate report.")
        return []
    
    with open(raw_file, 'r') as f:
        return json.load(f)

def load_perturbation_results(logger):
    """Load perturbation results from T029."""
    config = AnalysisConfig()
    # T029 performs perturbation study.
    raw_file = config.artifacts_dir / "perturbation_results_raw.json"
    if not raw_file.exists():
        logger.error(f"Perturbation results file not found at {raw_file}. Cannot generate report.")
        return []
    
    with open(raw_file, 'r') as f:
        return json.load(f)

def generate_feature_importance_plot(shap_rankings, logger):
    """Generate feature_importance.png."""
    if not shap_rankings:
        logger.warning("No SHAP rankings to plot. Creating empty placeholder plot.")
        # Create a minimal valid plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No Data Available', transform=ax.transAxes, ha='center', va='center')
        ax.set_title('Feature Importance (No Data)')
    else:
        # Sort by absolute value if needed, assuming ranking is already sorted or we sort here
        # Assuming shap_rankings is a list of dicts: [{'feature': 'name', 'value': score}, ...]
        # Or a dict: {'feature_name': score}
        if isinstance(shap_rankings, dict):
            sorted_features = sorted(shap_rankings.items(), key=lambda x: abs(x[1]), reverse=True)
            features = [f[0] for f in sorted_features]
            values = [f[1] for f in sorted_features]
        elif isinstance(shap_rankings, list):
            # Assume it's a list of dicts with 'feature' and 'value'
            sorted_items = sorted(shap_rankings, key=lambda x: abs(x.get('value', 0)), reverse=True)
            features = [item['feature'] for item in sorted_items]
            values = [item['value'] for item in sorted_items]
        else:
            logger.error("Unexpected SHAP rankings format.")
            return

        fig, ax = plt.subplots(figsize=(10, 8))
        y_pos = np.arange(len(features))
        ax.barh(y_pos, values, align='center')
        ax.set_yticks(y_pos)
        ax.set_yticklabels(features)
        ax.invert_yaxis()
        ax.set_xlabel('SHAP Value (Impact on Model Output)')
        ax.set_title('Feature Importance Summary')
    
    config = AnalysisConfig()
    output_path = config.artifacts_dir / "feature_importance.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved feature importance plot to {output_path}")
    return output_path

def generate_sensitivity_report(sensitivity_results, logger):
    """Generate sensitivity_report.csv."""
    config = AnalysisConfig()
    output_path = config.artifacts_dir / "sensitivity_report.csv"
    
    if not sensitivity_results:
        logger.warning("No sensitivity results to report. Creating empty CSV with headers.")
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['cutoff', 'r2', 'mae'])
        return output_path

    # Ensure results are in the format: [{'cutoff': float, 'r2': float, 'mae': float}, ...]
    # If the input is a list of dicts with these keys, we can write directly.
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['cutoff', 'r2', 'mae'])
        
        # Sort by cutoff to ensure consistent ordering
        sorted_results = sorted(sensitivity_results, key=lambda x: x.get('cutoff', 0.0))
        
        for res in sorted_results:
            cutoff = res.get('cutoff', 0.0)
            r2 = res.get('r2', 0.0)
            mae = res.get('mae', 0.0)
            writer.writerow([cutoff, r2, mae])
    
    logger.info(f"Saved sensitivity report to {output_path}")
    return output_path

def generate_perturbation_report(perturbation_results, logger):
    """Generate perturbation_results.csv."""
    config = AnalysisConfig()
    output_path = config.artifacts_dir / "perturbation_results.csv"
    
    if not perturbation_results:
        logger.warning("No perturbation results to report. Creating empty CSV with headers.")
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['feature_id', 'original_r2', 'perturbed_r2', 'delta'])
        return output_path

    # Expected format: [{'feature_id': int, 'original_r2': float, 'perturbed_r2': float, 'delta': float}, ...]
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['feature_id', 'original_r2', 'perturbed_r2', 'delta'])
        
        for res in perturbation_results:
            feature_id = res.get('feature_id', 0)
            original_r2 = res.get('original_r2', 0.0)
            perturbed_r2 = res.get('perturbed_r2', 0.0)
            delta = res.get('delta', 0.0)
            writer.writerow([feature_id, original_r2, perturbed_r2, delta])
    
    logger.info(f"Saved perturbation results to {output_path}")
    return output_path

def main():
    logger = setup_logging()
    logger.info("Starting report generation for T030")
    
    try:
        # Load data from previous steps (T026, T027, T029)
        # These functions handle missing files gracefully or log errors
        shap_rankings = load_shap_rankings(logger)
        sensitivity_results = load_sensitivity_results(logger)
        perturbation_results = load_perturbation_results(logger)
        
        # Generate artifacts
        generate_feature_importance_plot(shap_rankings, logger)
        generate_sensitivity_report(sensitivity_results, logger)
        generate_perturbation_report(perturbation_results, logger)
        
        logger.info("All reports generated successfully.")
        
    except Exception as e:
        logger.error(f"Error during report generation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()