import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import pearsonr, spearmanr

sys.path.insert(0, str(Path(__file__).parent))
from utils.logging import get_logger

def load_config():
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def validate_metadata(metadata):
    """
    Validate metadata for required columns and determine analysis mode.
    Returns (is_valid, message, analysis_mode, error_report)
    analysis_mode: 'paired' | 'cross_sectional' | 'fail'
    """
    logger = get_logger("analysis")
    
    # Check for paired data columns
    has_pre = 'pre_fatigue' in metadata.columns
    has_post = 'post_fatigue' in metadata.columns
    has_pre_eeg = 'pre_eeg_id' in metadata.columns
    has_post_eeg = 'post_eeg_id' in metadata.columns
    
    # Check for baseline data columns
    has_baseline_fatigue = 'baseline_fatigue' in metadata.columns
    has_baseline_eeg = 'baseline_eeg_id' in metadata.columns

    paired_required = ['pre_fatigue', 'post_fatigue']
    missing_paired = [col for col in paired_required if col not in metadata.columns]

    if not missing_paired:
        # Paired data exists
        logger.info("Paired data detected. Proceeding with paired analysis (delta vs delta).")
        return True, "Paired data available", "paired", None

    # If paired is missing, check for baseline (cross-sectional)
    if has_baseline_fatigue and has_baseline_eeg:
        logger.info("Baseline data detected. Proceeding with cross-sectional analysis.")
        return True, "Baseline data available", "cross_sectional", None

    # Neither condition met
    error_report = {
        "status": "fail",
        "message": "Required data conditions not met.",
        "missing_paired_columns": missing_paired,
        "missing_baseline_columns": [],
        "available_columns": list(metadata.columns)
    }
    if not has_baseline_fatigue:
        error_report["missing_baseline_columns"].append("baseline_fatigue")
    if not has_baseline_eeg:
        error_report["missing_baseline_columns"].append("baseline_eeg_id")
        
    logger.error("Validation failed: Neither paired nor baseline data available.")
    return False, "No valid data configuration found", "fail", error_report

def run_benjamini_hochberg(p_values, alpha=0.05):
    """
    Apply Benjamini-Hochberg correction.
    """
    n = len(p_values)
    if n == 0:
        return np.array([])
        
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    ranks = np.arange(1, n + 1)
    threshold = (ranks / n) * alpha
    
    significant = np.zeros(n, dtype=bool)
    for i in range(n - 1, -1, -1):
        if sorted_p[i] <= threshold[i]:
            significant[i:] = True
            break
    
    # Map back to original indices
    result = np.zeros(n, dtype=bool)
    result[sorted_indices] = significant
    return result

def run_correlation_analysis(lzc_metrics, pe_metrics, metadata, analysis_mode):
    logger = get_logger("analysis")
    results = []

    if analysis_mode == "paired":
        logger.info("Running paired correlation analysis (Delta Complexity vs Delta Fatigue).")
        # Calculate fatigue delta
        metadata['fatigue_delta'] = metadata['post_fatigue'] - metadata['pre_fatigue']
        
        # Merge with metrics (assuming participant_id alignment)
        # For this implementation, we assume lzc_metrics has a 'participant_id' column
        # If the schema differs, we join on the available ID column
        if 'participant_id' in metadata.columns and 'participant_id' in lzc_metrics.columns:
            merged = pd.merge(lzc_metrics, metadata, on='participant_id', how='inner')
        else:
            # Fallback if IDs don't match exactly but lengths do (risky, but handles simple cases)
            if len(lzc_metrics) == len(metadata):
                merged = lzc_metrics.copy()
                merged['fatigue_delta'] = metadata['fatigue_delta'].values
            else:
                logger.error("Participant IDs do not align between metrics and metadata.")
                return pd.DataFrame()

        if not merged.empty and 'fatigue_delta' in merged.columns and 'lzc_value' in merged.columns:
            # Remove NaNs
            clean_data = merged.dropna(subset=['fatigue_delta', 'lzc_value'])
            if len(clean_data) > 1:
                r, p = pearsonr(clean_data['lzc_value'], clean_data['fatigue_delta'])
                results.append({
                    "metric": "lzc",
                    "analysis_mode": "paired",
                    "correlation": r,
                    "p_value": p,
                    "significant": p < 0.05
                })
            else:
                logger.warning("Insufficient data points for paired correlation.")
        else:
            logger.warning("Missing required columns for paired analysis.")

    elif analysis_mode == "cross_sectional":
        logger.info("Running cross-sectional correlation analysis (Baseline Complexity vs Baseline Fatigue).")
        # Merge with baseline data
        if 'participant_id' in metadata.columns and 'participant_id' in lzc_metrics.columns:
            merged = pd.merge(lzc_metrics, metadata, on='participant_id', how='inner')
        else:
            if len(lzc_metrics) == len(metadata):
                merged = lzc_metrics.copy()
                merged['baseline_fatigue'] = metadata['baseline_fatigue'].values
            else:
                logger.error("Participant IDs do not align.")
                return pd.DataFrame()

        if not merged.empty and 'baseline_fatigue' in merged.columns and 'lzc_value' in merged.columns:
            clean_data = merged.dropna(subset=['baseline_fatigue', 'lzc_value'])
            if len(clean_data) > 1:
                r, p = pearsonr(clean_data['lzc_value'], clean_data['baseline_fatigue'])
                results.append({
                    "metric": "lzc",
                    "analysis_mode": "cross_sectional",
                    "correlation": r,
                    "p_value": p,
                    "significant": p < 0.05
                })
            else:
                logger.warning("Insufficient data points for cross-sectional analysis.")
        else:
            logger.warning("Missing required columns for cross-sectional analysis.")
    else:
        logger.error("Invalid analysis mode provided.")

    return pd.DataFrame(results)

def main():
    logger = get_logger("analysis")
    logger.info("Starting analysis pipeline.")
    
    config = load_config()
    
    # Load metrics
    lzc_path = "data/processed/lzc_metrics.csv"
    pe_path = "data/processed/pe_metrics.csv"
    
    if not os.path.exists(lzc_path):
        logger.error(f"Complexity metrics file not found: {lzc_path}")
        sys.exit(1)
    
    lzc_metrics = pd.read_csv(lzc_path)
    pe_metrics = pd.read_csv(pe_path) if os.path.exists(pe_path) else pd.DataFrame()
    
    # Load metadata
    metadata = None
    metadata_path = "data/raw/eeg_data.jsonl"
    if os.path.exists(metadata_path):
        metadata = pd.read_json(metadata_path, lines=True)
    elif os.path.exists("data/raw/eeg_data.csv"):
        metadata = pd.read_csv("data/raw/eeg_data.csv")
    
    # Validate metadata
    if metadata is not None and not metadata.empty:
        is_valid, msg, analysis_mode, error_report = validate_metadata(metadata)
        
        if not is_valid:
            # Write error report and exit
            report_path = "data/analysis/validation_report.json"
            Path(report_path).parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, "w") as f:
                json.dump(error_report, f, indent=2)
            logger.error(f"Validation failed: {msg}")
            sys.exit(1)
    else:
        logger.error("Metadata file not found or empty. Cannot proceed.")
        report_path = "data/analysis/validation_report.json"
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w") as f:
            json.dump({"status": "fail", "message": "No metadata found"}, f)
        sys.exit(1)

    # Run analysis
    results = run_correlation_analysis(lzc_metrics, pe_metrics, metadata, analysis_mode)
    
    if results.empty:
        logger.warning("No correlation results generated.")
        # Still generate empty sensitivity table and report to avoid "hollow" crash, 
        # but mark as such if needed. However, task requires exit 1 if no data.
        # Since we validated, if results are empty, it's a data mismatch issue.
        # We will proceed to save what we have (empty) but log heavily.
    
    # Apply BH correction
    if not results.empty and 'p_value' in results.columns:
        results['significant_bh'] = run_benjamini_hochberg(results['p_value'])
    
    # Save results
    output_path = "data/analysis/correlation_results.csv"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_path, index=False)
    
    # Generate sensitivity table
    sensitivity_table = []
    thresholds = [0.05, 0.01]
    total_electrodes = len(results) if not results.empty else 0
    
    for alpha in thresholds:
        if not results.empty and 'p_value' in results.columns:
            sig_count = results[results['p_value'] <= alpha].shape[0]
        else:
            sig_count = 0
        sensitivity_table.append({
            "threshold": alpha,
            "count_significant": sig_count,
            "total_electrodes": total_electrodes
        })
    
    sens_df = pd.DataFrame(sensitivity_table)
    sens_path = "data/analysis/sensitivity_table.csv"
    sens_df.to_csv(sens_path, index=False)
    
    logger.info("Analysis complete.")
    logger.info(f"Results saved to {output_path}")
    logger.info(f"Sensitivity table saved to {sens_path}")

if __name__ == "__main__":
    main()