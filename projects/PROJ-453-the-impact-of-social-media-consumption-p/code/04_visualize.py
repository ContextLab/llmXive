"""
Visualization module for the social media cognitive flexibility study.
Generates publication-ready plots including stratified regression analysis.
"""
import os
import sys
import logging
import json
import yaml
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import statsmodels.api as sm
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from scipy import stats

# Configure matplotlib for non-interactive backend (critical for CI/runner environments)
matplotlib.use('Agg')

# Import local utilities
from config import ensure_directories, DATA_ROOT, RESULTS_ROOT
from utils import log_setup

logger = log_setup()

# Constants
FIGURE_ROOT = Path(RESULTS_ROOT) / "figures"
MODEL_ROOT = Path(RESULTS_ROOT) / "models"
DATA_PROCESSED = Path(DATA_ROOT) / "processed"
RANDOM_SEED = 42

def load_model_summary() -> Dict[str, Any]:
    """
    Load the regression summary JSON produced by code/03_model.py.
    Returns the dictionary containing coefficients, diagnostics, and interpretation.
    """
    summary_path = MODEL_ROOT / "regression_summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Model summary not found at {summary_path}. "
                                "Run code/03_model.py first.")
    with open(summary_path, 'r') as f:
        return json.load(f)

def load_cleaned_data() -> pd.DataFrame:
    """
    Load the cleaned participant data.
    """
    data_path = DATA_PROCESSED / "participants_cleaned.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {data_path}. "
                                "Run code/02_engineer.py first.")
    return pd.read_csv(data_path)

def check_interaction_significance(model_summary: Dict[str, Any]) -> Tuple[bool, float]:
    """
    Check if the interaction term (switching_index * age) is statistically significant.
    
    Args:
        model_summary: The dictionary loaded from regression_summary.json.
        
    Returns:
        Tuple of (is_significant, p_value).
    """
    # The interaction term name depends on how it was named in 03_model.py
    # Typically: 'switching_index:age' or similar
    predictors = model_summary.get('coefficients', {})
    p_values = model_summary.get('p_values', {})
    
    # Look for interaction term keys
    interaction_key = None
    for key in predictors.keys():
        if ':' in key or '*' in key or 'interaction' in key.lower():
            interaction_key = key
            break
    
    if interaction_key is None:
        logger.warning("No interaction term found in model summary. "
                       "Stratified plot will not be generated.")
        return False, 1.0
    
    p_val = p_values.get(interaction_key, 1.0)
    is_sig = p_val < 0.05
    logger.info(f"Interaction term '{interaction_key}' p-value: {p_val:.4f}. "
                f"Significant: {is_sig}")
    return is_sig, p_val

def generate_stratified_plot(df: pd.DataFrame, is_significant: bool) -> None:
    """
    Generate a stratified plot showing regression lines for distinct age groups.
    
    If the interaction term is significant, it splits data into age < 30 and age >= 30.
    If not significant, it still generates the plot but notes the lack of significance.
    
    Args:
        df: The cleaned dataframe.
        is_significant: Boolean indicating if the interaction term was significant.
    """
    if not is_significant:
        logger.info("Interaction term not significant. Generating plot with note.")
    
    # Define age groups
    # Ensure column names match the schema
    age_col = 'age'
    switching_col = 'switching_index'
    outcome_col = 'cognitive_flexibility_score'
    
    # Check if columns exist
    missing_cols = [c for c in [age_col, switching_col, outcome_col] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for stratified plot: {missing_cols}")
    
    df = df.dropna(subset=[age_col, switching_col, outcome_col])
    
    # Create figure
    plt.figure(figsize=(10, 7))
    
    # Split data
    young_mask = df[age_col] < 30
    old_mask = df[age_col] >= 30
    
    df_young = df[young_mask]
    df_old = df[old_mask]
    
    # Colors
    color_young = '#1f77b4'  # blue
    color_old = '#ff7f0e'    # orange
    
    # Plot Young Group
    if len(df_young) > 0:
        x_young = df_young[switching_col]
        y_young = df_young[outcome_col]
        
        # Fit regression for young
        if len(x_young) > 1:
            X_young = sm.add_constant(x_young)
            model_young = sm.OLS(y_young, X_young).fit()
            y_pred_young = model_young.predict(X_young)
            
            # Sort for line plotting
            sort_idx = np.argsort(x_young)
            plt.scatter(x_young, y_young, alpha=0.6, color=color_young, label=f'Age < 30 (n={len(df_young)})')
            plt.plot(x_young[sort_idx], y_pred_young[sort_idx], color=color_young, linewidth=2, label=f'Fit (Age < 30)')
        else:
            plt.scatter(x_young, y_young, alpha=0.6, color=color_young, label=f'Age < 30 (n={len(df_young)})')
    
    # Plot Old Group
    if len(df_old) > 0:
        x_old = df_old[switching_col]
        y_old = df_old[outcome_col]
        
        # Fit regression for old
        if len(x_old) > 1:
            X_old = sm.add_constant(x_old)
            model_old = sm.OLS(y_old, X_old).fit()
            y_pred_old = model_old.predict(X_old)
            
            sort_idx = np.argsort(x_old)
            plt.scatter(x_old, y_old, alpha=0.6, color=color_old, label=f'Age >= 30 (n={len(df_old)})')
            plt.plot(x_old[sort_idx], y_pred_old[sort_idx], color=color_old, linewidth=2, label=f'Fit (Age >= 30)')
        else:
            plt.scatter(x_old, y_old, alpha=0.6, color=color_old, label=f'Age >= 30 (n={len(df_old)})')
    
    plt.xlabel('Switching Index (Platforms × Frequency)', fontsize=12)
    plt.ylabel('Cognitive Flexibility Score', fontsize=12)
    title = "Cognitive Flexibility by Switching Index (Stratified by Age)"
    if is_significant:
        title += " - Interaction Significant"
    else:
        title += " - Interaction Not Significant"
    plt.title(title, fontsize=14)
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    
    # Save
    output_path = FIGURE_ROOT / "stratified_plot.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Stratified plot saved to {output_path}")

def main():
    """
    Main entry point for the visualization script.
    """
    logger.info("Starting visualization pipeline (Task T037).")
    
    # Ensure directories exist
    ensure_directories()
    
    try:
        # Load dependencies
        logger.info("Loading cleaned data...")
        df = load_cleaned_data()
        
        logger.info("Loading model summary...")
        model_summary = load_model_summary()
        
        # Check interaction significance
        is_sig, p_val = check_interaction_significance(model_summary)
        
        # Generate stratified plot
        generate_stratified_plot(df, is_sig)
        
        logger.info("Visualization pipeline completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Visualization pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()