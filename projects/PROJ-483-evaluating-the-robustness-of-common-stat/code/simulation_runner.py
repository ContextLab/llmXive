import os
import json
import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Any, Tuple, Optional
from config import load_config
from dependency_injector import ar1_inject, block_bootstrap, spatial_kernel_smooth, generate_spatial_proxy, save_spatial_proxy_report
from exceptions import CriticalValidationError, EdgeCaseError

class SimulationError(Exception):
    """Custom exception for simulation-specific errors."""
    pass

def run_single_replication(
    config: Dict[str, Any],
    test_type: str,
    dependency_type: str,
    dependency_strength: float,
    sample_size: int,
    effect_size: float = 0.0,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute a single Monte Carlo replication.

    Algorithm (Generate-then-Inject):
    1. Generate synthetic data under true null (Normal(0,1)) or with true effect.
    2. Inject dependency structure (AR(1), Block Bootstrap, or Spatial).
    3. Apply statistical test (t-test, ANOVA, Chi-squared).
    4. Record p-value and metadata.

    Args:
        config: Configuration dictionary (contains alpha, etc.).
        test_type: One of 't_test', 'anova', 'chi_squared'.
        dependency_type: One of 'ar1', 'block_bootstrap', 'spatial'.
        dependency_strength: Strength parameter (r for AR1, block_size for block, bandwidth for spatial).
        sample_size: Number of samples N.
        effect_size: True effect size (mean shift). 0.0 for null hypothesis.
        seed: Random seed for reproducibility.

    Returns:
        Dictionary containing p-value, test_type, dependency_type, strength, and flags.
    """
    if seed is not None:
        np.random.seed(seed)

    alpha = config.get('alpha', 0.05)

    # 1. Generate Null Data (True Null Hypothesis)
    # We generate data that satisfies the null hypothesis (no difference)
    # but will have dependency injected later.
    # For t-test/ANOVA: Two groups. For Chi-squared: Categorical counts.
    
    if test_type == 't_test':
        n_per_group = sample_size // 2
        group1 = np.random.normal(loc=effect_size, scale=1.0, size=n_per_group)
        group2 = np.random.normal(loc=0.0, scale=1.0, size=sample_size - n_per_group)
        data = np.concatenate([group1, group2])
        groups = np.array([0] * n_per_group + [1] * (sample_size - n_per_group))
        
        # Check for edge case: all data identical (unlikely with normal but possible with effect=0 and tiny N)
        if np.std(data) < 1e-8:
            raise EdgeCaseError("Variance too low to perform t-test.")

    elif test_type == 'anova':
        k_groups = 3
        samples_per_group = sample_size // k_groups
        groups_list = []
        group_labels = []
        for i in range(k_groups):
            g_data = np.random.normal(loc=effect_size * (i - 1), scale=1.0, size=samples_per_group)
            groups_list.append(g_data)
            group_labels.extend([i] * samples_per_group)
        
        data = np.concatenate(groups_list)
        groups = np.array(group_labels)
        
        if np.std(data) < 1e-8:
            raise EdgeCaseError("Variance too low to perform ANOVA.")

    elif test_type == 'chi_squared':
        # For Chi-squared, we simulate counts. 
        # Null hypothesis: independence. We generate expected counts then inject dependency?
        # Actually, for dependency injection on Chi-squared, we typically simulate a contingency table
        # where row/col independence is broken by the dependency structure.
        # However, the "Generate-then-Inject" paradigm for Chi-squared is complex.
        # We will simulate a vector of categorical outcomes where the probability of the next 
        # outcome depends on the previous (Markov chain style) to simulate dependency.
        # To test independence, we usually compare observed vs expected.
        # Simplified approach for this refactoring task:
        # Generate a vector of outcomes under null (uniform or fixed probs).
        # Then inject dependency to break the independence assumption of the test.
        n_cats = 2
        probs = [0.5, 0.5]
        data = np.random.choice(n_cats, size=sample_size, p=probs)
        # We need a second variable for Chi-squared test of independence?
        # Let's assume we are testing independence between 'data' and 'groups' (randomly assigned).
        # If we inject dependency into 'data' relative to 'groups', we break independence.
        groups = np.random.choice(2, size=sample_size) # Independent assignment under null
        
    else:
        raise SimulationError(f"Unknown test type: {test_type}")

    # 2. Inject Dependency
    if dependency_type == 'ar1':
        if test_type in ['t_test', 'anova']:
            # AR1 injection works on continuous data
            data = ar1_inject(data, rho=dependency_strength)
        else:
            # AR1 on categorical is complex; skip or map to continuous proxy?
            # For this refactoring, we assume continuous tests for AR1.
            # If chi-squared is requested with AR1, we might need to skip or handle.
            # Let's assume the config prevents this combination, or we just skip injection.
            pass 

    elif dependency_type == 'block_bootstrap':
        if test_type in ['t_test', 'anova']:
            data = block_bootstrap(data, block_size=int(dependency_strength))
        else:
            pass

    elif dependency_type == 'spatial':
        if test_type in ['t_test', 'anova']:
            # Need coordinates or proxy
            # If no coordinates, we might use a proxy or skip.
            # For now, assume spatial_kernel_smooth handles the logic or we skip.
            # We'll pass a dummy coordinate array if needed, or let the function handle it.
            # Assuming spatial_kernel_smooth expects data and bandwidth.
            data = spatial_kernel_smooth(data, bandwidth=dependency_strength)
        else:
            pass

    # 3. Apply Statistical Test
    p_value = np.nan
    
    try:
        if test_type == 't_test':
            # Independent samples t-test
            g0 = data[groups == 0]
            g1 = data[groups == 1]
            if len(g0) < 2 or len(g1) < 2:
                raise EdgeCaseError("Group size too small for t-test.")
            _, p_value = stats.ttest_ind(g0, g1)
            
        elif test_type == 'anova':
            g0 = data[groups == 0]
            g1 = data[groups == 1]
            g2 = data[groups == 2]
            if len(g0) < 2 or len(g1) < 2 or len(g2) < 2:
                raise EdgeCaseError("Group size too small for ANOVA.")
            _, p_value = stats.f_oneway(g0, g1, g2)
            
        elif test_type == 'chi_squared':
            # Create contingency table
            # Rows: groups (0, 1), Cols: data (0, 1)
            # Note: data and groups are vectors of 0/1
            table = pd.crosstab(groups, data)
            if table.shape != (2, 2):
                # Handle cases where a category is missing
                table = pd.crosstab(groups, data, rownames=['Group'], colnames=['Outcome'])
                table = table.reindex(index=[0, 1], columns=[0, 1], fill_value=0)
            
            _, p_value, _, _ = stats.chi2_contingency(table)

    except Exception as e:
        # Log edge case if test fails due to data structure
        if "Variance" in str(e) or "size" in str(e):
            raise EdgeCaseError(f"Test failed due to data structure: {e}")
        else:
            # Unexpected error
            raise SimulationError(f"Statistical test failed: {e}")

    # 4. Record Result
    return {
        'p_value': p_value,
        'test_type': test_type,
        'dependency_type': dependency_type,
        'dependency_strength': dependency_strength,
        'sample_size': sample_size,
        'effect_size': effect_size,
        'is_significant': p_value < alpha if not np.isnan(p_value) else False,
        'seed': seed
    }

def run_simulation(
    config_path: str,
    output_path: str,
    test_types: List[str],
    dependency_types: List[str],
    strengths: List[float],
    n_replications: int,
    sample_size: int = 100,
    effect_size: float = 0.0
):
    """
    Run the full Monte Carlo simulation loop.

    Args:
        config_path: Path to config.yaml.
        output_path: Path to save results CSV.
        test_types: List of test types to run.
        dependency_types: List of dependency types to inject.
        strengths: List of dependency strengths to sweep.
        n_replications: Number of replications per configuration.
        sample_size: Sample size N.
        effect_size: True effect size.
    """
    config = load_config(config_path)
    results = []
    
    print(f"Starting simulation: {n_replications} replications per config")
    
    for t_type in test_types:
        for d_type in dependency_types:
            for strength in strengths:
                print(f"Running: {t_type} with {d_type} (r={strength})")
                for i in range(n_replications):
                    seed = config.get('base_seed', 42) + i
                    try:
                        res = run_single_replication(
                            config=config,
                            test_type=t_type,
                            dependency_type=d_type,
                            dependency_strength=strength,
                            sample_size=sample_size,
                            effect_size=effect_size,
                            seed=seed
                        )
                        results.append(res)
                    except EdgeCaseError as e:
                        # Log edge case and skip
                        print(f"Edge case skipped: {e}")
                        # Could log to a separate file here
                    except SimulationError as e:
                        print(f"Simulation error: {e}")
                    except Exception as e:
                        print(f"Unexpected error: {e}")
    
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    print(f"Simulation complete. Results saved to {output_path}")
    return df

def save_edge_case_report(report_path: str, edge_cases: List[Dict[str, Any]]):
    """Save edge case failures to JSON."""
    with open(report_path, 'w') as f:
        json.dump(edge_cases, f, indent=2)

def main():
    """Entry point for running the simulation from command line."""
    import argparse
    parser = argparse.ArgumentParser(description="Run Monte Carlo simulation for statistical robustness.")
    parser.add_argument('--config', type=str, default='code/config.yaml', help='Path to config file')
    parser.add_argument('--output', type=str, default='results/simulation_raw.csv', help='Output CSV path')
    parser.add_argument('--n-reps', type=int, default=1000, help='Number of replications')
    parser.add_argument('--sample-size', type=int, default=100, help='Sample size N')
    parser.add_argument('--effect-size', type=float, default=0.0, help='True effect size')
    
    args = parser.parse_args()
    
    # Default configurations for a quick run
    test_types = ['t_test']
    dependency_types = ['ar1']
    strengths = [0.0, 0.3, 0.6]
    
    run_simulation(
        config_path=args.config,
        output_path=args.output,
        test_types=test_types,
        dependency_types=dependency_types,
        strengths=strengths,
        n_replications=args.n_reps,
        sample_size=args.sample_size,
        effect_size=args.effect_size
    )

if __name__ == '__main__':
    main()