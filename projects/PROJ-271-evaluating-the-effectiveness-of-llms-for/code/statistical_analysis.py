import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from config import get_data_path, get_processed_path, get_results_path, setup_logging

logger = setup_logging(__name__)

def load_static_baseline() -> pd.DataFrame:
    """Load the static baseline data from CSV."""
    path = get_data_path() / "static_baseline.csv"
    if not path.exists():
        raise FileNotFoundError(f"Static baseline not found at {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded static baseline with {len(df)} rows")
    return df

def load_semantic_results() -> pd.DataFrame:
    """Load the semantic analysis results from JSON."""
    path = get_processed_path() / "semantic_results.json"
    if not path.exists():
        raise FileNotFoundError(f"Semantic results not found at {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Convert list of dicts to DataFrame
    df = pd.DataFrame(data)
    logger.info(f"Loaded semantic results with {len(df)} rows")
    return df

def merge_datasets() -> pd.DataFrame:
    """Merge static baseline and semantic results on code content."""
    static_df = load_static_baseline()
    semantic_df = load_semantic_results()
    
    # Ensure code columns are comparable (strip whitespace)
    static_df['code'] = static_df['code'].astype(str).str.strip()
    semantic_df['code'] = semantic_df['code'].astype(str).str.strip()
    
    # Merge on code content
    merged = pd.merge(static_df, semantic_df, on='code', how='inner')
    logger.info(f"Merged dataset has {len(merged)} rows")
    return merged

def validate_merged_dataset(df: pd.DataFrame) -> Tuple[bool, str]:
    """Validate that the merged dataset has sufficient completeness."""
    required_cols = ['code', 'loc', 'cyclomatic_complexity', 'nesting_depth', 
                    'static_smell_labels', 'semantic_vector', 'llm_smell_labels']
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return False, f"Missing required columns: {missing_cols}"
    
    # Check for non-null values in key columns
    for col in ['loc', 'cyclomatic_complexity', 'semantic_vector', 'llm_smell_labels']:
        if df[col].isnull().sum() > 0:
            logger.warning(f"Column {col} has {df[col].isnull().sum()} null values")
    
    completeness = (1 - df.isnull().any(axis=1).sum() / len(df)) * 100
    if completeness < 95:
        return False, f"Dataset completeness is {completeness:.2f}%, below 95% threshold"
    
    return True, f"Dataset validation passed with {completeness:.2f}% completeness"

def run_mcnemar_test(static_labels: List[str], llm_labels: List[str]) -> Dict[str, float]:
    """
    Perform McNemar's test for paired nominal data.
    
    Args:
        static_labels: List of boolean detection outcomes from static analysis
        llm_labels: List of boolean detection outcomes from LLM analysis
        
    Returns:
        Dictionary with chi2 statistic and p-value
    """
    # Create a 2x2 contingency table
    # Rows: Static (Yes/No), Cols: LLM (Yes/No)
    table = np.zeros((2, 2), dtype=int)
    
    for s, l in zip(static_labels, llm_labels):
        s_idx = 1 if s else 0
        l_idx = 1 if l else 0
        table[s_idx, l_idx] += 1
    
    # McNemar's test
    # chi2 = (|b - c| - 1)^2 / (b + c) where b and c are discordant pairs
    b = table[0, 1]  # Static No, LLM Yes
    c = table[1, 0]  # Static Yes, LLM No
    
    if b + c == 0:
        return {"chi2": 0.0, "p_value": 1.0, "note": "No discordant pairs"}
    
    chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    p_value = 1 - stats.chi2.cdf(chi2, df=1)
    
    return {"chi2": float(chi2), "p_value": float(p_value)}

def run_mcnemar_test_with_bootstrap(
    static_labels: List[str], 
    llm_labels: List[str], 
    n_bootstrap: int = 1000, 
    seed: int = 42
) -> Dict[str, Any]:
    """
    Perform McNemar's test with bootstrap confidence intervals.
    
    Args:
        static_labels: List of boolean detection outcomes
        llm_labels: List of boolean detection outcomes
        n_bootstrap: Number of bootstrap iterations
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary with test statistics and confidence intervals
    """
    np.random.seed(seed)
    n = len(static_labels)
    chi2_values = []
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(n, size=n, replace=True)
        s_resampled = [static_labels[i] for i in indices]
        l_resampled = [llm_labels[i] for i in indices]
        
        result = run_mcnemar_test(s_resampled, l_resampled)
        if "p_value" in result and result.get("note") != "No discordant pairs":
            chi2_values.append(result["chi2"])
    
    # Calculate statistics
    original_result = run_mcnemar_test(static_labels, llm_labels)
    
    if chi2_values:
        ci_lower = np.percentile(chi2_values, 2.5)
        ci_upper = np.percentile(chi2_values, 97.5)
        mean_chi2 = np.mean(chi2_values)
    else:
        ci_lower = ci_upper = mean_chi2 = original_result["chi2"]
    
    return {
        "original_chi2": original_result["chi2"],
        "original_p_value": original_result["p_value"],
        "bootstrap_mean_chi2": float(mean_chi2),
        "bootstrap_ci_95": [float(ci_lower), float(ci_upper)],
        "n_bootstrap": n_bootstrap
    }

def calculate_vif(df: pd.DataFrame, predictor_cols: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for each predictor.
    
    Args:
        df: DataFrame containing the predictors
        predictor_cols: List of column names to calculate VIF for
        
    Returns:
        Dictionary mapping predictor names to VIF scores
    """
    # Filter to only numeric columns that exist
    available_cols = [col for col in predictor_cols if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    if len(available_cols) < 2:
        logger.warning("Not enough predictors for VIF calculation")
        return {}
    
    # Create design matrix with constant
    X = df[available_cols].dropna()
    if len(X) < 2:
        return {}
    
    X = add_constant(X)
    
    vif_scores = {}
    for i, col in enumerate(X.columns):
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_scores[col] = float(vif)
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
    
    return vif_scores

def fit_logistic_regression(
    df: pd.DataFrame, 
    predictors: List[str], 
    outcome_col: str = 'llm_detected',
    vif_threshold: float = 5.0
) -> Dict[str, Any]:
    """
    Fit a logistic regression model with VIF-based predictor exclusion.
    
    Args:
        df: DataFrame with predictors and outcome
        predictors: Initial list of predictor columns
        outcome_col: Name of the outcome variable column
        vif_threshold: VIF threshold for exclusion
        
    Returns:
        Dictionary with model results, VIF scores, and exclusion history
    """
    result = {
        "initial_predictors": predictors,
        "vif_scores": {},
        "exclusion_history": [],
        "final_predictors": [],
        "coefficients": {},
        "intercept": None,
        "residualization_applied": []
    }
    
    # Create a copy of the dataframe
    working_df = df.copy()
    
    # Ensure outcome is binary
    if outcome_col not in working_df.columns:
        # Create a simple binary outcome from LLM labels if not present
        working_df[outcome_col] = working_df['llm_smell_labels'].apply(
            lambda x: 1 if x and len(str(x).strip()) > 0 else 0
        )
    
    current_predictors = [p for p in predictors if p in working_df.columns]
    result["initial_predictors"] = current_predictors[:]
    
    # Iterative VIF calculation and exclusion
    max_iterations = len(current_predictors)
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Calculate VIF for current predictors
        vif_scores = calculate_vif(working_df, current_predictors)
        result["vif_scores"] = vif_scores
        
        if not vif_scores:
            break
        
        # Check for high VIF
        high_vif_predictors = {k: v for k, v in vif_scores.items() if v >= vif_threshold}
        
        if not high_vif_predictors:
            # No more exclusions needed
            result["final_predictors"] = current_predictors
            break
        
        # Find predictor with highest VIF
        max_vif_predictor = max(high_vif_predictors, key=high_vif_predictors.get)
        max_vif_value = high_vif_predictors[max_vif_predictor]
        
        # Record exclusion step
        result["exclusion_history"].append({
            "iteration": iteration,
            "excluded_predictor": max_vif_predictor,
            "vif_value": max_vif_value,
            "remaining_predictors": [p for p in current_predictors if p != max_vif_predictor]
        })
        
        logger.info(f"Iteration {iteration}: Excluding {max_vif_predictor} (VIF={max_vif_value:.2f})")
        
        # Exclude the predictor
        current_predictors.remove(max_vif_predictor)
        
        if not current_predictors:
            break
    
    # Fit the final model with remaining predictors
    if current_predictors:
        X = working_df[current_predictors].dropna()
        y = working_df.loc[X.index, outcome_col]
        
        if len(X) > 0 and len(y) > 0:
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Fit logistic regression
            model = LogisticRegression(max_iter=1000, random_state=42)
            model.fit(X_scaled, y)
            
            result["coefficients"] = {
                pred: float(coeff) for pred, coeff in zip(current_predictors, model.coef_[0])
            }
            result["intercept"] = float(model.intercept_[0])
            result["final_predictors"] = current_predictors
            result["model_score"] = float(model.score(X_scaled, y))
    
    return result

def run_sensitivity_analysis(
    df: pd.DataFrame, 
    loc_thresholds: List[int] = [50, 100, 150],
    outcome_col: str = 'llm_detected'
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by sweeping LOC thresholds.
    
    Args:
        df: DataFrame with LOC and detection outcomes
        loc_thresholds: List of LOC thresholds to test
        outcome_col: Name of the outcome variable
        
    Returns:
        Dictionary with sensitivity metrics for each threshold
    """
    results = {}
    
    # Ensure outcome is binary
    if outcome_col not in df.columns:
        df[outcome_col] = df['llm_smell_labels'].apply(
            lambda x: 1 if x and len(str(x).strip()) > 0 else 0
        )
    
    for threshold in loc_thresholds:
        # Static detection based on LOC threshold
        static_detection = (df['loc'] >= threshold).astype(int)
        llm_detection = df[outcome_col]
        
        # Calculate confusion matrix components
        tp = ((static_detection == 1) & (llm_detection == 1)).sum()
        fp = ((static_detection == 1) & (llm_detection == 0)).sum()
        tn = ((static_detection == 0) & (llm_detection == 0)).sum()
        fn = ((static_detection == 0) & (llm_detection == 1)).sum()
        
        # Calculate rates
        total_positive = tp + fn
        total_negative = tn + fp
        
        sensitivity = tp / total_positive if total_positive > 0 else 0
        specificity = tn / total_negative if total_negative > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        f1 = 2 * (precision * sensitivity) / (precision + sensitivity) if (precision + sensitivity) > 0 else 0
        
        # False positive and false negative rates
        fpr = fp / total_negative if total_negative > 0 else 0
        fnr = fn / total_positive if total_positive > 0 else 0
        
        results[str(threshold)] = {
            "threshold": threshold,
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn),
            "sensitivity": float(sensitivity),
            "specificity": float(specificity),
            "precision": float(precision),
            "f1_score": float(f1),
            "false_positive_rate": float(fpr),
            "false_negative_rate": float(fnr)
        }
    
    return results

def run_statistical_analysis() -> Dict[str, Any]:
    """
    Main function to run the full statistical analysis pipeline.
    
    Returns:
        Dictionary containing all analysis results
    """
    logger.info("Starting statistical analysis pipeline...")
    
    # Load and merge data
    merged_df = merge_datasets()
    is_valid, validation_msg = validate_merged_dataset(merged_df)
    logger.info(validation_msg)
    
    if not is_valid:
        logger.warning("Dataset validation failed, proceeding with caution")
    
    # Prepare data for analysis
    # Create binary outcome variable
    merged_df['llm_detected'] = merged_df['llm_smell_labels'].apply(
        lambda x: 1 if x and len(str(x).strip()) > 0 else 0
    )
    merged_df['static_detected'] = merged_df['static_smell_labels'].apply(
        lambda x: 1 if x and len(str(x).strip()) > 0 else 0
    )
    
    # Calculate semantic mean
    if 'semantic_vector' in merged_df.columns:
        merged_df['semantic_mean'] = merged_df['semantic_vector'].apply(
            lambda x: np.mean(eval(x)) if isinstance(x, str) else np.mean(x)
        )
    
    # Run McNemar's test per smell category (simplified for overall detection)
    mcnemar_result = run_mcnemar_test_with_bootstrap(
        merged_df['static_detected'].tolist(),
        merged_df['llm_detected'].tolist()
    )
    
    # Calculate VIF and fit logistic regression
    predictors = ['loc', 'cyclomatic_complexity', 'semantic_mean']
    vif_regression_result = fit_logistic_regression(
        merged_df, 
        predictors, 
        outcome_col='llm_detected',
        vif_threshold=5.0
    )
    
    # Run sensitivity analysis
    sensitivity_results = run_sensitivity_analysis(
        merged_df, 
        loc_thresholds=[50, 100, 150],
        outcome_col='llm_detected'
    )
    
    # Compile all results
    all_results = {
        "mcnemar_test": mcnemar_result,
        "logistic_regression": vif_regression_result,
        "sensitivity_analysis": sensitivity_results,
        "dataset_info": {
            "total_rows": len(merged_df),
            "validation_message": validation_msg
        }
    }
    
    logger.info("Statistical analysis pipeline completed.")
    return all_results

def main():
    """Main entry point for statistical analysis."""
    logger.info("Running statistical analysis...")
    
    try:
        results = run_statistical_analysis()
        
        # Save results
        results_path = get_results_path() / "statistical_significance.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to {results_path}")
        print(f"Statistical analysis completed. Results saved to {results_path}")
        
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
