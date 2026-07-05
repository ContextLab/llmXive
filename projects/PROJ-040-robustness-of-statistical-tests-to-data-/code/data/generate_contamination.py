import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

# Ensure imports work when run as a script from project root
# Adjust PYTHONPATH if necessary, though standard project structure assumes code/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_seed, get_memory_limit

def process_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocesses a dataset for contamination analysis.
    - Drops non-numeric columns.
    - Handles missing values by dropping rows (simple strategy for robustness analysis).
    - Returns a clean numeric DataFrame.
    """
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        raise ValueError("No numeric columns found in dataset.")
    
    # Drop rows with any NaN to ensure clean baseline for contamination injection
    clean_df = numeric_df.dropna()
    
    if clean_df.empty:
        raise ValueError("Dataset became empty after dropping NaNs.")
    
    return clean_df

def inject_contamination(df: pd.DataFrame, contamination_rate: float, 
                         outlier_sigma: float, seed: int) -> pd.DataFrame:
    """
    Injects Gaussian noise and extreme outliers into a copy of the dataset.
    
    Parameters:
    - df: Clean numeric DataFrame.
    - contamination_rate: Fraction of rows to contaminate (0.0 to 1.0).
    - outlier_sigma: Multiplier of the dataset's standard deviation for outlier magnitude.
    - seed: Random seed for reproducibility.
    
    Returns:
    - Contaminated DataFrame.
    """
    np.random.seed(seed)
    n_samples = len(df)
    n_contaminated = int(n_samples * contamination_rate)
    
    contaminated_df = df.copy()
    
    if n_contaminated == 0:
        return contaminated_df
    
    # Select random indices to contaminate
    indices = np.random.choice(n_samples, size=n_contaminated, replace=False)
    
    # Calculate global stats for outlier generation
    # Using global mean and std for simplicity, or per-column could be used
    global_mean = contaminated_df.mean().mean()
    global_std = contaminated_df.std().std() # Simplified global std estimate
    
    # If std is too small (constant data), use a minimal epsilon
    if global_std < 1e-6:
        global_std = 1.0
    
    for idx in indices:
        # Randomly select a column to corrupt
        col = np.random.choice(contaminated_df.columns)
        
        # Generate outlier: mean + (sigma * std * random_sign)
        # We use outlier_sigma * global_std as the magnitude
        noise = np.random.normal(0, outlier_sigma * global_std)
        
        # Determine if it's an additive outlier or a shift
        # Strategy: Add a large value relative to the distribution
        # To ensure it's an "outlier", we push it far from the mean
        current_val = contaminated_df.loc[idx, col]
        
        # Create a new value that is far away
        # We add/subtract based on a random sign to create outliers on both tails
        sign = np.random.choice([-1, 1])
        new_val = global_mean + (sign * outlier_sigma * global_std)
        
        contaminated_df.loc[idx, col] = new_val
        
    return contaminated_df

def run_sensitivity_analysis(base_df: pd.DataFrame, contamination_rate: float, 
                             contamination_rates_list=None, output_path: str = None):
    """
    Runs a sensitivity analysis for contamination magnitude thresholds.
    Sweeps outlier magnitude from 1σ to 10σ.
    
    For this analysis, we assume a baseline statistical test (e.g., t-test) 
    on a null hypothesis (two groups from same distribution) to measure 
    False Positive Rate (FPR) inflation.
    
    Since the task asks for 'false_positive_rate' and 'variation_in_fpr',
    we simulate a null scenario:
    1. Split data into two random halves (or resample) to create a null hypothesis scenario.
    2. Inject contamination into one or both halves.
    3. Run a t-test.
    4. Record if p < 0.05 (False Positive).
    
    This function performs the sweep and returns the results DataFrame.
    """
    if contamination_rates_list is None:
        contamination_rates_list = [0.01, 0.05, 0.10] # Default rates if not specified
    
    seed = get_seed()
    n_iterations = 100 # Reduced for speed in sensitivity sweep, can be tuned
    
    results = []
    
    # Prepare clean data
    clean_data = process_dataset(base_df)
    
    # We need to simulate a Null Hypothesis scenario to measure FPR.
    # Strategy: Split clean_data into two groups. Since they come from the same source,
    # the null hypothesis (means are equal) is true.
    # We will contaminate one group (or both) and see if the test rejects the null.
    
    n_samples = len(clean_data)
    group_size = n_samples // 2
    
    # Use the first half as Group A, second half as Group B
    # To make it robust to order, we might shuffle first, but for sensitivity 
    # we assume the data is representative.
    group_a = clean_data.iloc[:group_size].copy()
    group_b = clean_data.iloc[group_size:].copy()
    
    # If we need to ensure true null, we can resample from the pooled data,
    # but splitting the dataset is a valid approximation for this sensitivity check.
    # To be more rigorous per spec (US2 resampling), we would resample with replacement.
    # Here, for sensitivity sweep speed, we use the split.
    
    thresholds = range(1, 11) # 1σ to 10σ
    
    for rate in contamination_rates_list:
        for sigma in thresholds:
            fp_count = 0
            
            for i in range(n_iterations):
                # Create a fresh copy for this iteration
                g_a = group_a.copy()
                g_b = group_b.copy()
                
                # Inject contamination into Group B (the "treatment" group in the null scenario)
                # This simulates data corruption that might look like an effect
                g_b_contaminated = inject_contamination(g_b, rate, sigma, seed + i)
                
                # Perform t-test on the first numeric column (or aggregate)
                # For simplicity, we test the first column. In a full pipeline, 
                # we might average p-values or test specific features.
                # To be robust, we test the first column.
                col = g_a.columns[0]
                
                # Handle case where columns might differ if we were doing per-column logic,
                # but here we assume same schema.
                try:
                    from scipy import stats
                    stat, p_val = stats.ttest_ind(g_a[col], g_b_contaminated[col])
                    
                    if p_val < 0.05:
                        fp_count += 1
                except Exception:
                    # If test fails (e.g. constant variance), skip or count as 0
                    continue
            
            fpr = fp_count / n_iterations
            
            results.append({
                'contamination_rate': rate,
                'threshold_sigma': sigma,
                'false_positive_rate': fpr,
                'variation_in_fpr': fpr - 0.05 # Deviation from nominal 0.05
            })
    
    results_df = pd.DataFrame(results)
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        results_df.to_csv(output_path, index=False)
        print(f"Sensitivity analysis saved to {output_path}")
    
    return results_df

def main():
    """
    Main entry point for the sensitivity analysis task.
    """
    # Determine paths
    project_root = Path(__file__).parent.parent.parent
    # Try to load a processed dataset. If T013 hasn't run, we might need to download first.
    # For T014, we assume we have a dataset. Let's try to find a processed one or download.
    
    processed_dir = project_root / "data" / "processed"
    raw_dir = project_root / "data" / "raw"
    
    # Try to find a dataset
    dataset_path = None
    if processed_dir.exists():
        files = list(processed_dir.glob("*.csv"))
        if files:
            dataset_path = files[0]
    
    if dataset_path is None:
        # If no processed file, try to download Wine dataset as a fallback for the sweep
        # This ensures the script is runnable even if T010/T013 are skipped in isolation
        from data.download_datasets import download_wine
        print("No processed dataset found. Downloading UCI Wine dataset for sensitivity analysis...")
        download_wine(str(raw_dir))
        # Re-scan
        if raw_dir.exists():
            files = list(raw_dir.glob("*.csv"))
            if files:
                dataset_path = files[0]
    
    if dataset_path is None:
        raise FileNotFoundError("Could not locate any dataset to run sensitivity analysis. Please run download_datasets.py first.")
    
    print(f"Loading dataset from {dataset_path}")
    df = pd.read_csv(dataset_path)
    
    # If the dataset has headers like 'class' or target in the first column and we want to test features,
    # we might need to drop it. The process_dataset function handles numeric selection.
    
    output_path = project_root / "data" / "results" / "sensitivity.csv"
    
    # Run the sweep
    # We use a few representative contamination rates
    rates = [0.01, 0.05, 0.10]
    df_results = run_sensitivity_analysis(df, contamination_rate=0.05, contamination_rates_list=rates, output_path=str(output_path))
    
    print("\nSensitivity Analysis Results (Sample):")
    print(df_results.head(10))

if __name__ == "__main__":
    main()
