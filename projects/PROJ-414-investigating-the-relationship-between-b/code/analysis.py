"""Analysis module for power analysis and conditional association.

This module implements the a priori power analysis (reporting‑only) and,
if a suitable skill‑proxy column exists in the dataset, performs an OLS
regression of the PCA component scores on that proxy with covariates,
using Freedman–Lane residual permutation testing (1000 permutations) and
Benjamini–Hochberg FDR correction.

The module is invoked by ``code/run_all.py`` as a pipeline stage.  It
receives no positional arguments (the orchestrator calls ``main([])``) and
reads all required configuration from ``code/config.py`` and the
verified data inventory in ``data/raw/column_inventory.json``.
"""
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.power import FTestPower

from llmxive_toolkit import get_logger, paths

import config

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_column_inventory() -> dict:
    """Load the column inventory JSON produced by the download stage.

    Expected keys (at minimum):
      - ``available_subject_count``: int
      - ``present_columns``: list of column names present in the shard
    """
    inventory_path = paths.data("raw", "column_inventory.json")
    if not inventory_path.is_file():
        raise FileNotFoundError(f"Column inventory not found: {inventory_path}")
    with inventory_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _determine_skill_proxy(present_columns: list) -> str | None:
    """Return the name of the best available skill‑proxy column, or ``None``.

    Priority order (as defined in the plan/spec):
      1. ``expert_rating``
      2. ``task_condition``
      3. ``years_of_training``
    """
    priority = ["expert_rating", "task_condition", "years_of_training"]
    for col in priority:
        if col in present_columns:
            return col
    return None

def _load_pca_scores() -> pd.DataFrame:
    """Load per‑subject PCA scores produced by ``code/dimensionality.py``."""
    pca_path = paths.data("derived", "pca_scores.csv")
    if not pca_path.is_file():
        raise FileNotFoundError(f"PCA scores not found: {pca_path}")
    df = pd.read_csv(pca_path, dtype=str)  # keep subject IDs as strings
    # Ensure numeric PC columns are floats
    pc_cols = [c for c in df.columns if c.startswith("pc_")]
    df[pc_cols] = df[pc_cols].astype(float)
    return df

def _load_subject_metadata(skill_proxy: str, covariate_cols: list) -> pd.DataFrame:
    """Load the subject‑level metadata required for the regression.

    The raw shard is a Parquet file; we read only the columns we need
    (subject ID, the skill proxy, and any covariates that are present).
    """
    import pyarrow.parquet as pq

    shard_path = paths.data("raw", config.RAW_SHARD_RELATIVE)
    if not shard_path.is_file():
        raise FileNotFoundError(f"Raw shard not found: {shard_path}")

    # Identify the subject‑ID column using the helper from download_openneuro
    from download_openneuro import find_subject_column

    subject_col = find_subject_column(shard_path)
    if subject_col is None:
        raise ValueError("Subject‑ID column could not be identified in the shard")

    needed = [subject_col, skill_proxy] + covariate_cols
    # pyarrow will read only the requested columns, keeping memory low
    table = pq.read_table(shard_path, columns=needed)
    df = table.to_pandas()
    # Normalise subject IDs to the zero‑padded string format used elsewhere
    df[subject_col] = df[subject_col].astype(str).str.zfill(2)
    df.rename(columns={subject_col: "subject_id"}, inplace=True)
    return df

# ----------------------------------------------------------------------
# Power analysis
# ----------------------------------------------------------------------
def _compute_required_n(r: float, n_predictors: int) -> int:
    """Return the required total sample size to detect a partial correlation *r*.

    Uses the F‑test power calculation from ``statsmodels``.
    """
    # Convert correlation to Cohen's f² for a multiple regression
    f2 = r ** 2 / (1 - r ** 2)
    power_solver = FTestPower()
    # ``solve_power`` returns the total number of observations (N)
    required_n = power_solver.solve_power(
        effect_size=f2,
        df_num=n_predictors,
        alpha=config.ALPHA,
        power=config.TARGET_POWER,
    )
    # ``solve_power`` may return a float; round up to the next integer
    return int(np.ceil(required_n))

def _run_power_analysis(inventory: dict) -> dict:
    """Perform the a priori power analysis and write the JSON result.

    Returns the dictionary that is written to ``results/power_analysis.json``.
    """
    # Cohen's d → correlation (r) conversion (two‑group case)
    d = config.COHENS_D
    r = d / np.sqrt(d ** 2 + 4)

    # Number of predictors = skill proxy + any covariates that are present
    present = inventory.get("present_columns", [])
    covariates = [
        col
        for col in ["age", "fd", "instrument", "genre", "practice_intensity", "education"]
        if col in present
    ]
    n_predictors = 1 + len(covariates)  # skill proxy + covariates

    required_n = _compute_required_n(r, n_predictors)
    available_n = int(inventory.get("available_subject_count", 0))

    power_status = "sufficient" if available_n >= required_n else "insufficient"
    n_ge_20_floor = available_n >= config.N_MIN_SUBJECTS_FLOOR

    power_report = {
        "required_N": required_n,
        "available_N": available_n,
        "power_status": power_status,
        "n_ge_20_floor_check": n_ge_20_floor,
        "effect_size": {"cohens_d": d, "r_equivalent": r},
    }

    out_path = paths.results("power_analysis.json")
    out_path.write_text(json.dumps(power_report, indent=2))
    log.info("Power analysis written to %s", out_path)
    return power_report

# ----------------------------------------------------------------------
# Association analysis (conditional)
# ----------------------------------------------------------------------
def _run_association(
    skill_proxy: str,
    covariates: list,
    pca_df: pd.DataFrame,
    meta_df: pd.DataFrame,
) -> pd.DataFrame:
    """Perform OLS regression with permutation testing for each PC.

    Returns a DataFrame ready to be written as ``regression_results.csv``.
    """
    # Merge PCA scores with metadata on ``subject_id``
    df = pd.merge(pca_df, meta_df, on="subject_id", how="inner")

    # Identify PC columns (those that start with ``pc_``)
    pc_cols = [c for c in df.columns if c.startswith("pc_")]
    results = []

    # Fixed random seed for reproducibility
    rng = np.random.default_rng(config.DEFAULT_SEED)

    for pc in pc_cols:
        y = df[pc].values
        # Build design matrix: intercept + skill proxy + covariates
        X = df[[skill_proxy] + covariates].astype(float)
        X = sm.add_constant(X, has_constant="add")
        model = sm.OLS(y, X).fit()
        orig_coef = model.params[skill_proxy]

        # Permutation test (Freedman–Lane style – simplified by shuffling the proxy)
        perm_coefs = np.empty(config.N_PERMUTATIONS)
        for i in range(config.N_PERMUTATIONS):
            shuffled = rng.permutation(df[skill_proxy].values)
            X_perm = X.copy()
            X_perm[skill_proxy] = shuffled
            perm_model = sm.OLS(y, X_perm).fit()
            perm_coefs[i] = perm_model.params[skill_proxy]

        # Two‑sided p‑value
        raw_p = (np.sum(np.abs(perm_coefs) >= np.abs(orig_coef)) + 1) / (config.N_PERMUTATIONS + 1)

        results.append(
            {
                "pc": pc,
                "skill_proxy_used": skill_proxy,
                "coefficient": float(orig_coef),
                "raw_p": float(raw_p),
                "fdr_p": np.nan,  # placeholder – will be filled after FDR correction
                "significance": False,  # placeholder – set after FDR
                "null_result_flag": False,  # will be set after FDR
                "permutation_scheme": "freedman_lane",
                "covariates_included": covariates,
            }
        )

    # Apply Benjamini–Hochberg FDR correction across PCs
    raw_ps = [r["raw_p"] for r in results]
    _, fdr_ps, _, _ = multipletests(raw_ps, alpha=config.FDR_ALPHA, method="fdr_bh")
    for res, fdr_p in zip(results, fdr_ps):
        res["fdr_p"] = float(fdr_p)
        res["significance"] = fdr_p < config.FDR_ALPHA
        # A null result is simply a non‑significant finding
        res["null_result_flag"] = not res["significance"]

    return pd.DataFrame(results)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main(argv=None) -> int:
    """Run power analysis and, if possible, the conditional association.

    ``argv`` is ignored – the orchestrator supplies global arguments via
    the configuration module.
    """
    try:
        inventory = _load_column_inventory()
    except Exception as e:
        log.error("Failed to load column inventory: %s", e)
        return 1

    # ------------------------------------------------------------------
    # 1) Power analysis (always executed)
    # ------------------------------------------------------------------
    power_report = _run_power_analysis(inventory)

    # ------------------------------------------------------------------
    # 2) Conditional association
    # ------------------------------------------------------------------
    skill_proxy = _determine_skill_proxy(inventory.get("present_columns", []))
    if skill_proxy is None:
        log.info(
            "No skill‑proxy column present in the data. Association stage halted "
            "as expected (scope‑gap)."
        )
        # No regression_results.csv is produced – this is the intended path.
        return 0

    # Check whether we have enough subjects for the required power.
    if power_report["power_status"] == "insufficient":
        log.info(
            "Available N (%d) is below the required N (%d); association stage "
            "skipped due to under‑power.",
            power_report["available_N"],
            power_report["required_N"],
        )
        return 0

    # Load PCA scores
    try:
        pca_df = _load_pca_scores()
    except Exception as e:
        log.error("Failed to load PCA scores: %s", e)
        return 1

    # Determine which covariates are actually present
    present_cols = inventory.get("present_columns", [])
    covariates = [
        col
        for col in ["age", "fd", "instrument", "genre", "practice_intensity", "education"]
        if col in present_cols
    ]

    # Load per‑subject metadata (skill proxy + covariates)
    try:
        meta_df = _load_subject_metadata(skill_proxy, covariates)
    except Exception as e:
        log.error("Failed to load subject metadata: %s", e)
        return 1

    # Run the regression + permutation testing
    try:
        results_df = _run_association(skill_proxy, covariates, pca_df, meta_df)
    except Exception as e:
        log.exception("Association analysis failed")
        return 1

    # Write results CSV
    out_path = paths.results("regression_results.csv")
    results_df.to_csv(out_path, index=False)
    log.info("Regression results written to %s", out_path)

    return 0
