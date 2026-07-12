import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

from config import get_project_root, get_metrics_path
from logging_setup import get_logger

logger = get_logger(__name__)

def generate_initial_report(correlations: Dict[str, tuple], n_samples: Optional[int] = None) -> None:
    """
    Generate the initial associational report.

    Args:
        correlations: Dict mapping metric pair names to (r, p) tuples.
                     Example: {'entropy_sa': (0.85, 0.001), 'entropy_qed': (-0.12, 0.45)}
        n_samples: Optional explicit sample size. If None, will attempt to infer from
                   the processed metrics file.
    
    Writes:
        data/processed/report.json with structure:
        {
            "type": "associational",
            "n": int,
            "correlations": {
                "entropy_sa": {"r": float, "p": float},
                ...
            }
        }
    """
    project_root = get_project_root()
    metrics_path = get_metrics_path()
    report_path = project_root / "data" / "processed" / "report.json"

    # Determine sample size
    if n_samples is None:
        if metrics_path.exists():
            try:
                df = pd.read_csv(metrics_path)
                n_samples = len(df)
                logger.info(f"Inferred sample size from {metrics_path}: {n_samples}")
            except Exception as e:
                logger.warning(f"Could not load {metrics_path} to infer sample size: {e}. Setting n=0.")
                n_samples = 0
        else:
            logger.warning(f"Metrics file {metrics_path} not found. Setting n=0.")
            n_samples = 0

    # Format correlations for JSON
    formatted_correlations = {}
    for key, (r, p) in correlations.items():
        formatted_correlations[key] = {
            "r": float(r),
            "p": float(p)
        }

    report_data = {
        "type": "associational",
        "n": n_samples,
        "correlations": formatted_correlations
    }

    # Ensure directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)

    logger.info(f"Initial report written to {report_path}")
    return report_path

def main():
    """
    Entry point for report generation if run directly.
    This expects correlations to be passed or loaded from a previous step.
    For the initial pipeline, this is typically called from main.py after analysis.
    """
    # Mock data for direct execution testing
    mock_correlations = {
        "entropy_sa": (0.65, 0.0001),
        "entropy_qed": (-0.15, 0.12),
        "lz_sa": (0.62, 0.0002),
        "lz_qed": (-0.18, 0.09)
    }
    
    try:
        path = generate_initial_report(mock_correlations)
        print(f"Report generated at: {path}")
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise

if __name__ == "__main__":
    main()