"""
Wrapper script that runs the training pipeline for both low‑ and high‑potential bins
and consolidates the results into a single JSON file required by downstream
evaluation steps.

The original ``trainer.py`` writes ``model_run_low.json`` and ``model_run_high.json``.
This wrapper loads both files (if they exist) and merges the metrics into
``data/processed/model_run.json``.
"""

import json
from pathlib import Path

from config import get_data_dir, get_processed_dir
from models.trainer import run_trainer_pipeline

def main() -> None:
    # Execute training for both bins
    low_metrics = run_trainer_pipeline("low")
    high_metrics = run_trainer_pipeline("high")

    # Consolidate into a single dictionary
    consolidated = {
        "low_bin": low_metrics,
        "high_bin": high_metrics,
    }

    processed_dir = Path(get_processed_dir())
    output_path = processed_dir / "model_run.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(consolidated, f, indent=2)
    print(f"Training completed. Consolidated model run written to {output_path}")


if __name__ == "__main__":
    main()
