"""
run_all.py

Orchestrates the full research pipeline by sequentially invoking the
main entry points of each component module. This script is the definitive
runnable command referenced in ``quickstart.md`` and ensures that all
declared deliverables (output JSON and PNG figures) are produced.

The script performs the following steps:

  1. Ensure required project directories exist.
  2. Download experimental data.
  3. Fetch DFT elastic constants from the Materials Project API.
  4. Merge and filter the datasets.
  5. Validate and save the final merged dataset.
  6. Generate SHA‑256 checksums for provenance.
  7. Update the project state file with artifact hashes.
  8. Train the DFT‑enhanced Random Forest model.
  9. Train the composition‑only baseline model.
 10. Run SHAP analysis on the final DFT‑enhanced model.
 11. Run bootstrap stability analysis.
 12. Generate summary plots (SHAP and stability).
 13. Assemble the final ``output.json`` file.

Each step calls the ``main`` function of the corresponding module,
which already implements the required functionality and writes its
output to the appropriate location under ``data/`` or ``figures/``.
Any failure aborts the pipeline with a clear error message, satisfying
the “fail loudly” requirement for the ingestion stage.

Usage:
    python code/run_all.py
"""
import sys
import logging
from pathlib import Path

# Add the project root to the import path so that sibling modules can be imported.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Import the global logger utility from the toolkit.
from llmxive_toolkit import get_logger

# Import the ensure_dirs helper to create required directories.
from config import ensure_dirs, CONFIG

# Import main functions from each pipeline component.
from ingestion.fetch_experimental import main as fetch_experimental_main
from ingestion.fetch_dft import main as fetch_dft_main
from ingestion.merge_and_filter import main as merge_and_filter_main
from ingestion.finalize_dataset import main as finalize_dataset_main
from ingestion.generate_checksums import main as generate_checksums_main
from ingestion.update_state import main as update_state_main

from modeling.train import main as train_dft_main
from modeling.train_baseline import main as train_baseline_main

from interpretability.shap_analysis import main as shap_analysis_main
from interpretability.bootstrap_stability import main as bootstrap_stability_main
from interpretability.plot_results import main as plot_results_main
from interpretability.finalize_output import main as finalize_output_main

# Set up a module‑level logger.
logger = get_logger(__name__)

def run_step(step_func, step_name):
    """Execute a pipeline step and log its outcome."""
    logger.info(f"=== Starting step: {step_name} ===")
    try:
        result = step_func()
        logger.info(f"=== Completed step: {step_name} ===")
        return result
    except Exception as exc:
        logger.error(f"Step '{step_name}' failed: {exc}", exc_info=True)
        sys.exit(1)

def main():
    """Run the full pipeline in the correct order."""
    # 1. Ensure directory structure exists.
    ensure_dirs()
    logger.info("Project directories verified/created.")

    # 2–7. Ingestion pipeline.
    run_step(fetch_experimental_main, "Fetch experimental data")
    run_step(fetch_dft_main, "Fetch DFT data")
    run_step(merge_and_filter_main, "Merge and filter datasets")
    run_step(finalize_dataset_main, "Finalize merged dataset")
    run_step(generate_checksums_main, "Generate checksums")
    run_step(update_state_main, "Update project state")

    # 8–9. Modeling.
    run_step(train_dft_main, "Train DFT‑enhanced Random Forest")
    run_step(train_baseline_main, "Train composition‑only baseline model")

    # 10–13. Interpretability and final output.
    run_step(shap_analysis_main, "SHAP analysis")
    run_step(bootstrap_stability_main, "Bootstrap stability analysis")
    run_step(plot_results_main, "Generate SHAP and stability plots")
    run_step(finalize_output_main, "Assemble final output.json")

    logger.info("All pipeline steps completed successfully.")
    logger.info(f"Results are available under: {CONFIG.DATA_RESULTS_DIR}")

if __name__ == "__main__":
    main()
