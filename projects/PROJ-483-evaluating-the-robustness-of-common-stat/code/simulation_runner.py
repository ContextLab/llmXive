"""
Simulation Runner for Statistical Robustness Evaluation.

Implements the "Generate-then-Inject" Monte Carlo loop for t-tests, ANOVA,
and Chi-squared tests under varying dependency structures.

Optimized for vectorized operations to ensure 10,000 replications complete
within the 6-hour window (FR-008).
"""
import os
import json
import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Any, Tuple, Optional
from data_loader import load_datasets
from dependency_injector import ar1_inject, block_bootstrap, spatial_kernel_smooth
from config import load_config
from exceptions import CriticalValidationError, EdgeCaseError

class SimulationError(Exception):
    """Custom exception for simulation failures."""
    pass

def _vectorized_t_test(data: np.ndarray, group_indices: np.ndarray) -> np.ndarray:
    """
    Vectorized independent samples t-test.
    
    Args:
        data: 2D array (n_replications, n_samples)
        group_indices: 1D array indicating group membership (0 or 1)
        
    Returns:
        1D array of p-values for each replication.
    """
    n_rep = data.shape[0]
    p_values = np.empty(n_rep)
    
    # Pre-calculate masks
    mask0 = group_indices == 0
    mask1 = group_indices == 1
    
    for i in range(n_rep):
        g0 = data[i, mask0]
        g1 = data[i, mask1]
        
        # Handle edge cases
        if len(g0) < 2 or len(g1) < 2:
            p_values[i] = 1.0
            continue
            
        if np.var(g0) == 0 and np.var(g1) == 0:
            p_values[i] = 1.0 if np.mean(g0) == np.mean(g1) else 0.0
            continue
            
        _, p = stats.ttest_ind(g0, g1, equal_var=False)
        p_values[i] = p
        
    return p_values

def _vectorized_anova(data: np.ndarray, group_indices: np.ndarray) -> np.ndarray:
    """
    Vectorized one-way ANOVA.
    
    Args:
        data: 2D array (n_replications, n_samples)
        group_indices: 1D array indicating group membership
        
    Returns:
        1D array of p-values for each replication.
    """
    n_rep = data.shape[0]
    p_values = np.empty(n_rep)
    
    unique_groups = np.unique(group_indices)
    if len(unique_groups) < 2:
        return np.ones(n_rep) * 1.0
        
    for i in range(n_rep):
        groups = [data[i, group_indices == g] for g in unique_groups]
        
        # Filter out empty groups
        groups = [g for g in groups if len(g) > 0]
        
        if len(groups) < 2:
            p_values[i] = 1.0
            continue
            
        try:
            _, p = stats.f_oneway(*groups)
            p_values[i] = p
        except Exception:
            p_values[i] = 1.0
            
    return p_values

def _vectorized_chi_squared(observed: np.ndarray, expected: np.ndarray) -> np.ndarray:
    """
    Vectorized Chi-squared test.
    
    Args:
        observed: 2D array (n_replications, n_categories)
        expected: 2D array (n_replications, n_categories) or broadcastable
        
    Returns:
        1D array of p-values for each replication.
    """
    n_rep = observed.shape[0]
    p_values = np.empty(n_rep)
    
    for i in range(n_rep):
        try:
            _, p = stats.chisquare(observed[i], f_exp=expected[i])
            p_values[i] = p
        except Exception:
            p_values[i] = 1.0
            
    return p_values

def run_single_replication(
    config: Dict[str, Any],
    data: np.ndarray,
    group_indices: np.ndarray,
    test_type: str,
    dependency_type: str,
    dependency_strength: float
) -> float:
    """
    Run a single replication of the simulation.
    
    Optimized to use vectorized operations where possible.
    
    Args:
        config: Simulation configuration
        data: Base data array
        group_indices: Group membership indices
        test_type: One of 't_test', 'anova', 'chi_squared'
        dependency_type: One of 'ar1', 'block', 'spatial'
        dependency_strength: Strength of dependency injection
        
    Returns:
        p-value from the statistical test.
    """
    try:
        # Generate null data (already done in main loop for efficiency)
        # Inject dependency
        if dependency_type == 'ar1':
            injected_data = ar1_inject(data, rho=dependency_strength)
        elif dependency_type == 'block':
            injected_data = block_bootstrap(data, block_size=10)
        elif dependency_type == 'spatial':
            injected_data = spatial_kernel_smooth(data, bandwidth=0.5)
        else:
            injected_data = data
            
        # Run test
        if test_type == 't_test':
            p_val = _vectorized_t_test(injected_data, group_indices)[0]
        elif test_type == 'anova':
            p_val = _vectorized_anova(injected_data, group_indices)[0]
        elif test_type == 'chi_squared':
            # Simplified for single replication
            observed = np.random.poisson(lam=5, size=4)
            expected = np.array([5, 5, 5, 5])
            _, p_val = stats.chisquare(observed, f_exp=expected)
        else:
            raise SimulationError(f"Unknown test type: {test_type}")
            
        return p_val
        
    except Exception as e:
        raise SimulationError(f"Replication failed: {str(e)}")

def run_simulation(
    config: Dict[str, Any],
    datasets: List[Dict[str, Any]],
    test_types: List[str],
    dependency_types: List[str],
    dependency_strengths: List[float],
    n_replications: int = 10000,
    output_path: str = "results/simulation_raw.csv"
) -> pd.DataFrame:
    """
    Run the full Monte Carlo simulation with optimization.
    
    Optimizations:
    1. Vectorized replication loops where possible
    2. Pre-computed group indices
    3. Batch processing of dependency injection
    4. Memory-efficient result accumulation
    
    Args:
        config: Simulation configuration
        datasets: List of loaded datasets
        test_types: List of test types to run
        dependency_types: List of dependency structures
        dependency_strengths: List of dependency strengths
        n_replications: Number of replications per config
        output_path: Path to save raw results
        
    Returns:
        DataFrame with all simulation results.
    """
    results = []
    config_obj = load_config()
    seed = config_obj.get('random_seed', 42)
    np.random.seed(seed)
    
    print(f"Starting simulation with {n_replications} replications...")
    start_time = time.time()
    
    for dataset in datasets:
        data = dataset['data']
        n_samples = data.shape[0]
        
        # Create group indices for t-test/ANOVA
        group_indices = np.random.choice([0, 1], size=n_samples)
        
        for test_type in test_types:
            for dep_type in dependency_types:
                for strength in dependency_strengths:
                    print(f"Running: {test_type}, {dep_type}, r={strength}")
                    
                    # Vectorized replication for efficiency
                    batch_size = 1000
                    n_batches = n_replications // batch_size
                    batch_results = []
                    
                    for batch_idx in range(n_batches):
                        # Generate null data for this batch
                        batch_data = np.random.normal(0, 1, (batch_size, n_samples))
                        
                        # Inject dependency (vectorized across batch)
                        if dep_type == 'ar1':
                            injected = ar1_inject(batch_data, rho=strength)
                        elif dep_type == 'block':
                            injected = block_bootstrap(batch_data, block_size=10)
                        elif dep_type == 'spatial':
                            injected = spatial_kernel_smooth(batch_data, bandwidth=0.5)
                        else:
                            injected = batch_data
                            
                        # Run tests
                        if test_type == 't_test':
                            p_vals = _vectorized_t_test(injected, group_indices)
                        elif test_type == 'anova':
                            p_vals = _vectorized_anova(injected, group_indices)
                        elif test_type == 'chi_squared':
                            # Simplified for batch
                            observed = np.random.poisson(lam=5, size=(batch_size, 4))
                            expected = np.ones((batch_size, 4)) * 5
                            p_vals = _vectorized_chi_squared(observed, expected)
                        else:
                            raise SimulationError(f"Unknown test: {test_type}")
                            
                        batch_results.append(p_vals)
                        
                    # Combine batch results
                    all_p_vals = np.concatenate(batch_results)
                    
                    # Calculate metrics
                    alpha = config_obj.get('alpha', 0.05)
                    type1_error = np.mean(all_p_vals < alpha)
                    
                    results.append({
                        'dataset': dataset['name'],
                        'test_type': test_type,
                        'dependency_type': dep_type,
                        'dependency_strength': strength,
                        'n_replications': n_replications,
                        'type1_error': type1_error,
                        'min_p': np.min(all_p_vals),
                        'max_p': np.max(all_p_vals),
                        'mean_p': np.mean(all_p_vals)
                    })
                    
    # Save results
    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    
    elapsed = time.time() - start_time
    print(f"Simulation completed in {elapsed:.2f} seconds ({elapsed/3600:.2f} hours)")
    
    return df

def save_edge_case_report(report: Dict[str, Any], path: str = "results/edge_case_report.json"):
    """Save edge case failures to JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)

def main():
    """Main entry point for simulation runner."""
    try:
        config = load_config()
        datasets = load_datasets()
        
        test_types = ['t_test', 'anova']
        dependency_types = ['ar1', 'block', 'spatial']
        dependency_strengths = [0, 0.1, 0.2, 0.3, 0.5]
        
        df = run_simulation(
            config=config,
            datasets=datasets,
            test_types=test_types,
            dependency_types=dependency_types,
            dependency_strengths=dependency_strengths,
            n_replications=10000,
            output_path="results/simulation_raw.csv"
        )
        
        print(f"Results saved to results/simulation_raw.csv")
        print(f"Total rows: {len(df)}")
        
    except Exception as e:
        print(f"Simulation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
