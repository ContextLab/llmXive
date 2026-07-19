import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

def calculate_confidence_interval(proportions: List[float], n: int, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculates the Clopper-Pearson exact confidence interval for a proportion.
    
    Args:
        proportions: List of boolean-like values (1.0 for success, 0.0 for failure)
        n: Total number of trials
        alpha: Significance level (default 0.05 for 95% CI)
    
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if n == 0:
        return 0.0, 0.0
    
    successes = int(sum(proportions))
    # Clopper-Pearson exact interval
    lower = stats.beta.ppf(alpha/2, successes, n - successes + 1) if successes > 0 else 0.0
    upper = stats.beta.ppf(1 - alpha/2, successes + 1, n - successes) if successes < n else 1.0
    
    return float(lower), float(upper)

def generate_error_rate_plot(results_df: pd.DataFrame, output_path: str = "figures/error_rate_plot.png"):
    """
    Generates a plot showing empirical error rates vs nominal alpha with 95% CI.
    
    Input DataFrame expected to have columns: 
    [scaling_method, error_rate, ci_lower, ci_upper] OR 
    raw simulation results with [p_value, ground_truth, scaling_method, test_type]
    
    If the input contains pre-aggregated metrics (error_rate, ci_lower, ci_upper), 
    it plots those directly. If it contains raw p-values, it aggregates them first.
    
    Args:
        results_df: DataFrame containing simulation results or aggregate metrics
        output_path: Path to save the generated figure
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    nominal_alpha = 0.05
    
    # Check if we have pre-aggregated data or need to aggregate raw data
    has_pre_aggregated = all(col in results_df.columns for col in ['scaling_method', 'error_rate', 'ci_lower', 'ci_upper'])
    
    if has_pre_aggregated:
        plot_df = results_df.copy()
        # Ensure we only plot relevant columns
        if 'test_type' in plot_df.columns:
            hue_col = 'test_type'
        else:
            hue_col = None
    else:
        # Aggregate raw simulation results
        plot_data = []
        
        # Group by scaling_method and optionally test_type
        group_cols = ['scaling_method']
        if 'test_type' in results_df.columns:
            group_cols.append('test_type')
        
        for group_name, group in results_df.groupby(group_cols):
            if isinstance(group_name, tuple):
                scaling_method = group_name[0]
                test_type = group_name[1]
            else:
                scaling_method = group_name
                test_type = None
            
            # Filter for null hypothesis cases to calculate Type I error
            if 'ground_truth' in group.columns:
                null_group = group[group['ground_truth'] == 'null']
            else:
                # If no ground_truth column, assume all are null for this aggregation
                null_group = group
            
            if len(null_group) == 0:
                continue
            
            # Calculate empirical error rate
            if 'p_value' in null_group.columns:
                empirical_rate = (null_group['p_value'] < nominal_alpha).mean()
                # Calculate Clopper-Pearson CI
                successes = int((null_group['p_value'] < nominal_alpha).sum())
                n = len(null_group)
                ci_low, ci_high = calculate_confidence_interval(
                    [1.0 if p < nominal_alpha else 0.0 for p in null_group['p_value']], 
                    n
                )
            else:
                # If error_rate is already provided in the group
                empirical_rate = group['error_rate'].iloc[0] if 'error_rate' in group.columns else 0.0
                ci_low = group['ci_lower'].iloc[0] if 'ci_lower' in group.columns else 0.0
                ci_high = group['ci_upper'].iloc[0] if 'ci_upper' in group.columns else 0.0
            
            row = {
                'scaling_method': scaling_method,
                'empirical_rate': empirical_rate,
                'ci_low': ci_low,
                'ci_high': ci_high
            }
            
            if test_type:
                row['test_type'] = test_type
            
            plot_data.append(row)
        
        plot_df = pd.DataFrame(plot_data)
        hue_col = 'test_type' if 'test_type' in plot_df.columns else None
    
    if plot_df.empty:
        logger.warning("No data available for error rate plot.")
        # Create an empty plot to satisfy the requirement of producing the file
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Empirical Error Rate vs Nominal Alpha')
        ax.set_xlabel('Scaling Method')
        ax.set_ylabel('Empirical Error Rate')
        plt.savefig(output_path, dpi=150)
        plt.close()
        return

    # Create the plot
    plt.figure(figsize=(12, 8))
    
    if hue_col and hue_col in plot_df.columns:
        sns.scatterplot(
            data=plot_df,
            x='scaling_method',
            y='empirical_rate',
            hue=hue_col,
            s=100,
            edgecolor='black',
            palette='viridis'
        )
    else:
        sns.scatterplot(
            data=plot_df,
            x='scaling_method',
            y='empirical_rate',
            s=100,
            edgecolor='black',
            color='steelblue'
        )
    
    # Add error bars for 95% CI
    for i, row in plot_df.iterrows():
        x_pos = i if hue_col is None else plot_df[plot_df[hue_col] == row.get(hue_col, '')].index.get_loc(i)
        
        # Calculate asymmetric error bars
        yerr_lower = row['empirical_rate'] - row['ci_low']
        yerr_upper = row['ci_high'] - row['empirical_rate']
        
        plt.errorbar(
            x=row['scaling_method'],
            y=row['empirical_rate'],
            yerr=[[yerr_lower], [yerr_upper]],
            fmt='none',
            ecolor='gray',
            capsize=5,
            capthick=1.5,
            elinewidth=1.5
        )
    
    # Add nominal alpha reference line
    plt.axhline(y=nominal_alpha, color='red', linestyle='--', linewidth=2, 
               label=f'Nominal Alpha ({nominal_alpha})')
    
    # Add a band for the 95% CI of the nominal rate (optional, for context)
    # This shows the expected variation if the test is perfectly calibrated
    expected_count = int(nominal_alpha * 1000) # Assuming ~1000 tests per group
    _, expected_ci = calculate_confidence_interval([nominal_alpha]*1000, 1000)
    plt.axhspan(expected_ci[0], expected_ci[1], color='red', alpha=0.1, label='Expected 95% CI band')
    
    plt.title('Empirical Type I Error Rate vs Nominal Alpha (Clopper-Pearson 95% CI)', fontsize=14, pad=20)
    plt.xlabel('Scaling Method', fontsize=12)
    plt.ylabel('Empirical Error Rate', fontsize=12)
    plt.ylim(0, max(0.15, plot_df['ci_high'].max() * 1.2))
    plt.legend(loc='best', framealpha=0.9)
    plt.grid(True, alpha=0.3, linestyle=':')
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Error rate plot saved to {output_path}")