import os
import json
import logging
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_metrics(metrics_path: str) -> pd.DataFrame:
    """
    Load clutter metrics from CSV.
    Expected columns: file_path, flanker_count, spatial_frequency_energy, local_contrast_variance
    """
    path = Path(metrics_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    df = pd.read_csv(path)
    required_cols = ['file_path', 'flanker_count', 'spatial_frequency_energy']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in metrics file: {missing}")
    
    logger.info(f"Loaded {len(df)} records from {metrics_path}")
    return df

def validate_correlation(df: pd.DataFrame, metric_col: str = 'spatial_frequency_energy', 
                         predictor_col: str = 'flanker_count', alpha: float = 0.05) -> dict:
    """
    Validate that the specified metric correlates with the predictor (flanker count).
    Uses Pearson correlation for linear relationship.
    Returns a dictionary with test statistics and pass/fail status.
    """
    # Clean data
    clean_df = df[[predictor_col, metric_col]].dropna()
    
    if len(clean_df) < 3:
        raise ValueError(f"Insufficient data for correlation analysis (n={len(clean_df)}).")

    x = clean_df[predictor_col].values
    y = clean_df[metric_col].values

    # Calculate Pearson correlation
    r, p_value = stats.pearsonr(x, y)
    
    # Determine significance
    is_significant = p_value < alpha
    direction = "positive" if r > 0 else "negative"
    
    result = {
        "test": "Pearson Correlation",
        "metric": metric_col,
        "predictor": predictor_col,
        "sample_size": len(clean_df),
        "correlation_coefficient": float(r),
        "p_value": float(p_value),
        "alpha_threshold": alpha,
        "is_significant": is_significant,
        "direction": direction,
        "status": "PASS" if is_significant else "FAIL",
        "message": f"Correlation is {'significant' if is_significant else 'NOT significant'} (p={p_value:.4f} < {alpha})"
    }
    
    return result

def main():
    """
    Main entry point to generate the validation report.
    Reads clutter metrics, performs correlation analysis, and writes the report.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parents[2]
    metrics_path = project_root / "data" / "processed" / "clutter_metrics.csv"
    report_path = project_root / "data" / "processed" / "validation_report.json"

    logger.info(f"Project root: {project_root}")
    logger.info(f"Loading metrics from: {metrics_path}")

    try:
        # Load data
        df = load_metrics(str(metrics_path))

        # Perform validation
        report_data = validate_correlation(df)

        # Add metadata
        report_data["generated_at"] = str(pd.Timestamp.now())
        report_data["source_file"] = str(metrics_path)

        # Ensure output directory exists
        report_path.parent.mkdir(parents=True, exist_ok=True)

        # Write report
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"Validation report written to: {report_path}")
        logger.info(f"Result: {report_data['status']} - {report_data['message']}")

        return report_data

    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        raise

if __name__ == "__main__":
    main()
