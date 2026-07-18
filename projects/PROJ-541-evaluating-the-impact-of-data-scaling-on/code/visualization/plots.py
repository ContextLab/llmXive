import os
import logging
from pathlib import Path
from typing import Optional
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def generate_error_rate_plot(results_df: pd.DataFrame, output_path: str, nominal_alpha: float = 0.05) -> bool:
    """
    Generate a plot showing empirical error rates vs nominal alpha with 95% CI.
    
    Args:
        results_df: DataFrame with columns 'scaling_method', 'empirical_error_rate', 
                   'ci_lower', 'ci_upper'
        output_path: Path to save the plot
        nominal_alpha: Nominal significance level for reference line
        
    Returns:
        True if plot was generated successfully
    """
    try:
        logger.info(f"Generating error rate plot at {output_path}")
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Set style
        sns.set_style("whitegrid")
        plt.figure(figsize=(10, 6))
        
        # Plot error rates with error bars
        x_pos = range(len(results_df))
        plt.errorbar(
            x_pos, 
            results_df['empirical_error_rate'],
            yerr=[
                results_df['empirical_error_rate'] - results_df['ci_lower'],
                results_df['ci_upper'] - results_df['empirical_error_rate']
            ],
            fmt='o',
            capsize=5,
            label='Empirical Error Rate (95% CI)',
            color='blue'
        )
        
        # Add nominal alpha line
        plt.axhline(
            y=nominal_alpha,
            color='red',
            linestyle='--',
            label=f'Nominal Alpha ({nominal_alpha})'
        )
        
        # Labels and title
        plt.xticks(x_pos, results_df['scaling_method'], rotation=45)
        plt.xlabel('Scaling Method')
        plt.ylabel('Empirical Error Rate')
        plt.title('Empirical Type I Error Rate vs Nominal Alpha by Scaling Method')
        plt.legend()
        plt.ylim(0, max(0.1, results_df['ci_upper'].max() * 1.2))
        
        # Save plot
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Error rate plot saved to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate error rate plot: {e}")
        return False
