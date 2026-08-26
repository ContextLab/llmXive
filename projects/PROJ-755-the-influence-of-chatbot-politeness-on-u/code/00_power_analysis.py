import os
import sys
import math
import json
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np
from statsmodels.stats.power import TTestIndPower, FTestAnovaPower
from statsmodels.stats.weightstats import ttest_ind

# Constants
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.80
DEFAULT_EFFECT_SIZE = 0.3  # Cohen's d for medium effect

def estimate_sample_size_from_pilot(pilot_data: pd.DataFrame, 
                                    treatment_col: str, 
                                    outcome_col: str,
                                    alpha: float = DEFAULT_ALPHA,
                                    power: float = DEFAULT_POWER) -> Dict[str, Any]:
    """
    Estimates required sample size based on pilot data.
    Assumes a two-group comparison (treatment vs control) for simplicity.
    
    Args:
        pilot_data: DataFrame containing pilot data.
        treatment_col: Column name indicating group (e.g., 'politeness_level' or binary group).
        outcome_col: Column name for the outcome variable (e.g., 'quality_rating').
        alpha: Significance level.
        power: Desired statistical power.
        
    Returns:
        Dictionary with estimated sample size per group, effect size, and total sample size.
    """
    # Ensure we have data
    if pilot_data is None or pilot_data.empty:
        raise ValueError("Pilot data cannot be empty.")
        
    # Simple heuristic: if treatment_col is continuous, bin into two groups (high/low)
    if treatment_col not in pilot_data.columns:
        raise ValueError(f"Treatment column '{treatment_col}' not found in pilot data.")
        
    if outcome_col not in pilot_data.columns:
        raise ValueError(f"Outcome column '{outcome_col}' not found in pilot data.")
        
    # Create binary groups if necessary (median split)
    if pilot_data[treatment_col].dtype in ['float64', 'int64']:
        median_val = pilot_data[treatment_col].median()
        groups = (pilot_data[treatment_col] > median_val).astype(int)
    else:
        groups = pilot_data[treatment_col]
        
    # Filter out NaNs in outcome
    valid_mask = ~pilot_data[outcome_col].isna() & ~groups.isna()
    df_clean = pilot_data[valid_mask]
    groups_clean = groups[valid_mask]
    outcomes_clean = df_clean[outcome_col]
    
    # Split into two groups (0 and 1)
    g0 = outcomes_clean[groups_clean == 0]
    g1 = outcomes_clean[groups_clean == 1]
    
    if len(g0) < 2 or len(g1) < 2:
        # Fallback to default effect size if groups are too small
        effect_size = DEFAULT_EFFECT_SIZE
        sample_size_per_group = TTestIndPower().solve_power(
            effect_size=effect_size, alpha=alpha, power=power, ratio=1.0
        )
        return {
            "effect_size": effect_size,
            "sample_size_per_group": int(math.ceil(sample_size_per_group)),
            "total_sample_size": int(math.ceil(sample_size_per_group * 2)),
            "method": "default_effect_size",
            "reason": "Pilot groups too small to estimate effect size reliably"
        }
        
    # Calculate Cohen's d
    mean_diff = g1.mean() - g0.mean()
    pooled_std = np.sqrt(((len(g0) - 1) * g0.var() + (len(g1) - 1) * g1.var()) / (len(g0) + len(g1) - 2))
    
    if pooled_std == 0:
        effect_size = 0.0
    else:
        effect_size = mean_diff / pooled_std
        
    # Estimate sample size using TTestIndPower
    power_analysis = TTestIndPower()
    try:
        sample_size_per_group = power_analysis.solve_power(
            effect_size=abs(effect_size), alpha=alpha, power=power, ratio=1.0
        )
    except Exception:
        # Fallback if calculation fails
        sample_size_per_group = TTestIndPower().solve_power(
            effect_size=DEFAULT_EFFECT_SIZE, alpha=alpha, power=power, ratio=1.0
        )
        
    return {
        "effect_size": float(effect_size),
        "sample_size_per_group": int(math.ceil(sample_size_per_group)),
        "total_sample_size": int(math.ceil(sample_size_per_group * 2)),
        "method": "pilot_data",
        "pilot_group_0_n": int(len(g0)),
        "pilot_group_1_n": int(len(g1)),
        "pilot_mean_0": float(g0.mean()) if len(g0) > 0 else None,
        "pilot_mean_1": float(g1.mean()) if len(g1) > 0 else None,
        "pilot_std_0": float(g0.std()) if len(g0) > 0 else None,
        "pilot_std_1": float(g1.std()) if len(g1) > 0 else None
    }

def calculate_mde_for_proportions_or_means(sample_size: int, 
                                           alpha: float = DEFAULT_ALPHA,
                                           power: float = DEFAULT_POWER,
                                           baseline_rate: Optional[float] = None,
                                           group_ratio: float = 1.0) -> Dict[str, Any]:
    """
    Calculates the Minimum Detectable Effect (MDE) for a given sample size.
    Supports both proportion tests (if baseline_rate is provided) and mean tests.
    
    Args:
        sample_size: Total sample size.
        alpha: Significance level.
        power: Desired statistical power.
        baseline_rate: Baseline rate for proportion tests (e.g., 0.5 for 50%).
        group_ratio: Ratio of sample sizes between groups (n1/n2).
        
    Returns:
        Dictionary with MDE, type of test, and parameters used.
    """
    n_per_group = sample_size / (1 + group_ratio)
    
    if baseline_rate is not None:
        # Proportion test
        from statsmodels.stats.power import zt_ind_solve_power
        try:
            # Solve for effect size (difference in proportions)
            mde = zt_ind_solve_power(
                power=power, alpha=alpha, nobs1=n_per_group, ratio=group_ratio
            )
            # This is an approximation; we need to solve for effect size explicitly
            # Using a numerical approach
            effect_size = None
            for est_effect in np.linspace(0.01, 1.0, 1000):
                # Approximate power for proportion test
                # Using normal approximation
                p1 = baseline_rate
                p2 = baseline_rate + est_effect
                if p2 > 1.0:
                    break
                
                pooled_p = (p1 + p2) / 2
                se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n_per_group + 1/n_per_group))
                z_stat = est_effect / se
                # Critical z for alpha
                from scipy.stats import norm
                z_crit = norm.ppf(1 - alpha/2)
                # Power is probability of rejecting null when alternative is true
                # This is a simplification
                if z_stat > z_crit:
                    effect_size = est_effect
                    break
                    
            if effect_size is None:
                effect_size = 0.5 # Default fallback
                
            return {
                "mde": float(effect_size),
                "type": "proportion",
                "baseline_rate": baseline_rate,
                "sample_size": sample_size,
                "alpha": alpha,
                "power": power
            }
        except Exception:
            # Fallback
            return {
                "mde": 0.2,
                "type": "proportion",
                "baseline_rate": baseline_rate,
                "sample_size": sample_size,
                "alpha": alpha,
                "power": power,
                "note": "Calculation fallback"
            }
    else:
        # Mean test (Cohen's d)
        power_analysis = TTestIndPower()
        try:
            effect_size = power_analysis.solve_power(
                nobs1=n_per_group, alpha=alpha, power=power, ratio=group_ratio
            )
            return {
                "mde": float(effect_size),
                "type": "mean",
                "sample_size": sample_size,
                "alpha": alpha,
                "power": power
            }
        except Exception:
            return {
                "mde": 0.5,
                "type": "mean",
                "sample_size": sample_size,
                "alpha": alpha,
                "power": power,
                "note": "Calculation fallback"
            }

def update_research_md(research_md_path: str, power_results: Dict[str, Any]) -> None:
    """
    Appends the MDE_Estimation section to research.md.
    
    Args:
        research_md_path: Path to the research.md file.
        power_results: Dictionary containing power analysis results.
    """
    research_md_path = Path(research_md_path)
    
    if not research_md_path.exists():
        # Create the file if it doesn't exist
        research_md_path.parent.mkdir(parents=True, exist_ok=True)
        with open(research_md_path, 'w') as f:
            f.write("# Research Notes\n\n")
            
    section_header = "\n## MDE_Estimation\n\n"
    section_content = f"""- **minimum_detectable_effect**: {power_results.get('mde', 'N/A')}
- **power**: {power_results.get('power', DEFAULT_POWER)}
- **sample_size**: {power_results.get('total_sample_size', power_results.get('sample_size', 'N/A'))}
- **method**: {power_results.get('method', 'N/A')}
"""
    
    if power_results.get('type'):
        section_content += f"- **effect_type**: {power_results.get('type')}\n"
        
    if power_results.get('reason'):
        section_content += f"- **notes**: {power_results.get('reason')}\n"
        
    # Read existing content
    with open(research_md_path, 'r') as f:
        content = f.read()
        
    # Check if section already exists
    if "## MDE_Estimation" in content:
        # Replace the existing section
        lines = content.split('\n')
        new_lines = []
        skip_until_next_header = False
        for i, line in enumerate(lines):
            if line.strip().startswith("## MDE_Estimation"):
                skip_until_next_header = True
                new_lines.append(line)
                new_lines.append(section_content.strip())
                # Skip until next header
                continue
            elif skip_until_next_header and line.strip().startswith("##"):
                skip_until_next_header = False
                new_lines.append(line)
            elif not skip_until_next_header:
                new_lines.append(line)
                
        content = '\n'.join(new_lines)
    else:
        content += section_header + section_content
        
    with open(research_md_path, 'w') as f:
        f.write(content)

def main():
    """
    Main entry point for power analysis.
    Tries to load pilot data from data/processed/scored_dialogues.parquet if available,
    otherwise uses default parameters.
    """
    # Default paths
    research_md_path = Path("research.md")
    pilot_data_path = Path("data/processed/scored_dialogues.parquet")
    
    # Check if pilot data exists
    if pilot_data_path.exists():
        print(f"Loading pilot data from {pilot_data_path}")
        try:
            pilot_data = pd.read_parquet(pilot_data_path)
            
            # Try to find relevant columns
            # Assuming 'politeness_score' and 'quality_rating' are available
            if 'politeness_score' in pilot_data.columns and 'quality_rating' in pilot_data.columns:
                results = estimate_sample_size_from_pilot(
                    pilot_data, 
                    treatment_col='politeness_score', 
                    outcome_col='quality_rating'
                )
                print("Power analysis completed using pilot data.")
            else:
                print("Required columns not found in pilot data. Using default parameters.")
                # Fall back to default
                sample_size = 200 # Default guess
                results = calculate_mde_for_proportions_or_means(sample_size)
                results['method'] = 'default_parameters'
                results['reason'] = 'Pilot data missing required columns'
        except Exception as e:
            print(f"Error loading pilot data: {e}. Using default parameters.")
            sample_size = 200
            results = calculate_mde_for_proportions_or_means(sample_size)
            results['method'] = 'default_parameters'
            results['reason'] = f'Error loading pilot data: {e}'
    else:
        print("Pilot data not found. Using default parameters.")
        sample_size = 200
        results = calculate_mde_for_proportions_or_means(sample_size)
        results['method'] = 'default_parameters'
        results['reason'] = 'Pilot data not found'
        
    # Update research.md
    update_research_md(str(research_md_path), results)
    print(f"Updated {research_md_path} with MDE estimation.")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()