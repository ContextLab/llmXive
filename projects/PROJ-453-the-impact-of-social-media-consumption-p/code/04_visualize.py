import os
import sys
import logging
import json
import warnings
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from matplotlib.gridspec import GridSpec

from logging_config import setup_logging, get_logger
from config import DATA_ROOT, RESULTS_ROOT
from utils import causal_language_scanner

logger = get_logger("visualize")

def load_schema_contract(schema_path: Path) -> Dict[str, Any]:
    """Load the schema contract from YAML."""
    import yaml
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_output_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate output structure."""
    required_keys = list(schema.get("keys", {}).keys())
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise ValueError(f"Output schema validation failed: Missing keys {missing}")
    return True

def load_model_summary(path: Path) -> Dict[str, Any]:
    """Load the model summary JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Model summary not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_cleaned_data(path: Path) -> pd.DataFrame:
    """Load the cleaned CSV data."""
    if not path.exists():
        raise FileNotFoundError(f"Cleaned data not found: {path}")
    return pd.read_csv(path)

def check_interaction_significance(model_summary: Dict[str, Any]) -> bool:
    """Check if interaction term is significant (p < 0.05)."""
    # Assuming interaction term is named 'switching_index_x_age' or similar
    # We look for it in the p_values
    p_values = model_summary.get("p_values", {})
    # Heuristic: look for any key containing 'x' or 'interaction'
    interaction_keys = [k for k in p_values.keys() if 'x' in k.lower() or 'interaction' in k.lower()]
    
    if not interaction_keys:
        # If no interaction term found, assume non-significant
        return False
    
    # Take the first found interaction p-value
    p_val = p_values.get(interaction_keys[0], 1.0)
    return p_val < 0.05

def generate_regression_plot(df: pd.DataFrame, output_path: Path):
    """Generate scatter plot with regression line and CI."""
    logger.info("Generating regression plot...")
    
    plt.figure(figsize=(10, 6))
    x = df['switching_index']
    y = df['cognitive_flexibility_score']
    
    # Scatter
    plt.scatter(x, y, alpha=0.6, label='Data')
    
    # Regression line
    X = sm.add_constant(x)
    model = sm.OLS(y, X).fit()
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = model.params[0] + model.params[1] * x_line
    
    plt.plot(x_line, y_line, 'r-', label='Regression Line')
    
    # Confidence Interval (approximate)
    # Using statsmodels get_prediction for CI
    pred = model.get_prediction(sm.add_constant(x_line))
    ci = pred.conf_int()
    plt.fill_between(x_line, ci[:, 0], ci[:, 1], color='r', alpha=0.2, label='95% CI')
    
    plt.xlabel('Switching Index')
    plt.ylabel('Cognitive Flexibility Score')
    plt.title('Association between Switching Index and Cognitive Flexibility')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Regression plot saved to {output_path}")

def generate_stratified_plot(df: pd.DataFrame, model_summary: Dict[str, Any], output_path: Path):
    """Generate stratified plot for age groups if interaction significant."""
    logger.info("Generating stratified plot...")
    
    significant = check_interaction_significance(model_summary)
    label = "Significant Interaction" if significant else "Non-Significant Interaction"
    
    plt.figure(figsize=(10, 6))
    
    # Split by age
    df_young = df[df['age'] < 30]
    df_old = df[df['age'] >= 30]
    
    # Plot Young
    if not df_young.empty:
        x = df_young['switching_index']
        y = df_young['cognitive_flexibility_score']
        plt.scatter(x, y, alpha=0.6, label='Age < 30', color='blue')
        X = sm.add_constant(x)
        model = sm.OLS(y, X).fit()
        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = model.params[0] + model.params[1] * x_line
        plt.plot(x_line, y_line, 'b-', label='Fit (Age < 30)')
        
    # Plot Old
    if not df_old.empty:
        x = df_old['switching_index']
        y = df_old['cognitive_flexibility_score']
        plt.scatter(x, y, alpha=0.6, label='Age >= 30', color='green')
        X = sm.add_constant(x)
        model = sm.OLS(y, X).fit()
        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = model.params[0] + model.params[1] * x_line
        plt.plot(x_line, y_line, 'g-', label='Fit (Age >= 30)')
    
    plt.xlabel('Switching Index')
    plt.ylabel('Cognitive Flexibility Score')
    plt.title(f'Stratified by Age: {label}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Stratified plot saved to {output_path}")

def generate_sensitivity_table(sensitivity_path: Path, output_path: Path):
    """Generate a visual table from sensitivity analysis results."""
    logger.info("Generating sensitivity table...")
    
    df = pd.read_csv(sensitivity_path)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis('off')
    
    # Create table
    table_data = df[['definition', 'beta', 'p_value', 'fdr_p_value', 'n', 'sign']].values
    col_labels = ['Definition', 'Beta', 'P-Value', 'FDR P-Value', 'N', 'Sign']
    
    table = ax.table(cellText=table_data, colLabels=col_labels, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    
    # Style header
    for i in range(len(col_labels)):
        table[(0, i)].set_facecolor('#4472C4')
        table[(0, i)].set_text_props(color='white', weight='bold')
    
    plt.title("Sensitivity Analysis Results", fontsize=14, pad=20)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Sensitivity table saved to {output_path}")

def write_final_report(model_summary: Dict[str, Any], output_path: Path):
    """Write the final JSON report."""
    logger.info("Writing final report...")
    
    # Merge model summary with interpretation
    final_report = model_summary.copy()
    final_report["interpretation"] = "Associational estimates only. No causal claims are made."
    
    # Validate causal language
    if causal_language_scanner(final_report["interpretation"], ["causes", "leads to", "impacts"]):
        raise ValueError("Causal language detected in final report interpretation. Failing per FR-004.")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2, default=str)
    logger.info(f"Final report saved to {output_path}")

def main():
    """Main entry point for visualization pipeline."""
    logger.info("Starting visualization pipeline.")
    
    # Paths
    data_path = Path(DATA_ROOT) / "processed" / "participants_cleaned.csv"
    model_summary_path = Path(RESULTS_ROOT) / "models" / "regression_summary.json"
    sensitivity_path = Path(RESULTS_ROOT) / "sensitivity_comparison.csv"
    figures_dir = Path(RESULTS_ROOT) / "figures"
    final_report_path = Path(RESULTS_ROOT) / "final_report.json"
    
    # Load Data
    df = load_cleaned_data(data_path)
    model_summary = load_model_summary(model_summary_path)
    
    # Generate Plots
    generate_regression_plot(df, figures_dir / "regression_plot.png")
    generate_stratified_plot(df, model_summary, figures_dir / "stratified_plot.png")
    generate_sensitivity_table(sensitivity_path, figures_dir / "sensitivity_table.png")
    
    # Write Final Report
    write_final_report(model_summary, final_report_path)
    
    logger.info("Visualization pipeline completed successfully.")

if __name__ == "__main__":
    setup_logging()
    main()
