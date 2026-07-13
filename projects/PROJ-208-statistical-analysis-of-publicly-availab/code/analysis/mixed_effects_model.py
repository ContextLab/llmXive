"""
Linear Mixed-Effects Model Implementation for Issue Resolution Analysis.

Fits a linear mixed-effects model with random intercepts for repository
to analyze the associational relationship between issue characteristics
and resolution time.

This module implements FR-005: Fit linear mixed-effects model with random
intercepts for repository.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

# Import config utilities
from utils.config import get_config, set_seed, get_path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_cleaned_data() -> pd.DataFrame:
    """
    Load the cleaned issues dataset from the processed directory.

    Returns:
        pd.DataFrame: The cleaned issues dataset.

    Raises:
        FileNotFoundError: If the cleaned dataset does not exist.
    """
    config = get_config()
    data_path = get_path(config, 'processed_cleaned_issues')
    
    if not data_path.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found at {data_path}. "
            "Please run the preprocessing pipeline (T010, T011) first."
        )
    
    logger.info(f"Loading cleaned data from {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} records")
    return df


def prepare_data_for_lme(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Prepare the dataset for linear mixed-effects modeling.

    Filters out records with missing values in key columns and
    handles outliers in resolution time if necessary.

    Args:
        df (pd.DataFrame): The raw cleaned dataset.

    Returns:
        Tuple[pd.DataFrame, List[str]]: Prepared dataframe and list of dropped rows.
    """
    required_cols = ['resolution_time_hours', 'repo_name', 'issue_type', 
                     'author_forks', 'author_followers', 'priority', 
                     'programming_language']
    
    # Check for required columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for LME: {missing_cols}")
    
    # Drop rows with missing values in required columns
    initial_count = len(df)
    df_clean = df.dropna(subset=required_cols)
    dropped_count = initial_count - len(df_clean)
    
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows due to missing values")
    
    # Log-transform resolution time to handle skewness (common in time data)
    # Add small epsilon to avoid log(0) if any zero values exist
    epsilon = 1e-6
    df_clean['log_resolution_time'] = np.log(df_clean['resolution_time_hours'] + epsilon)
    
    # Convert categorical variables to string type for formula handling
    categorical_cols = ['issue_type', 'priority', 'programming_language']
    for col in categorical_cols:
        df_clean[col] = df_clean[col].astype(str)
    
    return df_clean, [col for col in required_cols if col in df.columns]


def fit_mixed_effects_model(df: pd.DataFrame) -> Any:
    """
    Fit a linear mixed-effects model with random intercepts for repository.

    The model formula is:
    log_resolution_time ~ issue_type + priority + programming_language + 
                         author_forks + author_followers + (1 | repo_name)

    This models the associational relationship between issue characteristics
    and resolution time, accounting for the hierarchical structure of issues
    nested within repositories.

    Args:
        df (pd.DataFrame): Prepared dataframe with log-transformed target.

    Returns:
        statsmodels.regression.mixed_linear_model.MixedLMResults: Fitted model results.
    """
    # Define the model formula
    # Note: Using log-transformed resolution time to normalize residuals
    formula = "log_resolution_time ~ C(issue_type) + C(priority) + C(programming_language) + author_forks + author_followers"
    
    # Random effect: random intercepts for each repository
    # (1 | repo_name) specifies random intercepts
    
    logger.info("Fitting linear mixed-effects model with random intercepts for repository...")
    
    try:
        # Fit the model
        # Using REML (Restricted Maximum Likelihood) for unbiased variance estimates
        model = smf.mixedlm(formula, df, groups=df["repo_name"])
        fitted_model = model.fit(reml=True, maxiter=1000)
        
        logger.info(f"Model converged: {fitted_model.converged}")
        logger.info(f"Number of groups (repositories): {len(fitted_model.groups)}")
        logger.info(f"Number of observations: {len(df)}")
        
        return fitted_model
        
    except Exception as e:
        logger.error(f"Failed to fit mixed-effects model: {e}")
        raise


def extract_results(fitted_model: Any) -> Dict[str, Any]:
    """
    Extract and summarize results from the fitted mixed-effects model.

    Args:
        fitted_model: The fitted statsmodels MixedLMResults object.

    Returns:
        Dict[str, Any]: Dictionary containing model summary, coefficients,
                       variance components, and fit statistics.
    """
    results = {
        "model_summary": {},
        "fixed_effects": [],
        "random_effects": {},
        "fit_statistics": {}
    }
    
    # Extract fixed effects (associational relationships)
    # Note: These represent correlational associations, not causal effects
    params = fitted_model.params
    conf_int = fitted_model.conf_int()
    
    for param_name, param_value in params.items():
        if param_name != "group":  # Skip the group variance parameter
            row = conf_int.loc[param_name]
            results["fixed_effects"].append({
                "term": param_name,
                "estimate": float(param_value),
                "std_err": float(fitted_model.bse.get(param_name, np.nan)),
                "z_value": float(fitted_model.tvalues.get(param_name, np.nan)),
                "p_value": float(fitted_model.pvalues.get(param_name, np.nan)),
                "ci_lower": float(row[0]),
                "ci_upper": float(row[1])
            })
    
    # Extract random effects (variance components)
    # Variance of random intercepts (repository-level variation)
    try:
        random_cov = fitted_model.cov_re
        if random_cov is not None:
            # The variance of the random intercepts
            var_intercept = float(random_cov.iloc[0, 0])
            results["random_effects"]["variance_intercept"] = var_intercept
            results["random_effects"]["std_intercept"] = float(np.sqrt(var_intercept))
            
            # Calculate ICC (Intraclass Correlation Coefficient)
            # ICC = sigma^2_group / (sigma^2_group + sigma^2_residual)
            sigma2_group = var_intercept
            sigma2_residual = float(fitted_model.scale)
            icc = sigma2_group / (sigma2_group + sigma2_residual)
            results["random_effects"]["icc"] = float(icc)
            results["random_effects"]["interpretation"] = f"{icc:.2%} of variance is at the repository level"
    except Exception as e:
        logger.warning(f"Could not extract random effects: {e}")
    
    # Fit statistics
    # Log-likelihood and AIC/BIC
    try:
        results["fit_statistics"]["log_likelihood"] = float(fitted_model.llf)
        results["fit_statistics"]["aic"] = float(fitted_model.aic)
        results["fit_statistics"]["bic"] = float(fitted_model.bic)
    except Exception as e:
        logger.warning(f"Could not extract fit statistics: {e}")
    
    # Number of observations and groups
    results["fit_statistics"]["n_observations"] = int(len(fitted_model.data.endog))
    results["fit_statistics"]["n_groups"] = int(len(fitted_model.groups))
    
    # Model convergence status
    results["fit_statistics"]["converged"] = bool(fitted_model.converged)
    
    return results


def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save the model results to a JSON file.

    Args:
        results (Dict[str, Any]): The extracted model results.
        output_path (Path): Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add metadata
    results["metadata"] = {
        "model_type": "Linear Mixed-Effects Model",
        "formula": "log_resolution_time ~ C(issue_type) + C(priority) + C(programming_language) + author_forks + author_followers + (1 | repo_name)",
        "interpretation_note": "Results describe associational/correlational relationships. Fixed effects coefficients represent the estimated change in log-resolution time associated with each predictor, holding other variables constant. Random effects capture repository-level variation.",
        "timestamp": str(pd.Timestamp.now())
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_path}")


def print_summary(results: Dict[str, Any]) -> None:
    """
    Print a human-readable summary of the model results.

    Args:
        results (Dict[str, Any]): The extracted model results.
    """
    print("\n" + "="*80)
    print("LINEAR MIXED-EFFECTS MODEL SUMMARY")
    print("="*80)
    
    print("\n--- Fit Statistics ---")
    fit_stats = results.get("fit_statistics", {})
    print(f"Converged: {fit_stats.get('converged', 'N/A')}")
    print(f"Observations: {fit_stats.get('n_observations', 'N/A')}")
    print(f"Groups (Repositories): {fit_stats.get('n_groups', 'N/A')}")
    print(f"AIC: {fit_stats.get('aic', 'N/A'):.4f}")
    print(f"BIC: {fit_stats.get('bic', 'N/A'):.4f}")
    
    print("\n--- Random Effects (Repository Level) ---")
    rand_eff = results.get("random_effects", {})
    if rand_eff:
        print(f"Variance of Random Intercepts: {rand_eff.get('variance_intercept', 'N/A'):.6f}")
        print(f"Std Dev of Random Intercepts: {rand_eff.get('std_intercept', 'N/A'):.6f}")
        print(f"Intraclass Correlation (ICC): {rand_eff.get('icc', 'N/A'):.4f}")
        print(f"Interpretation: {rand_eff.get('interpretation', 'N/A')}")
    else:
        print("Could not extract random effects.")
    
    print("\n--- Fixed Effects (Associational Relationships) ---")
    print("(Note: Coefficients represent correlational associations, not causal effects)")
    print("-" * 80)
    print(f"{'Term':<40} {'Estimate':>10} {'Std Err':>10} {'Z-value':>10} {'P-value':>10}")
    print("-" * 80)
    
    for effect in results.get("fixed_effects", []):
        term = effect["term"]
        if len(term) > 38:
            term = term[:35] + "..."
        print(f"{term:<40} {effect['estimate']:>10.4f} {effect['std_err']:>10.4f} "
              f"{effect['z_value']:>10.4f} {effect['p_value']:>10.6f}")
    
    print("-" * 80)
    print("\nNote: This model examines the associational relationship between issue")
    print("characteristics and resolution time, accounting for the nested structure")
    print("of issues within repositories. Results should be interpreted as correlational.")
    print("="*80 + "\n")


def analyze_mixed_effects() -> Dict[str, Any]:
    """
    Main analysis function to run the full mixed-effects modeling pipeline.

    Returns:
        Dict[str, Any]: The complete results dictionary.
    """
    # Load data
    df = load_cleaned_data()
    
    # Prepare data
    df_prepared, _ = prepare_data_for_lme(df)
    
    # Fit model
    fitted_model = fit_mixed_effects_model(df_prepared)
    
    # Extract results
    results = extract_results(fitted_model)
    
    return results


def main() -> None:
    """
    Entry point for the mixed-effects model analysis.
    
    Executes the full pipeline: load data, fit model, extract results,
    save to JSON, and print summary.
    """
    config = get_config()
    set_seed(config.get('random_seed', 42))
    
    output_path = get_path(config, 'mixed_effects_results')
    
    try:
        logger.info("Starting Linear Mixed-Effects Model analysis...")
        
        # Run analysis
        results = analyze_mixed_effects()
        
        # Save results
        save_results(results, output_path)
        
        # Print summary to console
        print_summary(results)
        
        logger.info("Analysis completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()