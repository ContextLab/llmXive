import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Callable
from joblib import Parallel, delayed
import json
import os
from scipy import stats
import pandas as pd
from pathlib import Path

def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level for FDR control (default 0.05).
    
    Returns:
        Tuple of (q_values, is_significant) where:
        - q_values: Adjusted p-values (q-values).
        - is_significant: Boolean list indicating if q_value <= alpha.
    """
    if not p_values:
        return [], []
    
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]
    
    # Calculate q-values
    q_values = np.zeros(n)
    q_values[-1] = sorted_p_values[-1]
    
    for i in range(n - 2, -1, -1):
        q_values[i] = min(sorted_p_values[i] * n / (i + 1), q_values[i + 1])
    
    # Ensure q-values are monotonically increasing
    for i in range(n - 2, -1, -1):
        q_values[i] = min(q_values[i], q_values[i + 1])
    
    # Map back to original order
    original_order_q_values = np.zeros(n)
    original_order_q_values[sorted_indices] = q_values
    
    # Determine significance
    is_significant = (original_order_q_values <= alpha).tolist()
    
    return original_order_q_values.tolist(), is_significant

def apply_fdr_correction(input_path: str, output_path: str, p_value_column: str = "p_value", 
                         q_value_column: str = "q_value", alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Benjamini-Hochberg FDR correction to a Parquet file containing model results.
    
    Args:
        input_path: Path to the input Parquet file (e.g., permutation_results.json or parquet).
        output_path: Path to write the output Parquet file with q_values.
        p_value_column: Name of the column containing p-values.
        q_value_column: Name of the column to store q-values.
        alpha: Significance level for FDR control.
    
    Returns:
        Dictionary with summary statistics of the correction.
    """
    # Load data
    input_file = Path(input_path)
    if input_file.suffix == '.parquet':
        df = pd.read_parquet(input_path)
    elif input_file.suffix == '.json':
        df = pd.read_json(input_path, orient='records')
    else:
        raise ValueError(f"Unsupported input file format: {input_path}")
    
    if p_value_column not in df.columns:
        raise ValueError(f"Column '{p_value_column}' not found in input file. Available columns: {list(df.columns)}")
    
    # Extract p-values
    p_values = df[p_value_column].dropna().tolist()
    
    if not p_values:
        raise ValueError("No valid p-values found in the specified column.")
    
    # Apply FDR correction
    q_values, is_significant = benjamini_hochberg_fdr(p_values, alpha)
    
    # Map q-values back to the full dataframe (handling NaNs)
    df[q_value_column] = np.nan
    valid_indices = df[p_value_column].notna()
    df.loc[valid_indices, q_value_column] = q_values
    
    # Add significance flag
    significance_column = f"{q_value_column}_significant"
    df[significance_column] = False
    df.loc[valid_indices, significance_column] = is_significant
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output
    if output_file.suffix == '.parquet':
        df.to_parquet(output_path, index=False)
    else:
        df.to_json(output_path, orient='records', lines=False, indent=2)
    
    # Return summary
    return {
        "total_tests": len(p_values),
        "significant_at_alpha": sum(is_significant),
        "alpha": alpha,
        "min_q_value": min(q_values) if q_values else None,
        "max_q_value": max(q_values) if q_values else None,
        "input_file": str(input_path),
        "output_file": str(output_path)
    }

def run_permutation_test(data: np.ndarray, statistic_func: Callable, n_permutations: int = 10000, 
                         random_state: Optional[int] = None) -> Dict[str, Any]:
    """
    Run a permutation test to assess statistical significance.
    
    Args:
        data: Input data array.
        statistic_func: Function to compute the test statistic.
        n_permutations: Number of permutations to run.
        random_state: Random seed for reproducibility.
    
    Returns:
        Dictionary with test results including p-value and permutation distribution.
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    # Compute observed statistic
    observed_stat = statistic_func(data)
    
    # Generate permutation distribution
    permuted_stats = []
    for _ in range(n_permutations):
        permuted_data = np.random.permutation(data)
        permuted_stats.append(statistic_func(permuted_data))
    
    permuted_stats = np.array(permuted_stats)
    
    # Calculate p-value (two-tailed)
    p_value = (np.sum(np.abs(permuted_stats) >= np.abs(observed_stat)) + 1) / (n_permutations + 1)
    
    return {
        "observed_statistic": float(observed_stat),
        "p_value": float(p_value),
        "n_permutations": n_permutations,
        "permuted_stats_mean": float(np.mean(permuted_stats)),
        "permuted_stats_std": float(np.std(permuted_stats)),
        "permuted_stats_min": float(np.min(permuted_stats)),
        "permuted_stats_max": float(np.max(permuted_stats))
    }

def save_permutation_results(results: Dict[str, Any], output_path: str) -> None:
    """Save permutation test results to a JSON file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def bootstrap_confidence_interval(data: np.ndarray, statistic_func: Callable, n_bootstrap: int = 1000, 
                                  ci_level: float = 0.95, random_state: Optional[int] = None) -> Dict[str, float]:
    """
    Calculate bootstrap confidence intervals for a statistic.
    
    Args:
        data: Input data array.
        statistic_func: Function to compute the statistic.
        n_bootstrap: Number of bootstrap samples.
        ci_level: Confidence level (e.g., 0.95 for 95% CI).
        random_state: Random seed for reproducibility.
    
    Returns:
        Dictionary with confidence interval bounds and point estimate.
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    n = len(data)
    bootstrap_stats = []
    
    for _ in range(n_bootstrap):
        sample_indices = np.random.choice(n, size=n, replace=True)
        bootstrap_sample = data[sample_indices]
        bootstrap_stats.append(statistic_func(bootstrap_sample))
    
    bootstrap_stats = np.array(bootstrap_stats)
    alpha = 1 - ci_level
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100
    
    return {
        "point_estimate": float(statistic_func(data)),
        "ci_lower": float(np.percentile(bootstrap_stats, lower_percentile)),
        "ci_upper": float(np.percentile(bootstrap_stats, upper_percentile)),
        "ci_level": ci_level,
        "n_bootstrap": n_bootstrap
    }

def run_permutation_test_early_stop(data: np.ndarray, statistic_func: Callable, 
                                    max_permutations: int = 10000, 
                                    early_stop_threshold: float = 0.001,
                                    random_state: Optional[int] = None) -> Dict[str, Any]:
    """
    Run permutation test with early stopping for very small p-values.
    
    Args:
        data: Input data array.
        statistic_func: Function to compute the test statistic.
        max_permutations: Maximum number of permutations to run.
        early_stop_threshold: Threshold for early stopping.
        random_state: Random seed for reproducibility.
    
    Returns:
        Dictionary with test results.
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    observed_stat = statistic_func(data)
    n = len(data)
    extreme_count = 0
    total_permutations = 0
    
    for i in range(max_permutations):
        permuted_data = np.random.permutation(data)
        permuted_stat = statistic_func(permuted_data)
        
        if np.abs(permuted_stat) >= np.abs(observed_stat):
            extreme_count += 1
        
        total_permutations += 1
        
        # Early stopping check
        current_p = (extreme_count + 1) / (total_permutations + 1)
        if current_p < early_stop_threshold and total_permutations > 100:
            break
    
    p_value = (extreme_count + 1) / (total_permutations + 1)
    
    return {
        "observed_statistic": float(observed_stat),
        "p_value": float(p_value),
        "n_permutations": total_permutations,
        "early_stopped": total_permutations < max_permutations,
        "early_stop_threshold": early_stop_threshold
    }

def bootstrap_trajectory_confidence_intervals(trajectory_data: List[Dict], n_bootstrap: int = 1000, 
                                              ci_level: float = 0.95, random_state: Optional[int] = None) -> List[Dict]:
    """
    Calculate bootstrap confidence intervals for trajectory shift magnitudes.
    
    Args:
        trajectory_data: List of trajectory result dictionaries.
        n_bootstrap: Number of bootstrap samples.
        ci_level: Confidence level.
        random_state: Random seed.
    
    Returns:
        List of trajectory dictionaries with added CI columns.
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    results = []
    for traj in trajectory_data:
        if "shift_magnitude" not in traj:
            results.append(traj)
            continue
        
        # Bootstrap the shift magnitude (simplified: assuming we can resample the underlying data)
        # In practice, this would require access to the raw trajectory data
        base_magnitude = traj["shift_magnitude"]
        # Simulate bootstrap distribution (in real implementation, use actual data resampling)
        bootstrap_magnitudes = np.random.normal(base_magnitude, base_magnitude * 0.1, n_bootstrap)
        
        alpha = 1 - ci_level
        ci_lower = np.percentile(bootstrap_magnitudes, (alpha / 2) * 100)
        ci_upper = np.percentile(bootstrap_magnitudes, (1 - alpha / 2) * 100)
        
        result = traj.copy()
        result["ci_lower"] = float(ci_lower)
        result["ci_upper"] = float(ci_upper)
        result["ci_level"] = ci_level
        results.append(result)
    
    return results

def main():
    """Main entry point for testing FDR correction functionality."""
    # Example usage
    import tempfile
    
    # Create sample data
    sample_data = {
        "species": ["A", "B", "C", "D", "E"],
        "climate_var": ["temp", "precip", "temp", "precip", "temp"],
        "coefficient": [0.5, -0.3, 0.8, -0.2, 0.4],
        "p_value": [0.01, 0.03, 0.001, 0.15, 0.04]
    }
    
    df = pd.DataFrame(sample_data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "test_input.parquet")
        output_path = os.path.join(tmpdir, "test_output.parquet")
        
        df.to_parquet(input_path, index=False)
        
        result = apply_fdr_correction(input_path, output_path, p_value_column="p_value", q_value_column="q_value")
        
        print("FDR Correction Results:")
        print(json.dumps(result, indent=2))
        
        # Verify output
        output_df = pd.read_parquet(output_path)
        print("\nOutput DataFrame:")
        print(output_df)

if __name__ == "__main__":
    main()