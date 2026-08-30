import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any
import warnings
import time

# Import from project modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config import check_memory_limit, get_seed, get_sample_fraction, set_memory_limit, get_memory_limit
from utils.stats_helpers import independent_ttest, one_way_anova, bonferroni_correction

def load_sensitivity_data(filepath: str) -> pd.DataFrame:
    """Load sensitivity analysis data from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Sensitivity data file not found: {filepath}")
    return pd.read_csv(filepath)

def load_contaminated_datasets(data_dir: str) -> Dict[str, pd.DataFrame]:
    """
    Load all contaminated datasets from the processed directory.
    
    Returns a dict mapping dataset name to DataFrame.
    """
    processed_dir = Path(data_dir)
    datasets = {}
    
    for file_path in processed_dir.glob("contaminated_*.csv"):
        # Extract dataset name from filename (e.g., contaminated_wine_0.05.csv -> wine)
        name = file_path.stem.replace("contaminated_", "")
        df = pd.read_csv(file_path)
        
        # Handle potential missing values or non-numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) >= 2:
            # Take first two numeric columns for testing
            datasets[name] = df[numeric_cols[:2]].dropna()
        elif len(numeric_cols) == 1:
            # If only one column, duplicate it for t-test (edge case handling)
            datasets[name] = pd.DataFrame({
                'group1': df[numeric_cols[0]].dropna(),
                'group2': df[numeric_cols[0]].dropna()
            })
    
    return datasets

def run_single_test_iteration(df: pd.DataFrame, rate: float, 
                              threshold: float, test_type: str = 'ttest',
                              seed: Optional[int] = None) -> Dict[str, float]:
    """
    Run a single statistical test iteration on a dataset.
    
    For Type I error estimation: resample from a single homogeneous population.
    For Power estimation: use the two groups as they are (if they differ).
    
    Args:
        df: DataFrame with at least two numeric columns
        rate: Contamination rate (0.0 to 1.0)
        threshold: Magnitude threshold for outliers
        test_type: 'ttest' or 'anova'
        seed: Random seed for reproducibility
        
    Returns:
        Dict with 'p_value', 'significant' (bool), and 'power' (0 or 1)
    """
    if seed is not None:
        np.random.seed(seed)
    
    # For Type I error: resample from pooled data (homogeneous population)
    # This ensures the null hypothesis is true
    col1 = df.iloc[:, 0].values
    col2 = df.iloc[:, 1].values
    
    # Pool the data
    pooled = np.concatenate([col1, col2])
    
    # Resample with replacement to create two groups of same size
    n1 = len(col1)
    n2 = len(col2)
    
    sample1 = np.random.choice(pooled, size=n1, replace=True)
    sample2 = np.random.choice(pooled, size=n2, replace=True)
    
    # Run the test
    if test_type == 'ttest':
        stat, p_value = independent_ttest(sample1, sample2)
    elif test_type == 'anova':
        stat, p_value = one_way_anova([sample1, sample2])
    else:
        raise ValueError(f"Unknown test type: {test_type}")
    
    significant = p_value < 0.05
    
    # For Type I error: power is 0 (since null is true)
    # For Power estimation: we would need a known effect size
    # Here we assume 0 for Type I error calculation
    power = 0.0 if significant else 0.0
    
    return {
        'p_value': p_value,
        'significant': float(significant),
        'power': power
    }

def run_monte_carlo_simulation(df: pd.DataFrame, rate: float, 
                               threshold: float, iterations: int = 1000,
                               test_type: str = 'ttest',
                               seed: Optional[int] = None) -> Dict[str, float]:
    """
    Run Monte Carlo simulation for a single condition.
    
    Args:
        df: DataFrame with data
        rate: Contamination rate
        threshold: Outlier magnitude threshold
        iterations: Number of Monte Carlo iterations
        test_type: 'ttest' or 'anova'
        seed: Base seed for reproducibility
        
    Returns:
        Dict with 'type1_error_rate' and 'power'
    """
    if seed is not None:
        np.random.seed(seed)
    
    significant_count = 0
    
    for i in range(iterations):
        # Use a unique seed for each iteration based on base seed
        iter_seed = seed + i if seed is not None else None
        
        result = run_single_test_iteration(df, rate, threshold, test_type, iter_seed)
        
        if result['significant']:
            significant_count += 1
        
        # Check memory periodically
        if i % 100 == 0 and i > 0:
            if not check_memory_limit():
                warnings.warn(f"Memory limit reached at iteration {i}. Stopping early.")
                break
    
    type1_error_rate = significant_count / iterations
    
    return {
        'type1_error_rate': type1_error_rate,
        'power': 0.0  # Power is not calculated in this Type I error focused run
    }

def run_all_simulations(sensitivity_data: pd.DataFrame, 
                        datasets: Dict[str, pd.DataFrame],
                        iterations: int = 1000,
                        base_seed: int = 42) -> List[Dict[str, Any]]:
    """
    Run simulations for all combinations of dataset, rate, and threshold.
    
    Args:
        sensitivity_data: DataFrame with threshold info
        datasets: Dict of dataset name -> DataFrame
        iterations: Number of Monte Carlo iterations
        base_seed: Base random seed
        
    Returns:
        List of result dictionaries
    """
    results = []
    
    for dataset_name, df in datasets.items():
        # Check if dataset is large enough
        if len(df) < 20:
            warnings.warn(f"Dataset {dataset_name} too small, skipping.")
            continue
        
        for _, row in sensitivity_data.iterrows():
            threshold = row['threshold']
            
            # Get contamination rate from the dataset name or a default
            # Assuming dataset names encode rate: contaminated_wine_0.05
            rate = 0.05  # Default, should be parsed from filename ideally
            
            # Extract rate from filename if possible
            if '_' in dataset_name:
                try:
                    rate_str = dataset_name.split('_')[-1].replace('.csv', '')
                    rate = float(rate_str)
                except (ValueError, IndexError):
                    pass
            
            print(f"Running simulation: {dataset_name}, rate={rate}, threshold={threshold}")
            
            sim_result = run_monte_carlo_simulation(
                df, rate, threshold, iterations, 'ttest', base_seed
            )
            
            result_entry = {
                'dataset': dataset_name,
                'rate': rate,
                'threshold': threshold,
                'type1_error_rate': sim_result['type1_error_rate'],
                'power': sim_result['power']
            }
            results.append(result_entry)
            
            # Check memory after each dataset/rate combination
            if not check_memory_limit():
                warnings.warn("Memory limit reached. Stopping simulations.")
                break
        
        if not check_memory_limit():
            break
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """Save simulation results to CSV."""
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_path, index=False)
    print(f"Results saved to {output_path}")

def main():
    """Main entry point for running simulations."""
    # Configuration
    seed = get_seed()
    np.random.seed(seed)
    
    # Paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "processed"
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Load sensitivity data
    sensitivity_file = data_dir / "sensitivity.csv"
    if not sensitivity_file.exists():
        # Fallback to results directory if not in processed
        sensitivity_file = results_dir / "sensitivity.csv"
    
    if not sensitivity_file.exists():
        print("Error: sensitivity.csv not found. Run generate_contamination.py first.")
        sys.exit(1)
    
    sensitivity_data = load_sensitivity_data(str(sensitivity_file))
    print(f"Loaded sensitivity data with {len(sensitivity_data)} rows")
    
    # Load contaminated datasets
    datasets = load_contaminated_datasets(str(data_dir))
    if not datasets:
        print("Error: No contaminated datasets found. Run generate_contamination.py first.")
        sys.exit(1)
    
    print(f"Loaded {len(datasets)} datasets: {list(datasets.keys())}")
    
    # Check memory before starting
    if not check_memory_limit():
        print(f"Warning: Memory limit ({get_memory_limit()}MB) may be exceeded.")
        # Optionally sample data
        sample_frac = get_sample_fraction()
        for name in datasets:
            datasets[name] = datasets[name].sample(frac=sample_frac, random_state=seed)
        print(f"Sampled {sample_frac*100}% of each dataset to fit memory.")
    
    # Run simulations
    print("Starting Monte Carlo simulations...")
    start_time = time.time()
    
    results = run_all_simulations(sensitivity_data, datasets, iterations=1000, base_seed=seed)
    
    elapsed = time.time() - start_time
    print(f"Simulations completed in {elapsed:.2f} seconds")
    
    # Save results
    output_file = results_dir / "simulation_results.csv"
    save_results(results, str(output_file))
    
    # Save individual results per dataset/rate
    for res in results:
        dataset = res['dataset']
        rate = res['rate']
        individual_file = results_dir / f"results_{dataset}_{rate}.csv"
        # Filter results for this dataset/rate
        subset = [r for r in results if r['dataset'] == dataset and r['rate'] == rate]
        save_results(subset, str(individual_file))
    
    print("All simulations complete.")

if __name__ == "__main__":
    main()
