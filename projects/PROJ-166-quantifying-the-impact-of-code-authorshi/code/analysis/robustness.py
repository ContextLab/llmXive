import os
import sys
import json
import logging
import warnings
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod.families import NegativeBinomial
from statsmodels.stats.outliers_influence import variance_inflation_factor

from config import ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/robustness.log')
    ]
)
logger = logging.getLogger(__name__)

def load_data() -> pd.DataFrame:
    """Load the merged dataset from data/processed/repo_metrics.csv."""
    input_path = Path("data/processed/repo_metrics.csv")
    if not input_path.exists():
        raise FileNotFoundError(f"Required input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def filter_zero_kloc(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out rows where kloc is 0 to avoid log(0) in offset."""
    initial_count = len(df)
    df = df[df['kloc'] > 0].copy()
    filtered_count = initial_count - len(df)
    if filtered_count > 0:
        logger.warning(f"Excluded {filtered_count} rows with kloc=0")
    return df

def calculate_shannon_entropy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Shannon entropy for author contributions.
    Assumes the dataframe has a column 'author_contributions' containing 
    a list of contribution counts or a string representation of such.
    If not present, we approximate entropy based on unique_authors and total_commits
    if available, or return a placeholder that will be handled by the model fitting.
    
    NOTE: In a real scenario, we would have a column with the distribution of 
    contributions per author. Here we assume 'unique_authors' and 'total_commits' 
    are available to approximate, or we use a synthetic distribution based on 
    unique_authors for demonstration if specific distribution data is missing.
    
    For this implementation, we assume the data has 'unique_authors' and we 
    generate a mock distribution to calculate entropy, as the exact distribution 
    isn't in the base 'repo_metrics.csv'. In a full implementation, this would 
    come from the git log analysis (T008).
    """
    df = df.copy()
    if 'author_contributions' in df.columns:
        # If we have the actual distribution, calculate entropy directly
        def calc_entropy_from_list(contribs):
            if isinstance(contribs, str):
                try:
                    contribs = eval(contribs) # Safe eval if stringified list
                except:
                    return 0.0
            if not contribs or sum(contribs) == 0:
                return 0.0
            probs = np.array(contribs) / sum(contribs)
            probs = probs[probs > 0]
            return -np.sum(probs * np.log2(probs))
        
        df['shannon_entropy'] = df['author_contributions'].apply(calc_entropy_from_list)
    else:
        # Fallback: Approximate entropy based on unique_authors assuming equal distribution
        # This is a simplification. Real entropy requires the actual distribution.
        # H = log2(N) for equal distribution of N authors.
        logger.warning("No 'author_contributions' column found. Approximating entropy as log2(unique_authors).")
        df['shannon_entropy'] = df['unique_authors'].apply(lambda x: np.log2(x) if x > 0 else 0.0)
    
    return df

def fit_negative_binomial_glm(df: pd.DataFrame, 
                              dependent_var: str = 'cve_count',
                              independent_vars: List[str] = ['unique_authors'],
                              offset_var: str = 'kloc',
                              use_entropy: bool = False) -> Dict[str, Any]:
    """
    Fit a Negative Binomial GLM.
    
    Args:
        df: DataFrame with data
        dependent_var: Name of the dependent variable column
        independent_vars: List of independent variable column names
        offset_var: Name of the offset variable column (will be log-transformed)
        use_entropy: If True, replace 'unique_authors' with 'shannon_entropy' in predictors
    
    Returns:
        Dictionary with model results (coefficients, p-values, etc.)
    """
    # Prepare data
    y = df[dependent_var].values
    
    # Handle independent variables
    X_cols = independent_vars.copy()
    if use_entropy:
        if 'unique_authors' in X_cols:
            X_cols.remove('unique_authors')
        X_cols.append('shannon_entropy')
    
    # Check for required columns
    missing_cols = [col for col in X_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns for X: {missing_cols}")
    
    X = df[X_cols].values
    
    # Add constant if not included in X_cols (usually not for GLM with offset)
    # But statsmodels GLM requires a constant for the intercept unless explicitly handled
    # We'll add a column of ones for the intercept
    X_with_const = sm.add_constant(X)
    
    # Offset: log(kloc)
    if offset_var not in df.columns:
        raise ValueError(f"Offset variable '{offset_var}' not found in dataframe")
    offset = np.log(df[offset_var].values)
    
    # Fit model
    try:
        model = GLM(y, X_with_const, family=NegativeBinomial(), offset=offset)
        results = model.fit()
        
        # Extract results
        coefficients = results.params.tolist()
        p_values = results.pvalues.tolist()
        std_errors = results.bse.tolist()
        conf_int = results.conf_int().values.tolist()
        
        # Map names to results
        var_names = ['intercept'] + X_cols
        result_dict = {
            "coefficients": {var_names[i]: coefficients[i] for i in range(len(var_names))},
            "p_values": {var_names[i]: p_values[i] for i in range(len(var_names))},
            "std_errors": {var_names[i]: std_errors[i] for i in range(len(var_names))},
            "confidence_intervals": {var_names[i]: conf_int[i] for i in range(len(var_names))},
            "convergence_status": results.converged,
            "model_type": "NegativeBinomial"
        }
        
        return result_dict
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        return {
            "coefficients": {},
            "p_values": {},
            "std_errors": {},
            "confidence_intervals": {},
            "convergence_status": False,
            "model_type": "NegativeBinomial",
            "error": str(e)
        }

def benjamini_hochberg(p_values: Dict[str, float]) -> Dict[str, float]:
    """
    Apply Benjamini-Hochberg correction to p-values.
    
    Args:
        p_values: Dictionary mapping variable names to p-values
    
    Returns:
        Dictionary mapping variable names to adjusted p-values
    """
    vars = list(p_values.keys())
    p_vals = list(p_values.values())
    
    # Sort p-values
    sorted_indices = np.argsort(p_vals)
    sorted_p = [p_vals[i] for i in sorted_indices]
    sorted_vars = [vars[i] for i in sorted_indices]
    
    n = len(p_vals)
    adjusted_p = []
    
    # BH procedure
    for i in range(n):
        rank = i + 1
        # Calculate adjusted p-value
        adj_p = sorted_p[i] * n / rank
        # Ensure it doesn't exceed 1.0 and is monotonic
        if adj_p > 1.0:
            adj_p = 1.0
        adjusted_p.append(adj_p)
    
    # Ensure monotonicity (cumulative min from the end)
    for i in range(n-2, -1, -1):
        adjusted_p[i] = min(adjusted_p[i], adjusted_p[i+1])
    
    # Map back to original order
    result = {}
    for i in range(n):
        result[sorted_vars[i]] = adjusted_p[i]
    
    return result

def extract_results(model_results: Dict[str, Any], 
                    adjusted_p_values: Dict[str, float]) -> Dict[str, Any]:
    """
    Format model results for JSON output.
    
    Args:
        model_results: Raw model results dictionary
        adjusted_p_values: Dictionary of adjusted p-values
    
    Returns:
        Formatted results dictionary
    """
    return {
        "coefficients": model_results["coefficients"],
        "p_values": model_results["p_values"],
        "adjusted_p_values": adjusted_p_values,
        "std_errors": model_results["std_errors"],
        "confidence_intervals": model_results["confidence_intervals"],
        "convergence_status": model_results.get("convergence_status", False),
        "model_type": model_results.get("model_type", "NegativeBinomial")
    }

def run_subsample_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run GLM analysis on subsamples by programming language.
    
    Args:
        df: Full dataframe
    
    Returns:
        Dictionary with results for each language subsample
    """
    results = {}
    
    # Get unique languages
    if 'language' not in df.columns:
        logger.warning("No 'language' column found. Skipping subsample analysis.")
        return results
    
    languages = df['language'].dropna().unique()
    logger.info(f"Performing subsample analysis for {len(languages)} languages: {languages}")
    
    for lang in languages:
        lang_df = df[df['language'] == lang].copy()
        
        # Filter zero kloc
        lang_df = filter_zero_kloc(lang_df)
        
        if len(lang_df) < 5:
            logger.warning(f"Insufficient data for language {lang} ({len(lang_df)} rows). Skipping.")
            continue
        
        logger.info(f"Fitting model for language: {lang} ({len(lang_df)} rows)")
        
        # Fit model with unique_authors
        model_res = fit_negative_binomial_glm(
            lang_df,
            dependent_var='cve_count',
            independent_vars=['unique_authors', 'project_age', 'release_count'],
            offset_var='kloc',
            use_entropy=False
        )
        
        # Apply BH correction
        adj_p = benjamini_hochberg(model_res["p_values"])
        
        results[lang] = extract_results(model_res, adj_p)
    
    return results

def run_entropy_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run GLM analysis using Shannon entropy as the diversity metric.
    
    Args:
        df: Full dataframe
    
    Returns:
        Dictionary with entropy model results
    """
    logger.info("Performing entropy-based analysis")
    
    # Calculate entropy
    df_with_entropy = calculate_shannon_entropy(df)
    
    # Filter zero kloc
    df_with_entropy = filter_zero_kloc(df_with_entropy)
    
    if len(df_with_entropy) < 10:
        logger.warning(f"Insufficient data for entropy analysis ({len(df_with_entropy)} rows).")
        return {}
    
    logger.info(f"Fitting entropy model with {len(df_with_entropy)} rows")
    
    # Fit model with shannon_entropy instead of unique_authors
    model_res = fit_negative_binomial_glm(
        df_with_entropy,
        dependent_var='cve_count',
        independent_vars=['shannon_entropy', 'project_age', 'release_count'],
        offset_var='kloc',
        use_entropy=True
    )
    
    # Apply BH correction
    adj_p = benjamini_hochberg(model_res["p_values"])
    
    return extract_results(model_res, adj_p)

def main():
    """
    Main function to run robustness checks and generate the final JSON output.
    """
    logger.info("Starting robustness analysis (T024)")
    
    # Ensure directories exist
    ensure_directories()
    
    # Load data
    df = load_data()
    
    # Run subsample analysis
    subsample_results = run_subsample_analysis(df)
    
    # Run entropy analysis
    entropy_results = run_entropy_analysis(df)
    
    # Compile final results
    final_results = {
        "subsample_analysis": subsample_results,
        "entropy_analysis": entropy_results,
        "metadata": {
            "total_repos_analyzed": len(df),
            "languages_processed": list(subsample_results.keys()),
            "timestamp": pd.Timestamp.now().isoformat()
        }
    }
    
    # Write output
    output_path = Path("data/processed/robustness_results.json")
    with open(output_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Robustness results written to {output_path}")
    print(f"Success: Generated {output_path}")

if __name__ == "__main__":
    main()
