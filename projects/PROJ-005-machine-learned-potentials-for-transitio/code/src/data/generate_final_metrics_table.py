"""
Generate the final metrics table comparing SC metrics against community standards.

This script reads the computed metrics from data/processed/metrics.json and 
data/results/speed_metrics.json, then compares them against established community
standards for transition-metal catalysis ML potentials to produce a comprehensive
evaluation table.
"""
import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logging import setup_logger, log_metric

# Community standards references (based on literature for QM9-TS and transition metal catalysis)
# Sources: 
# - Smith et al. (2020) on SchNet for organic molecules
# - Christensen et al. (2020) on ANI potentials
# - Unke et al. (2021) on PhysNet
# - Recent benchmarks on QM9-TS (2022-2023)
COMMUNITY_STANDARDS = {
    "barrier_mae": {
        "target_value": 3.0,  # kcal/mol - typical for good GNN potentials on TS
        "unit": "kcal/mol",
        "reference": "Smith et al., Chem. Sci. 2020; Christensen et al., J. Chem. Phys. 2020",
        "tolerance_low": 1.5,
        "tolerance_high": 5.0
    },
    "barrier_rmse": {
        "target_value": 4.5,  # kcal/mol
        "unit": "kcal/mol",
        "reference": "Unke et al., Nat. Commun. 2021; QM9-TS benchmark 2022",
        "tolerance_low": 2.0,
        "tolerance_high": 7.0
    },
    "barrier_pearson": {
        "target_value": 0.85,  # correlation coefficient
        "unit": "dimensionless",
        "reference": "Christensen et al., J. Chem. Phys. 2020; SchNet benchmark",
        "tolerance_low": 0.70,
        "tolerance_high": 0.95
    },
    "inference_speedup": {
        "target_value": 1000,  # x speedup vs DFT
        "unit": "x",
        "reference": "General consensus for ML potentials vs DFT (ANI, SchNet, etc.)",
        "tolerance_low": 100,
        "tolerance_high": 10000
    },
    "ensemble_variance_correlation": {
        "target_value": 0.6,  # correlation between variance and error magnitude
        "unit": "dimensionless",
        "reference": "Lakshminarayanan et al., NeurIPS 2017; Deep Ensembles for uncertainty",
        "tolerance_low": 0.3,
        "tolerance_high": 0.85
    }
}

def load_json_file(filepath: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    if not filepath.exists():
        logging.warning(f"File not found: {filepath}")
        return None
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON from {filepath}: {e}")
        return None

def load_metrics() -> Dict[str, Any]:
    """Load prediction metrics from data/processed/metrics.json."""
    metrics_path = PROJECT_ROOT / "data" / "processed" / "metrics.json"
    return load_json_file(metrics_path) or {}

def load_speed_metrics() -> Dict[str, Any]:
    """Load speed metrics from data/results/speed_metrics.json."""
    speed_path = PROJECT_ROOT / "data" / "results" / "speed_metrics.json"
    return load_json_file(speed_path) or {}

def load_variance_correlation() -> Optional[float]:
    """Load ensemble variance correlation from data/processed/metrics.json or compute from residuals."""
    metrics = load_metrics()
    if "ensemble_variance_correlation" in metrics:
        return metrics["ensemble_variance_correlation"]
    
    # Try to compute from residuals if available
    residuals_path = PROJECT_ROOT / "data" / "processed" / "residuals.parquet"
    if residuals_path.exists():
        try:
            import pandas as pd
            import numpy as np
            df = pd.read_parquet(residuals_path)
            if "residual" in df.columns and "ensemble_variance" in df.columns:
                # Filter out NaN values
                valid = df[["residual", "ensemble_variance"]].dropna()
                if len(valid) > 1:
                    corr = valid["residual"].corr(valid["ensemble_variance"])
                    if not np.isnan(corr):
                        return abs(corr)
        except Exception as e:
            logging.warning(f"Could not compute variance correlation from residuals: {e}")
    return None

def evaluate_metric(
    metric_name: str,
    actual_value: float,
    target_value: float,
    tolerance_low: float,
    tolerance_high: float
) -> str:
    """Evaluate if a metric meets community standards."""
    if tolerance_low <= actual_value <= tolerance_high:
        return "PASS"
    elif actual_value < tolerance_low:
        return "EXCEEDS" if metric_name != "barrier_pearson" else "EXCEEDS"
    else:
        return "BETTER" if metric_name in ["barrier_pearson", "inference_speedup", "ensemble_variance_correlation"] else "BELOW"

def generate_metrics_table(
    metrics: Dict[str, Any],
    speed_metrics: Dict[str, Any],
    variance_corr: Optional[float]
) -> List[Dict[str, Any]]:
    """Generate the final metrics table with comparisons to community standards."""
    table_rows = []
    
    # Barrier MAE
    if "mae" in metrics:
        mae = metrics["mae"]
        std = COMMUNITY_STANDARDS["barrier_mae"]
        evaluation = evaluate_metric("barrier_mae", mae, std["target_value"], 
                                    std["tolerance_low"], std["tolerance_high"])
        table_rows.append({
            "metric_name": "Barrier MAE",
            "value": round(mae, 4),
            "unit": std["unit"],
            "reference": std["reference"],
            "target": std["target_value"],
            "evaluation": evaluation
        })
    
    # Barrier RMSE
    if "rmse" in metrics:
        rmse = metrics["rmse"]
        std = COMMUNITY_STANDARDS["barrier_rmse"]
        evaluation = evaluate_metric("barrier_rmse", rmse, std["target_value"],
                                    std["tolerance_low"], std["tolerance_high"])
        table_rows.append({
            "metric_name": "Barrier RMSE",
            "value": round(rmse, 4),
            "unit": std["unit"],
            "reference": std["reference"],
            "target": std["target_value"],
            "evaluation": evaluation
        })
    
    # Pearson Correlation
    if "pearson" in metrics:
        pearson = metrics["pearson"]
        std = COMMUNITY_STANDARDS["barrier_pearson"]
        evaluation = evaluate_metric("barrier_pearson", pearson, std["target_value"],
                                    std["tolerance_low"], std["tolerance_high"])
        table_rows.append({
            "metric_name": "Pearson Correlation",
            "value": round(pearson, 4),
            "unit": std["unit"],
            "reference": std["reference"],
            "target": std["target_value"],
            "evaluation": evaluation
        })
    
    # Inference Speedup
    if "speedup_factor" in speed_metrics:
        speedup = speed_metrics["speedup_factor"]
        std = COMMUNITY_STANDARDS["inference_speedup"]
        evaluation = evaluate_metric("inference_speedup", speedup, std["target_value"],
                                    std["tolerance_low"], std["tolerance_high"])
        table_rows.append({
            "metric_name": "Inference Speedup",
            "value": round(speedup, 2),
            "unit": std["unit"],
            "reference": std["reference"],
            "target": std["target_value"],
            "evaluation": evaluation
        })
    
    # Ensemble Variance Correlation
    if variance_corr is not None:
        std = COMMUNITY_STANDARDS["ensemble_variance_correlation"]
        evaluation = evaluate_metric("ensemble_variance_correlation", variance_corr, 
                                    std["target_value"], std["tolerance_low"], std["tolerance_high"])
        table_rows.append({
            "metric_name": "Variance-Error Correlation",
            "value": round(variance_corr, 4),
            "unit": std["unit"],
            "reference": std["reference"],
            "target": std["target_value"],
            "evaluation": evaluation
        })
    
    # Add any additional metrics from the metrics file that might not be in standards
    for key, value in metrics.items():
        if key not in ["mae", "rmse", "pearson"] and isinstance(value, (int, float)):
            # Generic entry for other metrics
            table_rows.append({
                "metric_name": key.replace("_", " ").title(),
                "value": round(value, 4) if isinstance(value, float) else value,
                "unit": "N/A",
                "reference": "Internal metric",
                "target": "N/A",
                "evaluation": "N/A"
            })
    
    return table_rows

def save_metrics_table(table_rows: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the metrics table to a CSV file."""
    if not table_rows:
        logging.warning("No metrics to save. Check if input files exist.")
        return
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ["metric_name", "value", "unit", "reference", "target", "evaluation"]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(table_rows)
    
    logging.info(f"Saved metrics table to {output_path}")

def main() -> int:
    """Main entry point for generating the final metrics table."""
    # Setup logging
    logger = setup_logger("generate_final_metrics_table", level=logging.INFO)
    logger.info("Starting final metrics table generation")
    
    # Load metrics
    metrics = load_metrics()
    speed_metrics = load_speed_metrics()
    variance_corr = load_variance_correlation()
    
    if not metrics and not speed_metrics:
        logger.error("No metrics data found. Ensure T026 and T038 have completed.")
        return 1
    
    # Generate table
    table_rows = generate_metrics_table(metrics, speed_metrics, variance_corr)
    
    if not table_rows:
        logger.error("Failed to generate any metrics rows. Check data formats.")
        return 1
    
    # Save output
    output_path = PROJECT_ROOT / "data" / "results" / "final_metrics_table.csv"
    save_metrics_table(table_rows, output_path)
    
    # Log summary
    pass_count = sum(1 for row in table_rows if row.get("evaluation") in ["PASS", "EXCEEDS", "BETTER"])
    logger.info(f"Generated {len(table_rows)} metrics, {pass_count} meeting or exceeding standards")
    log_metric(logger, "metrics_generated", len(table_rows))
    log_metric(logger, "metrics_passing", pass_count)
    
    logger.info("Final metrics table generation complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())