"""Power‑analysis (and optional conditional association) for the
improvisation‑skill pipeline.

Only the power‑analysis portion is guaranteed to run because the
verified dataset does not contain any skill‑proxy columns.  The
module follows the public API declared in the project specification
(see ``code/analysis.py`` API surface).  All heavy numerical work
uses ``statsmodels`` which is already available in the runtime
environment.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.stats.power as sm_power
import statsmodels.api as sm

import config
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ------------------------------------------------------------------
# Helper functions that match the declared public API
# ------------------------------------------------------------------
def _load_column_inventory() -> dict:
    """Load the column inventory JSON produced by the download stage."""
    inv_path = paths.data("raw", "column_inventory.json")
    if not inv_path.is_file():
        raise RuntimeError(f"Column inventory missing: {inv_path}")
    return json.loads(inv_path.read_text())

def _determine_skill_proxy(present_columns: list) -> str | None:
    """Return the best available skill‑proxy column name, or ``None``."""
    for cand in ("expert_rating", "task_condition", "years_of_training"):
        if cand in present_columns:
            return cand
    return None

def _load_pca_scores() -> pd.DataFrame:
    """Load per‑subject PCA scores produced by ``dimensionality.py``."""
    pca_path = Path("data/derived/pca_scores.csv")
    if not pca_path.is_file():
        raise RuntimeError(f"PCA scores not found: {pca_path}")
    return pd.read_csv(pca_path)

def _load_subject_metadata(skill_proxy: str, covariate_cols: list) -> pd.DataFrame:
    """Load the subject‑level metadata required for the regression."""
    # The raw parquet contains many columns; we only keep those that are
    # present and needed for the model.
    inventory = _load_column_inventory()
    shard_path = paths.data("raw", config.SHARD_BASENAME)
    # Load lazily – only the columns we need.
    needed = [inventory.get("subject_column", "sub"), skill_proxy] + covariate_cols
    df = pd.read_parquet(shard_path, columns=needed)
    df = df.rename(columns={inventory.get("subject_column", "sub"): "subject_id"})
    return df

def _compute_required_n(r: float, n_predictors: int) -> int:
    """Return the required total sample size to detect a partial
    correlation *r* with 80 % power (two‑tailed α = 0.05).

    The calculation uses the F‑test formulation for a linear model:
    effect size f² = r² / (1 − r²).  ``statsmodels`` solves for the total
    number of observations needed.
    """
    f2 = r ** 2 / (1.0 - r ** 2)
    power_analysis = sm_power.FTestPower()
    # ``solve_power`` returns the required total number of observations.
    n_needed = power_analysis.solve_power(
        effect_size=f2,
        df_num=n_predictors,
        alpha=config.ALPHA,
        power=config.TARGET_POWER,
    )
    # ``solve_power`` may return a float; round up to the next integer.
    return int(np.ceil(n_needed))

def _run_power_analysis(inventory: dict) -> dict:
    """Perform the a‑priori power analysis and write the JSON result."""
    available_n = inventory.get("available_subject_count", 0)
    # Determine how many predictors will be in the regression:
    # skill proxy + all covariates that are present.
    present_cols = inventory.get("present_columns", [])
    skill_proxy = _determine_skill_proxy(present_cols)
    covariates = [
        col for col in (
            "age",
            "fd",
            "instrument",
            "genre",
            "practice_intensity",
            "education",
        )
        if col in present_cols
    ]
    n_predictors = 1 + len(covariates) if skill_proxy else len(covariates)

    # Convert the Cohen's d (0.5) to a correlation coefficient r.
    d = config.COHENS_D
    r = d / (np.sqrt(d ** 2 + 4))

    required_n = _compute_required_n(r, n_predictors)

    power_status = "sufficient" if available_n >= required_n else "insufficient"
    n_ge_20_floor_check = available_n >= config.N_MIN_SUBJECTS_FLOOR

    result = {
        "required_n": required_n,
        "available_n": available_n,
        "power_status": power_status,
        "n_ge_20_floor_check": n_ge_20_floor_check,
        "effect_size_r": r,
    }

    out_path = paths.results("power_analysis.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    log.info("Power analysis written to %s", out_path)
    return result

def _run_association(
    skill_proxy: str,
    covariates: list,
    pca_df: pd.DataFrame,
    meta_df: pd.DataFrame,
) -> pd.DataFrame:
    """Perform OLS regression with Freedman–Lane permutation testing.

    This function is only called when a real skill‑proxy column exists.
    """
    # Merge PCA scores with the metadata on ``subject_id``.
    df = pca_df.merge(meta_df, on="subject_id")
    # Build the design matrix.
    X_cols = [skill_proxy] + covariates
    X = df[X_cols]
    X = sm.add_constant(X, has_constant="add")
    y = df[[col for col in df.columns if col.startswith("pc_")]]

    # Fit the full model.
    model = sm.OLS(y, X).fit()
    # Residuals for Freedman–Lane permutations.
    resid = model.resid

    # Permutation loop.
    rng = np.random.default_rng(config.DEFAULT_SEED)
    n_perm = config.N_PERMUTATIONS
    perm_coefs = np.empty((n_perm, y.shape[1], X.shape[1]))
    for i in range(n_perm):
        # Shuffle residuals and add back the fitted values of the reduced
        # model (all covariates except the skill proxy).
        shuffled = resid.copy()
        rng.shuffle(shuffled, axis=0)
        # Re‑fit the model with shuffled residuals.
        y_perm = model.fittedvalues + shuffled
        perm_model = sm.OLS(y_perm, X).fit()
        perm_coefs[i] = perm_model.params.values

    # Compute p‑values (two‑tailed) for the skill‑proxy coefficient.
    # Index of the skill proxy in the parameter vector.
    skill_idx = list(X.columns).index(skill_proxy)
    observed = model.params.iloc[skill_idx]
    perm_dist = perm_coefs[:, :, skill_idx]
    # Two‑sided empirical p‑value.
    p_vals = (np.abs(perm_dist) >= np.abs(observed)).mean(axis=0)

    # Benjamini–Hochberg FDR correction.
    from statsmodels.stats.multitest import multipletests

    _, fdr_p, _, _ = multipletests(p_vals, alpha=config.FDR_ALPHA, method="fdr_bh")

    # Assemble results.
    results = pd.DataFrame({
        "pc": [f"pc_{i+1}" for i in range(y.shape[1])],
        "coef": observed,
        "perm_p": p_vals,
        "fdr_p": fdr_p,
    })
    out_path = paths.results("regression_results.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(out_path, index=False)
    log.info("Regression results written to %s", out_path)
    return results

def main(argv=None) -> int:
    """Entry point used by the pipeline orchestrator."""
    # ``argv`` is ignored – configuration is read from ``code/config.py``.
    inventory = _load_column_inventory()
    present_cols = inventory.get("present_columns", [])
    skill_proxy = _determine_skill_proxy(present_cols)

    # Always run the power analysis (report‑only).
    _run_power_analysis(inventory)

    # Conditional association stage.
    if skill_proxy:
        # Load PCA scores (produced by the PCA stage).
        pca_df = _load_pca_scores()
        # Load subject‑level metadata for the regression.
        covariates = [
            col for col in (
                "age",
                "fd",
                "instrument",
                "genre",
                "practice_intensity",
                "education",
            )
            if col in present_cols
        ]
        meta_df = _load_subject_metadata(skill_proxy, covariates)
        _run_association(skill_proxy, covariates, pca_df, meta_df)
    else:
        log.info(
            "No skill‑proxy column found; skipping association stage as "
            "the expected path."
        )
    return 0
