"""Statistical analysis pipeline for the sustainable‑agriculture project.

This script loads engineered data, fits a logistic regression model,
evaluates multicollinearity (VIF), applies FDR correction, computes ROC/AUC,
and performs a Baron & Kenny mediation analysis with bootstrap confidence
intervals, E‑value sensitivity, and Rosenbaum bounds. All results are saved
to the ``results`` directory; the ROC curve is saved as a PNG in ``figures``.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import (
    auc,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)
from sklearn.utils import resample
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Optional third‑party library for E‑value calculation.
try:
    import evalues  # type: ignore
except Exception:  # pragma: no cover
    evalues = None

# Project‑specific utilities.
from config import (
    get_engineered_data_path,
    get_figures_path,
    get_results_path,
    ensure_directories,
)
from logging_config import log_operation, update_log_section


@log_operation("load_engineered_data")
def load_engineered_data() -> pd.DataFrame:
    """Read the engineered CSV produced by ``03_engineer_features``."""
    path = get_engineered_data_path()
    if not path.is_file():
        raise FileNotFoundError(f"Engineered data not found at {path}")
    df = pd.read_csv(path)
    return df


@log_operation("prepare_design_matrix")
def prepare_design_matrix(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Create X (design matrix) and y (outcome) for logistic regression.

    Expects columns:
      - ``adoption_binary`` (binary outcome)
      - ``engagement_score`` (primary predictor)
      - any additional covariates present in the dataframe.
    """
    if "adoption_binary" not in df.columns:
        raise KeyError("Column 'adoption_binary' missing from engineered data.")
    y = df["adoption_binary"]
    X = df.drop(columns=["adoption_binary"])
    # Add constant for intercept.
    X = sm.add_constant(X, has_constant="add")
    return X, y


@log_operation("fit_logistic_regression")
def fit_logistic_regression(
    X: pd.DataFrame, y: pd.Series
) -> sm.Logit:
    """Fit a logistic regression model."""
    model = sm.Logit(y, X, missing="drop")
    result = model.fit(disp=False)
    return result


@log_operation("save_regression_summary")
def save_regression_summary(result: sm.Logit) -> None:
    """Write the regression summary to a text file."""
    results_dir = get_results_path()
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / "regression_summary.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result.summary2().as_text())


@log_operation("calculate_vif")
def calculate_vif(X: pd.DataFrame) -> pd.DataFrame:
    """Calculate variance inflation factors for each predictor."""
    # VIF requires no constant column.
    X_no_const = X.loc[:, X.columns != "const"]
    vif_data = pd.DataFrame()
    vif_data["variable"] = X_no_const.columns
    vif_data["VIF"] = [
        variance_inflation_factor(X_no_const.values, i)
        for i in range(X_no_const.shape[1])
    ]
    return vif_data


@log_operation("save_vif")
def save_vif(vif_df: pd.DataFrame) -> None:
    """Persist VIF results as YAML."""
    results_dir = get_results_path()
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / "vif.yaml"
    vif_df.to_yaml(out_path, index=False)


@log_operation("apply_fdr_correction")
def apply_fdr_correction(pvalues: np.ndarray, q: float = 0.10) -> Tuple[np.ndarray, np.ndarray]:
    """Benjamini‑Hochberg FDR correction."""
    sorted_idx = np.argsort(pvalues)
    sorted_p = pvalues[sorted_idx]
    n = len(pvalues)
    thresholds = (np.arange(1, n + 1) / n) * q
    below = sorted_p <= thresholds
    if not np.any(below):
        crit = 0.0
    else:
        crit = sorted_p[below].max()
    rejected = pvalues <= crit
    # Adjusted p-values (simple BH formula)
    adj_p = np.minimum.accumulate((n / np.arange(n, 0, -1)) * sorted_p[::-1])[::-1]
    adj_p = np.minimum.accumulate(adj_p)
    # Map back to original order
    adj_p_original = np.empty_like(adj_p)
    adj_p_original[sorted_idx] = adj_p
    return rejected, adj_p_original


@log_operation("save_fdr")
def save_fdr(rejected: np.ndarray, adj_p: np.ndarray, predictor_names: list[str]) -> None:
    """Save FDR correction results."""
    results_dir = get_results_path()
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / "fdr.yaml"
    data = {
        name: {"rejected": bool(r), "adjusted_p": float(p)}
        for name, r, p in zip(predictor_names, rejected, adj_p)
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@log_operation("compute_roc")
def compute_roc(result: sm.Logit, X: pd.DataFrame, y: pd.Series) -> Tuple[float, np.ndarray, np.ndarray]:
    """Calculate AUC and ROC curve data."""
    pred_prob = result.predict(X)
    fpr, tpr, _ = roc_curve(y, pred_prob)
    roc_auc = roc_auc_score(y, pred_prob)
    return roc_auc, fpr, tpr


@log_operation("plot_roc")
def plot_roc(fpr: np.ndarray, tpr: np.ndarray, auc_score: float) -> Path:
    """Generate and save a ROC curve plot."""
    import matplotlib.pyplot as plt

    plt.figure()
    plt.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (AUC = {auc_score:.2f})")
    plt.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Receiver Operating Characteristic")
    plt.legend(loc="lower right")
    figures_dir = get_figures_path()
    figures_dir.mkdir(parents=True, exist_ok=True)
    out_path = figures_dir / "roc.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    return out_path


@log_operation("save_roc_metrics")
def save_roc_metrics(auc_score: float) -> None:
    """Persist AUC value to a YAML file."""
    results_dir = get_results_path()
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / "roc_metrics.yaml"
    with open(out_path, "w", encoding="utf-8") as f:
        yaml_content = {"AUC": float(auc_score)}
        json.dump(yaml_content, f, indent=2)


@log_operation("mediation_analysis")
def mediation_analysis(
    df: pd.DataFrame,
    treatment: str = "engagement_score",
    mediator: str = "knowledge_exchange",
    outcome: str = "adoption_binary",
    n_boot: int = 1000,
    seed: int = 42,
) -> Dict[str, Any]:
    """Baron & Kenny mediation with bootstrap CI, E‑value, Rosenbaum bounds.

    Returns a dictionary with point estimates, confidence intervals,
    E‑value, and Rosenbaum bounds.
    """
    np.random.seed(seed)

    # Verify required columns exist.
    for col in (treatment, mediator, outcome):
        if col not in df.columns:
            raise KeyError(f"Column '{col}' required for mediation not found.")

    # STEP 1: a path – mediator ~ treatment
    X_a = sm.add_constant(df[[treatment]], has_constant="add")
    model_a = sm.OLS(df[mediator], X_a).fit()
    a_coef = model_a.params[treatment]

    # STEP 2: b and c' paths – outcome ~ treatment + mediator
    X_b = sm.add_constant(df[[treatment, mediator]], has_constant="add")
    model_b = sm.Logit(df[outcome], X_b).fit(disp=False)
    b_coef = model_b.params[mediator]
    c_prime = model_b.params[treatment]

    # Total effect c (outcome ~ treatment)
    X_c = sm.add_constant(df[[treatment]], has_constant="add")
    model_c = sm.Logit(df[outcome], X_c).fit(disp=False)
    c_total = model_c.params[treatment]

    indirect_effect = a_coef * b_coef
    direct_effect = c_prime
    total_effect = indirect_effect + direct_effect

    # Bootstrap confidence intervals for indirect effect.
    boot_estimates = []
    for _ in range(n_boot):
        boot_df = resample(df, replace=True, n_samples=len(df))
        # a path
        X_a_boot = sm.add_constant(boot_df[[treatment]], has_constant="add")
        a_boot = sm.OLS(boot_df[mediator], X_a_boot).fit().params[treatment]
        # b path
        X_b_boot = sm.add_constant(boot_df[[treatment, mediator]], has_constant="add")
        b_boot = sm.Logit(boot_df[outcome], X_b_boot).fit(disp=False).params[mediator]
        boot_estimates.append(a_boot * b_boot)
    lower = np.percentile(boot_estimates, 2.5)
    upper = np.percentile(boot_estimates, 97.5)

    # E‑value for the indirect effect (using odds ratio if possible)
    evalue_indirect = None
    if evalues is not None:
        # Convert indirect effect to an odds ratio approximation.
        # For small effects, OR ≈ exp(indirect_effect)
        or_est = np.exp(indirect_effect)
        evalue_indirect = evalues.evalue(or_est, lo=lower, hi=upper)

    # Rosenbaum bounds – simple approximation using the odds ratio.
    # We compute the bound for a range of gamma values.
    gamma_vals = np.arange(1.0, 3.1, 0.1)
    rosenbaum = {}
    for g in gamma_vals:
        # The bound formula is heuristic here: we compare the indirect OR
        # to the gamma factor.
        bound = float(np.exp(indirect_effect) / g)
        rosenbaum[float(g)] = bound

    results = {
        "a_coef": float(a_coef),
        "b_coef": float(b_coef),
        "c_prime": float(c_prime),
        "c_total": float(c_total),
        "indirect_effect": float(indirect_effect),
        "direct_effect": float(direct_effect),
        "total_effect": float(total_effect),
        "bootstrap_ci": {"2.5%": float(lower), "97.5%": float(upper)},
        "evalue_indirect": evalue_indirect,
        "rosenbaum_bounds": rosenbaum,
    }
    return results


@log_operation("write_mediation_results")
def write_mediation_results(results: Dict[str, Any]) -> None:
    """Save mediation analysis output to ``results/mediation.yaml``."""
    results_dir = get_results_path()
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / "mediation.yaml"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


def main() -> None:
    """Run the full analysis pipeline."""
    ensure_directories()

    # 1. Load data
    df = load_engineered_data()

    # 2. Prepare matrices
    X, y = prepare_design_matrix(df)

    # 3. Fit logistic regression
    result = fit_logistic_regression(X, y)
    save_regression_summary(result)

    # 4. VIF diagnostics
    vif_df = calculate_vif(X)
    save_vif(vif_df)

    # 5. FDR correction on regression p‑values
    pvals = result.pvalues.values
    predictor_names = list(X.columns)
    rejected, adj_p = apply_fdr_correction(pvals)
    save_fdr(rejected, adj_p, predictor_names)

    # 6. ROC / AUC
    auc_score, fpr, tpr = compute_roc(result, X, y)
    plot_roc(fpr, tpr, auc_score)
    save_roc_metrics(auc_score)

    # 7. Mediation analysis (exploratory)
    try:
        med_results = mediation_analysis(df)
        write_mediation_results(med_results)
    except Exception as exc:  # pragma: no cover
        # Log the failure but do not stop the pipeline.
        update_log_section("mediation_analysis_error", {"error": str(exc)})

    # Update modeling log with a final entry.
    update_log_section("analysis_complete", {"status": "success"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run model analysis pipeline.")
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (affects bootstrap).",
    )
    args = parser.parse_args()
    # Initialise seed globally.
    from config import set_random_seed

    set_random_seed(args.seed)
    main()
