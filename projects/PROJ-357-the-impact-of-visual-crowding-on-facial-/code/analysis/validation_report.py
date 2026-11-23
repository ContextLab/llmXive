"""
Generate validation report confirming clutter metrics correlate with flanker count.

This script validates that spatial frequency energy correlates with flanker count
(p < 0.05) as a mandatory gate for Phase 4 completion.

Output: data/processed/validation_report.json
Schema: {
    'correlation_p_value': float,
    'threshold_met': bool,
    'status': 'pass'|'fail',
    'sample_size': int
}
"""
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories

def setup_logging():
    """Configure logging for the validation report generation."""
    log_dir = project_root / "data" / "interim"
    ensure_directories([log_dir])
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "validation_report.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def load_metrics():
    """
    Load clutter metrics from data/processed/clutter_metrics.csv.
    
    Returns:
        pd.DataFrame: DataFrame with columns including 'spatial_frequency_energy' 
                     and 'flanker_count'.
        
    Raises:
        FileNotFoundError: If the metrics file does not exist.
        ValueError: If required columns are missing.
    """
    metrics_path = project_root / "data" / "processed" / "clutter_metrics.csv"
    
    if not metrics_path.exists():
        raise FileNotFoundError(
            f"Metrics file not found at {metrics_path}. "
            "Run code/utils/clutter_metrics.py first to generate this file."
        )
    
    df = pd.read_csv(metrics_path)
    
    required_columns = ['spatial_frequency_energy', 'flanker_count']
    missing = [col for col in required_columns if col not in df.columns]
    
    if missing:
        raise ValueError(
            f"Missing required columns in metrics file: {missing}. "
            "Ensure code/utils/clutter_metrics.py generates these columns."
        )
    
    logging.info(f"Loaded {len(df)} rows from {metrics_path}")
    return df

def validate_correlation(df, alpha=0.05):
    """
    Validate that spatial frequency energy correlates with flanker count.
    
    Performs a Pearson correlation test between spatial_frequency_energy and 
    flanker_count.
    
    Args:
        df (pd.DataFrame): DataFrame containing the metrics.
        alpha (float): Significance level threshold (default 0.05).
        
    Returns:
        dict: Validation report with correlation p-value, threshold met status,
              overall status, and sample size.
    """
    # Remove rows with missing values in the relevant columns
    clean_df = df[['spatial_frequency_energy', 'flanker_count']].dropna()
    sample_size = len(clean_df)
    
    if sample_size < 2:
        logging.warning("Insufficient data for correlation analysis (need at least 2 rows)")
        return {
            'correlation_p_value': None,
            'threshold_met': False,
            'status': 'fail',
            'sample_size': sample_size,
            'reason': 'Insufficient data'
        }
    
    # Perform Pearson correlation test
    correlation, p_value = stats.pearsonr(
        clean_df['spatial_frequency_energy'], 
        clean_df['flanker_count']
    )
    
    logging.info(f"Pearson correlation: r={correlation:.4f}, p={p_value:.4f}")
    
    threshold_met = p_value < alpha
    status = 'pass' if threshold_met else 'fail'
    
    report = {
        'correlation_p_value': float(p_value),
        'correlation_coefficient': float(correlation),
        'threshold_met': threshold_met,
        'status': status,
        'sample_size': sample_size,
        'alpha_threshold': alpha
    }
    
    if not threshold_met:
        logging.warning(
            f"Correlation p-value ({p_value:.4f}) did not meet threshold ({alpha}). "
            "This is a blocking gate for Phase 4 completion."
        )
    else:
        logging.info(
            f"Validation PASSED: p-value ({p_value:.4f}) < threshold ({alpha}). "
            "Phase 4 completion gate cleared."
        )
    
    return report

def main():
    """Main entry point for generating the validation report."""
    logger = setup_logging()
    logger.info("Starting validation report generation")
    
    try:
        # Load metrics
        df = load_metrics()
        
        # Validate correlation
        report = validate_correlation(df)
        
        # Ensure output directory exists
        output_dir = project_root / "data" / "processed"
        ensure_directories([output_dir])
        
        # Write report
        output_path = output_dir / "validation_report.json"
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report written to {output_path}")
        
        # Exit with appropriate code
        if report['status'] == 'pass':
            logger.info("Validation PASSED - Phase 4 gate cleared")
            sys.exit(0)
        else:
            logger.error("Validation FAILED - Phase 4 gate blocked")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
