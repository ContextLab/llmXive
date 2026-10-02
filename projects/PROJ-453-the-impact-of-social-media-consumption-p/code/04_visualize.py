"""
Visualization pipeline for User Story 3 (T036-T039).
Generates regression plots, stratified plots, and sensitivity tables.
"""

import os
import sys
import logging
import json
import warnings
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.table import Table
from matplotlib.font_manager import FontProperties

# Local imports
from config import DATA_ROOT, RESULTS_ROOT
from logging_config import setup_logging, get_logger
from utils import causal_language_scanner

# Ensure logger is initialized immediately
logger = setup_logging()
if logger is None:
    # Fallback if setup_logging fails (should not happen if T010 is correct)
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)


def load_schema_contract(schema_path: str) -> dict:
    """Load the output schema contract."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def validate_output_schema(data: dict, schema: dict) -> bool:
    """Validate data against the output schema."""
    # Simplified validation for this task
    required_keys = ['coefficients', 'diagnostics']
    for key in required_keys:
        if key not in data:
            logger.error(f"Schema validation failed: missing key '{key}'")
            return False
    return True


def load_model_summary(summary_path: str) -> dict:
    """Load the core model summary JSON."""
    if not Path(summary_path).exists():
        raise FileNotFoundError(f"Model summary not found at {summary_path}")
    with open(summary_path, 'r') as f:
        return json.load(f)


def load_cleaned_data(data_path: str) -> pd.DataFrame:
    """Load the cleaned participant data."""
    if not Path(data_path).exists():
        raise FileNotFoundError(f"Cleaned data not found at {data_path}")
    return pd.read_csv(data_path)


def check_interaction_significance(model_summary: dict, threshold: float = 0.05) -> bool:
    """Check if the interaction term is significant."""
    try:
        # Attempt to find interaction p-value in diagnostics or coefficients
        diagnostics = model_summary.get('diagnostics', {})
        p_value = diagnostics.get('interaction_p_value')
        
        if p_value is None:
            # Try to infer from coefficients if interaction term exists
            coeffs = model_summary.get('coefficients', {})
            interaction_key = None
            for key in coeffs.keys():
                if 'interaction' in key.lower() or '*' in key:
                    interaction_key = key
                    break
            
            if interaction_key:
                p_value = coeffs[interaction_key].get('p_value')
        
        if p_value is None:
            logger.warning("Interaction p-value not found in model summary. Assuming not significant.")
            return False
        
        return p_value < threshold
    except Exception as e:
        logger.error(f"Error checking interaction significance: {e}")
        return False


def generate_regression_plot(data: pd.DataFrame, output_path: str):
    """Generate scatter plot with regression line and 95% CI."""
    logger.info(f"Generating regression plot: {output_path}")
    
    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=data, 
        x='switching_index', 
        y='cognitive_flexibility_score',
        alpha=0.6,
        edgecolor='k'
    )
    
    # Add regression line with CI
    sns.regplot(
        data=data,
        x='switching_index',
        y='cognitive_flexibility_score',
        scatter=False,
        ci=95,
        color='red',
        line_kws={'linewidth': 2}
    )
    
    plt.title('Switching Index vs Cognitive Flexibility Score')
    plt.xlabel('Switching Index')
    plt.ylabel('Cognitive Flexibility Score')
    plt.grid(True, alpha=0.3)
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved regression plot to {output_path}")


def generate_stratified_plot(data: pd.DataFrame, model_summary: dict, output_path: str, threshold: float = 0.05):
    """Generate stratified plot by age groups if interaction is significant."""
    is_significant = check_interaction_significance(model_summary, threshold)
    
    if not is_significant:
        logger.info("Interaction term not significant. Skipping stratified plot generation.")
        return
    
    logger.info(f"Generating stratified plot: {output_path}")
    
    # Create age groups
    data['age_group'] = data['age'].apply(lambda x: '<30' if x < 30 else '>=30')
    
    plt.figure(figsize=(10, 6))
    
    # Plot for each group
    for group in data['age_group'].unique():
        subset = data[data['age_group'] == group]
        sns.regplot(
            data=subset,
            x='switching_index',
            y='cognitive_flexibility_score',
            label=f'Age {group}',
            ci=95
        )
    
    plt.title('Stratified Analysis: Age Groups')
    plt.xlabel('Switching Index')
    plt.ylabel('Cognitive Flexibility Score')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Add significance label
    plt.figtext(0.95, 0.05, 'Significant Interaction', ha='right', fontsize=10, style='italic')
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved stratified plot to {output_path}")


def generate_sensitivity_table(sensitivity_path: str, output_path: str):
    """Generate a visual table of sensitivity analysis results."""
    logger.info(f"Generating sensitivity table: {output_path}")
    
    if not Path(sensitivity_path).exists():
        raise FileNotFoundError(f"Sensitivity data not found at {sensitivity_path}")
    
    df = pd.read_csv(sensitivity_path)
    
    # Ensure required columns exist
    required_cols = ['definition', 'beta', 'p_value', 'fdr_p_value', 'n', 'sign']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in sensitivity data: {missing_cols}")
    
    # Setup figure
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis('off')
    ax.axis('tight')
    
    # Format data for display
    display_df = df[required_cols].copy()
    display_df['beta'] = display_df['beta'].round(4)
    display_df['p_value'] = display_df['p_value'].round(4)
    display_df['fdr_p_value'] = display_df['fdr_p_value'].round(4)
    
    # Create table
    table = Table(
        ax, 
        bbox=[0, 0, 1, 1],
        colLabels=display_df.columns,
        cellLoc='center',
        rowLoc='center',
        colColours=['#4472C4'] * len(required_cols)
    )
    
    for i, row in enumerate(display_df.values):
        for j, val in enumerate(row):
            # Color code significance
            if j == 2: # p_value column
                color = '#C65911' if float(val) < 0.05 else '#F2F2F2'
            elif j == 3: # fdr_p_value column
                color = '#C65911' if float(val) < 0.05 else '#F2F2F2'
            else:
                color = '#F2F2F2'
                
            table.add_cell(i+1, j, width=0.15, height=0.08, facecolor=color)
            table._cells[(i+1, j)].set_text_props(text=str(val))
    
    # Title
    ax.set_title('Sensitivity Analysis: Model Robustness Across Operationalizations', fontsize=14, pad=20)
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved sensitivity table to {output_path}")


def write_final_report(report_path: str, model_summary: dict, sensitivity_data: pd.DataFrame):
    """Write the final report merging model and sensitivity results."""
    logger.info(f"Writing final report: {report_path}")
    
    # Validate model summary
    schema_path = Path(RESULTS_ROOT) / 'contracts' / 'output.schema.yaml'
    if schema_path.exists():
        schema = load_schema_contract(str(schema_path))
        if not validate_output_schema(model_summary, schema):
            raise ValueError("Model summary failed schema validation")
    
    # Scan for causal language
    report_text = json.dumps(model_summary, default=str)
    if causal_language_scanner(report_text, ["causes", "leads to", "impacts", "effect"]):
        raise ValueError("Causal language detected in report. Aborting.")
    
    # Merge results
    final_report = {
        "model_summary": model_summary,
        "sensitivity_analysis": sensitivity_data.to_dict(orient='records'),
        "status": "complete"
    }
    
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Final report saved to {report_path}")


def main():
    """Main execution pipeline for visualization tasks."""
    logger.info("Starting visualization pipeline (T036-T039).")
    
    # Paths
    data_path = Path(DATA_ROOT) / "processed" / "participants_cleaned.csv"
    model_summary_path = Path(RESULTS_ROOT) / "models" / "core_model.json"
    sensitivity_path = Path(RESULTS_ROOT) / "sensitivity_comparison.csv"
    
    fig_dir = Path(RESULTS_ROOT) / "figures"
    regression_plot_path = fig_dir / "regression_plot.png"
    stratified_plot_path = fig_dir / "stratified_plot.png"
    sensitivity_table_path = fig_dir / "sensitivity_table.png"
    final_report_path = Path(RESULTS_ROOT) / "final_report.json"
    
    try:
        # Load data
        data = load_cleaned_data(str(data_path))
        model_summary = load_model_summary(str(model_summary_path))
        
        # T036: Regression Plot
        generate_regression_plot(data, str(regression_plot_path))
        
        # T037: Stratified Plot
        generate_stratified_plot(data, model_summary, str(stratified_plot_path))
        
        # T038: Sensitivity Table
        if Path(sensitivity_path).exists():
            generate_sensitivity_table(str(sensitivity_path), str(sensitivity_table_path))
        else:
            logger.warning(f"Sensitivity data not found at {sensitivity_path}. Skipping T038.")
        
        # T039: Final Report
        if Path(sensitivity_path).exists():
            sensitivity_df = pd.read_csv(sensitivity_path)
            write_final_report(str(final_report_path), model_summary, sensitivity_df)
        else:
            logger.warning(f"Sensitivity data not found. Skipping final report generation.")
        
        logger.info("Visualization pipeline completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()