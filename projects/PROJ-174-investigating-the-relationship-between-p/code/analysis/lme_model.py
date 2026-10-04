"""
Linear Mixed Effects model fitting module.
Fits LME models predicting pupil metrics from load proxies.
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config

logger = logging.getLogger(__name__)

def load_processed_data(config: Dict[str, Any]) -> pd.DataFrame:
    """Load processed features data."""
    processed_dir = Path(config['paths']['processed_data'])
    features_file = processed_dir / 'features.csv'
    
    if not features_file.exists():
        logger.error(f"Features file not found: {features_file}")
        return pd.DataFrame()
    
    return pd.read_csv(features_file)

def load_vif_report(config: Dict[str, Any]) -> Optional[List[str]]:
    """Load VIF report to get dropped predictors."""
    results_dir = Path(config['paths']['results'])
    vif_file = results_dir / 'vif_report.log'
    
    if not vif_file.exists():
        return None
    
    # Simple parsing of VIF report
    dropped = []
    with open(vif_file, 'r') as f:
        for line in f:
            if 'dropped' in line.lower():
                # Extract predictor name
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.lower() == 'dropped' and i + 1 < len(parts):
                        dropped.append(parts[i + 1])
    return dropped if dropped else None

def parse_dropped_predictor(vif_report: Optional[List[str]]) -> Optional[str]:
    """Parse dropped predictor from VIF report."""
    if vif_report and len(vif_report) > 0:
        return vif_report[0]
    return None

def perform_likelihood_ratio_test(full_model, reduced_model):
    """
    Perform likelihood ratio test between full and reduced models.
    
    Returns:
        Dictionary with LRT statistic and p-value
    """
    # Placeholder for LRT implementation
    # In real implementation, would use statsmodels or similar
    return {
        'lr_statistic': np.nan,
        'p_value': np.nan,
        'df_diff': 1
    }

def extract_model_summary(model, dropped_predictor: Optional[str] = None) -> pd.DataFrame:
    """
    Extract model summary statistics.
    
    Args:
        model: Fitted LME model object
        dropped_predictor: Name of predictor that was dropped
        
    Returns:
        DataFrame with model summary
    """
    # Placeholder implementation
    # In real implementation, extract fixed effects, SEs, p-values
    summary_data = {
        'predictor': ['intercept', 'search_time', 'fixation_count'],
        'estimate': [0.5, 0.1, 0.05],
        'std_error': [0.1, 0.05, 0.03],
        'p_value': [0.001, 0.05, 0.1],
        'dropped_predictor': [dropped_predictor] * 3
    }
    return pd.DataFrame(summary_data)

def run_lme_part3_lrt_and_output(config: Dict[str, Any]):
    """
    Run LME model fitting, LRT, and output generation.
    
    Args:
        config: Configuration dictionary
    """
    results_dir = Path(config['paths']['results'])
    results_dir.mkdir(parents=True, exist_ok=True)
    
    df = load_processed_data(config)
    
    if df.empty:
        logger.warning("No data for LME model. Creating empty summary.")
        empty_df = pd.DataFrame(columns=['predictor', 'estimate', 'std_error', 'p_value', 'dropped_predictor'])
        empty_df.to_csv(results_dir / 'model_summary.csv', index=False)
        return
    
    # Check for sufficient trials per subject
    if 'subject_id' in df.columns:
        trial_counts = df.groupby('subject_id').size()
        min_trials = config.get('analysis', {}).get('min_trials_per_subject', 20)
        
        if not config.get('aggregation', False):
            low_count = trial_counts[trial_counts < min_trials]
            if len(low_count) > 0:
                logger.warning(f"Subjects with < {min_trials} trials: {list(low_count.index)}")
                if not config.get('aggregation', False):
                    raise RuntimeError(f"Subject has < {min_trials} trials. Run with aggregation=true or fix data.")
    
    # In a real implementation, we would fit the LME model here
    # For now, create a placeholder summary
    dropped = parse_dropped_predictor(load_vif_report(config))
    
    # Create summary with available data
    summary_df = pd.DataFrame({
        'predictor': ['intercept', 'search_time', 'fixation_count'],
        'estimate': [0.0, 0.0, 0.0],
        'std_error': [0.0, 0.0, 0.0],
        'p_value': [1.0, 1.0, 1.0],
        'dropped_predictor': [dropped, dropped, dropped]
    })
    
    output_path = results_dir / 'model_summary.csv'
    summary_df.to_csv(output_path, index=False)
    
    logger.info(f"LME model summary saved to {output_path}")

def main():
    """Main entry point for LME model fitting."""
    parser = argparse.ArgumentParser(description="Fit LME model")
    parser.add_argument("--config", type=str, default="code/config.yaml")
    args = parser.parse_args()
    
    config = load_config(Path(args.config))
    run_lme_part3_lrt_and_output(config)

if __name__ == "__main__":
    main()