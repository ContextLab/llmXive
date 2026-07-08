"""
Verification and fallback logic for the data ingestion pipeline.

This module checks that ``plan.md`` records a dataset URL (added by
``fetch_real`` after a successful download).  If the URL is missing or the
expected raw data file is not present, the module invokes the synthetic
dataset generator (``code/ingestion/generate_synthetic.py``) and records the
data source in ``data/data_source_flag.json``.
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional

from utils.config import get_project_root
from utils.logging import get_logger, log_error, log_info

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def _read_plan_md() -> str:
    """Read the contents of ``plan.md`` as a string."""
    plan_path = get_project_root() / "plan.md"
    if not plan_path.is_file():
        raise FileNotFoundError(f"plan.md not found at expected location: {plan_path}")
    return plan_path.read_text(encoding="utf-8")

def _write_plan_md(contents: str) -> None:
    """Overwrite ``plan.md`` with the supplied contents."""
    plan_path = get_project_root() / "plan.md"
    plan_path.write_text(contents, encoding="utf-8")

# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def verify_plan_url() -> Optional[str]:
    """
    Scan ``plan.md`` for a URL that points to the dataset.

    Returns
    -------
    str or None
        The first URL found in the file, or ``None`` if no URL is present.
    """
    logger = get_logger()
    try:
        plan_text = _read_plan_md()
    except Exception as exc:
        logger.error(f"Failed to read plan.md: {exc}")
        return None

    # Very simple regex to capture http/https URLs
    url_match = re.search(r"https?://\S+", plan_text)
    if url_match:
        url = url_match.group(0).strip()
        logger.debug(f"Found dataset URL in plan.md: {url}")
        return url
    logger.debug("No dataset URL found in plan.md.")
    return None

def check_data_availability() -> bool:
    """
    Confirm that the raw dataset CSV exists and is non‑empty.

    Returns
    -------
    bool
        ``True`` if ``data/raw/dataset.csv`` exists and has size > 0,
        otherwise ``False``.
    """
    data_path = get_project_root() / "data" / "raw" / "dataset.csv"
    if data_path.is_file() and data_path.stat().st_size > 0:
        get_logger().debug(f"Raw dataset found at {data_path}")
        return True
    get_logger().debug(f"Raw dataset missing or empty at {data_path}")
    return False

def run_synthetic_fallback() -> None:
    """
    Execute the synthetic data generator.

    The generator lives in ``code/ingestion/generate_synthetic.py`` and must
    provide a ``main`` function that creates ``data/raw/dataset.csv``.
    """
    logger = get_logger()
    try:
        # Import inside the function so that the module can be added later
        from ingestion.generate_synthetic import main as synthetic_main
    except ImportError as exc:
        logger.error(
            "Synthetic generator not available. Expected module "
            "'code/ingestion/generate_synthetic.py' with a ``main`` function."
        )
        raise NotImplementedError(
            "Synthetic data generation is not implemented yet."
        ) from exc

    logger.info("Running synthetic data fallback generator.")
    synthetic_main()
    logger.info("Synthetic dataset generation completed.")

def write_source_flag(source: str) -> None:
    """
    Write ``data/data_source_flag.json`` indicating the origin of the data.

    Parameters
    ----------
    source : {"real", "synthetic"}
        Identifier for the data source.
    """
    if source not in {"real", "synthetic"}:
        raise ValueError("source must be either 'real' or 'synthetic'")

    flag_path = get_project_root() / "data" / "data_source_flag.json"
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    flag_content = {"source": source}
    flag_path.write_text(json.dumps(flag_content, indent=2), encoding="utf-8")
    get_logger().debug(f"Wrote data source flag: {flag_path} -> {flag_content}")

def main() -> None:
    """
    Entry point for the verification step.

    1. Verify that ``plan.md`` contains a dataset URL.
    2. Verify that the raw CSV exists.
    3. If either check fails, invoke the synthetic fallback generator.
    4. Record the data source in ``data/data_source_flag.json``.
    """
    logger = get_logger()
    logger.info("Starting verification of plan.md and raw dataset.")

    url = verify_plan_url()
    data_ok = check_data_availability()

    if url and data_ok:
        logger.info("Dataset URL present and raw data available – proceeding with real data.")
        write_source_flag("real")
        return

    # Something went wrong – fall back to synthetic data
    logger.warning(
        "Dataset URL missing or raw data unavailable. Falling back to synthetic data."
    )
    run_synthetic_fallback()
    write_source_flag("synthetic")
    logger.info("Verification step completed with synthetic data.")

# --------------------------------------------------------------------------- #
# When executed as a script, run ``main``.
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()
