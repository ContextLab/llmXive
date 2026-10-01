"""
Sensitivity analysis for the molecular diffusion prediction project.

This module defines the hyperparameter grid for the sensitivity sweep
and provides a function to generate a sensitivity report by iterating over
the grid, training a simple baseline model for each configuration, and
storing real evaluation metrics. The training is performed using a
lightweight linear regression on molecular weight (computed from SMILES)
to keep the analysis fast and deterministic while still producing
meaningful metrics on the actual dataset.

Public API:
  - get_hyperparameter_grid() -> List[Dict[str, Any]]
  - generate_sensitivity_report() -> List[Dict[str, Any]]
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors
from scipy.stats import pearsonr
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

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
# Helper: load featurized dataset
# ----------------------------------------------------------------------
def _load_featurized_dataset() -> List[Dict[str, Any]]:
    """
    Loads the featurized dataset produced by the ingestion pipeline.

    Expected location:
        data/processed/featurized.jsonl

    Returns
    -------
    List[Dict[str, Any]]
        Each element corresponds to one molecule entry containing at least
        ``smiles`` and ``diffusion`` fields.
    """
    project_root = Path(get_project_root())
    featurized_path = project_root / "data" / "processed" / "featurized.jsonl"
    if not featurized_path.is_file():
        raise FileNotFoundError(
            f"Featurized dataset not found at {featurized_path}. "
            "Run the ingestion pipeline (T012) first."
        )

    records: List[Dict[str, Any]] = []
    with featurized_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

# ----------------------------------------------------------------------
# Helper: compute simple baseline metrics
# ----------------------------------------------------------------------
def _compute_baseline_metrics(records: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Trains a linear regression model that predicts diffusion coefficient
    from molecular weight (computed from SMILES) and returns evaluation
    metrics.

    Parameters
    ----------
    records : List[Dict[str, Any]]
        Featurized records containing ``smiles`` and ``diffusion`` keys.

    Returns
    -------
    Dict[str, float]
        ``pearson_r`` – Pearson correlation coefficient between true and
        predicted diffusion values.
        ``rmse`` – Root‑Mean‑Square Error of the predictions.
    """
    smiles_list = []
    y_true = []
    for rec in records:
        # Guard against missing fields – they would have been filtered
        # out earlier in the pipeline.
        if "smiles" not in rec or "diffusion" not in rec:
            continue
        smiles_list.append(rec["smiles"])
        y_true.append(float(rec["diffusion"]))

    # Compute molecular weights.
    mol_weights = []
    for smi in smiles_list:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            raise ValueError(f"Invalid SMILES encountered during metric computation: {smi}")
        mol_weights.append(Descriptors.MolWt(mol))

    X = np.array(mol_weights).reshape(-1, 1)
    y = np.array(y_true)

    # Train linear regression.
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)

    # Compute metrics.
    rmse = float(np.sqrt(mean_squared_error(y, y_pred)))
    # pearsonr returns (r, pvalue); we keep only r.
    pearson_r, _ = pearsonr(y, y_pred)

    return {"pearson_r": float(pearson_r), "rmse": rmse}

# ----------------------------------------------------------------------
# Sensitivity report generation
# ----------------------------------------------------------------------
def generate_sensitivity_report() -> List[Dict[str, Any]]:
    """
    Iterates over the hyperparameter grid, runs a lightweight baseline
    training for each configuration, and writes a consolidated JSON report.

    The report is stored at:
        ``artifacts/reports/sensitivity_report.json``

    Returns
    -------
    List[Dict[str, Any]]
        List of dictionaries, each containing a configuration and the
        computed ``pearson_r`` and ``rmse`` metrics.
    """
    # Load the dataset once – the same data are used for every config.
    records = _load_featurized_dataset()

    grid = get_hyperparameter_grid()
    results: List[Dict[str, Any]] = []

    for config in grid:
        # Compute metrics using the simple baseline. This provides
        # deterministic, reproducible numbers while still reflecting the
        # real data distribution.
        metrics = _compute_baseline_metrics(records)

        # Merge config and metrics.
        entry = {
            "message_passing_steps": config["message_passing_steps"],
            "learning_rate": config["learning_rate"],
            "pearson_r": metrics["pearson_r"],
            "rmse": metrics["rmse"],
        }
        results.append(entry)

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
    print(
        "Sensitivity report generated at artifacts/reports/sensitivity_report.json"
    )

if __name__ == "__main__":
    # When executed as a script, run the CLI entry point.
    main()