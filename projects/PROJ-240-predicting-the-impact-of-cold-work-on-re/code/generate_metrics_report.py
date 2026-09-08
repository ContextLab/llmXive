"""
Generate training metrics report (T028).
Reads the trained model and metrics from the training pipeline and writes
artifacts/reports/training_metrics.json with CV scores and test set performance.
"""
import json
import os
import sys
import pickle
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_project_root

def load_model(model_path: Path):
    """Load the trained Random Forest model."""
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_metrics(metrics_path: Path):
    """Load the metrics dictionary saved during training (T027)."""
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    with open(metrics_path, 'r') as f:
        return json.load(f)

def generate_metrics_report():
    """
    Generate artifacts/reports/training_metrics.json containing:
    - cv_r2_mean
    - cv_r2_std
    - test_mae
    - test_r2
    - pure_aluminum_flag
    """
    project_root = get_project_root()
    model_path = project_root / "artifacts" / "models" / "kinetic_model.pkl"
    metrics_path = project_root / "artifacts" / "reports" / "training_metrics_internal.json"
    output_path = project_root / "artifacts" / "reports" / "training_metrics.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load model to verify existence (optional, but good practice)
    try:
        model = load_model(model_path)
    except FileNotFoundError as e:
        raise RuntimeError(f"Cannot generate report: {e}")

    # Load internal metrics saved by train.py (T027)
    # Assuming train.py saved a JSON with keys: cv_r2_mean, cv_r2_std, test_mae, test_r2, pure_aluminum_flag
    try:
        internal_metrics = load_metrics(metrics_path)
    except FileNotFoundError:
        # Fallback: if train.py didn't save a separate JSON, try to infer from model or fail
        # However, per T027, we expect a JSON report to exist or be generated.
        # If T027 failed to write this, we must raise an error to avoid fabrication.
        raise RuntimeError(
            "Training metrics file (training_metrics_internal.json) not found. "
            "Ensure T027 (save_model/save_metrics) completed successfully."
        )

    # Construct the final report
    report = {
        "cv_r2_mean": internal_metrics.get("cv_r2_mean"),
        "cv_r2_std": internal_metrics.get("cv_r2_std"),
        "test_mae": internal_metrics.get("test_mae"),
        "test_r2": internal_metrics.get("test_r2"),
        "pure_aluminum_flag": internal_metrics.get("pure_aluminum_flag", False)
    }

    # Validate that all required fields are present and not None
    required_keys = ["cv_r2_mean", "cv_r2_std", "test_mae", "test_r2", "pure_aluminum_flag"]
    for key in required_keys:
        if report[key] is None:
            raise ValueError(f"Required metric '{key}' is missing or None in the internal metrics. "
                             "This indicates a failure in the training pipeline (T025-T027).")

    # Write the report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Training metrics report generated: {output_path}")
    return report

def main():
    try:
        generate_metrics_report()
    except Exception as e:
        print(f"Error generating metrics report: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
