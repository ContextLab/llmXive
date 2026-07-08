"""Deterministic quickstart script.

This script runs the full end‑to‑end pipeline on synthetic data.
It invokes the synthetic data generator, flags the data source,
runs ingestion/featurisation, training, evaluation, sensitivity
analysis and robustness checks.  After completion it asserts that
the key artefacts have been produced and prints a success message.

The script is deliberately minimal and does not require any
command‑line arguments – it can be executed directly with:

    python code/run_quickstart.py
"""

import sys
import random
import os
from pathlib import Path

# Set deterministic seeds for all libraries we use
random.seed(0)
os.environ["PYTHONHASHSEED"] = "0"
try:
    import numpy as np
    np.random.seed(0)
except Exception:
    pass
try:
    import torch
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
except Exception:
    pass

# Import pipeline entry points
from ingestion.generate_synthetic import generate_synthetic_dataset
from ingestion.flag_source import main as flag_source_main
from ingestion.ingest import main as ingest_main
from training.train import main as train_main
from training.evaluate import main as evaluate_main
from training.sensitivity import main as sensitivity_main
from training.robustness import main as robustness_main

def _run_step(step_func, name: str):
    """Run a pipeline step and raise a clear error on failure."""
    try:
        step_func()
    except Exception as exc:
        raise RuntimeError(f"Step '{name}' failed: {exc}") from exc

def main() -> None:
    """Execute the full synthetic‑data pipeline."""
    # 1. Generate a synthetic dataset (writes to data/raw/dataset.csv)
    _run_step(generate_synthetic_dataset, "generate_synthetic_dataset")

    # 2. Record that the source is synthetic
    _run_step(flag_source_main, "flag_source_main")

    # 3. Ingest & featurise the dataset (writes featurized.jsonl)
    _run_step(ingest_main, "ingest_main")

    # 4. Train models (creates model checkpoints under data/artifacts)
    _run_step(train_main, "train_main")

    # 5. Evaluate – for synthetic data this step should complete
    #    without creating an evaluation report (per spec)
    _run_step(evaluate_main, "evaluate_main")

    # 6. Sensitivity analysis (produces sensitivity_report.json)
    _run_step(sensitivity_main, "sensitivity_main")

    # 7. Robustness analysis (produces outlier_analysis.json)
    _run_step(robustness_main, "robustness_main")

    # -----------------------------------------------------------------
    # Assertions – ensure the pipeline produced the expected artefacts.
    # -----------------------------------------------------------------
    featurized_path = Path("data/processed/featurized.jsonl")
    assert featurized_path.is_file(), f"Missing featurized data at {featurized_path}"

    # At least one model checkpoint (torch .pt file) should exist.
    checkpoints = list(Path("data/artifacts").rglob("*.pt"))
    assert checkpoints, "No model checkpoint files found under data/artifacts"

    # Sensitivity report must exist.
    sensitivity_report = Path("artifacts/reports/sensitivity_report.json")
    assert sensitivity_report.is_file(), "Missing sensitivity_report.json"

    # Robustness report must exist.
    robustness_report = Path("artifacts/reports/outlier_analysis.json")
    assert robustness_report.is_file(), "Missing outlier_analysis.json"

    # Evaluation report is *not* created for synthetic data – ensure it is absent.
    evaluation_report = Path("artifacts/reports/evaluation.json")
    assert not evaluation_report.is_file(), (
        "Evaluation report should not be generated for synthetic data"
    )

    print("\n✅ Quickstart pipeline completed successfully on synthetic data.")
    print("   Produced artefacts:")
    print(f"   - {featurized_path}")
    print(f"   - {len(checkpoints)} model checkpoint(s) in data/artifacts")
    print(f"   - {sensitivity_report}")
    print(f"   - {robustness_report}")

if __name__ == "__main__":
    # Ensure the working directory is the repository root when the script
    # is invoked directly (helps when CI runs from a sub‑directory).
    repo_root = Path(__file__).resolve().parent.parent
    os.chdir(repo_root)

    main()