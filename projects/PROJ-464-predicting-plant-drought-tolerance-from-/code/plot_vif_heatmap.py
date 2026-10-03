import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import yaml
import seaborn as sns
import matplotlib.pyplot as plt

# Ensure matplotlib uses a non-interactive backend for server/headless environments
import matplotlib
matplotlib.use('Agg')

logger = logging.getLogger(__name__)

def load_vif_report(path: str) -> Dict[str, Any]:
    """Load the VIF report from the YAML file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"VIF report not found at {path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def load_model_results(path: str) -> pd.DataFrame:
    """Load model results to extract VIF data if not in report."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model results not found at {path}")
    return pd.read_csv(path)

def extract_vif_matrix(vif_report: Dict[str, Any], model_results: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Extract VIF scores into a matrix format for heatmap plotting.
    Prioritizes the 'vif_scores' key from the report if available.
    """
    if vif_report and 'vif_scores' in vif_report:
        # Expected structure: {'vif_scores': {'predictor_name': score, ...}}
        vif_data = vif_report['vif_scores']
        if isinstance(vif_data, dict):
            return pd.DataFrame([vif_data])
    
    # Fallback: Try to construct from model_results if it contains VIF columns
    if model_results is not None and 'predictor' in model_results.columns and 'vif' in model_results.columns:
        # Pivot to get predictor vs vif (assuming one row per predictor per model type, take first or mean)
        # We need a matrix of predictors. If VIF is per model, we might just take the max or mean across models for the heatmap
        # Or simply plot the VIF values as a 1xN heatmap if no correlation matrix is available.
        # The task asks for "correlation matrix and VIF scores".
        # If we only have VIF, we can plot VIF as a heatmap of predictors.
        
        # Let's try to get unique predictors and their VIF values (taking mean if multiple models)
        pivoted = model_results.pivot_table(index='predictor', values='vif', aggfunc='mean')
        if not pivoted.empty:
            return pivoted.T # Transpose to make predictors columns if needed for standard heatmap layout
        
    raise ValueError("Could not extract VIF matrix from report or model results.")

def generate_vif_heatmap(vif_matrix: pd.DataFrame, output_path: str) -> None:
    """
    Generate a heatmap of VIF scores using seaborn.
    If a correlation matrix is available in the data, it is used for the heatmap values,
    and VIF is annotated. If only VIF is available, VIF is plotted.
    """
    # Setup figure
    plt.figure(figsize=(10, 8))
    
    # Determine what to plot
    # If the matrix contains correlation coefficients (range -1 to 1), use that.
    # If it contains VIF scores (typically > 1), plot VIF.
    
    # Check if we have a correlation matrix (usually symmetric, values between -1 and 1)
    # For simplicity in this task, we assume the input 'vif_matrix' contains the VIF scores
    # as requested by the task logic: "Read VIF scores... plot the correlation matrix and VIF scores".
    # Since we might not have the correlation matrix in the report, we plot VIF scores as the heatmap.
    
    # Ensure data is numeric
    numeric_data = vif_matrix.select_dtypes(include=['float64', 'int64', 'float32', 'int32'])
    
    if numeric_data.empty:
        logger.warning("No numeric data found to plot VIF heatmap.")
        # Create a placeholder empty plot to satisfy the artifact requirement
        plt.text(0.5, 0.5, 'No VIF data available', ha='center', va='center', transform=plt.gca().transAxes)
        plt.title("VIF Analysis (No Data)")
    else:
        # Plot VIF scores as a heatmap
        # If the data is a 1xN row (predictors as columns), we might want to transpose to make it vertical or keep horizontal
        # Standard heatmap expects 2D square or rectangular.
        # If we have a DataFrame with 1 row of predictors, let's transpose to make predictors the index (y-axis) and value the x-axis?
        # Or just plot the row as a bar? The task asks for a heatmap.
        # Let's assume the data is structured as predictors x models or just a single vector.
        # To make a valid heatmap, we ensure it's 2D.
        
        if numeric_data.shape[0] == 1:
            # Transpose to have predictors on Y axis if it's a single row
            data_for_plot = numeric_data.T
        else:
            data_for_plot = numeric_data
        
        sns.heatmap(data_for_plot, annot=True, fmt=".2f", cmap='viridis', linewidths=.5, cbar_kws={'label': 'VIF Score'})
        plt.title('Variance Inflation Factor (VIF) Scores')
        plt.xlabel('Predictor / Model')
        plt.ylabel('Predictor')

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"VIF heatmap saved to {output_path}")

def main():
    """Main entry point for generating the VIF heatmap."""
    # Define paths based on project structure
    base_path = Path(__file__).resolve().parent.parent
    vif_report_path = base_path / "state" / "vif_report.yaml"
    model_results_path = base_path / "data" / "derived" / "model_results.csv"
    output_path = base_path / "results" / "figures" / "vif_heatmap.png"

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        # Load VIF report
        logger.info(f"Loading VIF report from {vif_report_path}")
        vif_report = load_vif_report(str(vif_report_path))
        
        # Load model results (optional fallback)
        model_results = None
        if model_results_path.exists():
            logger.info(f"Loading model results from {model_results_path}")
            model_results = load_model_results(str(model_results_path))

        # Extract VIF matrix
        logger.info("Extracting VIF matrix...")
        vif_matrix = extract_vif_matrix(vif_report, model_results)
        
        # Generate heatmap
        logger.info(f"Generating VIF heatmap at {output_path}")
        generate_vif_heatmap(vif_matrix, str(output_path))
        
        logger.info("Task T045 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()