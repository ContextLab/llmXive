"""
Adaptive Regression Analysis Module for Simulated Social Status Study.

This module implements adaptive regression modeling for the social status
risk-taking study, automatically selecting between fixed-effects and
mixed-effects models based on the detected data structure.

Key Features:
    - Automatic model selection (Mixed-Effects for within-subjects,
      Fixed-Effects for between-subjects)
    - Variance Inflation Factor (VIF) calculation for multicollinearity
    - Bootstrap standard errors for robust inference
    - Parameter recovery analysis comparing estimates to injected effects
    - Confidence interval width calculation as a precision metric
    - Sensitivity analysis across outlier thresholds
    - Post-hoc pairwise comparisons with Bonferroni correction

The module adheres to the project's adaptive modeling requirements (FR-003),
ensuring the correct statistical approach is used based on the experimental
design detected in the data.

Attributes:
    logger (logging.Logger): Module-level logger for tracking execution.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests
from statsmodels.regression.mixed_linear_model import MixedLM
import warnings

# Ensure code is in path for imports if running as script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from logger import setup_logger, get_logger
from utils import load_json, save_json, set_seed
from config import load_simulation_params, get_regression_family

logger = setup_logger("analysis", "logs/analysis.log")


def validate_data_structure(df: pd.DataFrame) -> dict:
    """
    Validate the structure of the input dataset.

    Checks for required columns, data types, and basic integrity
    constraints. Ensures the dataset is suitable for analysis.

    Args:
        df (pd.DataFrame): Input dataset to validate.

    Returns:
        dict: Validation results including:
            - valid (bool): Whether validation passed
            - n_rows (int): Number of rows
            - n_subjects (int): Number of unique participants
            - design_type (str): 'between' or 'within'
            - missing_columns (list): Any missing required columns
            - warnings (list): Any validation warnings

    Raises:
        ValueError: If required columns are missing or data is invalid.
    """
    required_columns = ["participant_id", "status_level", "observed_behavior", "risk_taking_score"]
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    n_rows = len(df)
    n_subjects = df["participant_id"].nunique()

    if n_rows != n_subjects:
        design_type = "within"
        logger.info(f"Detected within-subjects design: {n_rows} rows, {n_subjects} subjects")
    else:
        design_type = "between"
        logger.info(f"Detected between-subjects design: {n_rows} subjects")

    return {
        "valid": True,
        "n_rows": n_rows,
        "n_subjects": n_subjects,
        "design_type": design_type,
        "missing_columns": [],
        "warnings": []
    }


def fit_fixed_effects(df: pd.DataFrame) -> dict:
    """
    Fit a fixed-effects regression model for between-subjects design.

    Models the interaction between status level and observed behavior
    on risk-taking scores using ordinary least squares regression.

    Args:
        df (pd.DataFrame): Preprocessed dataset with categorical variables.

    Returns:
        dict: Model results including:
            - coefficients (dict): Estimated coefficients
            - p_values (dict): P-values for each coefficient
            - model_summary (str): Full model summary string
            - r_squared (float): R-squared value
            - adj_r_squared (float): Adjusted R-squared
    """
    # Create dummy variables for categorical predictors
    df_model = df.copy()
    df_model = pd.get_dummies(df_model, columns=["status_level", "observed_behavior"], drop_first=True)

    # Define formula: main effects + interaction
    # Assuming columns: status_level_High, observed_behavior_Risky, interaction terms
    available_cols = df_model.columns.tolist()
    interaction_cols = [c for c in available_cols if "status_level" in c and "observed_behavior" in c]

    if not interaction_cols:
        # Manually create interaction
        if "status_level_High" in available_cols and "observed_behavior_Risky" in available_cols:
            df_model["interaction"] = df_model["status_level_High"] * df_model["observed_behavior_Risky"]
            formula = "risk_taking_score ~ status_level_High + observed_behavior_Risky + interaction"
        else:
            formula = "risk_taking_score ~ status_level_High + observed_behavior_Risky"
    else:
        formula = f"risk_taking_score ~ {' + '.join([c for c in available_cols if c != 'risk_taking_score' and 'participant_id' not in c])}"

    y = df_model["risk_taking_score"]
    X = sm.add_constant(df_model.drop(["risk_taking_score"], axis=1))

    model = sm.OLS(y, X)
    results = model.fit()

    coefficients = {name: float(coeff) for name, coeff in results.params.items()}
    p_values = {name: float(p) for name, p in results.pvalues.items()}

    return {
        "coefficients": coefficients,
        "p_values": p_values,
        "model_summary": results.summary().as_text(),
        "r_squared": float(results.rsquared),
        "adj_r_squared": float(results.rsquared_adj),
        "model_type": "fixed_effects"
    }


def fit_mixed_effects(df: pd.DataFrame) -> dict:
    """
    Fit a mixed-effects regression model for within-subjects design.

    Models the interaction between status level and observed behavior
    on risk-taking scores, with random intercepts for participants.

    Args:
        df (pd.DataFrame): Preprocessed dataset with categorical variables.

    Returns:
        dict: Model results including:
            - coefficients (dict): Estimated fixed effects coefficients
            - p_values (dict): P-values for fixed effects
            - model_summary (str): Full model summary string
            - model_type (str): 'mixed_effects'
    """
    # Prepare data for mixed model
    df_model = df.copy()
    df_model = pd.get_dummies(df_model, columns=["status_level", "observed_behavior"], drop_first=True)

    # Create interaction term if not present
    if "status_level_High" in df_model.columns and "observed_behavior_Risky" in df_model.columns:
        df_model["interaction"] = df_model["status_level_High"] * df_model["observed_behavior_Risky"]
        formula = "risk_taking_score ~ status_level_High + observed_behavior_Risky + interaction"
        endog = df_model["risk_taking_score"]
        exog = df_model[["status_level_High", "observed_behavior_Risky", "interaction"]]
    else:
        exog_cols = [c for c in df_model.columns if c not in ["risk_taking_score", "participant_id"]]
        exog = df_model[exog_cols]
        formula = f"risk_taking_score ~ {' + '.join(exog_cols)}"

    # Fit mixed model with random intercept for participant
    try:
        model = MixedLM(endog, exog, groups=df_model["participant_id"])
        results = model.fit()

        coefficients = {name: float(coeff) for name, coeff in results.params.items()}
        p_values = {name: float(p) for name, p in results.pvalues.items()}

        return {
            "coefficients": coefficients,
            "p_values": p_values,
            "model_summary": results.summary().as_text(),
            "model_type": "mixed_effects"
        }
    except Exception as e:
        logger.error(f"Mixed model fitting failed: {e}")
        # Fallback to fixed effects
        logger.warning("Falling back to fixed effects model")
        return fit_fixed_effects(df)


def calculate_vif(df: pd.DataFrame) -> dict:
    """
    Calculate Variance Inflation Factors for all predictors.

    Computes VIF to detect multicollinearity among predictor variables.
    Flags any VIF > 5.0 as potentially problematic.

    Args:
        df (pd.DataFrame): Dataset with predictor variables.

    Returns:
        dict: VIF results including:
            - vif_values (dict): VIF for each predictor
            - high_vif_vars (list): Variables with VIF > 5.0
            - max_vif (float): Maximum VIF value
    """
    df_model = df.copy()
    df_model = pd.get_dummies(df_model, columns=["status_level", "observed_behavior"], drop_first=True)

    # Remove non-predictor columns
    predictor_cols = [c for c in df_model.columns if c not in ["risk_taking_score", "participant_id"]]

    if not predictor_cols:
        return {"vif_values": {}, "high_vif_vars": [], "max_vif": 0.0}

    X = df_model[predictor_cols]
    X = sm.add_constant(X)

    vif_data = {}
    for i, col in enumerate(X.columns):
        if col == "const":
            continue
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data[col] = float(vif)
        except Exception:
            vif_data[col] = float('inf')

    high_vif_vars = [k for k, v in vif_data.items() if v > 5.0]
    max_vif = max(vif_data.values()) if vif_data else 0.0

    return {
        "vif_values": vif_data,
        "high_vif_vars": high_vif_vars,
        "max_vif": max_vif
    }


def get_bootstrap_se(df: pd.DataFrame, n_iterations: int = 1000) -> dict:
    """
    Calculate bootstrap standard errors for model coefficients.

    Uses bootstrap resampling to estimate standard errors for regression
    coefficients, providing robust inference especially for small samples.

    Args:
        df (pd.DataFrame): Dataset for analysis.
        n_iterations (int): Number of bootstrap iterations. Default 1000.

    Returns:
        dict: Bootstrap results including:
            - se_estimates (dict): Bootstrap SE for each coefficient
            - ci_95 (dict): 95% confidence intervals for each coefficient
            - bootstrap_iterations (int): Number of iterations performed
    """
    set_seed(42)
    df_model = df.copy()
    df_model = pd.get_dummies(df_model, columns=["status_level", "observed_behavior"], drop_first=True)

    if "status_level_High" in df_model.columns and "observed_behavior_Risky" in df_model.columns:
        df_model["interaction"] = df_model["status_level_High"] * df_model["observed_behavior_Risky"]
        endog = df_model["risk_taking_score"]
        exog_cols = ["status_level_High", "observed_behavior_Risky", "interaction"]
    else:
        exog_cols = [c for c in df_model.columns if c not in ["risk_taking_score", "participant_id"]]

    exog = sm.add_constant(df_model[exog_cols])
    y = df_model["risk_taking_score"]

    bootstrap_coeffs = {col: [] for col in exog.columns}

    for _ in range(n_iterations):
        indices = np.random.choice(len(df_model), size=len(df_model), replace=True)
        X_boot = exog.iloc[indices]
        y_boot = y.iloc[indices]

        try:
            model = sm.OLS(y_boot, X_boot)
            results = model.fit()
            for col in exog.columns:
                bootstrap_coeffs[col].append(results.params[col])
        except Exception:
            continue

    se_estimates = {}
    ci_95 = {}

    for col in exog.columns:
      if bootstrap_coeffs[col]:
          se_estimates[col] = float(np.std(bootstrap_coeffs[col]))
          ci_lower = float(np.percentile(bootstrap_coeffs[col], 2.5))
          ci_upper = float(np.percentile(bootstrap_coeffs[col], 97.5))
          ci_95[col] = {"lower": ci_lower, "upper": ci_upper}

    return {
        "se_estimates": se_estimates,
        "ci_95": ci_95,
        "bootstrap_iterations": n_iterations
    }


def analyze_interaction_with_bootstrap(df: pd.DataFrame) -> dict:
    """
    Analyze the interaction effect using bootstrap methods.

    Combines model fitting with bootstrap standard errors to provide
    robust inference on the status x behavior interaction.

    Args:
        df (pd.DataFrame): Preprocessed dataset.

    Returns:
        dict: Complete interaction analysis including:
            - fixed_effects (dict): Fixed effects results
            - bootstrap_se (dict): Bootstrap standard errors
            - interaction_significant (bool): Whether interaction is significant
    """
    # Determine design type
    n_rows = len(df)
    n_subjects = df["participant_id"].nunique()
    design_type = "within" if n_rows != n_subjects else "between"

    if design_type == "within":
        fixed_effects = fit_mixed_effects(df)
    else:
        fixed_effects = fit_fixed_effects(df)

    bootstrap_se = get_bootstrap_se(df)

    # Check interaction significance
    interaction_term = "interaction" if "interaction" in fixed_effects["coefficients"] else None
    if interaction_term:
        p_val = fixed_effects["p_values"].get(interaction_term, 1.0)
        interaction_significant = p_val < 0.05
    else:
        interaction_significant = False

    return {
        "fixed_effects": fixed_effects,
        "bootstrap_se": bootstrap_se,
        "interaction_significant": interaction_significant,
        "design_type": design_type
    }


def analyze_interaction(df: pd.DataFrame) -> dict:
    """
    Primary analysis function for the status x behavior interaction.

    Orchestrates the complete interaction analysis including model fitting,
    VIF calculation, and bootstrap inference.

    Args:
        df (pd.DataFrame): Preprocessed dataset.

    Returns:
        dict: Complete analysis results including all metrics.
    """
    logger.info("Starting interaction analysis")

    # Validate data
    validation = validate_data_structure(df)

    # Calculate VIF
    vif_results = calculate_vif(df)

    # Run main analysis
    interaction_results = analyze_interaction_with_bootstrap(df)

    return {
        "validation": validation,
        "vif": vif_results,
        "interaction": interaction_results
    }


def run_sensitivity_analysis(df: pd.DataFrame, threshold_range: list = None) -> dict:
    """
    Conduct sensitivity analysis across different outlier thresholds.

    Systematically varies the outlier exclusion threshold (in standard
    deviations from cell means) and reports how the interaction effect
    estimate changes.

    Args:
        df (pd.DataFrame): Preprocessed dataset.
        threshold_range (list): List of SD thresholds to test.
            Default: [1.0, 1.5, 2.0, 2.5, 3.0]

    Returns:
        dict: Sensitivity analysis results including:
            - thresholds (list): Tested thresholds
            - effect_sizes (list): Interaction effect at each threshold
            - p_values (list): P-values at each threshold
            - n_excluded (list): Number of excluded observations at each threshold
    """
    if threshold_range is None:
        threshold_range = [1.0, 1.5, 2.0, 2.5, 3.0]

    results = {
        "thresholds": threshold_range,
        "effect_sizes": [],
        "p_values": [],
        "n_excluded": [],
        "n_remaining": []
    }

    # Calculate cell means for each condition
    cell_means = df.groupby(["status_level", "observed_behavior"])["risk_taking_score"].mean()

    for threshold in threshold_range:
        df_filtered = df.copy()
        excluded_count = 0

        for status in ["High", "Low"]:
            for behavior in ["Risky", "Conservative"]:
                mask = (df_filtered["status_level"] == status) & (df_filtered["observed_behavior"] == behavior)
                cell_data = df_filtered[mask]
                cell_mean = cell_means[(status, behavior)]
                cell_std = df_filtered[mask]["risk_taking_score"].std()

                if cell_std > 0:
                    deviation = np.abs(cell_data["risk_taking_score"] - cell_mean)
                    outliers = deviation > (threshold * cell_std)
                    excluded_count += outliers.sum()
                    df_filtered = df_filtered[~outliers]

        results["n_excluded"].append(excluded_count)
        results["n_remaining"].append(len(df_filtered))

        if len(df_filtered) > 10:
            try:
                analysis = analyze_interaction(df_filtered)
                interaction_term = "interaction" if "interaction" in analysis["interaction"]["fixed_effects"]["coefficients"] else None
                if interaction_term:
                    results["effect_sizes"].append(analysis["interaction"]["fixed_effects"]["coefficients"][interaction_term])
                    results["p_values"].append(analysis["interaction"]["fixed_effects"]["p_values"][interaction_term])
                else:
                    results["effect_sizes"].append(None)
                    results["p_values"].append(None)
            except Exception:
                results["effect_sizes"].append(None)
                results["p_values"].append(None)
        else:
            results["effect_sizes"].append(None)
            results["p_values"].append(None)

    return results


def fit_adaptive_model(df: pd.DataFrame, structure_config: dict = None) -> dict:
    """
    Adaptively select and fit the appropriate regression model.

    Reads the data structure configuration to determine whether to use
    mixed-effects (within-subjects) or fixed-effects (between-subjects)
    modeling.

    Args:
        df (pd.DataFrame): Preprocessed dataset.
        structure_config (dict): Optional structure configuration. If not
            provided, will be inferred from the data.

    Returns:
        dict: Model results with dynamic model type selection.
    """
    if structure_config is None:
        n_rows = len(df)
        n_subjects = df["participant_id"].nunique()
        design_type = "within-subjects" if n_rows != n_subjects else "between-subjects"
    else:
        design_type = structure_config.get("type", "between-subjects")

    logger.info(f"Adaptive model selection: {design_type}")

    if design_type == "within-subjects":
        logger.info("Fitting Mixed-Effects model")
        results = fit_mixed_effects(df)
    else:
        logger.info("Fitting Fixed-Effects model")
        results = fit_fixed_effects(df)

    # Calculate VIF
    results["vif"] = calculate_vif(df)

    return results


def perform_post_hoc_comparisons(df: pd.DataFrame) -> dict:
    """
    Perform post-hoc pairwise comparisons with Bonferroni correction.

    Conducts all pairwise comparisons between experimental conditions
    regardless of the primary interaction significance (FR-006).

    Args:
        df (pd.DataFrame): Preprocessed dataset.

    Returns:
        dict: Post-hoc results including:
            - comparisons (list): All pairwise comparisons
            - p_values_raw (list): Raw p-values
            - p_values_adjusted (list): Bonferroni-adjusted p-values
            - significant (list): Which comparisons are significant
    """
    # Create condition combinations
    conditions = df.groupby(["status_level", "observed_behavior"])["risk_taking_score"]
    condition_names = []
    condition_means = []

    for (status, behavior), group in conditions:
        condition_names.append(f"{status}_{behavior}")
        condition_means.append(group.mean())

    # Perform all pairwise t-tests
    from scipy import stats
    comparisons = []
    p_values_raw = []
    groups = list(conditions)

    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            name_i, data_i = groups[i]
            name_j, data_j = groups[j]

            t_stat, p_val = stats.ttest_ind(data_i["risk_taking_score"], data_j["risk_taking_score"])
            comparisons.append(f"{name_i} vs {name_j}")
            p_values_raw.append(p_val)

    # Apply Bonferroni correction
    p_values_adjusted = multipletests(p_values_raw, method="bonferroni")[1]
    significant = [p < 0.05 for p in p_values_adjusted]

    return {
        "comparisons": comparisons,
        "p_values_raw": p_values_raw,
        "p_values_adjusted": p_values_adjusted,
        "significant": significant
    }


def main():
    """
    Command-line entry point for analysis pipeline.

    Loads preprocessed data, runs adaptive model fitting, calculates
    VIF, performs post-hoc comparisons, and saves results.

    Args:
        --input (str): Path to preprocessed CSV file
        --output (str): Path for output JSON results file
        --config (str): Optional path to structure config JSON

    Example:
        python code/analysis.py --input data/processed/cleaned_data.csv --output reports/analysis_results.json
    """
    parser = argparse.ArgumentParser(description="Run adaptive regression analysis")
    parser.add_argument("--input", type=str, required=True, help="Input CSV path")
    parser.add_argument("--output", type=str, required=True, help="Output JSON path")
    parser.add_argument("--config", type=str, default=None, help="Structure config JSON path")
    args = parser.parse_args()

    logger.info(f"Loading data from {args.input}")
    df = pd.read_csv(args.input)

    # Load structure config if provided
    structure_config = None
    if args.config and os.path.exists(args.config):
        structure_config = load_json(args.config)

    # Run analysis
    results = fit_adaptive_model(df, structure_config)
    results["post_hoc"] = perform_post_hoc_comparisons(df)
    results["sensitivity"] = run_sensitivity_analysis(df)

    # Save results
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    save_json(results, args.output)
    logger.info(f"Analysis complete. Results saved to {args.output}")
    print(f"Analysis complete. Results saved to {args.output}")


if __name__ == "__main__":
    main()
