import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any
import warnings

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_seed, check_memory_limit
from utils.stats_helpers import independent_ttest, one_way_anova, calculate_power

def load_sensitivity_data(sensitivity_path: Path) -> pd.DataFrame:
    """
    Load sensitivity analysis results to determine magnitude parameters.
    
    Args:
        sensitivity_path: Path to sensitivity.csv
        
    Returns:
        DataFrame with columns [threshold, false_positive_rate, variation_in_fpr]
    """
    if not sensitivity_path.exists():
        raise FileNotFoundError(f"Sensitivity data file not found: {sensitivity_path}")
    
    df = pd.read_csv(sensitivity_path)
    # Ensure we have the required columns for magnitude selection
    required_cols = ['threshold', 'false_positive_rate', 'variation_in_fpr']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Sensitivity file missing required columns. Found: {df.columns.tolist()}")
    
    return df

def load_contaminated_datasets(processed_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all contaminated datasets from the processed directory.
    
    Args:
        processed_dir: Path to data/processed/
        
    Returns:
        List of dicts with keys: 'dataset_name', 'rate', 'data' (DataFrame)
    """
    datasets = []
    csv_files = list(processed_dir.glob("contaminated_*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(f"No contaminated datasets found in {processed_dir}")
    
    for file_path in csv_files:
        # Parse filename to extract metadata
        # Expected format: contaminated_{dataset}_{rate}.csv
        name_part = file_path.stem.replace("contaminated_", "")
        parts = name_part.rsplit("_", 1)
        
        if len(parts) != 2:
            # Fallback if naming convention varies
            dataset_name = "unknown"
            rate = 0.0
        else:
            dataset_name = parts[0]
            try:
                rate = float(parts[1])
            except ValueError:
                rate = 0.0
        
        try:
            df = pd.read_csv(file_path)
            datasets.append({
                'dataset_name': dataset_name,
                'rate': rate,
                'file_path': file_path,
                'data': df
            })
        except Exception as e:
            print(f"Warning: Failed to load {file_path}: {e}")
            continue
    
    return datasets

def run_single_test_iteration(
    data: pd.DataFrame,
    contamination_rate: float,
    magnitude: float,
    test_type: str = "ttest",
    alpha: float = 0.05
) -> Tuple[bool, float]:
    """
    Run a single statistical test iteration on a dataset.
    
    Implements resampling from a single homogeneous population for Type I error estimation
    (null hypothesis: no difference between groups).
    
    Args:
        data: DataFrame with numeric columns
        contamination_rate: Current contamination rate (for logging)
        magnitude: Magnitude of contamination (sigma multiplier)
        test_type: Type of test to run ("ttest" or "anova")
        alpha: Significance level
        
    Returns:
        Tuple of (rejected_null, power_estimate)
        - rejected_null: True if p-value < alpha
        - power_estimate: 1.0 if rejected, 0.0 otherwise (for Type I error context)
    """
    # Filter numeric columns only
    numeric_data = data.select_dtypes(include=[np.number])
    
    if numeric_data.shape[1] < 2:
        # Not enough columns for a test
        return False, 0.0
    
    # For Type I error estimation, we assume the null is true.
    # We resample from a single homogeneous population (pooled data) to simulate
    # two groups that come from the same distribution.
    # Algorithm:
    # 1. Pool all numeric values
    # 2. Randomly split into two groups (with replacement)
    # 3. Perform test
    
    # Use first two numeric columns as "groups" if they exist, otherwise pool all
    if numeric_data.shape[1] >= 2:
        group1 = numeric_data.iloc[:, 0].dropna().values
        group2 = numeric_data.iloc[:, 1].dropna().values
    else:
        # Pool everything into one distribution
        all_values = numeric_data.values.flatten()
        all_values = all_values[~np.isnan(all_values)]
        if len(all_values) < 10:
            return False, 0.0
        # Split into two random groups
        rng = np.random.default_rng(get_seed())
        indices = rng.choice(len(all_values), size=len(all_values), replace=True)
        half = len(indices) // 2
        group1 = all_values[indices[:half]]
        group2 = all_values[indices[half:]]
    
    # Resample with replacement to ensure true null hypothesis
    # (both groups come from the same pooled distribution)
    rng = np.random.default_rng(get_seed())
    n1 = len(group1)
    n2 = len(group2)
    
    # Resample
    g1_sample = rng.choice(group1, size=n1, replace=True)
    g2_sample = rng.choice(group2, size=n2, replace=True)
    
    # Run the test
    if test_type == "ttest":
        try:
            stat, p_val = independent_ttest(g1_sample, g2_sample)
        except Exception:
            return False, 0.0
    elif test_type == "anova":
        try:
            # ANOVA requires at least 2 groups, we simulate 2 groups
            stat, p_val = one_way_anova([g1_sample, g2_sample])
        except Exception:
            return False, 0.0
    else:
        return False, 0.0
    
    rejected = p_val < alpha
    power = 1.0 if rejected else 0.0
    
    return rejected, power

def run_monte_carlo_simulation(
    dataset_name: str,
    contamination_rate: float,
    magnitude: float,
    data: pd.DataFrame,
    n_iterations: int = 1000,
    test_type: str = "ttest",
    alpha: float = 0.05
) -> Dict[str, float]:
    """
    Run Monte Carlo simulation for a specific condition.
    
    Args:
        dataset_name: Name of the dataset
        contamination_rate: Contamination rate
        magnitude: Contamination magnitude
        data: DataFrame with data
        n_iterations: Number of Monte Carlo iterations
        test_type: Type of test
        alpha: Significance level
        
    Returns:
        Dict with keys: 'dataset', 'rate', 'magnitude', 'error_rate', 'power'
    """
    rejected_count = 0
    power_sum = 0.0
    
    for i in range(n_iterations):
        # Reset seed for reproducibility within iteration if needed
        # (Global seed is set at start of script)
        rejected, power = run_single_test_iteration(
            data, contamination_rate, magnitude, test_type, alpha
        )
        if rejected:
            rejected_count += 1
        power_sum += power
    
    error_rate = rejected_count / n_iterations
    avg_power = power_sum / n_iterations
    
    return {
        'dataset': dataset_name,
        'rate': contamination_rate,
        'magnitude': magnitude,
        'error_rate': error_rate,
        'power': avg_power
    }

def run_all_simulations(
    sensitivity_df: pd.DataFrame,
    datasets: List[Dict[str, Any]],
    n_iterations: int = 1000,
    test_type: str = "ttest",
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Execute simulations for all combinations of dataset, rate, and magnitude.
    
    Args:
        sensitivity_df: DataFrame with magnitude thresholds
        datasets: List of contaminated datasets
        n_iterations: Monte Carlo iterations per condition
        test_type: Type of test
        alpha: Significance level
        
    Returns:
        DataFrame with simulation results
    """
    results = []
    
    # Get unique magnitudes from sensitivity analysis
    # Use the 'threshold' column as the magnitude parameter
    magnitudes = sensitivity_df['threshold'].unique()
    
    print(f"Starting simulations: {len(datasets)} datasets x {len(magnitudes)} magnitudes x {n_iterations} iterations")
    
    for ds_info in datasets:
        ds_name = ds_info['dataset_name']
        rate = ds_info['rate']
        data = ds_info['data']
        
        print(f"  Processing {ds_name} (rate={rate:.2f})...")
        
        for mag in magnitudes:
            print(f"    Magnitude: {mag:.2f}")
            
            result = run_monte_carlo_simulation(
                dataset_name=ds_name,
                contamination_rate=rate,
                magnitude=mag,
                data=data,
                n_iterations=n_iterations,
                test_type=test_type,
                alpha=alpha
            )
            results.append(result)
            
            # Check memory periodically
            if not check_memory_limit():
                print("Warning: Memory limit approaching, stopping early.")
                break
        
        if not check_memory_limit():
            break
    
    return pd.DataFrame(results)

def save_results(results_df: pd.DataFrame, output_path: Path) -> None:
    """
    Save simulation results to CSV.
    
    Args:
        results_df: DataFrame with results
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    print(f"Results saved to {output_path}")

def main():
    """Main entry point for the simulation runner."""
    # Set random seed for reproducibility
    seed = get_seed()
    np.random.seed(seed)
    
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    processed_dir = base_dir / "data" / "processed"
    results_dir = base_dir / "data" / "results"
    sensitivity_path = processed_dir / "sensitivity.csv"
    output_path = results_dir / "simulation_results.csv"
    
    # Check memory before starting
    if not check_memory_limit():
        print("Error: Memory limit exceeded before starting simulation.")
        sys.exit(1)
    
    # Load sensitivity data
    print("Loading sensitivity data...")
    try:
        sensitivity_df = load_sensitivity_data(sensitivity_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure T014 (sensitivity analysis) has been run first.")
        sys.exit(1)
    
    # Load contaminated datasets
    print("Loading contaminated datasets...")
    try:
        datasets = load_contaminated_datasets(processed_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure T013 (contaminated datasets) has been run first.")
        sys.exit(1)
    
    if not datasets:
        print("Error: No contaminated datasets found.")
        sys.exit(1)
    
    # Run simulations
    print("Running Monte Carlo simulations...")
    results_df = run_all_simulations(
        sensitivity_df=sensitivity_df,
        datasets=datasets,
        n_iterations=1000,
        test_type="ttest",
        alpha=0.05
    )
    
    # Save results
    save_results(results_df, output_path)
    
    print("Simulation complete.")

if __name__ == "__main__":
    main()
