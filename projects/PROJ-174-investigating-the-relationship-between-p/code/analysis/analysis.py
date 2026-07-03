"""
Analysis pipeline for pupil dilation and cognitive load relationship.
Refactored to reduce cyclomatic complexity (< 15 per function).
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

# Import existing modules
from analysis.correlations import (
    calculate_pearson_correlation,
    benjamini_hochberg_fdr,
    load_processed_data,
    compute_correlations,
    save_results as save_correlation_results
)
from analysis.lme_model import (
    fit_lme_model,
    calculate_vif,
    mitigate_collinearity,
    save_model_summary,
    run_lme_pipeline
)

logger = logging.getLogger(__name__)

def load_analysis_data(input_dir: str) -> pd.DataFrame:
    """Load processed data for analysis."""
    input_path = Path(input_dir)
    csv_files = list(input_path.glob("processed_*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(f"No processed data found in {input_dir}")
    
    # Concatenate all processed files
    dfs = []
    for f in csv_files:
        df = pd.read_csv(f)
        # Add source filename as subject identifier if not present
        if 'subject_id' not in df.columns:
            df['subject_id'] = f.stem.replace("processed_", "")
        dfs.append(df)
    
    return pd.concat(dfs, ignore_index=True)

def run_correlation_analysis(
    data: pd.DataFrame,
    output_dir: str
) -> Dict[str, Any]:
    """
    Run Pearson correlation analysis between pupil metrics and load proxies.
    Returns correlation results summary.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Compute correlations
    correlations = compute_correlations(data)
    
    # Apply FDR correction
    corrected_results = benjamini_hochberg_fdr(correlations)
    
    # Save results
    save_correlation_results(corrected_results, str(output_path / "correlations.csv"))
    
    return {
        'num_correlations': len(corrected_results),
        'significant_count': sum(1 for r in corrected_results if r['p_adj'] < 0.05)
    }

def run_mixed_effects_analysis(
    data: pd.DataFrame,
    output_dir: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run Linear Mixed Effects model analysis.
    Returns model summary and diagnostics.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Run LME pipeline
    model_results = run_lme_pipeline(data, config)
    
    # Save model summary
    save_model_summary(
        model_results['coefficients'],
        model_results['std_errors'],
        model_results['p_values'],
        model_results['likelihood_ratio'],
        str(output_path / "model_summary.csv")
    )
    
    return model_results

def run_full_analysis_pipeline(
    input_dir: str,
    output_dir: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute the full analysis pipeline: correlations + LME models.
    Returns comprehensive results summary.
    """
    logger.info("Loading analysis data...")
    data = load_analysis_data(input_dir)
    
    results = {
        'data_points': len(data),
        'subjects': data['subject_id'].nunique() if 'subject_id' in data.columns else 0,
        'correlations': None,
        'lme_model': None
    }
    
    # Run correlation analysis
    logger.info("Running correlation analysis...")
    results['correlations'] = run_correlation_analysis(data, output_dir)
    
    # Run LME analysis
    logger.info("Running mixed effects model...")
    results['lme_model'] = run_mixed_effects_analysis(data, output_dir, config)
    
    return results

def main():
    """Main entry point for analysis pipeline."""
    import argparse
    from config import load_config
    
    parser = argparse.ArgumentParser(description="Analyze pupil dilation and cognitive load")
    parser.add_argument("--input", required=True, help="Input directory with processed data")
    parser.add_argument("--output", required=True, help="Output directory for results")
    parser.add_argument("--config", default="code/config.yaml", help="Config file path")
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Run pipeline
    results = run_full_analysis_pipeline(args.input, args.output, config)
    
    # Log summary
    logger.info(f"Analysis complete: {results}")
    print(f"Analysis complete. Results saved to {args.output}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
