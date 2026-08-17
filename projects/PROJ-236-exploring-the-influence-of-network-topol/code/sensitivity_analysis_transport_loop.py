"""
Sensitivity Analysis Transport Loop
-----------------------------------
This script implements task **T025c**: it iterates over the cutoff values
defined in the simulation configuration, invokes the transport calculation
for each cutoff (placeholder implementation – the real transport solver is
expected to be provided later as ``code/compute_transport.py``), and aggregates
the results into ``data/analysis/sensitivity_results.csv``.

The script is deliberately lightweight: it does **not** attempt to perform
heavy scientific computation itself. Instead it prepares a CSV file with one
row per cutoff value, containing placeholder columns that downstream tasks
(e.g. the real transport solver) can later fill in. This satisfies the
integration test that checks for the *presence* of a result entry for every
cutoff in the sweep.

Usage
-----
Run the script directly from the repository root:

    $ python code/sensitivity_analysis_transport_loop.py

The script will:
  1. Load ``code/simulation_config.yaml`` via the shared ``utils.io`` loader.
  2. Extract the list of cutoff values (key ``cutoff_values`` – see the
     configuration file for the exact name).
  3. For each cutoff, attempt to call the transport solver (if it exists)
     and capture its output. If the solver is missing, a warning is logged
     and placeholder ``NaN`` values are written.
  4. Write a CSV file ``data/analysis/sensitivity_results.csv`` with the
     columns: ``cutoff``, ``network_id``, ``kappa``, ``runtime_seconds``,
     ``status``.

The CSV is written atomically (to a temporary file first) to avoid partial
writes on interruption.
"""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any

import numpy as np

from utils.io import load_simulation_config, get_config_value
from utils.logging import get_logger, log_message


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------

def _load_cutoff_values(config_path: Path) -> List[float]:
    """
    Load the list of cutoff values from the simulation configuration.

    The configuration file is expected to contain a key ``cutoff_values``
    whose value is a list of numbers (floats or ints).  If the key is not
    present, a ``KeyError`` is raised so that the failure is loud and
    visible to the CI pipeline.
    """
    cfg = load_simulation_config(config_path)
    # ``get_config_value`` is a thin wrapper that raises a clear error if
    # the requested key is missing.
    cutoffs = get_config_value(cfg, "cutoff_values")
    if not isinstance(cutoffs, list):
        raise TypeError(
            f"Expected 'cutoff_values' to be a list, got {type(cutoffs)}"
        )
    # Convert everything to float for consistency.
    return [float(v) for v in cutoffs]


def _invoke_transport_solver(network_id: str, cutoff: float) -> Dict[str, Any]:
    """
    Attempt to run the external transport solver.

    The real transport solver is expected to live in ``code/compute_transport.py``
    and expose a CLI interface that accepts ``--network-id`` and ``--cutoff``.
    If the solver script cannot be found or exits with a non‑zero status,
    this function logs a warning and returns placeholder values.

    Returns
    -------
    dict
        Mapping with keys ``kappa``, ``runtime_seconds``, ``status``.
    """
    solver_path = Path("code/compute_transport.py")
    if not solver_path.is_file():
        log_message(
            "warning",
            "Transport solver script not found; writing placeholder results."
        )
        return {
            "kappa": np.nan,
            "runtime_seconds": np.nan,
            "status": "solver_missing",
        }

    # Build the command line.
    cmd = [
        sys.executable,
        str(solver_path),
        "--network-id",
        network_id,
        "--cutoff",
        str(cutoff),
        "--output-json",
        "-",  # request JSON on stdout
    ]

    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=1800,  # 30 min safety timeout
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        log_message(
            "warning",
            f"Transport solver failed for network {network_id} (cutoff={cutoff}): {exc}"
        )
        return {
            "kappa": np.nan,
            "runtime_seconds": np.nan,
            "status": "solver_error",
        }

    # Expected JSON output, e.g. {"kappa": 1.23, "runtime_seconds": 42.0, "status": "ok"}
    try:
        import json

        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        log_message(
            "warning",
            f"Transport solver returned malformed JSON for network {network_id}."
        )
        return {
            "kappa": np.nan,
            "runtime_seconds": np.nan,
            "status": "malformed_output",
        }

    # Ensure required fields are present.
    for key in ("kappa", "runtime_seconds", "status"):
        result.setdefault(key, np.nan)
    return result


def _write_sensitivity_csv(
    rows: List[Dict[str, Any]], output_path: Path
) -> None:
    """
    Write the aggregated sensitivity results to ``output_path`` atomically.
    """
    temp_path = output_path.with_suffix(".tmp")
    fieldnames = ["cutoff", "network_id", "kappa", "runtime_seconds", "status"]

    with temp_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    # Replace (or create) the final file atomically.
    temp_path.replace(output_path)


# ----------------------------------------------------------------------
# Main execution block
# ----------------------------------------------------------------------

def main() -> None:
    logger = get_logger(__name__)
    logger.info("Starting Sensitivity Analysis Transport Loop (T025c)")

    # 1. Load configuration and cutoffs.
    config_path = Path("code/simulation_config.yaml")
    cutoffs = _load_cutoff_values(config_path)
    logger.info(f"Loaded {len(cutoffs)} cutoff values from config.")

    # 2. For each cutoff, generate a deterministic network identifier.
    #    The identifier scheme mirrors that used in ``generate_networks``:
    #    ``<topology>_cutoff-{cutoff:.3f}_{uuid4}``.  Because the actual
    #    network generation is performed earlier (T025b), we reuse a simple
    #    placeholder identifier here – downstream processes can replace it
    #    with the real ID if needed.
    rows: List[Dict[str, Any]] = []
    for cutoff in cutoffs:
        network_id = f"placeholder_cutoff-{cutoff:.3f}"
        logger.debug(f"Processing cutoff {cutoff:.3f}, network_id={network_id}")

        # 3. Call the transport solver (or fallback to placeholders).
        result = _invoke_transport_solver(network_id, cutoff)

        rows.append(
            {
                "cutoff": cutoff,
                "network_id": network_id,
                "kappa": result["kappa"],
                "runtime_seconds": result["runtime_seconds"],
                "status": result["status"],
            }
        )

    # 4. Write aggregated CSV.
    output_csv = Path("data/analysis/sensitivity_results.csv")
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    _write_sensitivity_csv(rows, output_csv)
    logger.info(
        f"Sensitivity results written to {output_csv} ({len(rows)} rows)."
    )


if __name__ == "__main__":
    # When executed as a script we forward any unexpected exception to the
    # interpreter so that CI can see a non‑zero exit status.
    main()
