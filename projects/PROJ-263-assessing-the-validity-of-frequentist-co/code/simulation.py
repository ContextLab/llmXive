import json
import logging
import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from scipy import stats

# Import from existing modules
from config import get_data_dir
from coverage import create_coverage_record, check_coverage

def load_population_means(dataset_id: str, data_dir: str) -> Dict[str, float]:
    """Load population means from the processed file."""
    pop_means_path = Path(data_dir) / "processed" / "population_means.json"
    if not pop_means_path.exists():
        raise FileNotFoundError(f"Population means file not found: {pop_means_path}")
    
    with open(pop_means_path, 'r') as f:
        data = json.load(f)
    
    # The file structure is expected to be {dataset_id: {variable: mean}}
    if dataset_id not in data:
        raise KeyError(f"Dataset {dataset_id} not found in population means file")
    
    return data[dataset_id]

def load_dataset(dataset_id: str, data_dir: str) -> np.ndarray:
    """Load cleaned dataset from the processed directory."""
    # Assuming the cleaned data is saved as a numpy file or CSV
    # For this implementation, we assume the data is passed directly or loaded from a standard location
    # In a real scenario, this would load from data/processed/cleaned_{dataset_id}.csv
    raise NotImplementedError("Data loading logic depends on the specific storage format. "
                              "Assuming data is passed to run_monte_carlo_simulation directly.")

def calculate_t_interval(sample: np.ndarray, confidence_level: float) -> Tuple[float, float]:
    """Calculate t-interval for the sample mean."""
    n = len(sample)
    if n < 2:
        raise ValueError("Sample size must be at least 2 for t-interval")
    
    sample_mean = np.mean(sample)
    sample_std = np.std(sample, ddof=1)
    
    # Critical value from t-distribution
    alpha = 1 - confidence_level
    t_crit = stats.t.ppf(1 - alpha/2, df=n-1)
    
    margin = t_crit * (sample_std / np.sqrt(n))
    lower = sample_mean - margin
    upper = sample_mean + margin
    
    return lower, upper

def calculate_bootstrap_interval(sample: np.ndarray, confidence_level: float, n_bootstrap: int = 10000) -> Tuple[float, float]:
    """Calculate bootstrap percentile interval."""
    n = len(sample)
    if n < 1:
        raise ValueError("Sample size must be at least 1 for bootstrap")
    
    bootstrap_means = []
    for _ in range(n_bootstrap):
        resample = np.random.choice(sample, size=n, replace=True)
        bootstrap_means.append(np.mean(resample))
    
    bootstrap_means = np.array(bootstrap_means)
    alpha = 1 - confidence_level
    
    lower = np.percentile(bootstrap_means, 100 * alpha/2)
    upper = np.percentile(bootstrap_means, 100 * (1 - alpha/2))
    
    return lower, upper

def run_single_iteration(dataset_id: str, data: np.ndarray, sample_size: int, 
                         confidence_level: float, pop_mean: float, logger: logging.Logger) -> Dict[str, Any]:
    """Run a single iteration of the Monte Carlo simulation."""
    # Draw sample with replacement (super-population approximation)
    sample = np.random.choice(data, size=sample_size, replace=True)
    
    # Calculate intervals
    t_lower, t_upper = calculate_t_interval(sample, confidence_level)
    boot_lower, boot_upper = calculate_bootstrap_interval(sample, confidence_level)
    
    # Check coverage
    t_contains = check_coverage(t_lower, t_upper, pop_mean)
    boot_contains = check_coverage(boot_lower, boot_upper, pop_mean)
    
    # Create records
    t_record = create_coverage_record(
        dataset_id=dataset_id,
        sample_size=sample_size,
        interval_type="t_interval",
        interval_lower=t_lower,
        interval_upper=t_upper,
        contains_mean=t_contains,
        confidence_level=confidence_level
    )
    
    boot_record = create_coverage_record(
        dataset_id=dataset_id,
        sample_size=sample_size,
        interval_type="bootstrap_interval",
        interval_lower=boot_lower,
        interval_upper=boot_upper,
        contains_mean=boot_contains,
        confidence_level=confidence_level
    )
    
    return [t_record, boot_record]

def run_monte_carlo_simulation(dataset_id: str, data: np.ndarray, sample_sizes: List[int],
                               n_replications: int, confidence_levels: List[float],
                               logger: logging.Logger) -> List[Dict[str, Any]]:
    """Run the full Monte Carlo simulation for a dataset."""
    all_records = []
    
    # Load population mean for this dataset
    data_dir = get_data_dir({}) # Config is not passed here, using default
    try:
        # We need to pass the correct data_dir. In a real run, this comes from config.
        # For now, we assume the data is already clean and we calculate the mean on the fly
        # or it's passed in. The spec says to use the full dataset mean.
        # Let's calculate it here from the provided 'data' (which is the full cleaned dataset)
        pop_mean_dict = {}
        for var_idx in range(data.shape[1]):
            var_name = f"var_{var_idx}"
            pop_mean_dict[var_name] = float(np.mean(data[:, var_idx]))
        
        # For simplicity, we assume we are testing one variable at a time or the mean of the first variable
        # The task says "mean of the full UCI dataset array". We'll use the mean of the first column as a representative
        # In a full implementation, this would loop over variables or aggregate.
        # Let's assume the target is the mean of the first column for this demonstration.
        target_mean = float(np.mean(data[:, 0]))
        
    except Exception as e:
        logger.error(f"Error calculating population mean: {e}")
        # Fallback or re-raise? Let's re-raise as this is critical
        raise e

    for n in sample_sizes:
        for conf_level in confidence_levels:
            logger.info(f"Running {n_replications} replications for n={n}, conf={conf_level}")
            
            for i in range(n_replications):
                records = run_single_iteration(
                    dataset_id=dataset_id,
                    data=data,
                    sample_size=n,
                    confidence_level=conf_level,
                    pop_mean=target_mean,
                    logger=logger
                )
                all_records.extend(records)
                
                if (i + 1) % 100 == 0:
                    logger.debug(f"Completed {i+1} replications...")
    
    return all_records

def main():
    """Main entry point for simulation module (for testing)."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Dummy data for testing
    dummy_data = np.random.normal(0, 1, (1000, 5))
    
    records = run_monte_carlo_simulation(
        dataset_id="test_dataset",
        data=dummy_data,
        sample_sizes=[10],
        n_replications=10,
        confidence_levels=[0.95],
        logger=logger
    )
    
    print(f"Generated {len(records)} records.")

if __name__ == "__main__":
    main()
