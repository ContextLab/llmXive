"""
Logistic regression training utilities for the PROJ-110 project.

This module implements the `train_logistic_regression` function required by
task T035. The function loads the pre‑processed gene expression matrix,
filtered phenotype data, and baseline MetS labels, prepares a feature matrix
(including one‑hot encoding of categorical covariates), fits a scikit‑learn
LogisticRegression model, saves the trained model to disk, and returns the
fitted estimator.
"""

import logging
from pathlib import Path
from typing import Any

import pandas as pd
from joblib import dump
from sklearn.linear_model import LogisticRegression

from utils.config import get_project_paths
from .modeling import prepare_model_features  # type: ignore


def train_logistic_regression() -> LogisticRegression:
    """
    Train a logistic regression model to predict Metabolic Syndrome (MetS)
    status using core circadian gene expression and covariates.

    The model formula is:
        MetS ~ Gene_Expression + Age + Sex + Tissue + PMI + Time_of_Death

    Returns
    -------
    LogisticRegression
        The fitted scikit‑learn LogisticRegression estimator.

    Side Effects
    -------------
    - Writes the trained model to
      ``data/processed/logistic_regression_model.pkl``.
    - Logs progress and any errors to the project logger.
    """
    logger = logging.getLogger(__name__)

    # Resolve project directories via the central config utility.
    paths = get_project_paths()
    processed_dir = Path(paths["processed_data_dir"])

    # Expected input files.
    expr_path = processed_dir / "core_genes_log2_matrix.csv"
    phenotype_path = processed_dir / "filtered_phenotype.csv"
    labels_path = processed_dir / "baseline_labels.csv"

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    logger.debug("Loading core gene expression matrix from %s", expr_path)
    expr_df = pd.read_csv(expr_path)
    # Ensure a column named ``sample_id`` exists for joins.
    if "sample_id" not in expr_df.columns:
        # Assume the first column holds the identifiers.
        expr_df = expr_df.rename(columns={expr_df.columns[0]: "sample_id"})

    logger.debug("Loading filtered phenotype data from %s", phenotype_path)
    phenotype_df = pd.read_csv(phenotype_path)

    logger.debug("Loading baseline MetS labels from %s", labels_path)
    labels_df = pd.read_csv(labels_path)

    # ------------------------------------------------------------------
    # Merge datasets
    # ------------------------------------------------------------------
    logger.debug("Merging expression, phenotype, and label data")
    merged_df = (
        expr_df.merge(phenotype_df, on="sample_id", how="inner")
        .merge(labels_df[["sample_id", "label"]], on="sample_id", how="inner")
    )

    if merged_df.empty:
        logger.error("Merged dataset is empty after joining inputs")
        raise ValueError("No data available for model training after merge.")

    # ------------------------------------------------------------------
    # Prepare feature matrix X and target vector y
    # ------------------------------------------------------------------
    logger.debug("Preparing feature matrix and target vector")
    try:
        X, y = prepare_model_features(merged_df, target_col="label")
    except Exception as exc:
        logger.exception("Feature preparation failed: %s", exc)
        raise

    # ------------------------------------------------------------------
    # Fit logistic regression
    # ------------------------------------------------------------------
    logger.info("Fitting LogisticRegression model (max_iter=1000, lbfgs solver)")
    model = LogisticRegression(max_iter=1000, solver="lbfgs")
    try:
        model.fit(X, y)
    except Exception as exc:
        logger.exception("Model fitting failed: %s", exc)
        raise

    # ------------------------------------------------------------------
    # Persist the trained model
    # ------------------------------------------------------------------
    model_path = processed_dir / "logistic_regression_model.pkl"
    logger.debug("Saving trained model to %s", model_path)
    try:
        dump(model, model_path)
    except Exception as exc:
        logger.exception("Failed to write model file: %s", exc)
        raise

    logger.info("Logistic regression model training complete")
    return model

__all__: list[str] = ["train_logistic_regression"]