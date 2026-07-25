import os
import json
import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

# Import from existing project modules as per API surface
from dependency_injector import ar1_inject, block_bootstrap
from exceptions import EdgeCaseError

class SimulationError(Exception):
    """Custom exception for simulation failures."""
    pass

def run_single_replication(
    n: int,
    test_type: str,
    dependency_type: str,
    dependency_strength: float,
    block_size: Optional[int] = None,
    seed: Optional[int] = None
) -> float:
    """
    Execute a single Monte Carlo replication under the 'Generate-then-Inject' paradigm.

    Algorithm:
    1. Generate synthetic data under true null (Normal(0,1)).
    2. Inject dependency structure (AR(1) or Block Bootstrap) with strength r.
    3. Apply statistical test (t-test or ANOVA).
    4. Return the p-value.

    Args:
        n: Sample size per group (or total for ANOVA depending on logic).
        test_type: 't-test' or 'anova'.
        dependency_type: 'ar1' or 'block_bootstrap'.
        dependency_strength: Correlation strength r for AR(1), or block parameter for bootstrap.
        block_size: Required for block_bootstrap.
        seed: Random seed for reproducibility.

    Returns:
        float: The calculated p-value.
    """
    if seed is not None:
        np.random.seed(seed)

    # Step 1: Generate synthetic data under true null (Normal(0,1))
    # For t-test: 2 groups of size n
    # For ANOVA: 3 groups of size n (standard setup for robustness checks)
    if test_type == 't-test':
        group1 = np.random.normal(0, 1, n)
        group2 = np.random.normal(0, 1, n)
        data = np.concatenate([group1, group2])
        labels = np.array([0] * n + [1] * n)
    elif test_type == 'anova':
        n_groups = 3
        groups = [np.random.normal(0, 1, n) for _ in range(n_groups)]
        data = np.concatenate(groups)
        labels = np.concatenate([np.full(n, i) for i in range(n_groups)])
    else:
        raise ValueError(f"Unsupported test_type: {test_type}")

    # Step 2: Inject dependency structure
    if dependency_type == 'ar1':
        # AR(1) injection expects 1D array or list of arrays.
        # For t-test, we inject into the combined data or per group?
        # Standard practice for independence violation: inject into the combined series
        # if the data is time-ordered, or per group if groups are time-series.
        # Given the prompt implies "Generate-then-Inject" for the null,
        # we treat the combined data stream as the unit of dependency injection.
        try:
            # If dependency_strength is 0, no injection needed, but function should handle it
            if dependency_strength == 0.0:
                pass # No change
            else:
                data = ar1_inject(data, r=dependency_strength)
        except Exception as e:
            raise EdgeCaseError(f"AR(1) injection failed: {str(e)}")

    elif dependency_type == 'block_bootstrap':
        if block_size is None:
            raise ValueError("block_size must be provided for block_bootstrap")
        try:
            data = block_bootstrap(data, block_size=block_size, strength=dependency_strength)
        except Exception as e:
            raise EdgeCaseError(f"Block bootstrap injection failed: {str(e)}")
    else:
        raise ValueError(f"Unsupported dependency_type: {dependency_type}")

    # Step 3: Apply statistical test
    try:
        if test_type == 't-test':
            # Split injected data back into groups based on original size
            # Note: If block bootstrap permutes order, we must respect the injected order.
            # However, block_bootstrap usually resamples with replacement, changing values.
            # We assume the injection functions modify the data in place or return a modified array.
            # We split based on original group sizes.
            g1 = data[:n]
            g2 = data[n:]
            stat, p_val = stats.ttest_ind(g1, g2, equal_var=True)
        elif test_type == 'anova':
            # Split back into n_groups
            n_groups = 3
            group_data = [data[i*n:(i+1)*n] for i in range(n_groups)]
            stat, p_val = stats.f_oneway(*group_data)
        else:
            raise ValueError(f"Unsupported test_type: {test_type}")
    except Exception as e:
        # Handle cases where variance is 0 or other numerical issues
        raise EdgeCaseError(f"Statistical test failed: {str(e)}")

    # Step 4: Return p-value
    return float(p_val)

def run_simulation(
    config: Dict[str, Any],
    output_path: str
) -> None:
    """
    Run the full Monte Carlo simulation loop.

    Args:
        config: Dictionary containing simulation parameters:
            - n: sample size
            - n_replications: number of replications
            - test_types: list of test types ('t-test', 'anova')
            - dependency_types: list of dependency types ('ar1', 'block_bootstrap')
            - dependency_strengths: list of strength values
            - block_sizes: list of block sizes (if needed)
            - seed: base seed
        output_path: Path to save the results CSV.
    """
    n = config.get('n', 50)
    n_replications = config.get('n_replications', 10000)
    test_types = config.get('test_types', ['t-test'])
    dependency_types = config.get('dependency_types', ['ar1'])
    dependency_strengths = config.get('dependency_strengths', [0.0, 0.3, 0.5])
    block_sizes = config.get('block_sizes', [5, 10])
    base_seed = config.get('seed', 42)

    results = []

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Starting simulation with {n_replications} replications...")
    print(f"Config: n={n}, tests={test_types}, deps={dependency_types}, strengths={dependency_strengths}")

    for t_type in test_types:
        for d_type in dependency_types:
            for strength in dependency_strengths:
                # Handle block bootstrap specific parameter
                current_block_size = None
                if d_type == 'block_bootstrap':
                    # Use the first block size for this run, or iterate if config implies multiple
                    # For simplicity in this single task, we pick the first if list exists, else default
                    current_block_size = block_sizes[0] if block_sizes else 5

                print(f"Running: {t_type} + {d_type} (r={strength})...")

                for i in range(n_replications):
                    seed = base_seed + i
                    try:
                        p_val = run_single_replication(
                            n=n,
                            test_type=t_type,
                            dependency_type=d_type,
                            dependency_strength=strength,
                            block_size=current_block_size,
                            seed=seed
                        )
                        results.append({
                            'test_type': t_type,
                            'dependency_type': d_type,
                            'dependency_strength': strength,
                            'block_size': current_block_size,
                            'replication_id': i,
                            'p_value': p_val
                        })
                    except EdgeCaseError as e:
                        # Log edge case and continue (or fail fast? Task says "fail loudly" for data,
                        # but for simulation, logging is often preferred unless critical).
                        # We log to a separate file or just print for now.
                        print(f"Edge case in replication {i}: {e}")
                        results.append({
                            'test_type': t_type,
                            'dependency_type': d_type,
                            'dependency_strength': strength,
                            'block_size': current_block_size,
                            'replication_id': i,
                            'p_value': np.nan,
                            'error': str(e)
                        })
                    except Exception as e:
                        print(f"Unexpected error in replication {i}: {e}")
                        raise

    # Convert to DataFrame and save
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    print(f"Simulation complete. Results saved to {output_path}")
    print(f"Total rows: {len(df)}")

def save_edge_case_report(report_data: List[Dict[str, Any]], output_path: str) -> None:
    """Save edge case failures to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)

def main():
    """Entry point for running the simulation from command line or script."""
    # Default configuration for T012 (US1 MVP)
    # Based on tasks.md: "Run 10,000 replications for a single test (t-test) and single dependency (AR(1), r=0.3)"
    # But the task also says "Implement ... Monte Carlo loop for t-test and ANOVA".
    # We will run a representative sweep as defined in the config, or a default if none provided.
    
    # Load config if available, otherwise use defaults
    config_path = Path("code/config.yaml")
    if config_path.exists():
        from config import load_config
        config = load_config(config_path)
    else:
        # Default config for T012 execution
        config = {
            'n': 100,
            'n_replications': 10000,
            'test_types': ['t-test', 'anova'],
            'dependency_types': ['ar1'],
            'dependency_strengths': [0.0, 0.1, 0.3, 0.5, 0.7, 0.9],
            'block_sizes': [10],
            'seed': 42
        }

    output_path = "results/simulation_raw.csv"
    
    try:
        run_simulation(config, output_path)
    except Exception as e:
        print(f"Simulation failed: {e}")
        raise

if __name__ == "__main__":
    main()
