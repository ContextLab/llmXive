import os
import json
import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Any, Tuple, Optional
import logging

# Import from project modules as defined in API surface
from config import load_config
from dependency_injector import ar1_inject, block_bootstrap, spatial_kernel_smooth
from data_loader import load_datasets
from exceptions import CriticalValidationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EdgeCaseError(Exception):
    """Raised when a simulation edge case prevents valid execution."""
    pass

def run_single_replication(
    test_type: str,
    data: np.ndarray,
    dependency_type: str,
    dependency_strength: float,
    effect_size: float = 0.0,
    block_size: Optional[int] = None,
    seed: Optional[int] = None
) -> float:
    """
    Execute a single Monte Carlo replication.
    
    Algorithm:
    1. (Optional) Inject true effect (mean shift) if effect_size > 0.
    2. Inject dependency structure (AR(1), Block Bootstrap, or Spatial).
    3. Apply statistical test (t-test, ANOVA, or Chi-squared).
    4. Return p-value.
    
    Args:
        test_type: 't_test', 'anova', or 'chi_squared'.
        data: 2D numpy array (n_samples, n_features) or 1D for single group.
        dependency_type: 'ar1', 'block_bootstrap', 'spatial'.
        dependency_strength: Strength parameter r (0 to 0.9) or block size.
        effect_size: Mean shift delta (sigma units) to inject BEFORE dependency.
        block_size: Required for block_bootstrap.
        seed: Random seed for reproducibility.
        
    Returns:
        float: p-value from the statistical test.
    """
    if seed is not None:
        np.random.seed(seed)

    # 1. Inject True Effect (if specified)
    # This shifts the mean of the data to simulate a non-null hypothesis
    if effect_size > 0.0:
        logger.debug(f"Injecting true effect delta={effect_size}")
        if data.ndim == 1:
            data = data + effect_size
        elif data.ndim == 2:
            # Assume second column is the group of interest or apply to all if single group
            # For t-test/ANOVA context, usually we shift one group relative to another.
            # Here we assume 'data' represents the combined sample or a specific group.
            # If data is (n, 2) for two groups, we shift the second column.
            if data.shape[1] == 2:
                data[:, 1] = data[:, 1] + effect_size
            else:
                data = data + effect_size
        else:
            raise EdgeCaseError(f"Unsupported data shape for effect injection: {data.shape}")

    # 2. Inject Dependency Structure
    if dependency_type == 'ar1':
        # ar1_inject expects (n,) or (n, k) and returns dependency-injected data
        # We assume data is 1D for t-test or we process columns
        if data.ndim == 1:
            data_injected = ar1_inject(data, r=dependency_strength)
        else:
            # Apply to each column independently or flatten? 
            # Standard practice: apply to the residual structure. 
            # For simplicity in this runner, we apply to the flattened data or row-wise.
            # Let's assume row-wise injection for multivariate or column-wise.
            # Based on typical usage in this pipeline, we apply to the 1D vector of interest.
            # If data is 2D, we might need to reshape or handle groups.
            # For now, assume 1D input for t-test/ANOVA or reshape if necessary.
            # If data is (n_groups * n_per_group), we might need to handle groups.
            # Let's assume the input 'data' is already prepared as a single vector 
            # or a tuple of vectors. 
            # To be safe with the API of ar1_inject (which takes a 1D array usually):
            if data.shape[1] == 2:
                # Two groups: apply AR1 to each group separately? Or combined?
                # Usually, dependency is within a time series. 
                # Let's assume we are testing the difference of means of two series.
                # We inject AR1 into both series.
                g0 = ar1_inject(data[:, 0], r=dependency_strength)
                g1 = ar1_inject(data[:, 1], r=dependency_strength)
                data_injected = np.column_stack((g0, g1))
            else:
                # Fallback: treat as single vector
                data_injected = ar1_inject(data.flatten(), r=dependency_strength)
    
    elif dependency_type == 'block_bootstrap':
        if block_size is None:
            raise EdgeCaseError("block_size required for block_bootstrap")
        # block_bootstrap returns resampled data
        if data.ndim == 1:
            data_injected = block_bootstrap(data, block_size=block_size, strength=dependency_strength)
        else:
            # Apply to columns or rows? 
            # Assuming we need to resample rows (observations) for independence violation
            # block_bootstrap signature in API: block_bootstrap(data, block_size, strength)
            data_injected = block_bootstrap(data, block_size=block_size, strength=dependency_strength)
    
    elif dependency_type == 'spatial':
        # spatial_kernel_smooth expects data and bandwidth
        data_injected = spatial_kernel_smooth(data, bandwidth=dependency_strength)
    
    else:
        raise EdgeCaseError(f"Unknown dependency type: {dependency_type}")

    # 3. Apply Statistical Test
    if test_type == 't_test':
        if data_injected.ndim == 1:
            # One-sample t-test against 0? Or two-sample if structured?
            # Assuming two-sample if shape is (n, 2)
            if data_injected.shape[1] == 2:
                t_stat, p_val = stats.ttest_ind(data_injected[:, 0], data_injected[:, 1])
            else:
                # One-sample t-test against mean 0 (Null: mu=0)
                t_stat, p_val = stats.ttest_1samp(data_injected, 0.0)
        else:
            # Reshape or error
            if data_injected.ndim == 2 and data_injected.shape[1] == 2:
                t_stat, p_val = stats.ttest_ind(data_injected[:, 0], data_injected[:, 1])
            else:
                t_stat, p_val = stats.ttest_1samp(data_injected.flatten(), 0.0)
    
    elif test_type == 'anova':
        # One-way ANOVA
        if data_injected.ndim == 1:
            # If 1D, maybe split into groups? Assuming 2 groups for simplicity
            # Or if it's already a list of arrays? 
            # Let's assume data_injected is (n, k) where k is groups
            if data_injected.shape[1] >= 2:
                groups = [data_injected[:, i] for i in range(data_injected.shape[1])]
                f_stat, p_val = stats.f_oneway(*groups)
            else:
                raise EdgeCaseError("ANOVA requires at least 2 groups")
        else:
            groups = [data_injected[:, i] for i in range(data_injected.shape[1])]
            f_stat, p_val = stats.f_oneway(*groups)
    
    elif test_type == 'chi_squared':
        # Chi-squared test for independence
        # Requires categorical data. 
        # If data is continuous, we might need to bin it or assume input is already counts.
        # For this simulation runner, we assume the caller provides appropriate data 
        # or we convert continuous to categorical (e.g., median split) for demonstration.
        # However, the spec says "Chi-squared test logic".
        # If data_injected is 2D (n, 2) representing counts or categories?
        # Let's assume we are testing independence of two categorical variables.
        # If input is continuous, we bin.
        if data_injected.dtype.kind in 'fc':
            # Bin into 2x2 contingency table
            median = np.median(data_injected)
            # Assuming 2D (n, 2)
            if data_injected.ndim == 2 and data_injected.shape[1] == 2:
                # Create contingency table
                # Row: Var1 > median, Col: Var2 > median
                row1 = np.sum((data_injected[:, 0] > median) & (data_injected[:, 1] > median))
                row2 = np.sum((data_injected[:, 0] <= median) & (data_injected[:, 1] > median))
                row3 = np.sum((data_injected[:, 0] > median) & (data_injected[:, 1] <= median))
                row4 = np.sum((data_injected[:, 0] <= median) & (data_injected[:, 1] <= median))
                contingency = np.array([[row1, row2], [row3, row4]])
                chi2, p_val, dof, expected = stats.chi2_contingency(contingency)
            else:
                raise EdgeCaseError("Chi-squared requires 2D data for contingency or counts")
        else:
            # Assume integer counts
            chi2, p_val, dof, expected = stats.chi2_contingency(data_injected)
    
    else:
        raise EdgeCaseError(f"Unknown test type: {test_type}")

    return float(p_val)

def run_simulation(
    config: Dict[str, Any],
    datasets: Optional[List[pd.DataFrame]] = None,
    output_path: str = "results/simulation_raw.csv"
) -> pd.DataFrame:
    """
    Run the full Monte Carlo simulation loop.
    
    Args:
        config: Configuration dictionary from config.yaml.
        datasets: Pre-loaded datasets. If None, load from data_loader.
        output_path: Path to save results.
        
    Returns:
        DataFrame with simulation results.
    """
    logger.info("Starting simulation run...")
    
    # Load datasets if not provided
    if datasets is None:
        logger.info("Loading datasets from manifest...")
        datasets = load_datasets()
        if not datasets:
            raise CriticalValidationError("No datasets loaded. Simulation cannot proceed.")

    results = []
    
    # Extract simulation parameters from config
    n_replications = config.get('simulation', {}).get('n_replications', 1000)
    dependency_types = config.get('simulation', {}).get('dependency_types', ['ar1'])
    test_types = config.get('simulation', {}).get('test_types', ['t_test'])
    dependency_strengths = config.get('simulation', {}).get('dependency_strengths', [0.0, 0.3])
    effect_sizes = config.get('simulation', {}).get('effect_sizes', [0.0]) # [0.0] for Type I, >0 for Power
    
    seed_base = config.get('simulation', {}).get('seed', 42)
    
    for dataset_idx, df in enumerate(datasets):
        logger.info(f"Processing dataset {dataset_idx}: {df.shape}")
        
        # Convert to numpy
        # Assume first column is target or all columns are relevant
        # For t-test, we might need 2 groups. For ANOVA, multiple.
        # We'll iterate over columns or specific configurations.
        # Simplified: treat each dataset as a single vector or 2-group structure if shape allows.
        data_np = df.values
        
        for test_type in test_types:
            for dep_type in dependency_types:
                for strength in dependency_strengths:
                    for effect in effect_sizes:
                        logger.debug(f"Config: test={test_type}, dep={dep_type}, strength={strength}, effect={effect}")
                        
                        p_values = []
                        for rep in range(n_replications):
                            try:
                                seed = seed_base + dataset_idx * 10000 + rep
                                p_val = run_single_replication(
                                    test_type=test_type,
                                    data=data_np,
                                    dependency_type=dep_type,
                                    dependency_strength=strength,
                                    effect_size=effect,
                                    seed=seed
                                )
                                p_values.append(p_val)
                            except EdgeCaseError as e:
                                logger.warning(f"Edge case in replication {rep}: {e}")
                                # Handle edge case: maybe skip or log
                                continue
                        
                        if p_values:
                            avg_p = np.mean(p_values)
                            results.append({
                                'dataset_id': dataset_idx,
                                'test_type': test_type,
                                'dependency_type': dep_type,
                                'dependency_strength': strength,
                                'effect_size': effect,
                                'n_replications': len(p_values),
                                'mean_p_value': avg_p,
                                'p_values': p_values # Store list for later aggregation
                            })
    
    # Create DataFrame
    df_results = pd.DataFrame(results)
    
    # Save to CSV (flattening p_values list to separate rows or keeping as JSON string)
    # For raw output, we usually want one row per replication.
    # But the task says "Save raw p-values". Let's expand.
    expanded_results = []
    for row in results:
        for i, p in enumerate(row['p_values']):
            expanded_results.append({
                'dataset_id': row['dataset_id'],
                'test_type': row['test_type'],
                'dependency_type': row['dependency_type'],
                'dependency_strength': row['dependency_strength'],
                'effect_size': row['effect_size'],
                'replication_id': i,
                'p_value': p
            })
    
    df_expanded = pd.DataFrame(expanded_results)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_expanded.to_csv(output_path, index=False)
    
    logger.info(f"Simulation complete. Results saved to {output_path}")
    return df_expanded

def save_edge_case_report(report: Dict[str, Any], path: str = "results/edge_case_report.json"):
    """Save edge case failures to JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Edge case report saved to {path}")

def main():
    """Entry point for running the simulation."""
    config = load_config()
    df_results = run_simulation(config)
    print(f"Simulation finished. Output: {df_results.shape}")

if __name__ == "__main__":
    main()