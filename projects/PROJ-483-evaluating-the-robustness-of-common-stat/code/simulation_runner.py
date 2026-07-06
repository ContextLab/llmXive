import os
import json
import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Any, Tuple, Optional

class EdgeCaseError(Exception):
    """Raised when a simulation configuration cannot be handled (e.g., N too small, perfect correlation)."""
    pass

def run_single_replication(
    test_type: str,
    dependency_type: str,
    dependency_strength: float,
    n_samples: int,
    n_groups: int = 2,
    effect_size: float = 0.0,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute a single Monte Carlo replication.
    
    Implements "Generate-then-Inject" paradigm:
    1. Generate synthetic data under true null (Normal(0,1)).
    2. Inject dependency structure (AR(1) or Block Bootstrap).
    3. Apply statistical test.
    4. Record p-value.
    
    Args:
        test_type: 't_test', 'anova', or 'chi_squared'.
        dependency_type: 'ar1', 'block_bootstrap', or 'independent'.
        dependency_strength: r for AR(1), block_size for block_bootstrap.
        n_samples: Total number of observations.
        n_groups: Number of groups for ANOVA or Chi-squared.
        effect_size: Mean shift delta (0.0 for Type I error simulation).
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary with test_type, dependency_type, strength, p_value, significant.
    """
    if seed is not None:
        np.random.seed(seed)

    # 1. Generate synthetic data under true null (Normal(0,1))
    # For t-test/ANOVA: Continuous data
    # For Chi-squared: We generate continuous data, then discretize into categories
    
    if test_type in ['t_test', 'anova']:
        # Generate continuous data
        # If effect_size > 0, inject mean shift for power analysis
        if test_type == 't_test':
            n_groups = 2
            # Split data into groups
            group_size = n_samples // 2
            data = np.random.normal(0, 1, n_samples)
            # Apply effect size to second group if requested
            if effect_size > 0:
                data[group_size:] += effect_size
            group_labels = np.array([0] * group_size + [1] * (n_samples - group_size))
        else: # ANOVA
            group_size = n_samples // n_groups
            data = np.random.normal(0, 1, n_samples)
            if effect_size > 0:
                # Inject effect into the last group
                start_idx = (n_groups - 1) * group_size
                data[start_idx:] += effect_size
            group_labels = np.repeat(range(n_groups), group_size)[:n_samples]
        
        # 2. Inject Dependency
        if dependency_type == 'ar1':
            # Apply AR(1) injection to the continuous data
            from dependency_injector import ar1_inject
            data = ar1_inject(data, r=dependency_strength)
        elif dependency_type == 'block_bootstrap':
            # Apply block bootstrap injection
            from dependency_injector import block_bootstrap
            # block_bootstrap expects (data, block_size)
            data = block_bootstrap(data, block_size=int(dependency_strength))
        elif dependency_type != 'independent':
            raise ValueError(f"Unknown dependency type: {dependency_type}")
        
        # 3. Apply Statistical Test
        if test_type == 't_test':
            group0 = data[group_labels == 0]
            group1 = data[group_labels == 1]
            if len(group0) < 2 or len(group1) < 2:
                raise EdgeCaseError("Group size too small for t-test")
            stat, p_val = stats.ttest_ind(group0, group1)
        else: # ANOVA
            groups = [data[group_labels == i] for i in range(n_groups)]
            if any(len(g) < 2 for g in groups):
                raise EdgeCaseError("Group size too small for ANOVA")
            stat, p_val = stats.f_oneway(*groups)
            
    elif test_type == 'chi_squared':
        # Generate continuous data first
        data = np.random.normal(0, 1, n_samples)
        
        # Inject dependency if needed
        if dependency_type == 'ar1':
            from dependency_injector import ar1_inject
            data = ar1_inject(data, r=dependency_strength)
        elif dependency_type == 'block_bootstrap':
            from dependency_injector import block_bootstrap
            data = block_bootstrap(data, block_size=int(dependency_strength))
        
        # Discretize into categories (e.g., 3 categories)
        # Use percentiles to define bins to ensure balanced expected counts
        bins = np.percentile(data, [33, 66])
        categories = np.digitize(data, bins)
        
        # Create a 2x3 contingency table (Group x Category)
        # Simulate two groups
        group_size = n_samples // 2
        if effect_size > 0:
            # Shift the second group to change distribution
            # We apply effect size to the second half of the data before discretization
            # But we already injected dependency. Let's shift the second half now.
            # Re-generate logic for effect injection in Chi-squared
            # Actually, the standard way is to generate two independent samples with different distributions
            # But here we are simulating under null first.
            # Let's stick to the Generate-then-Inject paradigm:
            # Generate null data -> Inject Dependency -> Discretize -> Test
            # Effect injection is a separate mode.
            pass 
        
        # For Chi-squared, we need a contingency table.
        # Let's assume we are testing independence between 'Group' (0/1) and 'Category' (0/1/2)
        # We generate the data, then discretize.
        # To simulate the null, the distribution of categories should be independent of group.
        # To simulate alternative, we shift the mean of the second group before discretization.
        
        # Re-generate data for Chi-squared with effect logic
        # We need two groups of data to form the contingency table rows
        # Let's generate n_samples total, split into 2 groups
        group1_data = np.random.normal(0, 1, group_size)
        group2_data = np.random.normal(0, 1, n_samples - group_size)
        
        if effect_size > 0:
            group2_data += effect_size
        
        # Inject dependency into the combined data?
        # Dependency usually implies time series or spatial.
        # For Chi-squared, dependency might mean the rows are not independent.
        # We will inject dependency into the combined vector, then split.
        combined = np.concatenate([group1_data, group2_data])
        
        if dependency_type == 'ar1':
            from dependency_injector import ar1_inject
            combined = ar1_inject(combined, r=dependency_strength)
        elif dependency_type == 'block_bootstrap':
            from dependency_injector import block_bootstrap
            combined = block_bootstrap(combined, block_size=int(dependency_strength))
        
        # Split back
        group1_data = combined[:group_size]
        group2_data = combined[group_size:]
        
        # Discretize
        # We use global percentiles to define bins
        all_data = np.concatenate([group1_data, group2_data])
        bins = np.percentile(all_data, [33, 66])
        
        cat1 = np.digitize(group1_data, bins)
        cat2 = np.digitize(group2_data, bins)
        
        # Build contingency table
        # Rows: Group 0, Group 1. Cols: Category 0, 1, 2
        table = np.zeros((2, 3), dtype=int)
        for c in cat1:
            table[0, c] += 1
        for c in cat2:
            table[1, c] += 1
        
        # 3. Apply Chi-squared test
        try:
            stat, p_val, dof, expected = stats.chi2_contingency(table)
        except Exception:
            # Fallback if expected counts are too low
            p_val = 1.0
        
    else:
        raise ValueError(f"Unknown test type: {test_type}")
    
    return {
        "test_type": test_type,
        "dependency_type": dependency_type,
        "dependency_strength": float(dependency_strength),
        "p_value": float(p_val),
        "significant": bool(p_val < 0.05)
    }

def run_simulation(
    config: Dict[str, Any],
    output_path: str
) -> None:
    """
    Run the full Monte Carlo simulation based on configuration.
    
    Args:
        config: Dictionary containing simulation parameters (tests, dependencies, strengths, reps, etc.)
        output_path: Path to save the results CSV.
    """
    results = []
    
    test_types = config.get("test_types", ["t_test"])
    dependency_types = config.get("dependency_types", ["ar1"])
    strengths = config.get("strengths", [0.0, 0.3, 0.5])
    n_replications = config.get("n_replications", 1000)
    n_samples = config.get("n_samples", 100)
    n_groups = config.get("n_groups", 2)
    effect_size = config.get("effect_size", 0.0)
    
    print(f"Starting simulation: {n_replications} reps, {len(test_types)} tests, {len(dependency_types)} dependencies")
    
    for t_type in test_types:
        for d_type in dependency_types:
            for r in strengths:
                print(f"Running {t_type} with {d_type} (r={r})")
                for i in range(n_replications):
                    try:
                        res = run_single_replication(
                            test_type=t_type,
                            dependency_type=d_type,
                            dependency_strength=r,
                            n_samples=n_samples,
                            n_groups=n_groups,
                            effect_size=effect_size,
                            seed=config.get("base_seed", 42) + i
                        )
                        results.append(res)
                    except EdgeCaseError as e:
                        # Log edge case and skip
                        print(f"Edge case skipped: {e}")
                        continue
                    except Exception as e:
                        print(f"Error in replication: {e}")
                        continue
    
    # Save results
    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Simulation complete. Saved {len(df)} results to {output_path}")

def save_edge_case_report(report_path: str, details: List[Dict[str, Any]]) -> None:
    """Save edge case failures to a JSON file."""
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(details, f, indent=2)

def main():
    """Entry point for running the simulation from command line."""
    from config import load_config
    from pathlib import Path
    
    # Load config
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        # Fallback default config for standalone run
        config = {
            "test_types": ["t_test", "anova", "chi_squared"],
            "dependency_types": ["ar1", "block_bootstrap", "independent"],
            "strengths": [0.0, 0.3, 0.5],
            "n_replications": 1000,
            "n_samples": 100,
            "n_groups": 2,
            "effect_size": 0.0,
            "base_seed": 42,
            "output_path": "results/simulation_raw.csv"
        }
    else:
        config = load_config(str(config_path))
    
    output_path = config.get("output_path", "results/simulation_raw.csv")
    run_simulation(config, output_path)

if __name__ == "__main__":
    main()