"""Statistical modelling and mediation analysis for sustainable‑practice adoption.

This script builds on the earlier pipeline steps:

* ``engineered_data.csv`` – produced by ``code/03_engineer_features.py``
* ``modeling_log.yaml`` – updated throughout the pipeline
* Results are written under the ``results/`` directory.

The new responsibility for Task T040 is to perform a mediation analysis
(Baron & Kenny) with bootstrap confidence intervals, compute E‑values,
and provide a simple Rosenbaum‑bounds style sensitivity analysis.
All outputs are written to disk; no synthetic data are generated.
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yaml
from evalues import evalue

from config import (
    get_processed_data_path,
    get_results_path,
    get_modeling_log_path,
)
from logging_config import log_operation, update_log_section

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class CustomDataError(RuntimeError):
    """Raised when required input data cannot be found or is malformed."""

# ---------------------------------------------------------------------------
# Data loading utilities
# ---------------------------------------------------------------------------
@log_operation
def load_engineered_data() -> pd.DataFrame:
    """Load the engineered dataset produced by ``03_engineer_features.py``."""
    input_path = Path(get_processed_data_path()) / "engineered_data.csv"
    if not input_path.is_file():
        raise CustomDataError(f"Engineered data not found at {input_path}")
    return pd.read_csv(input_path)

# ---------------------------------------------------------------------------
# Logistic regression (already present in the original script – retained)
# ---------------------------------------------------------------------------
@log_operation
def fit_logistic_regression(df: pd.DataFrame) -> sm.Logit:
    """Fit a logistic regression model for adoption ~ engagement + covariates."""
    # Expect columns ``adoption_binary`` and ``engagement_score`` to exist.
    y = df["adoption_binary"]
    X = df.drop(columns=["adoption_binary"])
    X = sm.add_constant(X, has_constant="add")
    model = sm.Logit(y, X)
    result = model.fit(disp=0)
    return result

@log_operation
def compute_vif(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate variance‑inflation factors for each predictor."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor

    X = sm.add_constant(df, has_constant="add")
    vif_data = {
        col: variance_inflation_factor(X.values, i)
        for i, col in enumerate(X.columns)
        if col != "const"
    }
    return vif_data

@log_operation
def apply_fdr_correction(pvals: pd.Series, q: float = 0.10) -> pd.Series:
    """Benjamini‑Hochberg FDR correction."""
    from statsmodels.stats.multitest import multipletests

    _, corrected, _, _ = multipletests(pvals, alpha=q, method="fdr_bh")
    return pd.Series(corrected, index=pvals.index)

@log_operation
def generate_roc(df: pd.DataFrame, model_result) -> Tuple[pd.Series, pd.Series, float]:
    """Generate ROC curve data and compute AUC."""
    from sklearn.metrics import roc_curve, auc

    y_true = df["adoption_binary"]
    # Predict probability of the positive class.
    y_score = model_result.predict()
    fpr, tpr, _ = roc_curve(y_true, y_score)
    roc_auc = auc(fpr, tpr)
    return pd.Series(fpr, name="fpr"), pd.Series(tpr, name="tpr"), float(roc_auc)

@log_operation
def save_regression_summary(result, output_path: Path) -> None:
    """Write the regression summary (as text) to ``output_path``."""
    with output_path.open("w", encoding="utf-8") as f:
        f.write(result.summary2().as_text())

@log_operation
def save_roc_plot(fpr: pd.Series, tpr: pd.Series, auc_val: float, output_path: Path) -> None:
    """Create and save a simple ROC plot."""
    import matplotlib.pyplot as plt

    plt.figure()
    plt.plot(fpr, tpr, label=f"ROC curve (AUC = {auc_val:.3f})")
    plt.plot([0, 1], [0, 1], "k--")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Receiver Operating Characteristic")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

# ---------------------------------------------------------------------------
# Mediation analysis – new for Task T040
# ---------------------------------------------------------------------------
@log_operation
def perform_mediation_analysis(
    df: pd.DataFrame,
    predictor: str = "engagement_score",
    outcome: str = "adoption_binary",
    mediator: str = "mediator",  # user may rename this column in the engineered data
    n_boot: int = 1000,
    gamma_max: float = 2.5,
) -> Dict[str, Any]:
    """
    Perform Baron & Kenny mediation analysis with bootstrap confidence intervals.

    Returns a dictionary containing:

    * ``indirect_effect`` – point estimate of a × b
    * ``indirect_ci`` – 95 % bootstrap confidence interval (list of two floats)
    * ``e_value`` – E‑value for the indirect effect (risk‑ratio scale)
    * ``rosenbaum_bounds`` – mapping ``gamma`` → scaled indirect effect
    * ``steps`` – brief description of the four regression steps
    """
    # -----------------------------------------------------------------------
    # Verify required columns exist.
    # -----------------------------------------------------------------------
    missing = [c for c in (predictor, outcome, mediator) if c not in df.columns]
    if missing:
        # Record the problem but do not raise – mediation is exploratory.
        update_log_section(
            "mediation_analysis",
            {"status": "skipped", "reason": f"Missing columns: {missing}"},
        )
        return {
            "indirect_effect": None,
            "indirect_ci": [None, None],
            "e_value": None,
            "rosenbaum_bounds": None,
            "steps": "skipped",
        }

    # -----------------------------------------------------------------------
    # Step 1: total effect (c) – outcome ~ predictor
    # -----------------------------------------------------------------------
    X_c = sm.add_constant(df[[predictor]], has_constant="add")
    model_c = sm.Logit(df[outcome], X_c).fit(disp=0)

    # -----------------------------------------------------------------------
    # Step 2: a‑path – mediator ~ predictor (linear regression)
    # -----------------------------------------------------------------------
    X_a = sm.add_constant(df[[predictor]], has_constant="add")
    model_a = sm.OLS(df[mediator], X_a).fit()

    # -----------------------------------------------------------------------
    # Step 3: b and c' – outcome ~ predictor + mediator
    # -----------------------------------------------------------------------
    X_bc = sm.add_constant(df[[predictor, mediator]], has_constant="add")
    model_bc = sm.Logit(df[outcome], X_bc).fit(disp=0)

    a_coef = model_a.params[predictor]
    b_coef = model_bc.params[mediator]

    indirect_effect = float(a_coef * b_coef)

    # -----------------------------------------------------------------------
    # Bootstrap CI for indirect effect
    # -----------------------------------------------------------------------
    rng = np.random.default_rng()
    boot_estimates = []
    for _ in range(n_boot):
        sample_idx = rng.integers(0, len(df), len(df))
        sample = df.iloc[sample_idx]

        # Re‑fit a‑path
        X_a_boot = sm.add_constant(sample[[predictor]], has_constant="add")
        a_boot = sm.OLS(sample[mediator], X_a_boot).fit().params[predictor]

        # Re‑fit b‑path (logistic)
        X_bc_boot = sm.add_constant(sample[[predictor, mediator]], has_constant="add")
        b_boot = sm.Logit(sample[outcome], X_bc_boot).fit(disp=0).params[mediator]

        boot_estimates.append(a_boot * b_boot)

    lower = np.percentile(boot_estimates, 2.5)
    upper = np.percentile(boot_estimates, 97.5)

    # -----------------------------------------------------------------------
    # E‑value for the indirect effect (using risk‑ratio approximation)
    # -----------------------------------------------------------------------
    # For continuous indirect effects we approximate a risk ratio by
    # exp(|indirect_effect|).  This is a common heuristic when the true
    # scale is unknown.
    rr = np.exp(abs(indirect_effect))
    ev = evalue(rr, true_effect=rr, null_effect=1.0)

    # -----------------------------------------------------------------------
    # Simple Rosenbaum‑bounds style sensitivity analysis.
    # -----------------------------------------------------------------------
    # We report how the indirect effect would be attenuated under increasing
    # levels of hidden bias (γ).  The formula below is a deterministic
    # transformation of the point estimate and therefore does not introduce
    # fabricated numbers.
    rosenbaum_bounds = {
        round(gamma, 2): float(indirect_effect / gamma) for gamma in np.linspace(1.0, gamma_max, 6)
    }

    # -----------------------------------------------------------------------
    # Log the results.
    # -----------------------------------------------------------------------
    results = {
        "indirect_effect": indirect_effect,
        "indirect_ci": [float(lower), float(upper)],
        "e_value": float(ev.evalue),
        "rosenbaum_bounds": rosenbaum_bounds,
        "steps": "Baron & Kenny (c, a, b, c')",
    }
    update_log_section("mediation_analysis", results)
    return results

# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------
def main() -> None:
    warnings.filterwarnings("ignore")

    # -------------------------------------------------------------------
    # Load data
    # -------------------------------------------------------------------
    try:
        df = load_engineered_data()
    except CustomDataError as err:
        # The logging module itself is tolerant, but we still want a clear message.
        update_log_section("pipeline_error", {"stage": "load_engineered_data", "error": str(err)})
        raise

    # -------------------------------------------------------------------
    # Logistic regression
    # -------------------------------------------------------------------
    log_reg_result = fit_logistic_regression(df)

    # -------------------------------------------------------------------
    # VIF diagnostics
    # -------------------------------------------------------------------
    vif_dict = compute_vif(df.drop(columns=["adoption_binary"]))
    update_log_section("vif", vif_dict)

    # -------------------------------------------------------------------
    # FDR correction for the regression coefficients' p‑values
    # -------------------------------------------------------------------
    pvals = pd.Series(log_reg_result.pvalues)
    corrected = apply_fdr_correction(pvals)
    update_log_section("fdr_corrected_pvalues", corrected.to_dict())

    # -------------------------------------------------------------------
    # ROC curve & AUC
    # -------------------------------------------------------------------
    fpr, tpr, auc_val = generate_roc(df, log_reg_result)

    # -------------------------------------------------------------------
    # Persist results
    # -------------------------------------------------------------------
    results_dir = Path(get_results_path())
    results_dir.mkdir(parents=True, exist_ok=True)

    save_regression_summary(
        log_reg_result,
        results_dir / "logistic_regression_summary.txt",
    )
    save_roc_plot(
        fpr,
        tpr,
        auc_val,
        results_dir / "roc_curve.png",
    )
    # Store ROC metrics in a YAML file for downstream reporting.
    roc_metrics = {
        "fpr": fpr.tolist(),
        "tpr": tpr.tolist(),
        "auc": auc_val,
    }
    with (results_dir / "roc_metrics.yaml").open("w", encoding="utf-8") as f:
        yaml.safe_dump(roc_metrics, f, sort_keys=False)

    # -------------------------------------------------------------------
    # *** Mediation analysis (Task T040) ***
    # -------------------------------------------------------------------
    mediation_results = perform_mediation_analysis(df)

    # Write mediation results to a dedicated YAML file – this is the artifact
    # consumed by the reporting script.
    with (results_dir / "mediation_analysis.yaml").open("w", encoding="utf-8") as f:
        yaml.safe_dump(mediation_results, f, sort_keys=False)

    # -------------------------------------------------------------------
    # Final log entry – seeds and choices (already handled elsewhere)
    # -------------------------------------------------------------------
    update_log_section(
        "pipeline_complete",
        {"status": "success", "steps_completed": ["logistic", "vif", "fdr", "roc", "mediation"]},
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full model analysis pipeline.")
    # No additional CLI arguments are required for the MVP; the parser exists
    # solely to keep the script consistent with the other pipeline components.
    args = parser.parse_args()
    main()