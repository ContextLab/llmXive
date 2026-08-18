"""
odds_extractor.py
-----------------
Implements the extraction of odds ratios, standard errors, and p‑values for the
logistic regression model used in the GTEx metabolic syndrome analysis.

The function reads the processed expression matrix, filtered phenotype data,
and baseline classification labels, builds a design matrix that includes
core circadian gene expression and covariates, fits a logistic regression
using ``statsmodels`` (to obtain standard errors and p‑values), and writes the
results to ``data/processed/odds_ratios_main.csv``.
"""

import logging
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
import statsmodels.api as sm

from utils.config import get_project_paths

logger = logging.getLogger(__name__)

def _load_data() -> pd.DataFrame:
    """
    Load and merge the required data sources:

    * ``core_genes_log2_matrix.csv`` – log2‑transformed TPM values for core circadian genes.
    * ``filtered_phenotype.csv`` – phenotype information (age, sex, tissue, PMI, time_of_death, …).
    * ``baseline_labels.csv`` – binary MetS / Control labels.

    Returns
    -------
    pd.DataFrame
        A DataFrame where each row corresponds to a donor and contains:
        - gene expression columns (one per core gene)
        - covariate columns (age, sex, tissue, PMI, time_of_death)
        - a ``label`` column (1 for MetS, 0 for Control)
    """
    paths = get_project_paths()
    # Resolve concrete file locations
    expr_path = Path(paths["processed"]) / "core_genes_log2_matrix.csv"
    phen_path = Path(paths["processed"]) / "filtered_phenotype.csv"
    label_path = Path(paths["processed"]) / "baseline_labels.csv"

    logger.info("Loading expression matrix from %s", expr_path)
    expr_df = pd.read_csv(expr_path)

    logger.info("Loading phenotype data from %s", phen_path)
    phen_df = pd.read_csv(phen_path)

    logger.info("Loading baseline labels from %s", label_path)
    label_df = pd.read_csv(label_path)

    # Assume a common identifier column named ``sample_id`` across all files.
    # If the real dataset uses a different name, this will raise a clear error.
    merge_keys = ["sample_id"]
    for key in merge_keys:
        if key not in expr_df.columns:
            raise KeyError(f"Expression matrix missing required column '{key}'")
        if key not in phen_df.columns:
            raise KeyError(f"Phenotype file missing required column '{key}'")
        if key not in label_df.columns:
            raise KeyError(f"Label file missing required column '{key}'")

    merged = expr_df.merge(phen_df, on=merge_keys, how="inner")
    merged = merged.merge(label_df, on=merge_keys, how="inner")

    # Convert textual labels to binary (MetS -> 1, Control -> 0)
    if "label" not in merged.columns:
        raise KeyError("Merged data missing 'label' column")
    merged["label"] = merged["label"].map({"MetS": 1, "Control": 0})
    if merged["label"].isnull().any():
        raise ValueError("Label column contains values other than 'MetS' or 'Control'")

    logger.info("Merged dataset contains %d samples and %d columns", merged.shape[0], merged.shape[1])
    return merged

def _prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the design matrix for logistic regression.

    Steps
    -----
    1. Identify gene expression columns (those that match the core circadian gene list
       defined in ``code/data/config.py``). All other columns are treated as covariates.
    2. One‑hot encode categorical covariates (e.g., ``sex`` and ``tissue``).
    3. Impute missing ``time_of_death`` using the ``PMI`` value as a proxy, as required by
       FR‑005. This mirrors the behaviour of ``impute_missing_time_of_death`` in
       ``analysis.modeling``.
    """
    # ----------------------------------------------------------------------
    # 1. Determine gene columns
    # ----------------------------------------------------------------------
    from data.config import CORE_CIRCADIAN_GENES  # constant defined in T012

    gene_cols = [col for col in df.columns if col.upper() in [g.upper() for g in CORE_CIRCADIAN_GENES]]
    if not gene_cols:
        raise ValueError("No core circadian gene columns found in the merged dataset")

    # ----------------------------------------------------------------------
    # 2. Select covariates
    # ----------------------------------------------------------------------
    covariate_cols = [
        "age",
        "sex",
        "tissue",
        "PMI",
        "time_of_death",
    ]

    missing_covs = [c for c in covariate_cols if c not in df.columns]
    if missing_covs:
        raise KeyError(f"Missing required covariate columns: {missing_covs}")

    # Impute missing time_of_death with PMI where needed
    df["time_of_death"] = df["time_of_death"].fillna(df["PMI"])

    # One‑hot encode categorical variables (sex, tissue)
    df_enc = pd.get_dummies(df[covariate_cols], drop_first=True)

    # Combine gene expression and covariate matrices
    X = pd.concat([df[gene_cols], df_enc], axis=1)

    logger.debug("Feature matrix shape after encoding: %s", X.shape)
    return X

def extract_odds_ratios() -> None:
    """
    Compute odds ratios (OR), standard errors (SE), and p‑values for each predictor
    in the logistic regression model that predicts MetS status.

    The results are written to ``data/processed/odds_ratios_main.csv`` with the
    following columns:

    * ``predictor`` – name of the gene or covariate
    * ``odds_ratio`` – exp(beta)
    * ``std_error`` – standard error of the beta estimate
    * ``p_value`` – two‑sided Wald test p‑value
    """
    logger.info("Starting odds‑ratio extraction")
    merged = _load_data()
    X = _prepare_features(merged)
    y = merged["label"].astype(int)

    # Add intercept term for statsmodels
    X_const = sm.add_constant(X, has_constant="add")

    logger.info("Fitting logistic regression with %d predictors", X_const.shape[1] - 1)
    logit_model = sm.Logit(y, X_const)
    result = logit_model.fit(disp=False)

    # Extract statistics
    params = result.params
    std_err = result.bse
    p_vals = result.pvalues

    # Convert to odds ratios
    odds_ratios = np.exp(params)

    # Build output DataFrame (exclude the intercept)
    output = pd.DataFrame({
        "predictor": params.index,
        "odds_ratio": odds_ratios,
        "std_error": std_err,
        "p_value": p_vals,
    })
    output = output[output["predictor"] != "const"]  # drop intercept row

    # Resolve output path
    paths = get_project_paths()
    out_path = Path(paths["processed"]) / "odds_ratios_main.csv"
    output.to_csv(out_path, index=False)
    logger.info("Odds‑ratio table written to %s (%d rows)", out_path, output.shape[0])
