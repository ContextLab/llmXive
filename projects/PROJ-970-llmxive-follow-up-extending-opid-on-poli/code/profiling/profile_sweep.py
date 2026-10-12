"""
Profile the full experiment sweep to ensure runtime feasibility.

This script runs the full threshold sweep across all tiers using the
existing `ExperimentRunner` implementation. It records the actual wall‑clock
time taken and writes a short profiling report to ``data/results/profile.txt``.
The purpose is to verify that the estimated runtime reported by
``src.config.verify_feasibility`` (which must be ≤ 6 h) is realistic after
any refactoring or optimisation work.

Usage (from the repository root):
    python -m profiling.profile_sweep

The script respects the project‑wide random seed and logging conventions.
"""
import time
from llmxive_toolkit import paths, get_logger

# Project imports – use absolute imports relative to the repository root.
# The source files live under the ``code`` directory.
from code.config import set_seed, verify_feasibility
from code.experiments.runner import ExperimentRunner

def main() -> None:
    """
    Execute the full sweep and write a profiling summary.
    """
    # Initialise reproducibility
    set_seed()
    episodes_per_setting, estimated_hours = verify_feasibility()

    logger = get_logger(__name__)
    logger.info(
        "Starting full sweep profiling: %d episodes per setting (≈ %.2f h estimated)",
        episodes_per_setting,
        estimated_hours,
    )

    start_time = time.time()

    # Run the full experimental sweep using the existing ExperimentRunner.
    # The runner streams results to CSV files under ``data/processed``.
    runner = ExperimentRunner(episodes_per_setting=episodes_per_setting)
    runner.run_sweep()

    elapsed_seconds = time.time() - start_time
    elapsed_hours = elapsed_seconds / 3600.0

    logger.info(
        "Full sweep completed in %.2f seconds (≈ %.2f hours).",
        elapsed_seconds,
        elapsed_hours,
    )

    # Write a concise profiling report for later inspection.
    profile_path = paths.results("profile.txt")
    profile_path.write_text(
        f"elapsed_seconds: {elapsed_seconds:.2f}\\n"
        f"elapsed_hours: {elapsed_hours:.4f}\\n"
        f"estimated_hours: {estimated_hours:.4f}\\n"
    )
    logger.info("Profiling report written to %s", profile_path)

if __name__ == "__main__":
    main()
