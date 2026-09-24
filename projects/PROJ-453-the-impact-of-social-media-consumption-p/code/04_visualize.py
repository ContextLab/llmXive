import os
import sys
import logging
import json
import yaml
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

def log_setup():
    """Configure logging to stdout."""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        stream=sys.stdout
    )

def load_model_summary() -> Dict[str, Any]:
    """Load the regression summary JSON."""
    path = Path("results/models/regression_summary.json")
    if not path.exists():
        raise FileNotFoundError(f"Model summary not found at {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned participant data."""
    path = Path("data/processed/participants_cleaned.csv")
    if not path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {path}")
    return pd.read_csv(path)

def check_interaction_significance(model_summary: Dict[str, Any]) -> bool:
    """Check if interaction term is significant (p < 0.05)."""
    p_values = model_summary.get('p_values', {})
    interaction_p = p_values.get('interaction', 1.0)
    return interaction_p < 0.05

def generate_regression_plot(df: pd.DataFrame, output_path: Path):
    """Generate scatter plot with regression line and confidence interval."""
    plt.figure(figsize=(10, 6))
    sns.regplot(
        data=df,
        x='switching_index',
        y='cognitive_flexibility_score',
        ci=95,
        scatter_kws={'alpha': 0.6}
    )
    plt.title('Switching Index vs Cognitive Flexibility Score')
    plt.xlabel('Switching Index')
    plt.ylabel('Cognitive Flexibility Score')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved regression plot to {output_path}")

def generate_stratified_plot(df: pd.DataFrame, output_path: Path):
    """Generate stratified plot for age groups."""
    df['age_group'] = df['age'].apply(lambda x: '<30' if x < 30 else '>=30')
    plt.figure(figsize=(10, 6))
    sns.lmplot(
        data=df,
        x='switching_index',
        y='cognitive_flexibility_score',
        hue='age_group',
        ci=95
    )
    plt.title('Stratified by Age Group')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved stratified plot to {output_path}")

def generate_sensitivity_table(model_summary: Dict[str, Any], output_path: Path):
    """Generate sensitivity table as image."""
    # Create a simple table visualization
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis('off')
    
    # Prepare data for table
    coeffs = model_summary.get('coefficients', {})
    p_vals = model_summary.get('p_values', {})
    
    table_data = [
        ['Variable', 'Coefficient', 'P-value'],
        ['switching_index', f"{coeffs.get('switching_index', 0):.4f}", f"{p_vals.get('switching_index', 1):.4f}"],
        ['total_screen_time', f"{coeffs.get('total_screen_time', 0):.4f}", f"{p_vals.get('total_screen_time', 1):.4f}"],
        ['age', f"{coeffs.get('age', 0):.4f}", f"{p_vals.get('age', 1):.4f}"],
    ]
    
    table = ax.table(cellText=table_data, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    plt.title('Model Coefficients')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved sensitivity table to {output_path}")

def write_final_report(model_summary: Dict[str, Any], output_path: Path):
    """Write final JSON report."""
    report = {
        **model_summary,
        'generated_at': str(pd.Timestamp.now())
    }
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved final report to {output_path}")

def main():
    """Main entry point for visualization."""
    log_setup()
    logger.info("Starting visualization pipeline.")

    # Load data
    model_summary = load_model_summary()
    df = load_cleaned_data()

    # Check interaction significance
    is_significant = check_interaction_significance(model_summary)

    # Generate plots
    Path("results/figures").mkdir(parents=True, exist_ok=True)
    
    generate_regression_plot(
        df,
        Path("results/figures/regression_plot.png")
    )
    
    if is_significant:
        generate_stratified_plot(
            df,
            Path("results/figures/stratified_plot.png")
        )
    
    generate_sensitivity_table(
        model_summary,
        Path("results/figures/sensitivity_table.png")
    )

    # Write final report
    write_final_report(
        model_summary,
        Path("results/final_report.json")
    )

    logger.info("Visualization complete.")

if __name__ == "__main__":
    main()
