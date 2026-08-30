import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import time
import psutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_memory_limit, check_memory_limit, get_sample_fraction

def get_memory_usage_mb() -> float:
    """
    Get current memory usage of the process in MB.
    
    Returns:
        Memory usage in MB
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)

def estimate_dataset_memory(data: pd.DataFrame) -> float:
    """
    Estimate memory usage of a DataFrame in MB.
    
    Args:
        data: DataFrame to estimate
        
    Returns:
        Estimated memory in MB
    """
    return data.memory_usage(deep=True).sum() / (1024 * 1024)

def smart_load_datasets(
    processed_dir: Path,
    max_memory_mb: float = None
) -> list:
    """
    Load contaminated datasets with memory-aware sampling.
    
    If a dataset is too large, it will be downsampled to fit within memory limits.
    
    Args:
        processed_dir: Path to data/processed/
        max_memory_mb: Maximum memory to use for a single dataset (default: limit from config)
        
    Returns:
        List of dicts with keys: 'dataset_name', 'rate', 'data'
    """
    if max_memory_mb is None:
        max_memory_mb = get_memory_limit()
    
    # Safety margin: use 80% of limit
    target_memory_mb = max_memory_mb * 0.8
    
    datasets = []
    csv_files = list(processed_dir.glob("contaminated_*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(f"No contaminated datasets found in {processed_dir}")
    
    for file_path in csv_files:
        # Check current memory
        current_mem = get_memory_usage_mb()
        if current_mem > target_memory_mb:
            print(f"Warning: Current memory usage ({current_mem:.1f} MB) is high. Stopping load.")
            break
        
        # Parse filename
        name_part = file_path.stem.replace("contaminated_", "")
        parts = name_part.rsplit("_", 1)
        
        if len(parts) != 2:
            dataset_name = "unknown"
            rate = 0.0
        else:
            dataset_name = parts[0]
            try:
                rate = float(parts[1])
            except ValueError:
                rate = 0.0
        
        try:
            # Load data
            df = pd.read_csv(file_path)
            
            # Estimate memory
            est_mem = estimate_dataset_memory(df)
            
            if est_mem > target_memory_mb:
                print(f"  Dataset {dataset_name} too large ({est_mem:.1f} MB > {target_memory_mb:.1f} MB). Sampling...")
                
                # Calculate sample fraction
                sample_fraction = target_memory_mb / est_mem
                sample_fraction = min(sample_fraction, 1.0)
                sample_fraction = max(sample_fraction, 0.1) # At least 10%
                
                n_rows = len(df)
                n_sample = max(int(n_rows * sample_fraction), 100) # At least 100 rows
                
                df = df.sample(n=n_sample, random_state=42).reset_index(drop=True)
                print(f"    Sampled {n_sample} rows ({sample_fraction:.1%} of original)")
            
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

def main():
    """Main entry point for memory-aware dataset loading."""
    base_dir = Path(__file__).parent.parent.parent
    processed_dir = base_dir / "data" / "processed"
    
    print("Memory-aware dataset loading...")
    print(f"Memory limit: {get_memory_limit()} MB")
    print(f"Current usage: {get_memory_usage_mb():.1f} MB")
    
    try:
        datasets = smart_load_datasets(processed_dir)
        print(f"Successfully loaded {len(datasets)} datasets.")
        for ds in datasets:
            print(f"  - {ds['dataset_name']}: {len(ds['data'])} rows, {estimate_dataset_memory(ds['data']):.1f} MB")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
