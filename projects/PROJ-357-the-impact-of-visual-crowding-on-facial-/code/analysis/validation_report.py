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
    """Load clutter metrics from CSV."""
    path = Path(metrics_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    df = pd.read_csv(path)
    required_cols = ['file_path', 'flanker_count', 'spatial_frequency_energy']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in metrics CSV: {missing}")
    return df

def validate_correlation(df: pd.DataFrame) -> dict:
    """
    Validate that spatial_frequency_energy correlates with flanker_count.
    Returns a dict with correlation stats and p-value.
    """
    # Clean data
    clean_df = df.dropna(subset=['flanker_count', 'spatial_frequency_energy'])
    if len(clean_df) < 2:
        return {
            "status": "failed",
            "reason": "Insufficient data points for correlation (need >= 2)",
            "p_value": None,
            "correlation": None,
            "n": 0
        }

    # Calculate Pearson correlation
    correlation, p_value = stats.pearsonr(
        clean_df['flanker_count'].values,
        clean_df['spatial_frequency_energy'].values
    )

    # Check significance (p < 0.05)
    is_significant = p_value < 0.05

    return {
        "status": "passed" if is_significant else "failed",
        "reason": "Correlation is significant" if is_significant else "Correlation not significant (p >= 0.05)",
        "p_value": float(p_value),
        "correlation": float(correlation),
        "n": int(len(clean_df)),
        "is_significant": is_significant
    }

def main():
    """
    Generate validation_report.json confirming clutter metrics correlate with flanker count.
    """
    # Paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    metrics_path = project_root / "data" / "processed" / "clutter_metrics.csv"
    output_path = project_root / "data" / "processed" / "validation_report.json"

    logger.info(f"Loading metrics from: {metrics_path}")
    try:
        df = load_metrics(str(metrics_path))
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load metrics: {e}")
        report = {
            "status": "failed",
            "reason": str(e),
            "timestamp": pd.Timestamp.now().isoformat()
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return 1

    logger.info(f"Validating correlation on {len(df)} records...")
    validation_result = validate_correlation(df)

    # Add metadata
    report = {
        "task_id": "T023",
        "description": "Mandatory Validation: Correlation between clutter metrics and flanker count",
        "timestamp": pd.Timestamp.now().isoformat(),
        "input_file": str(metrics_path.relative_to(project_root)),
        "output_file": str(output_path.relative_to(project_root)),
        "validation": validation_result
    }

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report written to: {output_path}")
    logger.info(f"Result: {validation_result['status']} (p={validation_result['p_value']:.4f}, r={validation_result['correlation']:.4f})")

    # Return exit code based on validation
    return 0 if validation_result['status'] == 'passed' else 1

if __name__ == "__main__":
    exit(main())