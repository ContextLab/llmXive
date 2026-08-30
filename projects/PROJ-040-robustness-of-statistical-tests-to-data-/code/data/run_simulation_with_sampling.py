"""
Enhanced simulation runner with memory-aware sampling.

This script wraps run_simulation.py to handle large datasets by:
1. Checking memory limits before loading
2. Sampling data if memory is insufficient
3. Providing detailed logging
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import time
import warnings
import psutil

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import check_memory_limit, get_seed, get_sample_fraction, get_memory_limit
from data.run_simulation import (
    load_sensitivity_data, 
    load_contaminated_datasets, 
    run_all_simulations, 
    save_results
)

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def estimate_dataset_memory(df: pd.DataFrame) -> float:
    """Estimate memory usage of a DataFrame in MB."""
    return df.memory_usage(deep=True).sum() / (1024 * 1024)

def smart_load_datasets(data_dir: str, max_memory_mb: Optional[float] = None) -> Dict[str, pd.DataFrame]:
    """
    Load datasets with memory-aware sampling.
    
    Args:
        data_dir: Path to processed data directory
        max_memory_mb: Maximum memory to use for datasets (default: 50% of limit)
        
    Returns:
        Dict of dataset name -> sampled DataFrame
    """
    if max_memory_mb is None:
        limit = get_memory_limit()
        max_memory_mb = limit * 0.5  # Reserve half for processing
    
    processed_dir = Path(data_dir)
    datasets = {}
    total_memory = 0
    
    # First, collect all dataset info
    dataset_info = []
    for file_path in processed_dir.glob("contaminated_*.csv"):
        name = file_path.stem.replace("contaminated_", "")
        # Check size without loading full data
        try:
            # Read just the header and a few rows to estimate size
            sample_df = pd.read_csv(file_path, nrows=1000)
            rows_total = sum(1 for _ in open(file_path)) - 1  # -1 for header
            cols = len(sample_df.columns)
            # Rough estimate: 8 bytes per float64
            estimated_mb = (rows_total * cols * 8) / (1024 * 1024)
            dataset_info.append((name, file_path, estimated_mb, rows_total))
        except Exception as e:
            warnings.warn(f"Could not estimate size for {file_path}: {e}")
            continue
    
    # Sort by size (smallest first) to maximize number of datasets loaded
    dataset_info.sort(key=lambda x: x[2])
    
    for name, file_path, est_mb, rows_total in dataset_info:
        current_usage = get_memory_usage_mb()
        remaining = max_memory_mb - total_memory - current_usage
        
        if est_mb > remaining:
            # Need to sample
            sample_frac = remaining / est_mb if est_mb > 0 else 0.5
            sample_frac = max(0.1, min(sample_frac, 1.0))  # At least 10%, at most 100%
            
            print(f"Sampling {name} ({est_mb:.1f}MB -> {est_mb*sample_frac:.1f}MB) to fit memory")
            df = pd.read_csv(file_path).sample(frac=sample_frac, random_state=get_seed())
        else:
            print(f"Loading {name} fully ({est_mb:.1f}MB)")
            df = pd.read_csv(file_path)
        
        # Clean up data
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) >= 2:
            df = df[numeric_cols[:2]].dropna()
            datasets[name] = df
            total_memory += estimate_dataset_memory(df)
        elif len(numeric_cols) == 1:
            df = pd.DataFrame({
                'group1': df[numeric_cols[0]].dropna(),
                'group2': df[numeric_cols[0]].dropna()
            })
            datasets[name] = df
            total_memory += estimate_dataset_memory(df)
        
        # Check memory again
        if not check_memory_limit():
            warnings.warn("Memory limit reached during loading. Stopping.")
            break
    
    return datasets

def main():
    """Main entry point with memory management."""
    seed = get_seed()
    np.random.seed(seed)
    
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "processed"
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Memory limit: {get_memory_limit()}MB")
    print(f"Current usage: {get_memory_usage_mb():.1f}MB")
    
    # Load sensitivity data
    sensitivity_file = data_dir / "sensitivity.csv"
    if not sensitivity_file.exists():
        sensitivity_file = results_dir / "sensitivity.csv"
    
    if not sensitivity_file.exists():
        print("Error: sensitivity.csv not found.")
        sys.exit(1)
    
    sensitivity_data = load_sensitivity_data(str(sensitivity_file))
    print(f"Loaded {len(sensitivity_data)} sensitivity parameters")
    
    # Load datasets with memory awareness
    print("Loading datasets with memory-aware sampling...")
    start_load = time.time()
    datasets = smart_load_datasets(str(data_dir))
    load_time = time.time() - start_load
    
    if not datasets:
        print("Error: No datasets loaded.")
        sys.exit(1)
    
    print(f"Loaded {len(datasets)} datasets in {load_time:.1f}s")
    for name, df in datasets.items():
        print(f"  {name}: {len(df)} rows, {estimate_dataset_memory(df):.2f}MB")
    
    # Run simulations
    print("Starting simulations...")
    start_sim = time.time()
    results = run_all_simulations(sensitivity_data, datasets, iterations=1000, base_seed=seed)
    sim_time = time.time() - start_sim
    
    print(f"Simulations completed in {sim_time:.1f}s")
    print(f"Total results: {len(results)}")
    
    # Save
    output_file = results_dir / "simulation_results.csv"
    save_results(results, str(output_file))
    
    # Save individual files
    for res in results:
        dataset = res['dataset']
        rate = res['rate']
        individual_file = results_dir / f"results_{dataset}_{rate}.csv"
        subset = [r for r in results if r['dataset'] == dataset and r['rate'] == rate]
        save_results(subset, str(individual_file))
    
    print("Done.")

if __name__ == "__main__":
    main()