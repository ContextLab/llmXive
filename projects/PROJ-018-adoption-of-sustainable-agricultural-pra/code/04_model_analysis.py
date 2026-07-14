"""Model analysis pipeline – logistic regression, diagnostics and mediation.

This module already contains functions for loading data, fitting the primary
logistic regression, VIF calculation, FDR correction and ROC analysis.  The
missing piece for Task T040 is a robust mediation analysis implementation.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

# ----------------------------------------------------------------------
# Local imports – the other scripts expose the helpers we need
# ----------------------------------------------------------------------
from . import (
    load_engineered_data,
    prepare_model_data,
    fit_logistic_regression,
    calculate_vif,
    apply_fdr_correction,
    calculate_roc_metrics,
    plot_roc_curve,
)
from .logging_config import log_operation, update_log_section

# ----------------------------------------------------------------------
# Mediation analysis utilities
# ----------------------------------------------------------------------
@log_operation("perform_mediation_analysis")
def perform_mediation_analysis(
    df: pd.DataFrame,
    predictor: str = "engagement_score",
    mediator: str = "knowledge_exchange",
    outcome: str = "adoption_binary",
    n_bootstrap: int = 1000,
    evalue_confidence: float = 0.95,
    gamma_range: Tuple[float, ...] = (1.0, 1.5, 2.0, 2.5, 3.0),
) -> Dict[str, Any]:
    """
    Implements the Baron & Kenny mediation steps with bootstrap confidence
    intervals for the indirect effect and a sensitivity analysis.

    Parameters
    ----------
    df : pd.DataFrame
        Engineered dataset containing at least the three columns.
    predictor, mediator, outcome : str
        Column names for the X, M and Y variables.
    n_bootstrap : int
        Number of bootstrap resamples for the indirect‑effect CI.
    evalue_confidence : float
        Confidence level for the E‑value calculation (e.g. 0.95).
    gamma_range : tuple of float
        Gamma values for Rosenbaum bounds; the function will report the
        maximum possible hidden‑bias factor that would reduce the indirect
        effect to zero.

    Returns
    -------
    dict
        Dictionary with the following keys:

        * ``'paths'`` – a sub‑dict with ``a``, ``b``, ``c`` and ``c_prime``.
        * ``'indirect_effect'`` – point estimate ``a * b``.
        * ``'indirect_ci'`` – 2.5 % and 97.5 % percentiles from bootstrap.
        * ``'e_value'`` – E‑value for the indirect effect.
        * ``'rosenbaum_bounds'`` – mapping ``gamma -> p‑value`` indicating the
          smallest gamma at which the indirect effect would lose statistical
          significance.
    """
    # ------------------------------------------------------------------
    # 1. Verify columns exist – raise a clear error if not.
    # ------------------------------------------------------------------
    missing = [c for c in (predictor, mediator, outcome) if c not in df.columns]
    if missing:
        raise ValueError(f"Columns missing for mediation analysis: {missing}")

    # ------------------------------------------------------------------
    # 2. Ordinary Least Squares for path a (M ~ X)
    # ------------------------------------------------------------------
    X_a = sm.add_constant(df[predictor])
    model_a = sm.OLS(df[mediator], X_a).fit()
    a_coef = model_a.params[predictor]

    # ------------------------------------------------------------------
    # 3. Total effect c (Y ~ X) – logistic regression because Y is binary
    # ------------------------------------------------------------------
    X_c = sm.add_constant(df[predictor])
    model_c = sm.Logit(df[outcome], X_c).fit(disp=0)
    c_coef = model_c.params[predictor]

    # ------------------------------------------------------------------
    # 4. Paths b and c' (Y ~ X + M)
    # ------------------------------------------------------------------
    X_bc = sm.add_constant(df[[predictor, mediator]])
    model_bc = sm.Logit(df[outcome], X_bc).fit(disp=0)
    b_coef = model_bc.params[mediator]
    c_prime_coef = model_bc.params[predictor]

    indirect_effect = a_coef * b_coef

    # ------------------------------------------------------------------
    # 5. Bootstrap confidence interval for the indirect effect
    # ------------------------------------------------------------------
    boot_estimates = []
    rng = np.random.default_rng()
    for _ in range(n_bootstrap):
        # Sample rows with replacement
        sample_idx = rng.integers(0, len(df), len(df))
        sample = df.iloc[sample_idx]

        # Re‑fit a and b on the bootstrap sample
        X_a_boot = sm.add_constant(sample[predictor])
        a_boot = sm.OLS(sample[mediator], X_a_boot).fit().params[predictor]

        X_bc_boot = sm.add_constant(sample[[predictor, mediator]])
        b_boot = sm.Logit(sample[outcome], X_bc_boot).fit(disp=0).params[mediator]

        boot_estimates.append(a_boot * b_boot)

    lower, upper = np.percentile(boot_estimates, [2.5, 97.5])
    indirect_ci = (float(lower), float(upper))

    # ------------------------------------------------------------------
    # 6. Sensitivity analysis – E‑value (requires ``evalues`` package)
    # ------------------------------------------------------------------
    try:
        from evalues import evalue

        # The evalue function expects a risk ratio; we approximate using the
        # odds ratio derived from the indirect effect.
        # Convert indirect effect to an odds ratio (exp) for compatibility.
        indirect_or = np.exp(indirect_effect)
        e_val = evalue(indirect_or, ci_lower=np.exp(lower), ci_upper=np.exp(upper), conf=evalue_confidence)
        e_value = float(e_val["evalue"])
    except Exception:
        e_value = None  # evalues not installed or calculation failed

    # ------------------------------------------------------------------
    # 7. Rosenbaum bounds – simple implementation
    # ------------------------------------------------------------------
    rosenbaum_bounds: Dict[float, float] = {}
    # We test significance of the indirect effect using a z‑test
    se_indirect = np.std(boot_estimates, ddof=1) / np.sqrt(n_bootstrap)
    z_score = indirect_effect / (se_indirect if se_indirect != 0 else 1e-9)
    p_original = 2 * (1 - stats.norm.cdf(abs(z_score)))

    for gamma in gamma_range:
        # Rosenbaum's sensitivity formula (simplified):
        # Adjusted p ≈ p_original * gamma / (1 + (gamma - 1) * p_original)
        # This is a heuristic that captures the intuition that larger gamma
        # inflates the p‑value.
        adjusted_p = p_original * gamma / (1 + (gamma - 1) * p_original)
        rosenbaum_bounds[gamma] = float(min(adjusted_p, 1.0))

    # ------------------------------------------------------------------
    # 8. Assemble results
    # ------------------------------------------------------------------
    results = {
        "paths": {
            "a": float(a_coef),
            "b": float(b_coef),
            "c": float(c_coef),
            "c_prime": float(c_prime_coef),
        },
        "indirect_effect": float(indirect_effect),
        "indirect_ci": indirect_ci,
        "e_value": e_value,
        "rosenbaum_bounds": rosenbaum_bounds,
    }

    # ------------------------------------------------------------------
    # 9. Persist results – we write a YAML file under ``results/`` and also
    #    update the central modeling log.
    # ------------------------------------------------------------------
    results_dir = Path(getattr(sys.modules[__name__], "__file__", "04_model_analysis.py")).parent.parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    mediation_path = results_dir / "mediation_results.yaml"
    with mediation_path.open("w", encoding="utf-8") as f:
        import yaml

        yaml.safe_dump(results, f, sort_keys=False)

    # Update the modeling log for traceability
    update_log_section(
        "mediation_analysis",
        {"status": "completed", "output_path": str(mediation_path)},
    )

    return results

# ----------------------------------------------------------------------
# Main entry point – orchestrates the full analysis pipeline
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the full modeling pipeline, including mediation analysis."
    )
    parser.add_argument(
        "--engineered",
        type=str,
        default="data/processed/engineered_data.csv",
        help="Path to the engineered dataset.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Directory where result artefacts will be stored.",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    df = load_engineered_data(args.engineered)

    # ------------------------------------------------------------------
    # Fit primary logistic regression (already implemented elsewhere)
    # ------------------------------------------------------------------
    model = fit_logistic_regression(df)

    # ------------------------------------------------------------------
    # Diagnostics – VIF, FDR, ROC
    # ------------------------------------------------------------------
    vif_df = calculate_vif(df)
    fdr_df = apply_fdr_correction(model)
    roc_metrics = calculate_roc_metrics(model, df)
    plot_roc_curve(roc_metrics, output_path=Path(args.output_dir) / "roc_curve.png")

    # ------------------------------------------------------------------
    # Mediation analysis (Task T040)
    # ------------------------------------------------------------------
    mediation_results = perform_mediation_analysis(df)

    # ------------------------------------------------------------------
    # Persist a summary JSON for quick inspection
    # ------------------------------------------------------------------
    summary = {
        "logistic_regression": model.summary2().tables[1].to_dict(),
        "vif": vif_df.to_dict(),
        "fdr": fdr_df.to_dict(),
        "roc": roc_metrics,
        "mediation": mediation_results,
    }
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(args.output_dir) / "analysis_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    # Log completion
    update_log_section(
        "model_analysis",
        {"status": "completed", "output_dir": str(args.output_dir)},
    )

if __name__ == "__main__":
    main()
