import numpy as np
from scipy import stats
from typing import List, Tuple, Dict, Any, Optional
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import pandas as pd
import os

def clopper_pearson_ci(successes: int, trials: int, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate the Clopper-Pearson exact confidence interval for a binomial proportion.
    
    Args:
        successes: Number of successes (significant results under null).
        trials: Total number of trials (replications).
        alpha: Significance level for the confidence interval (default 0.05 for 95% CI).
    
    Returns:
        Tuple (lower_bound, upper_bound) for the confidence interval.
    """
    if trials == 0:
        return (0.0, 0.0)
    
    lower = stats.beta.ppf(alpha / 2, successes, trials - successes + 1)
    upper = stats.beta.ppf(1 - alpha / 2, successes + 1, trials - successes)
    
    # Handle edge cases where ppf might return NaN or out of bounds
    lower = 0.0 if np.isnan(lower) else lower
    upper = 1.0 if np.isnan(upper) else upper
    
    return (lower, upper)

def calculate_type1_error(p_values: List[float], alpha: float = 0.05) -> float:
    """
    Calculate the observed Type I error rate from a list of p-values.
    
    Args:
        p_values: List of p-values from hypothesis tests where the null is true.
        alpha: Nominal significance level.
    
    Returns:
        Observed error rate (proportion of p-values < alpha).
    """
    if not p_values:
        return 0.0
    return sum(1 for p in p_values if p < alpha) / len(p_values)

def calculate_power(p_values: List[float], alpha: float = 0.05) -> float:
    """
    Calculate the observed statistical power from a list of p-values.
    
    Args:
        p_values: List of p-values from hypothesis tests where the alternative is true.
        alpha: Nominal significance level.
    
    Returns:
        Observed power (proportion of p-values < alpha).
    """
    if not p_values:
        return 0.0
    return sum(1 for p in p_values if p < alpha) / len(p_values)

def calculate_chi_squared_error_rate(p_values: List[float], alpha: float = 0.05) -> float:
    """
    Calculate Type I error rate specifically for Chi-squared tests.
    Logic is identical to standard Type I error but semantically distinct for reporting.
    
    Args:
        p_values: List of p-values.
        alpha: Nominal significance level.
    
    Returns:
        Observed error rate.
    """
    return calculate_type1_error(p_values, alpha)

def aggregate_chi_squared_results(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Aggregate Chi-squared simulation results into a DataFrame.
    
    Args:
        results: List of dictionaries containing simulation results.
    
    Returns:
        Aggregated pandas DataFrame.
    """
    return pd.DataFrame(results)

def train_logistic_model(data: pd.DataFrame, target_col: str = 'error_rate', 
                         feature_cols: Optional[List[str]] = None) -> LogisticRegression:
    """
    Train a logistic regression model to predict error rate probability from dependency strength.
    
    Args:
        data: DataFrame containing features and target.
        target_col: Name of the column containing the error rate (0 or 1 or probability).
        feature_cols: List of feature column names (e.g., ['dependency_strength']).
    
    Returns:
        Trained LogisticRegression model.
    """
    if feature_cols is None:
        feature_cols = ['dependency_strength']
    
    X = data[feature_cols].values
    # If target is a rate (0-1), we need to treat it as a probability or convert to binary
    # For logistic regression in sklearn, we usually expect binary 0/1 or sample weights.
    # If 'error_rate' is a proportion from many trials, we might use sample_weight or binomial logic.
    # Here we assume the data passed is aggregated per r, so we treat the rate as the target probability.
    # However, sklearn's LogisticRegression expects binary labels or counts.
    # To fit a curve to rates, we can use the rate as the target and use class_weight or 
    # simply fit on the rate as a continuous target (which is technically linear regression).
    # But the task asks for a Logistic Regression model. 
    # Standard approach for rate data in logistic regression: use counts of successes/trials.
    # If the data only has the rate, we might need to simulate the binary outcomes or use a specific solver.
    # Given the context of "relating error rate to dependency strength", we will fit a model
    # where we predict the probability of error. 
    
    # If the input data is aggregated (one row per r), we can't easily fit a binary classifier 
    # without the raw counts. We will assume the data passed here is either:
    # 1. Raw binary outcomes (0/1) per replication.
    # 2. Or we treat the rate as a continuous target for a generalized linear model (GLM) approach,
    #    but sklearn's LogisticRegression is for classification.
    
    # Let's assume the 'data' passed here contains the raw binary outcomes if possible,
    # or we construct a synthetic binary dataset based on the rate for the purpose of the model
    # if only aggregated rates are available. However, the most robust way is to use the raw p-values.
    # Since this function signature takes a DataFrame, we assume it's the raw data or aggregated counts.
    # If aggregated counts are present (e.g., 'successes', 'trials'), we use them.
    # If only 'error_rate' exists, we will generate synthetic binary labels based on the rate to fit the curve.
    
    if 'successes' in data.columns and 'trials' in data.columns:
        # Expand to binary labels
        y = []
        for _, row in data.iterrows():
            y.extend([1] * int(row['successes']) + [0] * int(row['trials'] - row['successes']))
        y = np.array(y)
        # Repeat features for each sample
        X_expanded = []
        for _, row in data.iterrows():
            X_expanded.extend([row[feature_cols]] * int(row['trials']))
        X = np.vstack(X_expanded)
    else:
        # Fallback: If we only have rates, we treat the rate as the target probability
        # and fit a model that minimizes cross-entropy loss on the rates (using sample_weight logic implicitly
        # by duplicating rows or just fitting on the rate as a continuous approximation if needed).
        # For strict sklearn LogisticRegression, we need binary y.
        # We will create a pseudo-dataset: for each row, generate N samples based on the rate.
        y = []
        X_expanded = []
        for _, row in data.iterrows():
            rate = row[target_col]
            count = 100 # Arbitrary sample size for fitting the curve shape
            labels = np.random.binomial(1, rate, count)
            y.extend(labels)
            X_expanded.extend([row[feature_cols]] * count)
        y = np.array(y)
        X = np.vstack(X_expanded)

    model = LogisticRegression(max_iter=1000, solver='lbfgs')
    model.fit(X, y)
    return model

def save_logistic_model(model: LogisticRegression, filepath: str) -> None:
    """Save the trained logistic model to a pickle file."""
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)

def load_logistic_model(filepath: str) -> LogisticRegression:
    """Load a logistic model from a pickle file."""
    with open(filepath, 'rb') as f:
        return pickle.load(f)

def verify_trend_monotonicity(df: pd.DataFrame, 
                              strength_col: str = 'dependency_strength', 
                              error_col: str = 'observed_error_rate',
                              alpha: float = 0.05) -> Tuple[bool, float, float]:
    """
    Calculate Spearman rank correlation to verify monotonic increase of error rates with dependency strength.
    
    This function implements the trend verification logic required by US-1 AC-2.
    
    Args:
        df: DataFrame containing simulation results (e.g., from results/aggregated.csv).
            Must contain columns for dependency strength and observed error rate.
        strength_col: Name of the column containing dependency strength values (r).
        error_col: Name of the column containing observed error rates.
        alpha: Significance level for the trend test.
    
    Returns:
        Tuple (is_monotonic, correlation_coefficient, p_value)
        is_monotonic: True if correlation > 0 and p < alpha.
        correlation_coefficient: Spearman's rho.
        p_value: P-value for the correlation test.
    """
    # Ensure data is sorted by strength for consistent interpretation, though Spearman handles rank
    df_sorted = df.sort_values(by=strength_col)
    
    x = df_sorted[strength_col].values
    y = df_sorted[error_col].values
    
    # Remove NaNs if any
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        return False, 0.0, 1.0
    
    # Calculate Spearman rank correlation
    correlation, p_value = stats.spearmanr(x_clean, y_clean)
    
    # Check for positive monotonic trend
    is_monotonic = (correlation > 0) and (p_value < alpha)
    
    return is_monotonic, correlation, p_value

def calculate_power_delta(power_baseline: float, power_dependency: float) -> float:
    """
    Calculate the percentage reduction in power between baseline (r=0) and dependency (r>0).
    
    Args:
        power_baseline: Power at r=0.
        power_dependency: Power at r > 0.
    
    Returns:
        Percentage reduction in power.
    """
    if power_baseline == 0:
        return 0.0
    return ((power_baseline - power_dependency) / power_baseline) * 100.0

def update_aggregated_with_trend(input_path: str, output_path: str) -> None:
    """
    Reads the aggregated CSV, calculates the trend test, and adds a 'trend_status' column.
    
    Args:
        input_path: Path to results/aggregated.csv.
        output_path: Path to save the updated results/aggregated.csv.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Determine columns dynamically if names differ, but assume standard names from T013
    strength_col = 'dependency_strength'
    error_col = 'observed_error_rate'
    
    # Check if columns exist
    if strength_col not in df.columns or error_col not in df.columns:
        # Try to find similar columns
        available_cols = df.columns.tolist()
        raise KeyError(f"Required columns '{strength_col}' and/or '{error_col}' not found in {input_path}. Available: {available_cols}")
    
    is_monotonic, corr, p_val = verify_trend_monotonicity(df, strength_col, error_col)
    
    # Add the status to the dataframe
    # The task asks for a 'trend_status' column. We will store the boolean result or a string description.
    # Let's store a string for clarity: "Monotonic Increase (p < 0.05)" or similar.
    if is_monotonic:
        status = "Monotonic Increase (p < 0.05)"
    else:
        status = f"No Monotonic Trend (rho={corr:.3f}, p={p_val:.3f})"
    
    # Since the trend is a property of the whole dataset (across r values), 
    # we might add this as a constant column or just the boolean.
    # The task says "Output `trend_status` column".
    df['trend_status'] = status
    
    # Also add the metrics for verification
    df['trend_correlation'] = corr
    df['trend_p_value'] = p_val
    
    df.to_csv(output_path, index=False)
    print(f"Trend verification complete. Updated file saved to {output_path}")
    print(f"Trend Status: {status}")
    print(f"Correlation: {corr:.4f}, P-value: {p_val:.4f}")

if __name__ == "__main__":
    # Simple test if run directly
    print("metrics.py loaded successfully.")
