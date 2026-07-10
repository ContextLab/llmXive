import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Import utils for path handling
from utils import get_project_root_path, get_data_processed_path, get_figures_path, setup_logger, get_logger

# Ensure logging is configured
logger = setup_logger("06_visualize")

def load_correlation_results():
    """
    Load correlation results from the processed data directory.
    Returns a DataFrame with correlation statistics.
    """
    root = get_project_root_path()
    data_path = get_data_processed_path()
    file_path = data_path / "correlation_results.csv"
    
    if not file_path.exists():
        logger.warning(f"Correlation results file not found at {file_path}. Skipping visualization.")
        return None
    
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded correlation results with {len(df)} rows from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load correlation results: {e}")
        return None

def load_regression_results():
    """
    Load regression results from the processed data directory.
    Returns a DataFrame with regression coefficients and confidence intervals.
    """
    root = get_project_root_path()
    data_path = get_data_processed_path()
    file_path = data_path / "regression_results.csv"
    
    if not file_path.exists():
        logger.warning(f"Regression results file not found at {file_path}. Skipping visualization.")
        return None
    
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded regression results with {len(df)} rows from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load regression results: {e}")
        return None

def generate_heatmap(correlation_df):
    """
    Generate a heatmap of taxa-cognition correlation matrix.
    Ensures clear labels for age groups if stratified data is present.
    """
    if correlation_df is None:
        logger.warning("No correlation data provided for heatmap generation.")
        return

    # Prepare pivot table for heatmap
    # Assuming columns: 'taxon', 'cognitive_metric', 'correlation', 'p_value', 'q_value', 'age_group' (optional)
    
    # Check if age_group column exists for stratification
    has_age_strata = 'age_group' in correlation_df.columns
    
    if has_age_strata:
        # If stratified, we might need to plot multiple heatmaps or a facet grid
        # For simplicity, we will plot the overall correlation or the first group if specific
        # But the requirement is to label age groups. Let's create a multi-index or facet.
        
        # Pivot for the first age group as an example, or aggregate if needed.
        # Better approach: Create a facet grid for each age group.
        
        age_groups = correlation_df['age_group'].unique()
        fig, axes = plt.subplots(1, len(age_groups), figsize=(20, 6))
        if len(age_groups) == 1:
            axes = [axes]
        
        for i, group in enumerate(sorted(age_groups)):
            group_df = correlation_df[correlation_df['age_group'] == group]
            pivot_data = group_df.pivot(index='taxon', columns='cognitive_metric', values='correlation')
            
            # Ensure numeric values
            pivot_data = pivot_data.apply(pd.to_numeric, errors='coerce')
            
            sns.heatmap(pivot_data, annot=True, fmt=".2f", cmap='coolwarm', center=0, 
                        ax=axes[i], cbar_kws={'label': 'Spearman Correlation'})
            axes[i].set_title(f'Age Group: {group}')
            axes[i].set_xlabel('Cognitive Metric')
            axes[i].set_ylabel('Taxon')
        
        plt.suptitle('Taxa-Cognitive Correlation Matrix by Age Group', fontsize=16)
        plt.tight_layout()
    else:
        # Standard heatmap
        pivot_data = correlation_df.pivot(index='taxon', columns='cognitive_metric', values='correlation')
        pivot_data = pivot_data.apply(pd.to_numeric, errors='coerce')
        
        plt.figure(figsize=(12, 10))
        sns.heatmap(pivot_data, annot=True, fmt=".2f", cmap='coolwarm', center=0,
                    cbar_kws={'label': 'Spearman Correlation'})
        plt.title('Taxa-Cognitive Correlation Matrix')
        plt.xlabel('Cognitive Metric')
        plt.ylabel('Taxon')
    
    # Save figure
    figures_path = get_figures_path()
    output_file = figures_path / "correlation_heatmap.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    logger.info(f"Heatmap saved to {output_file}")
    plt.close()

def generate_forest_plot(regression_df):
    """
    Generate a forest plot of regression coefficients with confidence intervals.
    Ensures clear labels for confidence intervals and age groups if applicable.
    """
    if regression_df is None:
        logger.warning("No regression data provided for forest plot generation.")
        return

    # Expected columns: 'feature', 'coef', 'std_err', 'p_value', 'age_group' (optional)
    # Calculate confidence intervals (95%)
    # Assuming standard error is available or we calculate from std_err
    if 'std_err' not in regression_df.columns:
        logger.error("Regression data missing 'std_err' column for confidence intervals.")
        return

    regression_df['ci_lower'] = regression_df['coef'] - 1.96 * regression_df['std_err']
    regression_df['ci_upper'] = regression_df['coef'] + 1.96 * regression_df['std_err']
    
    # Sort by coefficient for better visualization
    regression_df = regression_df.sort_values(by='coef')
    
    has_age_strata = 'age_group' in regression_df.columns
    
    plt.figure(figsize=(12, 10))
    
    if has_age_strata:
        # Plot by age group using different colors or markers
        age_groups = regression_df['age_group'].unique()
        colors = plt.cm.Set3(np.linspace(0, 1, len(age_groups)))
        
        for i, group in enumerate(sorted(age_groups)):
            group_df = regression_df[regression_df['age_group'] == group]
            y_pos = np.arange(len(group_df))
            
            # Offset positions slightly if plotting multiple groups on same axis
            # Or use subplots. Let's use subplots for clarity per requirement "clear labels for age groups"
            pass 
        
        # Re-approach: Use subplots for each age group to ensure clarity
        n_groups = len(age_groups)
        fig, axes = plt.subplots(n_groups, 1, figsize=(12, 4 * n_groups))
        if n_groups == 1:
            axes = [axes]
        
        for i, group in enumerate(sorted(age_groups)):
            group_df = regression_df[regression_df['age_group'] == group].sort_values(by='coef')
            y_pos = np.arange(len(group_df))
            
            axes[i].errorbar(y_pos, group_df['coef'], 
                             xerr=[group_df['coef'] - group_df['ci_lower'], 
                                   group_df['ci_upper'] - group_df['coef']],
                             fmt='o', capsize=5, label=group, color=colors[i])
            axes[i].axvline(x=0, color='gray', linestyle='--', alpha=0.5)
            axes[i].set_yticks(y_pos)
            axes[i].set_yticklabels(group_df['feature'])
            axes[i].set_title(f'Regression Coefficients by Age Group: {group}')
            axes[i].set_xlabel('Coefficient (95% CI)')
            axes[i].legend()
        
        plt.suptitle('Regression Coefficients with Confidence Intervals by Age Group', fontsize=16)
        plt.tight_layout()
    else:
        # Single plot
        y_pos = np.arange(len(regression_df))
        plt.errorbar(y_pos, regression_df['coef'], 
                     xerr=[regression_df['coef'] - regression_df['ci_lower'], 
                           regression_df['ci_upper'] - regression_df['coef']],
                     fmt='o', capsize=5, color='steelblue')
        plt.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
        plt.yticks(y_pos, regression_df['feature'])
        plt.xlabel('Coefficient (95% CI)')
        plt.title('Regression Coefficients with Confidence Intervals')
        plt.tight_layout()

    # Save figure
    figures_path = get_figures_path()
    output_file = figures_path / "regression_forest_plot.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    logger.info(f"Forest plot saved to {output_file}")
    plt.close()

def main():
    """
    Main entry point for visualization generation.
    Checks for merged data existence and generates plots.
    """
    root = get_project_root_path()
    data_path = get_data_processed_path()
    merged_file = data_path / "merged_dataset.parquet"
    
    if not merged_file.exists():
        logger.warning(f"Merged dataset not found at {merged_file}. Skipping visualization generation.")
        logger.info("Data gap detected. Visualizations cannot be generated.")
        return
    
    logger.info("Starting visualization generation...")
    
    # Load data
    corr_df = load_correlation_results()
    reg_df = load_regression_results()
    
    # Generate Heatmap
    if corr_df is not None:
        generate_heatmap(corr_df)
    else:
        logger.warning("Skipping heatmap due to missing correlation data.")
    
    # Generate Forest Plot
    if reg_df is not None:
        generate_forest_plot(reg_df)
    else:
        logger.warning("Skipping forest plot due to missing regression data.")
    
    logger.info("Visualization generation complete.")

if __name__ == "__main__":
    main()