"""
Main pipeline orchestration script.

This script orchestrates the high‑level steps of the data pipeline:
1. Download bulk configurations.
2. Build grain‑boundary (GB) supercells.
3. Compute interface‑region clustering descriptors.
4. Run segregation‑energy simulations.

Each step is imported lazily so that the script can run even if a
downstream module has unmet optional dependencies (e.g. `pymatgen`).
Errors specific to data unavailability (`[DATA_UNAVAILABLE]`) are
caught, logged, and cause a clean exit with status code 1.
Other unexpected errors are re‑raised after logging.

The script can be invoked directly:

    python code/main.py --mode full

The `--mode` flag is accepted for future extensions but currently does
not alter behaviour.
"""

import argparse
import logging
import sys
from pathlib import Path

# Configure root logger for the pipeline
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def _run_step(step_name: str, import_path: str):
    """
    Helper to import a ``main`` function from a module and execute it.

    Parameters
    ----------
    step_name : str
        Human‑readable description of the step (used for logging).
    import_path : str
        Dotted import path to the module that defines ``main``.
    """
    try:
        module = __import__(import_path, fromlist=["main"])
        step_main = getattr(module, "main")
        logger.info("Running step: %s", step_name)
        step_main()
    except ImportError as exc:
        # The module (or one of its transitive imports) is missing.
        logger.warning(
            "Skipping step '%s' because the module could not be imported: %s",
            step_name,
            exc,
        )
    except RuntimeError as exc:
        # Specific handling for the `[DATA_UNAVAILABLE]` sentinel.
        if "[DATA_UNAVAILABLE]" in str(exc):
            logger.error("Data unavailable during step '%s': %s", step_name, exc)
            sys.exit(1)
        else:
            logger.exception("Runtime error in step '%s'", step_name)
            raise
    except Exception as exc:
        # Unexpected exception – log and re‑raise to make debugging easier.
        logger.exception("Unexpected error in step '%s'", step_name)
        raise

def run_pipeline():
    """
    Execute the complete pipeline in the logical order required by the
    specification.
    """
    logger.info("Starting pipeline orchestration...")

    # 1. Download bulk configurations
    _run_step("Download bulk configurations", "data.download")

    # 2. Build grain‑boundary supercells
    _run_step("Build GB supercells", "data.gb_builder")

    # 3. Compute clustering descriptors (interface region only)
    _run_step("Compute interface‑region descriptors", "data.descriptors")

    # 4. Run segregation‑energy simulations
    _run_step("Run segregation‑energy simulations", "data.simulate_energy")

    logger.info("Pipeline completed successfully.")

def _parse_args():
    parser = argparse.ArgumentParser(
        description="Orchestrate the impurity‑clustering data pipeline."
    )
    parser.add_argument(
        "--mode",
        choices=["full", "ci"],
        default="full",
        help="Execution mode (reserved for future use).",
    )
    return parser.parse_args()

def main():
    """
    Entry point for ``python code/main.py``.
    """
    _ = _parse_args()  # Currently unused but kept for CLI compatibility.
    run_pipeline()
    return 0

if __name__ == "__main__":
    sys.exit(main())