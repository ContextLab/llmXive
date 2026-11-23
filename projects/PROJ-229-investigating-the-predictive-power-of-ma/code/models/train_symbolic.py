"""
Train a symbolic regression model using PySR.

This script loads the processed feature matrix and the target variable
(as decided by ``data/results/target_decision.json``), fits a symbolic
regression model, evaluates R² on a held‑out test set and writes the
top formulas to ``data/models/symbolic_formulas.txt``.

If the resulting R² ≤ 0.0 a warning is logged and a ``LIMITATION`` flag
is added to the output file.
"""

import json
import logging
import os
from pathlib import Path

import pandas as pd
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split

# PySR is an optional heavy dependency; it is listed in ``requirements.txt``.
from pysr import PySRRegressor

from config import get_config
from utils.logger import get_pipeline_logger, log_info, log_warning, log_error

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def load_target_decision(decision_path: Path) -> str:
    """Read the chosen target name from the decision JSON."""
    if not decision_path.is_file():
        raise FileNotFoundError(f"Target decision file not found: {decision_path}")
    with decision_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Expected key – the spec uses ``target`` but we fall back to common variants.
    for key in ("target", "chosen_target", "target_name"):
        if key in data:
            return data[key]
    raise KeyError(f"Target name not found in {decision_path}")

def load_processed_dataset(csv_path: Path) -> pd.DataFrame:
    """Load the processed feature CSV."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"Processed dataset not found: {csv_path}")
    df = pd.read_csv(csv_path)
    return df

def write_formulas(output_path: Path, formulas: list, r2: float, limitation: bool):
    """Write the symbolic formulas and R² to the output file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write(f"# Symbolic regression results (R² = {r2:.4f})\n")
        if limitation:
            f.write("# LIMITATION: Model R² ≤ 0.0 – predictive power is insufficient.\n")
        f.write("\n")
        for idx, formula in enumerate(formulas, start=1):
            f.write(f"{idx}. {formula}\n")
    log_info(f"Symbolic formulas written to {output_path}")

# --------------------------------------------------------------------------- #
# Main training routine
# --------------------------------------------------------------------------- #
def train_symbolic_regression():
    logger = get_pipeline_logger(__name__)

    # ------------------------------------------------------------------- #
    # Load configuration (currently only used for random seed)
    # ------------------------------------------------------------------- #
    cfg = get_config()
    random_seed = cfg.get("random_seed", 42)

    # ------------------------------------------------------------------- #
    # Resolve paths
    # ------------------------------------------------------------------- #
    project_root = Path(__file__).resolve().parents[2]  # repo root
    target_decision_path = project_root / "data" / "results" / "target_decision.json"
    processed_csv_path = project_root / "data" / "processed" / "processed_dataset.csv"
    output_path = project_root / "data" / "models" / "symbolic_formulas.txt"

    # ------------------------------------------------------------------- #
    # Load data
    # ------------------------------------------------------------------- #
    try:
        target_name = load_target_decision(target_decision_path)
        log_info(f"Target selected for symbolic regression: {target_name}")
    except Exception as e:
        log_error(f"Failed to load target decision: {e}")
        raise

    try:
        df = load_processed_dataset(processed_csv_path)
        log_info(f"Processed dataset loaded with shape {df.shape}")
    except Exception as e:
        log_error(f"Failed to load processed dataset: {e}")
        raise

    if target_name not in df.columns:
        raise KeyError(f"Target column '{target_name}' not present in processed dataset.")

    X = df.drop(columns=[target_name])
    y = df[target_name]

    # ------------------------------------------------------------------- #
    # Train/validation split
    # ------------------------------------------------------------------- #
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_seed
    )
    log_info(
        f"Split data: {X_train.shape[0]} train rows, {X_test.shape[0]} test rows."
    )

    # ------------------------------------------------------------------- #
    # PySR symbolic regression
    # ------------------------------------------------------------------- #
    # Configuration – these defaults are reasonable for a CPU‑only run.
    # The later revision task (T038) will tighten the time limit; we expose
    # them via the config for easy tweaking.
    time_limit = cfg.get("pysr_time_limit_seconds", 3600)  # 1 hour default
    niterations = cfg.get("pysr_niterations", 1000)

    log_info(
        f"Starting PySR symbolic regression (time_limit={time_limit}s, niterations={niterations})"
    )
    try:
        model = PySRRegressor(
            niterations=niterations,
            binary_operators=["+", "-", "*", "/"],
            unary_operators=["exp", "log", "sqrt", "sin", "cos"],
            loss="loss(x, y) = (x - y)^2",
            timeout=time_limit,
            verbose=False,
            random_state=random_seed,
        )
        model.fit(X_train.values, y_train.values)
    except Exception as e:
        log_error(f"PySR training failed: {e}")
        raise

    # ------------------------------------------------------------------- #
    # Evaluate on test set
    # ------------------------------------------------------------------- #
    y_pred = model.predict(X_test.values)
    r2 = r2_score(y_test, y_pred)
    log_info(f"Symbolic regression R² on test set: {r2:.4f}")

    limitation_flag = r2 <= 0.0
    if limitation_flag:
        log_warning(
            "Model R² ≤ 0.0 – predictive power is insufficient; flagging limitation."
        )

    # ------------------------------------------------------------------- #
    # Extract top formulas (sorted by complexity then loss)
    # ------------------------------------------------------------------- #
    # ``model.equations_`` is a pandas DataFrame sorted by loss by default.
    # We pick the ten best distinct equations.
    top_n = cfg.get("symbolic_top_n", 10)
    equations_df = model.equations_
    # Ensure we have a column named 'equation' (PySR provides it)
    if "equation" not in equations_df.columns:
        raise KeyError("PySR output does not contain 'equation' column.")
    top_formulas = equations_df["equation"].head(top_n).tolist()

    # ------------------------------------------------------------------- #
    # Write results
    # ------------------------------------------------------------------- #
    write_formulas(output_path, top_formulas, r2, limitation_flag)

# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main():
    """CLI entry point."""
    try:
        train_symbolic_regression()
    except Exception as exc:
        log_error(f"Training symbolic regression failed: {exc}")
        raise

if __name__ == "__main__":
    main()
