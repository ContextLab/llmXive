import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from analysis.correlations import load_processed_data, extract_pupil_metrics, calculate_pearson_correlation, benjamini_hochberg_fdr, compute_correlations, save_results
from analysis.lme_model import calculate_vif, mitigate_collinearity, handle_unfulfillable_predictors, validate_sufficient_trials, fit_lme_model, likelihood_ratio_test, save_model_summary, run_lme_pipeline

logger = logging.getLogger(__name__)

def load_analysis_data(data_dir: Path) -> Optional[pd.DataFrame]:
    """Load processed data from the data directory."""
    try:
        df = load_processed_data(data_dir)
        if df is None or df.empty:
            logger.error("No data loaded for analysis.")
            return None
        return df
    except Exception as e:
        logger.error(f"Error loading analysis data: {str(e)}")
        return None

def run_correlation_analysis(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """Run correlation analysis on the dataset."""
    logger.info("Running correlation analysis...")

    # Extract metrics
    metrics = extract_pupil_metrics(df, config)
    if not metrics:
        logger.warning("No pupil metrics extracted.")
        return {'status': 'partial', 'metrics': {}}

    # Calculate correlations
    corr_results = []
    for metric_name, metric_data in metrics.items():
        for proxy in ['search_time', 'fixation_count', 'target_salience']:
            if proxy in df.columns:
                try:
                    r, p = calculate_pearson_correlation(metric_data, df[proxy])
                    corr_results.append({
                        'metric': metric_name,
                        'proxy': proxy,
                        'r': r,
                        'p_raw': p
                    })
                except Exception as e:
                    logger.warning(f"Correlation failed for {metric_name} vs {proxy}: {e}")

    if not corr_results:
        logger.warning("No correlations computed.")
        return {'status': 'partial', 'correlations': []}

    # FDR Correction
    p_values = np.array([c['p_raw'] for c in corr_results])
    adjusted_p = benjamini_hochberg_fdr(p_values)

    # Update results
    for i, adj_p in enumerate(adjusted_p):
        corr_results[i]['p_adjusted'] = adj_p

    # Save
    output_path = Path("results/correlations.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_results(corr_results, output_path)

    logger.info(f"Correlation analysis complete. Saved to {output_path}")
    return {'status': 'success', 'correlations': corr_results}

def run_mixed_effects_analysis(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """Run Linear Mixed Effects analysis."""
    logger.info("Running Mixed Effects analysis...")

    # Validate trials
    try:
        validate_sufficient_trials(df, config)
    except RuntimeError as e:
        logger.error(str(e))
        return {'status': 'fail', 'reason': str(e)}

    # Check collinearity
    vif_values = calculate_vif(df, config)
    if any(v > 5 for v in vif_values.values()):
        logger.warning("High VIF detected. Mitigating collinearity.")
        df_reduced, drop_info = mitigate_collinearity(df, config, vif_values)
    else:
        df_reduced = df
        drop_info = []

    # Handle unfulfillable predictors
    df_final, unfulfillable_info = handle_unfulfillable_predictors(df_reduced, config)

    # Fit model
    try:
        model_result = fit_lme_model(df_final, config)
        if model_result is None:
            return {'status': 'fail', 'reason': 'Model fitting failed'}
    except Exception as e:
        logger.error(f"LME fitting error: {e}")
        return {'status': 'fail', 'reason': str(e)}

    # Likelihood Ratio Test
    lr_test_result = likelihood_ratio_test(df_final, config)

    # Save summary
    output_path = Path("results/model_summary.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_model_summary(model_result, lr_test_result, output_path)

    logger.info(f"Mixed Effects analysis complete. Saved to {output_path}")
    return {
        'status': 'success',
        'dropped_predictors': drop_info,
        'unfulfillable': unfulfillable_info,
        'model': model_result
    }

def run_full_analysis_pipeline(data_dir: Path, config: Dict[str, Any]) -> Dict[str, Any]:
    """Run the full analysis pipeline (Correlation + LME)."""
    logger.info("Starting Full Analysis Pipeline")

    # Load Data
    df = load_analysis_data(data_dir)
    if df is None:
        return {'status': 'fail', 'reason': 'Data loading failed'}

    # Run Correlation
    corr_result = run_correlation_analysis(df, config)

    # Run LME
    lme_result = run_mixed_effects_analysis(df, config)

    return {
        'status': 'success' if corr_result['status'] == 'success' and lme_result['status'] == 'success' else 'partial',
        'correlation': corr_result,
        'lme': lme_result
    }

def main():
    """CLI entry point for analysis."""
    from config import load_config
    import argparse

    parser = argparse.ArgumentParser(description="Run Analysis Pipeline")
    parser.add_argument("--data", type=str, required=True, help="Processed data directory")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Config file path")
    args = parser.parse_args()

    config = load_config(args.config)

    from logging_config import setup_logging
    setup_logging()

    result = run_full_analysis_pipeline(Path(args.data), config)

    if result['status'] == 'fail':
        sys.exit(1)

    logger.info("Analysis pipeline finished.")

if __name__ == "__main__":
    main()
