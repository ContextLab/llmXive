"""
Analysis module for Gut Microbiome and Cognitive Performance correlation study.
Implements Spearman correlation, multivariate regression, and Lasso regression.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
import pickle

from config import INPUT_PATHS, RANDOM_SEED, SAMPLE_LIMIT, DQS_REQUIRED, ensure_directories
from logging_config import get_logger, log_provenance, log_warning, log_imputation_strategy, log_data_filtering, log_pipeline_start, log_pipeline_end
from diversity import calculate_shannon_index
from transformation import apply_clr
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.linear_model import Lasso, LassoCV
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from scipy.stats import shapiro

logger = get_logger(__name__)

# Global variables to store intermediate results for T029b
_lasso_coefficients = None
_lasso_non_zero_count = 0
_lasso_metrics = {}

def load_processed_data() -> pd.DataFrame:
    """Loads the cleaned data from data/processed/cleaned_data.csv"""
    path = "data/processed/cleaned_data.csv"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Cleaned data not found at {path}. Run ingestion pipeline first.")
    df = pd.read_csv(path)
    return df

def check_zero_variance(df: pd.DataFrame, column: str) -> bool:
    """Checks if a column has zero variance."""
    if column not in df.columns:
        raise ValueError(f"Column {column} not found in dataframe")
    var = df[column].var()
    return var < 1e-9

def log_zero_variance_warning(column: str) -> None:
    """Logs a warning for zero variance."""
    log_warning(f"Zero variance in {column}; skipping correlation.")
    # Save to analysis_warnings.log as per T025c
    warning_path = "data/processed/analysis_warnings.log"
    with open(warning_path, 'a') as f:
        f.write(f"Warning: Zero variance in {column}; skipping correlation.\n")

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """Calculates VIF for all predictors and logs warnings."""
    vif_data = {}
    X = df[predictors].dropna()
    if X.empty:
        return vif_data
    
    # Add constant for intercept
    X_const = sm.add_constant(X)
    
    for col in X.columns:
        try:
            vif = variance_inflation_factor(X_const.values, X_const.columns.get_loc(col))
            vif_data[col] = vif
            if vif > 5:
                log_warning(f"High multicollinearity detected: {col} has VIF {vif:.2f}")
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_data[col] = np.nan
    
    return vif_data

def save_vif_results(vif_data: Dict[str, float], path: str = "data/processed/vif_results.json") -> None:
    """Saves VIF results to JSON."""
    ensure_directories()
    import json
    with open(path, 'w') as f:
        json.dump(vif_data, f, indent=2)
    log_provenance(f"VIF results saved to {path}")

def compute_spearman_correlation(df: pd.DataFrame, x_col: str, y_col: str) -> Tuple[float, float, int]:
    """Computes Spearman correlation between two columns."""
    # Check for integer/raw counts validation for Shannon if applicable
    if x_col == "shannon_index":
        # T020b: Verify input is raw counts (integers) if this were taxa, but Shannon is float.
        # However, we must ensure we are not using CLR-transformed Shannon if that were a mistake.
        # The spec says Shannon is calculated on raw counts, so the resulting column is float.
        pass
    
    if df[x_col].var() < 1e-9 or df[y_col].var() < 1e-9:
        raise ValueError("Zero variance in one of the columns")

    r_value, p_value = stats.spearmanr(df[x_col], df[y_col])
    n_obs = len(df)
    return r_value, p_value, n_obs

def save_correlation_results(r_value: float, p_value: float, n_obs: int, path: str = "data/processed/correlation_results.csv") -> None:
    """Saves correlation results to CSV."""
    ensure_directories()
    df = pd.DataFrame({
        "r_value": [r_value],
        "p_value": [p_value],
        "n_obs": [n_obs]
    })
    df.to_csv(path, index=False)
    log_provenance(f"Correlation results saved to {path}")

def run_multivariate_regression(df: pd.DataFrame) -> sm.OLSResults:
    """Runs multivariate linear regression (Primary Path)."""
    # Formula: fluid_intelligence ~ shannon_index + age + C(sex) + bmi + dqs
    # Handle missing DQS
    predictors = ["shannon_index", "age", "bmi"]
    if "sex" in df.columns:
        predictors.append("sex")
    
    if DQS_REQUIRED and "dqs" not in df.columns:
        raise ValueError("DQS is required but missing from data")
    elif "dqs" in df.columns:
        predictors.append("dqs")
    elif not DQS_REQUIRED:
        log_warning("DQS column missing but not required; proceeding without DQS.")

    formula = f"fluid_intelligence ~ {' + '.join(predictors)}"
    # Handle categorical variables
    if "sex" in df.columns:
        formula = formula.replace("sex", "C(sex)")

    model = sm.formula.ols(formula=formula, data=df)
    results = model.fit()
    return results

def save_regression_results(results: sm.OLSResults, path: str = "data/processed/regression_results.csv") -> None:
    """Saves regression results to CSV."""
    ensure_directories()
    df = pd.DataFrame({
        "coefficient": results.params,
        "std_err": results.bse,
        "p_value": results.pvalues
    })
    df.to_csv(path)
    log_provenance(f"Regression results saved to {path}")

def perform_residual_normality_validation(results: sm.OLSResults, path: str = "data/processed/regression_diagnostics.json") -> bool:
    """Performs Shapiro-Wilk test on residuals."""
    residuals = results.resid
    stat, p_value = shapiro(residuals)
    
    is_normal = p_value > 0.05
    report = {
        "test": "Shapiro-Wilk",
        "statistic": float(stat),
        "p_value": float(p_value),
        "is_normal": is_normal
    }
    
    ensure_directories()
    import json
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    
    if not is_normal:
        log_warning("Residuals are not normally distributed (Shapiro-Wilk p <= 0.05)")
    
    return is_normal

def run_lasso_regression(df: pd.DataFrame) -> None:
    """
    Runs Lasso regression (Secondary Path) on CLR-transformed taxa.
    Stores results in global variables for T029b to save.
    """
    global _lasso_coefficients, _lasso_non_zero_count, _lasso_metrics

    # Identify taxa columns (assume they end with '_abundance' or are not in known non-taxon list)
    # For this implementation, we assume the dataframe contains CLR-transformed taxa columns.
    # In a real scenario, these would be identified dynamically.
    # We will select columns that are numeric and not the target or standard covariates.
    exclude_cols = ['fluid_intelligence', 'shannon_index', 'age', 'sex', 'bmi', 'dqs', 'participant_id']
    taxa_cols = [col for col in df.select_dtypes(include=[np.number]).columns if col not in exclude_cols]
    
    if not taxa_cols:
        log_warning("No taxa columns found for Lasso regression. Skipping.")
        return

    X = df[taxa_cols].fillna(0) # Handle any remaining NaNs
    y = df['fluid_intelligence']

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Use LassoCV for alpha selection
    lasso_cv = LassoCV(cv=5, random_state=RANDOM_SEED, max_iter=10000)
    lasso_cv.fit(X_scaled, y)

    # Get coefficients
    coefs = lasso_cv.coef_
    
    # Create a DataFrame for coefficients
    coef_dict = {col: coef for col, coef in zip(taxa_cols, coefs)}
    _lasso_coefficients = pd.Series(coef_dict)
    _lasso_non_zero_count = int(np.sum(coefs != 0))

    # Calculate metrics
    y_pred = lasso_cv.predict(X_scaled)
    r2 = r2_score(y, y_pred)
    mse = mean_squared_error(y, y_pred)
    
    _lasso_metrics = {
        "r2": float(r2),
        "mse": float(mse),
        "alpha": float(lasso_cv.alpha_)
    }

    # Save temp file for T029b to read
    temp_path = Path("data/processed/.lasso_temp_results.pkl")
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_path, 'wb') as f:
        pickle.dump({
            'coefficients': _lasso_coefficients,
            'non_zero_count': _lasso_non_zero_count,
            'metrics': _lasso_metrics
        }, f)
    
    log_provenance(f"Lasso regression completed. Non-zero features: {_lasso_non_zero_count}")

def run_analysis_pipeline() -> None:
    """Runs the full analysis pipeline."""
    log_pipeline_start("Analysis Pipeline")
    
    df = load_processed_data()
    
    # Check zero variance
    if check_zero_variance(df, 'fluid_intelligence'):
        log_zero_variance_warning('fluid_intelligence')
        log_pipeline_end("Analysis Pipeline (Skipped due to zero variance)")
        return

    # Correlation
    r, p, n = compute_spearman_correlation(df, 'shannon_index', 'fluid_intelligence')
    save_correlation_results(r, p, n)

    # Regression
    reg_results = run_multivariate_regression(df)
    save_regression_results(reg_results)
    
    # VIF
    predictors = [col for col in reg_results.params.index if col != 'Intercept']
    vif_data = calculate_vif(df, predictors)
    save_vif_results(vif_data)

    # Residual Validation
    perform_residual_normality_validation(reg_results)

    # Lasso (Secondary Path)
    run_lasso_regression(df)

    log_pipeline_end("Analysis Pipeline")

def main() -> None:
    run_analysis_pipeline()

def main():
    run_analysis_pipeline()

if __name__ == "__main__":
    main()