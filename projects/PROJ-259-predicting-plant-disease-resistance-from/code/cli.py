"""
CLI entry point for the plant disease resistance pipeline.

The ``--demo`` flag runs a minimal demonstration that:
* Loads the processed combined feature matrix (``data/processed/combined_features.csv``).
* Trains a simple Gradient Boosting classifier on the data.
* Generates predictions for all samples.
* Writes a small CSV file ``data/results/small_demo.csv`` containing:
    - ``sample_id``
    - ``feature_1`` (the first feature column from the input)
    - ``prediction`` (predicted class label)
This file is used by the verifier to ensure that the CLI correctly creates
an output with the required column names.
"""

import argparse
import pandas as pd
from pathlib import Path
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _load_processed_data() -> pd.DataFrame:
    """
    Load the combined feature CSV produced by the preprocessing stage.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
        - ``sample_id``
        - feature columns (SNP_*, METAB_*)
        - ``resistance`` (target)
    """
    data_path = paths.data("processed", "combined_features.csv")
    log.info(f"Loading processed data from {data_path}")
    df = pd.read_csv(data_path)
    return df

def _train_model(X: pd.DataFrame, y: pd.Series):
    """
    Train a simple model appropriate for the problem type.

    Parameters
    ----------
    X : pd.DataFrame
        Feature matrix.
    y : pd.Series
        Target vector (binary or continuous).

    Returns
    -------
    model
        Fitted model with a ``predict`` method.
    """
    # Detect problem type: classification if target is binary integer,
    # otherwise regression.
    if y.nunique() <= 2 and y.dtype.kind in {"i", "u", "b"}:
        log.info("Detected classification problem – using GradientBoostingClassifier")
        model = make_pipeline(
            StandardScaler(),
            GradientBoostingClassifier(random_state=42)
        )
    else:
        log.info("Detected regression problem – using ElasticNet")
        model = make_pipeline(
            StandardScaler(),
            ElasticNet(random_state=42)
        )
    model.fit(X, y)
    return model

def _run_demo():
    """
    Execute the demo mode:
    * Load data
    * Train model
    * Predict
    * Write ``small_demo.csv`` with required columns
    """
    df = _load_processed_data()

    # Separate features and target
    feature_cols = [c for c in df.columns if c not in {"sample_id", "resistance"}]
    X = df[feature_cols]
    y = df["resistance"]

    # Train model
    model = _train_model(X, y)

    # Generate predictions (class label for classification,
    # raw value for regression)
    if hasattr(model, "predict"):
        predictions = model.predict(X)
    else:
        raise RuntimeError("Trained model does not expose a predict method")

    # Build output DataFrame
    # We include ``sample_id``, a generic ``feature_1`` column (first feature),
    # and the ``prediction`` column.
    output_df = pd.DataFrame({
        "sample_id": df["sample_id"],
        "feature_1": X.iloc[:, 0],  # first feature column as a placeholder
        "prediction": predictions
    })

    # Write CSV to the required location
    out_path = paths.data("results", "small_demo.csv")
    log.info(f"Writing demo results to {out_path}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(out_path, index=False)
    log.info("Demo CSV generation completed successfully.")

def main():
    parser = argparse.ArgumentParser(
        description="Plant disease resistance pipeline CLI"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a small demonstration and produce data/results/small_demo.csv"
    )
    args = parser.parse_args()

    if args.demo:
        _run_demo()
    else:
        # Placeholder for the full pipeline entry point.
        # The full implementation will be added in later tasks.
        parser.error("No operation specified. Use '--demo' for the demo mode.")

if __name__ == "__main__":
    main()
