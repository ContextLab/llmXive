"""
Sweep script for the linear classifier (Task T006).

It iterates over the λ‑values {0.1, 0.5, 1.0} and the seed list
{42, 43, 44, 45, 46}, calling ``src.train.trainer`` for each
configuration.  After all runs the CSV ``results/training_log.csv``
contains a row per experiment.
"""
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Hyper‑parameter grid (as required by the specification)
LAMBDA_VALUES = [0.1, 0.5, 1.0]
SEEDS = [42, 43, 44, 45, 46]
EPOCHS = 15  # modest number to keep CPU runtime reasonable

def _run_one(lambda_: float, seed: int) -> int:
    """
    Execute ``src.train.trainer`` as a subprocess.  Using a subprocess
    mirrors the way the full pipeline orchestrates individual stages.
    """
    cmd = [
        sys.executable,
        "-m",
        "src.train.trainer",
        f"--lambda={lambda_}",
        f"--seed={seed}",
        f"--epochs={EPOCHS}",
    ]
    log.info(f"Running trainer: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=True)
    return result.returncode

def main() -> int:
    # Ensure the CSV header exists (empty file handled by trainer)
    csv_path = paths.results("training_log.csv")
    if not csv_path.is_file():
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path.write_text("model_id,lambda,seed,final_val_acc\n")

    for lam in LAMBDA_VALUES:
        for sd in SEEDS:
            ret = _run_one(lam, sd)
            if ret != 0:
                log.error(f"Trainer failed for λ={lam}, seed={sd}")
                return ret
    log.info(f"All sweeps completed – results written to {csv_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
