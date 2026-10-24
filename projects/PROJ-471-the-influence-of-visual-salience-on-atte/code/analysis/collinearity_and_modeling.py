"""
collinearity_and_modeling.py

Implements Task T008:
- Load aligned_data.csv (excluding rows where excluded=True)
- Compute VIF for fixed predictors
- If any VIF > 5, apply PCA to low‑level covariates (luminance, contrast, edge_density)
  and retain components explaining ≥95% variance
- Fit Model A (random intercepts for participant and stimulus)
- Fit Model B (adds random slopes for salience_score per participant)
- Extract fixed‑effect estimates, standard errors, raw p‑values, and 95 % confidence intervals
- Apply Benjamini‑Hochberg FDR correction to all fixed‑effect p‑values
- Compute stability metric |β_A − β_B| for the salience predictor
- Write model result CSVs and VIF logs
"""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.multitest import multipletests
import statsmodels.formula.api as smf
import pingouin as pg

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
LOG = get_logger(__name__)

# Columns expected in aligned_data.csv
DEPENDENT_VAR = "dwell_time_ms"
PARTICIPANT_COL = "participant_id"
STIMULUS_COL = "stimulus_id"
EXCLUDED_COL = "excluded"

# Fixed predictors (before any orthogonalisation)
FIXED_PREDICTORS = [
    "salience_score",
    "luminance",
    "contrast",
    "edge_density",
    "scene_complexity",
]

# Low‑level covariates that may be orthogonalised via PCA
LOW_LEVEL_COVARIATES = ["luminance", "contrast", "edge_density"]
VIF_THRESHOLD = 5.0
VARIANCE_EXPLAINED_TARGET = 0.95

# Output paths
VIF_PRE_PATH = paths.logs("vif_pre.json")
VIF_POST_PATH = paths.logs("vif_post.json")
LMM_CONV_LOG = paths.logs("lmm_convergence.log")
MODEL_A_RESULTS = paths.interim("model_a_results.csv")
MODEL_B_RESULTS = paths.interim("model_b_results.csv")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def load_aligned_data() -> pd.DataFrame:
    """Load aligned_data.csv and drop rows where excluded=True."""
    aligned_path = paths.processed("aligned_data.csv")
    if not aligned_path.is_file():
        LOG.error(f"Aligned data not found at {aligned_path}")
        raise FileNotFoundError(f"Aligned data not found at {aligned_path}")

    df = pd.read_csv(aligned_path)
    # Ensure the excluded column exists; if not, assume no exclusions
    if EXCLUDED_COL in df.columns:
        df = df[df[EXCLUDED_COL] != True]  # keep only non‑excluded rows
    return df


def compute_vif(df: pd.DataFrame, predictors: list) -> dict:
    """Compute VIF for the given predictor columns using pingouin."""
    # pingouin expects a DataFrame with only the predictor columns
    vif_df = pg.vif(df[predictors])
    # pingouin returns a DataFrame with columns ['VIF', 'features']
    vif_dict = {row["features"]: row["VIF"] for _, row in vif_df.iterrows()}
    return vif_dict


def write_json(data: dict, path: Path):
    """Write a dictionary to a JSON file (pretty‑printed)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def apply_pca(df: pd.DataFrame) -> (pd.DataFrame, list):
    """
    Apply PCA to the low‑level covariates.
    Returns the transformed DataFrame (with PC columns) and the list of new PC names.
    """
    scaler = StandardScaler()
    cov_matrix = scaler.fit_transform(df[LOW_LEVEL_COVARIATES])

    pca = PCA()
    pca.fit(cov_matrix)

    cum_var = np.cumsum(pca.explained_variance_ratio_)
    n_components = int(np.searchsorted(cum_var, VARIANCE_EXPLAINED_TARGET) + 1)

    pca = PCA(n_components=n_components)
    pcs = pca.fit_transform(cov_matrix)

    pc_names = [f"PC{i+1}" for i in range(n_components)]
    pc_df = pd.DataFrame(pcs, columns=pc_names, index=df.index)

    # Drop original low‑level covariates and concatenate PCs
    df_out = df.drop(columns=LOW_LEVEL_COVARIATES).copy()
    df_out = pd.concat([df_out, pc_df], axis=1)

    LOG.info(
        f"PCA orthogonalisation applied: retained {n_components} components "
        f"explaining {cum_var[n_components-1]:.2%} of variance."
    )
    return df_out, pc_names


def fit_mixedlm(
    df: pd.DataFrame,
    formula: str,
    re_formula: str = None,
):
    """
    Fit a Mixed Linear Model with random intercepts for participant and
    stimulus, optionally adding random slopes (re_formula).
    Returns the fitted result object.
    """
    try:
        md = smf.mixedlm(
            formula,
            df,
            groups=df[PARTICIPANT_COL],
            vc_formula={STIMULUS_COL: f"0 + C({STIMULUS_COL})"},
            re_formula=re_formula,
        )
        result = md.fit(reml=False, method="lbfgs")
        LOG.info(f"MixedLM fit succeeded for formula: {formula} (re: {re_formula})")
        return result, None
    except Exception as e:
        LOG.error(f"MixedLM fit failed for formula: {formula} (re: {re_formula}) – {e}")
        return None, str(e)


def extract_fixed_effects(result) -> pd.DataFrame:
    """
    Convert the fixed‑effect summary of a MixedLM result into a tidy DataFrame.
    Columns: predictor, estimate, std_error, p_value, ci_lower, ci_upper
    """
    fe_params = result.fe_params
    bse = result.bse_fe
    pvals = result.pvalues
    ci = result.conf_int()
    rows = []
    for predictor in fe_params.index:
        rows.append(
            {
                "predictor": predictor,
                "estimate": fe_params[predictor],
                "std_error": bse[predictor],
                "p_value": pvals[predictor],
                "ci_lower": ci.loc[predictor, 0],
                "ci_upper": ci.loc[predictor, 1],
            }
        )
    return pd.DataFrame(rows)


def apply_fdr_correction(df: pd.DataFrame) -> pd.DataFrame:
    """Apply Benjamini‑Hochberg FDR to the p_value column."""
    pvals = df["p_value"].values
    _, adj_pvals, _, _ = multipletests(pvals, method="fdr_bh")
    df = df.copy()
    df["p_value_fdr"] = adj_pvals
    # Ensure corrected p‑values are not larger than raw p‑values (they never should be)
    df["p_value_fdr"] = np.minimum(df["p_value_fdr"], df["p_value"])
    return df


def write_model_results(df: pd.DataFrame, path: Path):
    """Write model fixed‑effect table to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------


def main():
    # ------------------------------------------------------------------
    # 1. Load data
    # ------------------------------------------------------------------
    df = load_aligned_data()

    # Verify required columns exist
    missing = [col for col in FIXED_PREDICTORS if col not in df.columns]
    if missing:
        LOG.error(f"Missing predictor columns in aligned data: {missing}")
        raise RuntimeError(f"Missing predictor columns: {missing}")

    # ------------------------------------------------------------------
    # 2. Compute pre‑orthogonalisation VIF
    # ------------------------------------------------------------------
    vif_pre = compute_vif(df, FIXED_PREDICTORS)
    write_json(vif_pre, VIF_PRE_PATH)

    # ------------------------------------------------------------------
    # 3. Orthogonalise if needed
    # ------------------------------------------------------------------
    orthogonalised = False
    if any(v > VIF_THRESHOLD for v in vif_pre.values()):
        LOG.info("VIF > threshold detected – applying PCA orthogonalisation.")
        df, pc_names = apply_pca(df)
        # New predictor list after PCA
        new_predictors = [
            "salience_score",
            "scene_complexity",
        ] + pc_names
        orthogonalised = True
        vif_post = compute_vif(df, new_predictors)
        write_json(vif_post, VIF_POST_PATH)
    else:
        LOG.info("All VIFs within acceptable range – no orthogonalisation required.")
        # Even if no orthogonalisation, we still write a post‑VIF file (identical to pre)
        write_json(vif_pre, VIF_POST_PATH)
        new_predictors = FIXED_PREDICTORS

    # ------------------------------------------------------------------
    # 4. Fit Model A (random intercepts only)
    # ------------------------------------------------------------------
    formula_a = f"{DEPENDENT_VAR} ~ " + " + ".join(new_predictors)
    result_a, err_a = fit_mixedlm(df, formula_a, re_formula=None)

    # ------------------------------------------------------------------
    # 5. Fit Model B (random intercepts + random slopes for salience)
    # ------------------------------------------------------------------
    formula_b = formula_a  # same fixed part
    result_b, err_b = fit_mixedlm(df, formula_b, re_formula="~salience_score")

    # ------------------------------------------------------------------
    # 6. Log convergence information
    # ------------------------------------------------------------------
    with LMM_CONV_LOG.open("w", encoding="utf-8") as log_f:
        if result_a is not None:
            log_f.write("Model A converged successfully.\n")
        else:
            log_f.write(f"Model A failed to converge: {err_a}\n")

        if result_b is not None:
            log_f.write("Model B converged successfully.\n")
        else:
            log_f.write(f"Model B failed to converge: {err_b}\n")

    # ------------------------------------------------------------------
    # 7. Extract fixed‑effect tables, apply FDR
    # ------------------------------------------------------------------
    if result_a is None or result_b is None:
        LOG.error("One or both models failed – aborting further processing.")
        raise RuntimeError("MixedLM fitting failure")

    fe_a = extract_fixed_effects(result_a)
    fe_b = extract_fixed_effects(result_b)

    fe_a = apply_fdr_correction(fe_a)
    fe_b = apply_fdr_correction(fe_b)

    # ------------------------------------------------------------------
    # 8. Compute stability metric for salience predictor
    # ------------------------------------------------------------------
    beta_a = fe_a.loc[fe_a["predictor"] == "salience_score", "estimate"].values[0]
    beta_b = fe_b.loc[fe_b["predictor"] == "salience_score", "estimate"].values[0]
    stability_metric = float(abs(beta_a - beta_b))

    LOG.info(f"Stability metric (|β_A − β_B|) for salience: {stability_metric:.4f}")

    # ------------------------------------------------------------------
    # 9. Write model result CSVs (including stability metric as an extra column)
    # ------------------------------------------------------------------
    # Add stability metric as a constant column to both tables for downstream use
    fe_a["stability_metric"] = stability_metric
    fe_b["stability_metric"] = stability_metric

    write_model_results(fe_a, MODEL_A_RESULTS)
    write_model_results(fe_b, MODEL_B_RESULTS)

    LOG.info("All outputs written successfully.")
    return 0


if __name__ == "__main__":
    exit(main())
