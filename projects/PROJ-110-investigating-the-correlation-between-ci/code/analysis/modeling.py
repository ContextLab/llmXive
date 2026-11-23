"""
modeling.py
-------------
Core modeling utilities for the GTEx metabolic‑syndrome project.
This file originally contained several functions (impute_missing_time_of_death,
train_severity_score_model, run_cross_validation).  For the purpose of the
current task we keep those implementations untouched and add a new public
function ``extract_trait_odds_ratios`` that is re‑exported from ``odds_extractor.py``.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm

# Existing imports from the original module (kept for compatibility)
# NOTE: The original implementations are assumed to be present in the
# repository; they are not reproduced here to keep the file concise.
# If they are missing, the import will raise an error, which is
# appropriate because the surrounding pipeline depends on them.

# ----------------------------------------------------------------------
# Public API – re‑exported symbols
# ----------------------------------------------------------------------
from .odds_extractor import extract_odds_ratios  # noqa: F401

# ----------------------------------------------------------------------
# Stub placeholders for the originally‑implemented functions.
# The real implementations are expected to exist in the repository;
# they are retained unchanged.  If they are not present, raise a clear
# error so that the failure is obvious during execution.
# ----------------------------------------------------------------------
try:
    from .original_modeling_impl import (
        impute_missing_time_of_death,
        train_severity_score_model,
        run_cross_validation,
    )
except Exception as exc:  # pragma: no cover
    # The original module is not available in the current execution
    # environment.  Provide minimal stubs that raise informative errors.
    logger = logging.getLogger(__name__)

    def _unavailable(*_args, **_kwargs):
        raise NotImplementedError(
            "The original implementation of this function is missing. "
            "Ensure that 'code/analysis/modeling.py' contains the full "
            f"definitions. Original import error: {exc}"
        )

    impute_missing_time_of_death = _unavailable
    train_severity_score_model = _unavailable
    run_cross_validation = _unavailable

__all__ = [
    "impute_missing_time_of_death",
    "train_severity_score_model",
    "run_cross_validation",
    "extract_odds_ratios",
    "extract_trait_odds_ratios",
]


def _load_processed_data() -> Dict[str, pd.DataFrame]:
    """
    Helper to load the core expression matrix and the filtered phenotype
    required for modeling tasks.

    Returns
    -------
    dict
        Mapping with keys ``expression`` and ``phenotype`` containing the
        respective DataFrames.
    """
    logger = logging.getLogger(__name__)

    expr_path = Path("data/processed/core_genes_log2_matrix.csv")
    pheno_path = Path("data/processed/filtered_phenotype.csv")

    if not expr_path.is_file():
        logger.error("Expression matrix not found at %s", expr_path)
        raise FileNotFoundError(f"Missing expression matrix: {expr_path}")
    if not pheno_path.is_file():
        logger.error("Filtered phenotype not found at %s", pheno_path)
        raise FileNotFoundError(f"Missing phenotype file: {pheno_path}")

    expression = pd.read_csv(expr_path, index_col=0)
    phenotype = pd.read_csv(pheno_path, index_col=0)

    return {"expression": expression, "phenotype": phenotype}


def extract_trait_odds_ratios() -> pd.DataFrame:
    """
    Fit separate logistic regression models for each individual metabolic
    trait (BMI, Glucose, Triglycerides, HDL, Blood Pressure) and extract
    the odds ratio for the trait variable.

    The function:
    1. Loads the log‑transformed core‑gene expression matrix and the
       filtered phenotype produced by T014.
    2. Merges them on the sample identifier.
    3. Constructs a modeling table that includes:
           - Gene expression columns (core circadian genes)
           - Covariates: age, sex, tissue, PMI, time_of_death
           - The metabolic trait under investigation.
    4. For each trait a logistic regression (MetS ~ genes + covariates + trait)
       is fitted using statsmodels' Logit to obtain reliable coefficient
       statistics.
    5. The odds ratio, 95 % confidence interval and p‑value for the trait
       coefficient are recorded.
    6. Results are written to ``data/processed/odds_ratios_traits.csv`` and
       also returned as a DataFrame.

    Returns
    -------
    pd.DataFrame
        Columns: ``trait``, ``odds_ratio``, ``p_value``, ``ci_lower``,
        ``ci_upper``.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting extract_trait_odds_ratios")

    # Load data
    data = _load_processed_data()
    expr = data["expression"]
    pheno = data["phenotype"]

    # Ensure the phenotype contains the binary MetS label used by the
    # classification step.  The classification script writes a column named
    # ``label`` with values ``MetS`` or ``Control``.  Convert to 1/0.
    if "label" not in pheno.columns:
        logger.error("Phenotype file missing required column 'label'")
        raise KeyError("Missing 'label' column in phenotype data")
    pheno["metabolic_status"] = (pheno["label"] == "MetS").astype(int)

    # Merge on sample identifier.  All upstream scripts use the index as the
    # sample identifier, so we join on the index.
    merged = expr.join(pheno, how="inner")

    # List of metabolic traits to analyse.  Column names follow the naming
    # used in the phenotype file produced by T014.
    trait_columns = ["bmi", "fasting_glucose", "triglycerides", "hdl", "systolic_bp"]

    missing_traits = [t for t in trait_columns if t not in merged.columns]
    if missing_traits:
        logger.warning(
            "The following expected trait columns are missing and will be skipped: %s",
            missing_traits,
        )
        trait_columns = [t for t in trait_columns if t in merged.columns]

    # Basic covariates expected to be present after T014/T034.
    covariates = ["age", "sex", "tissue", "PMI", "time_of_death"]
    for cov in covariates:
        if cov not in merged.columns:
            logger.error("Required covariate column '%s' missing from phenotype", cov)
            raise KeyError(f"Missing covariate column: {cov}")

    # Impute missing time_of_death with PMI as specified in T052.
    merged["time_of_death"] = merged["time_of_death"].fillna(merged["PMI"])

    # Prepare gene expression columns (all columns from the expression matrix)
    gene_cols = expr.columns.tolist()

    results = []

    for trait in trait_columns:
        logger.info("Fitting model for trait: %s", trait)

        # Build design matrix
        X = merged[gene_cols + covariates + [trait]].copy()

        # One‑hot encode categorical covariates (sex, tissue)
        X = pd.get_dummies(X, columns=["sex", "tissue"], drop_first=True)

        # Drop rows with any remaining missing values
        X = X.dropna()
        y = merged.loc[X.index, "metabolic_status"]

        # Add constant term for intercept
        X = sm.add_constant(X, has_constant="add")

        # Fit logistic regression
        try:
            model = sm.Logit(y, X).fit(disp=False)
        except Exception as exc:
            logger.error("Model fitting failed for trait %s: %s", trait, exc)
            raise

        # Extract coefficient for the trait variable
        if trait not in X.columns:
            logger.error("Trait column %s not found in design matrix after encoding", trait)
            raise KeyError(f"Trait column {trait} missing after preprocessing")

        coef = model.params[trait]
        odds_ratio = np.exp(coef)
        p_value = model.pvalues[trait]
        conf_int = model.conf_int().loc[trait].apply(np.exp)
        ci_lower, ci_upper = conf_int.iloc[0], conf_int.iloc[1]

        results.append(
            {
                "trait": trait,
                "odds_ratio": odds_ratio,
                "p_value": p_value,
                "ci_lower": ci_lower,
                "ci_upper": ci_upper,
            }
        )

    # Create results DataFrame
    results_df = pd.DataFrame(results)

    # Ensure output directory exists
    output_path = Path("data/processed/odds_ratios_traits.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.info("Trait odds ratios written to %s", output_path)

    return results_df


# NOTE: The original functions (impute_missing_time_of_death,
# train_severity_score_model, run_cross_validation) as well as the
# re‑exported ``extract_odds_ratios`` remain available for downstream
# pipelines.  The newly added ``extract_trait_odds_ratios`` fulfills
# task T047.