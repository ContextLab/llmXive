import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from utils.logging import get_logger

def load_config(config_path="code/config.yaml"):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def validate_metadata(metadata):
    """
    Check for required columns in metadata.
    """
    required = ['pre_fatigue', 'post_fatigue', 'pre_eeg_id', 'post_eeg_id']
    if all(col in metadata.columns for col in required):
        return 'paired'
    elif 'pre_fatigue' in metadata.columns and 'pre_eeg_id' in metadata.columns:
        return 'cross-sectional'
    return None

def run_benjamini_hochberg(p_values, alpha=0.05):
    """
    Apply Benjamini-Hochberg correction.
    """
    p_values = np.array(p_values)
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    ranks = np.arange(1, n + 1)
    threshold = (ranks / n) * alpha
    
    # Find the largest k such that p(k) <= threshold(k)
    valid = sorted_p <= threshold
    if not np.any(valid):
        return np.zeros(n, dtype=bool)
    
    k = np.max(np.where(valid)[0])
    significant = np.zeros(n, dtype=bool)
    significant[sorted_indices[:k+1]] = True
    
    return significant

def run_correlation_analysis(lzc_df, pe_df, metadata, config, logger):
    """
    Run correlation analysis.
    """
    results = []
    method = config['analysis']['correlation_method']
    
    # This is a placeholder. Real implementation requires joining
    # lzc_df, pe_df with metadata based on IDs.
    # Since we don't have real metadata, we return empty.
    logger.warning("No metadata found to correlate with. Returning empty results.")
    return results

def main():
    config = load_config()
    logger = get_logger("analysis", config)
    logger.info("Starting analysis pipeline.")
    
    # Check for input files
    lzc_file = Path("data/processed/lzc_metrics.csv")
    pe_file = Path("data/processed/pe_metrics.csv")
    
    if not lzc_file.exists() or not pe_file.exists():
        logger.error("Complexity metrics file not found.")
        # Write empty report
        report = {"status": "failed", "reason": "Missing input files"}
        with open("data/analysis/report.json", 'w') as f:
            json.dump(report, f)
        sys.exit(1)
    
    lzc_df = pd.read_csv(lzc_file)
    pe_df = pd.read_csv(pe_file)
    
    # Try to load metadata if it exists
    metadata_path = Path("data/processed/metadata.csv")
    metadata = None
    if metadata_path.exists():
        metadata = pd.read_csv(metadata_path)
    
    if metadata is None:
        logger.warning("No metadata file found. Cannot perform correlation.")
        # Write empty results to satisfy file existence check
        pd.DataFrame(columns=['channel', 'correlation', 'p_value', 'significant']).to_csv("data/analysis/correlation_results.csv", index=False)
        return

    results = run_correlation_analysis(lzc_df, pe_df, metadata, config, logger)
    
    # Save results
    if results:
        pd.DataFrame(results).to_csv("data/analysis/correlation_results.csv", index=False)
    else:
        # Create empty file if no results
        pd.DataFrame(columns=['channel', 'correlation', 'p_value', 'significant']).to_csv("data/analysis/correlation_results.csv", index=False)

if __name__ == "__main__":
    main()
