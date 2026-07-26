import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from config import ensure_dirs

logger = logging.getLogger(__name__)

def load_csv_if_exists(path: Path) -> pd.DataFrame | None:
    """Load a CSV file if it exists, otherwise return None."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None
    try:
        return pd.read_csv(path)
    except Exception as e:
        logger.error(f"Failed to load {path}: {e}")
        return None

def calculate_overall_stability(density_stable: bool, artifact_stable: bool) -> bool:
    """
    Determine overall stability.
    Returns True only if BOTH density and artifact analyses are stable.
    """
    return density_stable and artifact_stable

def validate_density_stability(csv_path: Path) -> tuple[bool, float]:
    """
    Validate density stability from sensitivity_density_report.csv.
    
    Schema expected: threshold, metric_name, std_dev, is_stable
    Returns: (is_stable, avg_std_dev)
    """
    df = load_csv_if_exists(csv_path)
    if df is None or df.empty:
        logger.error("Density report is missing or empty.")
        return False, 0.0

    if 'is_stable' not in df.columns:
        logger.error("Density report missing 'is_stable' column.")
        return False, 0.0

    # Check if all rows indicate stability
    all_stable = df['is_stable'].all()
    
    # Calculate average std_dev as a secondary metric
    avg_std_dev = df['std_dev'].mean() if 'std_dev' in df.columns else 0.0

    logger.info(f"Density stability check: all_stable={all_stable}, avg_std_dev={avg_std_dev:.4f}")
    return all_stable, avg_std_dev

def validate_artifact_stability(csv_path: Path) -> tuple[bool, float]:
    """
    Validate artifact stability from sensitivity_artifact_report.csv.
    
    Schema expected: rejection_threshold, metric_name, std_dev, is_stable
    Returns: (is_stable, avg_std_dev)
    """
    df = load_csv_if_exists(csv_path)
    if df is None or df.empty:
        logger.error("Artifact report is missing or empty.")
        return False, 0.0

    if 'is_stable' not in df.columns:
        logger.error("Artifact report missing 'is_stable' column.")
        return False, 0.0

    # Check if all rows indicate stability
    all_stable = df['is_stable'].all()

    # Calculate average std_dev as a secondary metric
    avg_std_dev = df['std_dev'].mean() if 'std_dev' in df.columns else 0.0

    logger.info(f"Artifact stability check: all_stable={all_stable}, avg_std_dev={avg_std_dev:.4f}")
    return all_stable, avg_std_dev

def main():
    """
    Aggregate results from T018a and T018b to generate data/results/sensitivity_summary.json.
    Schema: {"density_stable": bool, "artifact_stable": bool, "overall_stable": bool}
    """
    config = ensure_dirs()
    data_results_dir = Path(config['data_results_dir'])
    data_quality_dir = Path(config['data_quality_dir'])

    density_report_path = data_results_dir / "sensitivity_density_report.csv"
    artifact_report_path = data_results_dir / "sensitivity_artifact_report.csv"
    summary_path = data_results_dir / "sensitivity_summary.json"

    logger.info("Starting sensitivity validation (T018c)...")

    # Validate Density Stability
    density_stable, density_std = validate_density_stability(density_report_path)

    # Validate Artifact Stability
    artifact_stable, artifact_std = validate_artifact_stability(artifact_report_path)

    # Calculate Overall Stability
    overall_stable = calculate_overall_stability(density_stable, artifact_stable)

    summary_data = {
        "density_stable": density_stable,
        "artifact_stable": artifact_stable,
        "overall_stable": overall_stable,
        "details": {
            "density_avg_std_dev": round(density_std, 6),
            "artifact_avg_std_dev": round(artifact_std, 6)
        }
    }

    # Ensure directory exists and write file
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)

    logger.info(f"Sensitivity summary written to {summary_path}")
    logger.info(f"Result: density_stable={density_stable}, artifact_stable={artifact_stable}, overall_stable={overall_stable}")

    return 0

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    exit(main())
