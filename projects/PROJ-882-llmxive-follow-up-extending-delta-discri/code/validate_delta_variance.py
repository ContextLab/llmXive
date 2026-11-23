"""
validate_delta_variance.py

This script verifies that the global variance of the DelTA coefficients
stored in ``data/processed/delta_coefficients.json`` exceeds a minimal
threshold (1e-9).  If the variance is less than or equal to the threshold,
a ``RuntimeError`` with the identifier ``ERR_TRIVIAL_TARGET`` is raised.

The script is deliberately lightweight – it does not write any new files.
It is intended to be used as a validation step after ``T015a`` (the
generation of the coefficients) and before downstream tasks that assume
non‑trivial coefficient variation.

Usage
-----
Run the module directly:

    python -m code.validate_delta_variance

The script will exit silently on success or raise the described
``RuntimeError`` on failure.
"""

import json
import sys
from pathlib import Path
from typing import List

import numpy as np

# Path to the generated coefficients file – this is the exact location
# mandated by task T015a.
COEFFICIENTS_PATH = Path("data/processed/delta_coefficients.json")

# Minimal acceptable variance (as specified in the task description).
MIN_VARIANCE = 1e-9


def load_coefficients(path: Path) -> List[float]:
    """
    Load the list of coefficient values from the JSON file.

    The JSON structure is defined by ``contracts/delta_oracle.schema.yaml``.
    For robustness we accept two common structures:

    1. A list of objects, each containing a ``coefficient`` field.
    2. A mapping ``example_id -> {token_id: coefficient, ...}``.

    Parameters
    ----------
    path: Path
        Path to the JSON file.

    Returns
    -------
    List[float]
        Flattened list of all coefficient values.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Delta coefficients file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    coeffs: List[float] = []

    if isinstance(data, list):
        # Expected format: [{... "coefficient": <float>, ...}, ...]
        for entry in data:
            if isinstance(entry, dict) and "coefficient" in entry:
                coeffs.append(float(entry["coefficient"]))
            else:
                raise ValueError(
                    f"Unexpected entry format in delta coefficients JSON: {entry}"
                )
    elif isinstance(data, dict):
        # Alternative format: example_id -> {token_id: coefficient, ...}
        for example_id, token_map in data.items():
            if isinstance(token_map, dict):
                for token_id, coeff in token_map.items():
                    coeffs.append(float(coeff))
            else:
                raise ValueError(
                    f"Unexpected token map for example {example_id}: {token_map}"
                )
    else:
        raise ValueError(
            f"Delta coefficients JSON must be a list or dict, got {type(data)}"
        )

    if not coeffs:
        raise ValueError("No coefficients found in the JSON file.")

    return coeffs


def verify_global_variance(coeffs: List[float], min_variance: float = MIN_VARIANCE) -> None:
    """
    Compute the variance of the provided coefficients and raise an error
    if the variance does not exceed ``min_variance``.

    Parameters
    ----------
    coeffs: List[float]
        Flat list of coefficient values.
    min_variance: float
        Threshold below which the variance is considered trivial.

    Raises
    ------
    RuntimeError
        If the computed variance is <= ``min_variance``.
    """
    variance = np.var(coeffs, dtype=np.float64)
    if variance <= min_variance:
        raise RuntimeError("ERR_TRIVIAL_TARGET")
    # No return value – success is silent.


def main() -> None:
    """
    Entry point for the script when executed directly.
    """
    try:
        coeffs = load_coefficients(COEFFICIENTS_PATH)
        verify_global_variance(coeffs)
    except Exception as exc:
        # Re‑raise the exception after printing a concise message so that
        # the caller (e.g., CI or the pipeline orchestrator) receives a
        # non‑zero exit code.
        print(f"[validate_delta_variance] Failure: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    # When run as a script we propagate any exception to the exit code.
    main()
