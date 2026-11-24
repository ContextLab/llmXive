"""
Runtime Budget Estimator

This script reads the required sample size (`N_required`) from the power
analysis results (`data/results/power_analysis.json`), estimates the total
wall‑clock time assuming a per‑image budget of 60 seconds, and flags whether
the estimated runtime exceeds the 6‑hour budget.

The output is written to `data/results/runtime_estimate.json` with the
following fields:
  - estimated_seconds: int
  - exceeds_budget: bool
  - status: "feasible" | "infeasible"
"""
import json
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Constants
SECONDS_PER_IMAGE = 60
BUDGET_SECONDS = 6 * 3600  # 6 hours


def load_power_analysis() -> dict:
    """Load the power analysis JSON produced by T004.

    Returns
    -------
    dict
        Parsed JSON dictionary containing at least the ``N_required`` key.

    Raises
    ------
    FileNotFoundError
        If the expected ``power_analysis.json`` file does not exist.
    json.JSONDecodeError
        If the file cannot be parsed as valid JSON.
    """
    power_path = paths.results("power_analysis.json")
    if not power_path.is_file():
        raise FileNotFoundError(
            f"Power analysis file not found at expected location: {power_path}"
        )
    with power_path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    return data


def compute_estimate(N_required: int) -> dict:
    """Compute the runtime estimate.

    Parameters
    ----------
    N_required: int
        Number of samples required (per group) from the power analysis.

    Returns
    -------
    dict
        Dictionary containing ``estimated_seconds``, ``exceeds_budget`` and
        ``status``.
    """
    if N_required < 0:
        raise ValueError("N_required must be a non‑negative integer")
    estimated_seconds = N_required * SECONDS_PER_IMAGE
    exceeds_budget = estimated_seconds > BUDGET_SECONDS
    status = "infeasible" if exceeds_budget else "feasible"
    return {
        "estimated_seconds": estimated_seconds,
        "exceeds_budget": exceeds_budget,
        "status": status,
    }


def write_output(result: dict) -> None:
    """Write the runtime estimate JSON to the results folder.

    Parameters
    ----------
    result: dict
        The dictionary produced by :func:`compute_estimate`.
    """
    out_path = paths.results("runtime_estimate.json")
    # ``paths.results`` already ensures the parent directory exists.
    with out_path.open("w", encoding="utf-8") as fp:
        json.dump(result, fp, indent=2)
    log.info(f"Runtime estimate written to {out_path}")


def main() -> None:
    """Entry point for the runtime‑budget estimator."""
    log.info("Starting runtime budget estimation...")
    try:
        power_data = load_power_analysis()
    except Exception as exc:
        log.error(f"Failed to load power analysis data: {exc}")
        raise

    N_required = power_data.get("N_required")
    if N_required is None:
        raise ValueError("Power analysis JSON does not contain 'N_required'")

    # Ensure we are working with an integer (JSON may encode numbers as floats)
    N_required_int = int(N_required)

    estimate = compute_estimate(N_required_int)
    write_output(estimate)

    log.info(
        f"Estimated runtime: {estimate['estimated_seconds']} seconds "
        f"({'exceeds' if estimate['exceeds_budget'] else 'within'} budget)."
    )


if __name__ == "__main__":
    main()