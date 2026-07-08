"""
Sensitivity analysis for the molecular diffusion prediction project.

This module defines the hyperparameter grid for the sensitivity sweep
and provides a function to generate a sensitivity report by iterating over
the grid, invoking the training pipeline for each configuration, and
storing placeholder results. The actual training invocation is performed
via a subprocess call to the project's training entrypoint (not fully
implemented here), but the grid logic is fully testable.

Public API:
  - get_hyperparameter_grid() -> List[Dict[str, Any]]
  - generate_sensitivity_report() -> List[Dict[str, Any]]
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any

from utils.config import get_project_root

# ----------------------------------------------------------------------
# Hyperparameter grid definition
# ----------------------------------------------------------------------
def get_hyperparameter_grid() -> List[Dict[str, Any]]:
    """
    Returns the list of hyperparameter configurations to be evaluated.

    The grid currently consists of:
      * message_passing_steps: 1, 2, 3
      * learning_rate: 1e-4, 1e-3

    Returns
    -------
    List[Dict[str, Any]]
        A list where each element is a dict with keys
        ``message_passing_steps`` and ``learning_rate``.
    """
    steps = [1, 2, 3]
    learning_rates = [1e-4, 1e-3]

    grid: List[Dict[str, Any]] = []
    for step in steps:
        for lr in learning_rates:
            grid.append(
                {
                    "message_passing_steps": step,
                    "learning_rate": lr,
                }
            )
    return grid

# ----------------------------------------------------------------------
# Sensitivity report generation
# ----------------------------------------------------------------------
def _run_training_for_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the training pipeline for a single hyperparameter configuration.

    In a full implementation this would invoke the project's training
    script (e.g., ``python -m training.train``) with the appropriate CLI
    arguments. Here we simulate the call with a subprocess that simply
    echoes the configuration; this keeps the function side‑effect free
    while still exercising the subprocess mechanism.

    Parameters
    ----------
    config : Dict[str, Any]
        Hyperparameter configuration.

    Returns
    -------
    Dict[str, Any]
        A dictionary containing the original configuration plus a placeholder
        ``result`` field.
    """
    # Build a command that prints the JSON representation of the config.
    # Using the current Python interpreter ensures portability.
    cmd = [
        sys.executable,
        "-c",
        f"import json, sys; print(json.dumps({config}))",
    ]

    # Execute the command and capture stdout.
    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )
    # Parse the echoed JSON back into a dict.
    echoed_config = json.loads(completed.stdout.strip())
    # Attach a dummy result placeholder.
    echoed_config["result"] = None
    return echoed_config

def generate_sensitivity_report() -> List[Dict[str, Any]]:
    """
    Iterates over the hyperparameter grid, runs training for each
    configuration, and writes a consolidated JSON report.

    The report is stored at:
        ``artifacts/reports/sensitivity_report.json``

    Returns
    -------
    List[Dict[str, Any]]
        List of dictionaries, each containing a configuration and its
        placeholder result.
    """
    grid = get_hyperparameter_grid()
    results: List[Dict[str, Any]] = []

    for config in grid:
        res = _run_training_for_config(config)
        results.append(res)

    # Ensure the output directory exists.
    project_root = Path(get_project_root())
    report_path = project_root / "artifacts" / "reports"
    report_path.mkdir(parents=True, exist_ok=True)

    output_file = report_path / "sensitivity_report.json"
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI entry point: generate the sensitivity report.
    """
    generate_sensitivity_report()
    print("Sensitivity report generated at artifacts/reports/sensitivity_report.json")

if __name__ == "__main__":
    main()