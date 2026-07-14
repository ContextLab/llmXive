"""
Model Analysis Script for Sustainable Agriculture Adoption Study

This script fits logistic regression models to analyze the relationship between
community engagement scores and sustainable agricultural practice adoption.
It includes VIF diagnostics, FDR correction, ROC analysis, and mediation testing.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import shared utilities
from config import get_config, get_config_path
from logging_config import log_operation, update_log_section

# Custom exceptions
class CustomDataError(Exception):
    """Raised when there is an error with input data."""
    pass

class ModelError(Exception):
    """Raised when there is an error during model fitting or analysis."""
    pass


def get_config_paths() -> Dict[str, Path]:
    """Get all required file paths from configuration."""
    base_dir = Path(get_config("project_root", "."))
    return {
        "engineered_data_path": base_dir / get_config("processed_data_path", "data/processed") / "engineered_data.csv",
        "results_dir": base_dir / get_config("results_path", "results"),
        "modeling_log_path": base_dir / get_config("modeling_log_path", "modeling_log.yaml"),
    }


def load_engineered_data(input_path: Path) -> pd.DataFrame:
    """Load the engineered dataset."""
    if not input_path.exists():
        raise CustomDataError(
            f"Engineered data not found at {input_path}. "
            "Please run code/03_engineer_features.py first."
        )
    df = pd.read_csv(input_path)
    logging.info(f"Loaded engineered data with {len(df)} records and {len(df.columns)} columns")
    return df


def prepare_model_data(
    df: pd.DataFrame,
    outcome_var: str = "adoption_binary",
    primary_predictor: str = "engagement_score",
    covariates: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """
    Prepare data for logistic regression.

    Returns:
        df_clean: DataFrame with no missing values in required columns
        predictors: List of all predictor variable names
        outcome: Name of the outcome variable
    """
    required_cols = [outcome_var, primary_predictor]
    if covariates:
        required_cols.extend(covariates)

    # Check for required columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise CustomDataError(f"Missing required columns: {missing_cols}")

    # Drop rows with missing values in required columns
    df_clean = df.dropna(subset=required_cols)

    if len(df_clean) == 0:
        raise CustomDataError("No valid records remaining after dropping missing values.")

    predictors = [primary_predictor]
    if covariates:
        predictors.extend(covariates)

    logging.info(f"Prepared model data: {len(df_clean)} records, predictors: {predictors}")
    return df_clean, predictors, outcome_var


def fit_logistic_regression(
    df: pd.DataFrame,
    outcome_var: str,
    predictors: List[str]
) -> sm.discrete.discrete_model.BinaryResultsWrapper:
    """
    Fit a logistic regression model using statsmodels.

    Args:
        df: Cleaned DataFrame
        outcome_var: Name of the binary outcome column
        predictors: List of predictor variable names

    Returns:
        Fitted model results object
    """
    X = df[predictors].copy()
    y = df[outcome_var].copy()

    # Add constant for intercept
    X = sm.add_constant(X)

    model = sm.Logit(y, X)
    results = model.fit(disp=False)

    logging.info(f"Logistic regression fitted: {len(predictors)} predictors, {len(df)} observations")
    return results


def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.

    Args:
        df: DataFrame with predictor variables
        predictors: List of predictor column names

    Returns:
        DataFrame with VIF values
    """
    X = df[predictors].copy()
    X = sm.add_constant(X)

    vif_data = []
    for i, col in enumerate(X.columns):
        if col == "const":
            continue
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data.append({"variable": col, "vif": vif})
        except Exception as e:
            logging.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data.append({"variable": col, "vif": np.nan})

    vif_df = pd.DataFrame(vif_data)
    return vif_df


def apply_fdr_correction(
    p_values: np.ndarray,
    alpha: float = 0.10
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.

    Args:
        p_values: Array of raw p-values
        alpha: Significance level for FDR

    Returns:
        Tuple of (adjusted p-values, boolean array of significant results)
    """
    from statsmodels.stats.multitest import multipletests

    rejected, p_adjusted, _, _ = multipletests(
        p_values,
        alpha=alpha,
        method='fdr_bh'
    )

    return p_adjusted, rejected


def calculate_roc_metrics(
    df: pd.DataFrame,
    results: sm.discrete.discrete_model.BinaryResultsWrapper,
    outcome_var: str
) -> Dict[str, float]:
    """
    Calculate ROC curve metrics (AUC).

    Args:
        df: DataFrame with outcome variable
        results: Fitted logistic regression results
        outcome_var: Name of the outcome column

    Returns:
        Dictionary with AUC and other metrics
    """
    y_true = df[outcome_var].values
    y_pred_prob = results.predict()

    # Calculate AUC using trapezoidal rule
    fpr, tpr, thresholds = stats.roc_curve(y_true, y_pred_prob)
    auc = stats.auc(fpr, tpr)

    return {
        "auc": float(auc),
        "fpr": fpr.tolist(),
        "tpr": tpr.tolist(),
        "thresholds": thresholds.tolist()
    }


def interpret_auc(auc: float) -> str:
    """Provide qualitative interpretation of AUC value."""
    if auc < 0.5:
        return "No discrimination (worse than random)"
    elif auc < 0.6:
        return "Poor discrimination"
    elif auc < 0.7:
        return "Fair discrimination"
    elif auc < 0.8:
        return "Good discrimination"
    elif auc < 0.9:
        return "Very good discrimination"
    else:
        return "Excellent discrimination"


def perform_mediation_analysis(
    df: pd.DataFrame,
    outcome_var: str,
    predictor_var: str,
    mediator_var: str = "engagement_score",
    n_bootstrap: int = 1000
) -> Dict[str, Any]:
    """
    Perform Baron & Kenny mediation analysis with bootstrap confidence intervals.

    Note: This is exploratory analysis as per study limitations.

    Args:
        df: Cleaned dataset
        outcome_var: Name of outcome variable
        predictor_var: Name of primary predictor
        mediator_var: Name of mediator variable
        n_bootstrap: Number of bootstrap resamples

    Returns:
        Dictionary with mediation analysis results
    """
    # For this implementation, we check if the mediator is the same as the predictor
    # In a real scenario, we would have distinct mediator and predictor variables
    if predictor_var == mediator_var:
        logging.warning("Predictor and mediator are the same variable. Skipping full mediation analysis.")
        return {
            "status": "skipped",
            "reason": "Predictor and mediator are identical",
            "direct_effect": None,
            "indirect_effect": None,
            "total_effect": None,
            "bootstrap_ci": None
        }

    # Step 1: Total effect (Y ~ X)
    X = sm.add_constant(df[[predictor_var]])
    y = df[outcome_var]
    model_total = sm.Logit(y, X).fit(disp=False)
    total_effect = model_total.params[predictor_var]

    # Step 2: Mediator model (M ~ X)
    # Using OLS for mediator as it's continuous
    med_model = sm.OLS(df[mediator_var], X).fit()
    path_a = med_model.params[predictor_var]

    # Step 3: Direct effect (Y ~ X + M)
    X_full = sm.add_constant(df[[predictor_var, mediator_var]])
    model_direct = sm.Logit(y, X_full).fit(disp=False)
    direct_effect = model_direct.params[predictor_var]
    path_b = model_direct.params[mediator_var]

    # Indirect effect = a * b
    indirect_effect = path_a * path_b

    # Bootstrap for confidence intervals
    boot_indirect = []
    rng = np.random.default_rng(42)
    for _ in range(n_bootstrap):
        idx = rng.choice(len(df), size=len(df), replace=True)
        df_boot = df.iloc[idx]

        # Bootstrap path a
        X_boot = sm.add_constant(df_boot[[predictor_var]])
        med_boot = sm.OLS(df_boot[mediator_var], X_boot).fit()
        a_boot = med_boot.params[predictor_var]

        # Bootstrap path b
        y_boot = df_boot[outcome_var]
        X_full_boot = sm.add_constant(df_boot[[predictor_var, mediator_var]])
        try:
            direct_boot = sm.Logit(y_boot, X_full_boot).fit(disp=False)
            b_boot = direct_boot.params[mediator_var]
            boot_indirect.append(a_boot * b_boot)
        except:
            continue

    if len(boot_indirect) > 0:
        ci_lower = np.percentile(boot_indirect, 2.5)
        ci_upper = np.percentile(boot_indirect, 97.5)
        bootstrap_ci = [float(ci_lower), float(ci_upper)]
    else:
        bootstrap_ci = None

    return {
        "status": "completed",
        "total_effect": float(total_effect),
        "direct_effect": float(direct_effect),
        "indirect_effect": float(indirect_effect),
        "path_a": float(path_a),
        "path_b": float(path_b),
        "bootstrap_ci_95": bootstrap_ci,
        "interpretation": "exploratory"
    }


def save_results(
    results: sm.discrete.discrete_model.BinaryResultsWrapper,
    vif_df: pd.DataFrame,
    roc_metrics: Dict[str, Any],
    mediation_results: Dict[str, Any],
    output_dir: Path,
    modeling_log_path: Path
) -> Dict[str, Any]:
    """
    Save all analysis results to files.

    Args:
        results: Fitted model results
        vif_df: VIF analysis DataFrame
        roc_metrics: ROC/AUC metrics
        mediation_results: Mediation analysis results
        output_dir: Directory to save results
        modeling_log_path: Path to modeling log file
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save regression summary as text
    summary_path = output_dir / "regression_summary.txt"
    with open(summary_path, "w") as f:
        f.write(results.summary().as_csv())

    # Save VIF results
    vif_path = output_dir / "vif_diagnostics.csv"
    vif_df.to_csv(vif_path, index=False)

    # Save ROC metrics
    roc_path = output_dir / "roc_metrics.json"
    # Convert numpy types to Python native types for JSON serialization
    roc_clean = {k: v if not isinstance(v, (np.ndarray, np.floating)) else (v.tolist() if isinstance(v, np.ndarray) else float(v))
                 for k, v in roc_metrics.items()}
    import json
    with open(roc_path, "w") as f:
        json.dump(roc_clean, f, indent=2)

    # Save mediation results
    mediation_path = output_dir / "mediation_results.json"
    with open(mediation_path, "w") as f:
        json.dump(mediation_results, f, indent=2, default=str)

    # Update modeling log
    log_data = {
        "model_type": "logistic_regression",
        "n_observations": results.nobs,
        "n_parameters": len(results.params),
        "auc": roc_metrics["auc"],
        "auc_interpretation": interpret_auc(roc_metrics["auc"]),
        "vif_max": float(vif_df["vif"].max()) if not vif_df.empty else None,
        "mediation_status": mediation_results.get("status", "unknown"),
        "timestamp": datetime.utcnow().isoformat()
    }

    update_log_section("model_analysis", log_data, log_path=modeling_log_path)

    logging.info(f"Results saved to {output_dir}")
    return {
        "summary_path": str(summary_path),
        "vif_path": str(vif_path),
        "roc_path": str(roc_path),
        "mediation_path": str(mediation_path)
    }


@log_operation("model_analysis_main")
def main():
    """Main entry point for model analysis."""
    parser = argparse.ArgumentParser(description="Fit logistic regression and perform analysis")
    parser.add_argument("--input", type=str, help="Path to engineered data CSV")
    parser.add_argument("--outcome", type=str, default="adoption_binary", help="Outcome variable name")
    parser.add_argument("--predictor", type=str, default="engagement_score", help="Primary predictor name")
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        # Get paths
        paths = get_config_paths()
        input_path = Path(args.input) if args.input else paths["engineered_data_path"]
        output_dir = paths["results_dir"]
        modeling_log_path = paths["modeling_log_path"]

        # Load data
        logging.info("Loading engineered data...")
        df = load_engineered_data(input_path)

        # Define covariates (excluding the primary predictor)
        # Based on typical agricultural studies: age, education, farm_size, credit_access
        covariates = ["age", "education_years", "farm_size_hectares", "credit_access"]
        # Filter to only those that exist in the data
        covariates = [c for c in covariates if c in df.columns]

        # Prepare data
        logging.info("Preparing model data...")
        df_clean, predictors, outcome_var = prepare_model_data(
            df,
            outcome_var=args.outcome,
            primary_predictor=args.predictor,
            covariates=covariates if covariates else None
        )

        # Fit logistic regression
        logging.info("Fitting logistic regression...")
        results = fit_logistic_regression(df_clean, outcome_var, predictors)

        # Calculate VIF
        logging.info("Calculating VIF diagnostics...")
        vif_df = calculate_vif(df_clean, predictors)
        high_vif = vif_df[vif_df["vif"] >= 5]
        if not high_vif.empty:
            logging.warning(f"High VIF detected: {high_vif['variable'].tolist()}")

        # Apply FDR correction to p-values
        logging.info("Applying FDR correction...")
        p_values = results.pvalues.drop("const")
        p_adjusted, significant = apply_fdr_correction(p_values.values)
        logging.info(f"Number of significant predictors after FDR: {sum(significant)}")

        # Calculate ROC metrics
        logging.info("Calculating ROC metrics...")
        roc_metrics = calculate_roc_metrics(df_clean, results, outcome_var)
        logging.info(f"AUC: {roc_metrics['auc']:.3f} ({interpret_auc(roc_metrics['auc'])})")

        # Perform mediation analysis (if applicable)
        logging.info("Performing mediation analysis...")
        mediation_results = perform_mediation_analysis(
            df_clean,
            outcome_var,
            args.predictor,
            mediator_var="engagement_score"
        )

        # Save results
        logging.info("Saving results...")
        saved_files = save_results(
            results,
            vif_df,
            roc_metrics,
            mediation_results,
            output_dir,
            modeling_log_path
        )

        logging.info("Model analysis completed successfully.")
        return 0

    except CustomDataError as e:
        logging.error(f"Data Error: {e}")
        update_log_section("model_analysis", {"status": "failed", "error": str(e)}, log_path=paths.get("modeling_log_path"))
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        update_log_section("model_analysis", {"status": "failed", "error": str(e)}, log_path=paths.get("modeling_log_path"))
        return 1


if __name__ == "__main__":
    sys.exit(main())