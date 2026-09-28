import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt
import pandas as pd
import os
import logging
from typing import Optional, List

from utils.constants import get_significance_level
from utils.logger import get_logger, log_pipeline_step

logger = get_logger(__name__)

def create_scatter_plot(df: pd.DataFrame, x_col: str, y_col: str, title: str, filename: str, model=None) -> str:
    """
    Creates a scatter plot with a regression line (if model provided) and saves it to a file.
    
    Args:
        df: DataFrame containing the data
        x_col: Column name for the x-axis (independent variable)
        y_col: Column name for the y-axis (dependent variable)
        title: Plot title
        filename: Full path to save the PNG file
        model: Optional fitted statsmodels model to extract regression line
    
    Returns:
        The path to the saved file
    """
    log_pipeline_step(logger, f"Creating scatter plot: {title}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    plt.figure(figsize=(10, 8))
    
    # Scatter plot
    plt.scatter(df[x_col], df[y_col], alpha=0.6, edgecolors='k', linewidth=0.5, label='Data Points')
    
    # Add regression line if model is provided
    if model is not None:
        try:
            # Sort x values for a clean line
            x_sorted = df[x_col].sort_values()
            y_pred = model.predict(df[[x_col]].sort_values())
            plt.plot(x_sorted, y_pred, color='red', linewidth=2, label='Regression Line')
        except Exception as e:
            logger.warning(f"Could not add regression line to scatter plot: {e}")
    
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel(x_col.replace('_', ' ').title(), fontsize=12)
    plt.ylabel(y_col.replace('_', ' ').title(), fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    log_pipeline_step(logger, f"Scatter plot saved to {filename}")
    return filename

def create_residual_plot(df: pd.DataFrame, predicted_col: str, actual_col: str, title: str, filename: str) -> str:
    """
    Creates a residual diagnostic plot and saves it to a file.
    
    Args:
        df: DataFrame containing actual and predicted values
        predicted_col: Column name for predicted values
        actual_col: Column name for actual observed values
        title: Plot title
        filename: Full path to save the PNG file
    
    Returns:
        The path to the saved file
    """
    log_pipeline_step(logger, f"Creating residual plot: {title}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Calculate residuals
    residuals = df[actual_col] - df[predicted_col]
    
    plt.figure(figsize=(10, 8))
    
    # Residuals vs Predicted
    plt.scatter(df[predicted_col], residuals, alpha=0.6, edgecolors='k', linewidth=0.5)
    
    # Add horizontal line at y=0
    plt.axhline(y=0, color='red', linestyle='--', linewidth=2, label='Zero Residual')
    
    # Add confidence bands if possible (approximate 95% CI)
    if len(residuals) > 0:
        std_res = residuals.std()
        plt.axhline(y=1.96 * std_res, color='gray', linestyle=':', alpha=0.7, label='+/- 1.96 Std Dev')
        plt.axhline(y=-1.96 * std_res, color='gray', linestyle=':', alpha=0.7)
    
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel("Predicted Values", fontsize=12)
    plt.ylabel("Residuals", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    log_pipeline_step(logger, f"Residual plot saved to {filename}")
    return filename

def run_viz_pipeline(results_df: pd.DataFrame, output_dir: str, model=None) -> List[str]:
    """
    Orchestrates the generation of all required visualization files.
    
    Args:
        results_df: DataFrame containing the regression results (with predicted and actual columns)
        output_dir: Directory to save the PNG files
        model: Optional fitted model for regression line on scatter plot
    
    Returns:
        List of paths to generated files
    """
    generated_files = []
    
    # Define exact filenames as per task requirements
    scatter_filename = os.path.join(output_dir, "scatter_plot.png")
    residual_filename = os.path.join(output_dir, "residuals.png")
    
    # Determine column names based on common conventions in this project
    # Assuming 'perceived_social_validation' (or similar) is X and 'self_perception' is Y
    # We look for columns in the dataframe or use generic names if not found
    x_col = None
    y_col = None
    
    # Heuristic to find the primary predictor and outcome
    possible_x = ['perceived_social_validation', 'engagement_count', 'psv_score']
    possible_y = ['self_perception', 'self_esteem_score', 'outcome']
    
    for col in possible_x:
        if col in results_df.columns:
            x_col = col
            break
    if x_col is None and len(results_df.columns) > 0:
        # Fallback to first numeric column that isn't ID
        numeric_cols = results_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
    
    for col in possible_y:
        if col in results_df.columns:
            y_col = col
            break
    if y_col is None:
        # Fallback
        if 'predicted' in results_df.columns:
            y_col = 'actual' if 'actual' in results_df.columns else results_df.columns[-1]
        elif len(results_df.columns) > 1:
            y_col = results_df.columns[-1]
    
    if x_col and y_col:
        create_scatter_plot(
            df=results_df,
            x_col=x_col,
            y_col=y_col,
            title="Scatter Plot: Perceived Social Validation vs Self-Perception",
            filename=scatter_filename,
            model=model
        )
        generated_files.append(scatter_filename)
    else:
        logger.warning("Could not identify X and Y columns for scatter plot.")
    
    if 'predicted' in results_df.columns and 'actual' in results_df.columns:
        create_residual_plot(
            df=results_df,
            predicted_col='predicted',
            actual_col='actual',
            title="Residual Diagnostic Plot: Predicted vs Actual",
            filename=residual_filename
        )
        generated_files.append(residual_filename)
    else:
        logger.warning("Could not find 'predicted' and 'actual' columns for residual plot.")
    
    return generated_files

def main():
    """
    Main entry point for generating visualization files.
    This function expects to be called after regression analysis has populated data/processed/.
    """
    import json
    import numpy as np
    
    # Load model results to get data for plotting
    results_path = os.path.join("data", "processed", "model_results.json")
    
    if not os.path.exists(results_path):
        logger.error(f"Model results file not found at {results_path}. Please run regression analysis first.")
        return
    
    with open(results_path, 'r') as f:
        results_data = json.load(f)
    
    # The results_data structure usually contains model stats. 
    # We need the underlying data to plot. 
    # For this task, we assume the pipeline has saved a processed data file 
    # or we reconstruct a dummy plot if raw data isn't explicitly stored in the JSON.
    # However, the task requires REAL plots. 
    # We will attempt to load the processed data if it exists, otherwise we rely on 
    # the main.py orchestration passing the dataframe to this function.
    
    # Since T027 is a standalone implementation, we assume the data is available 
    # via the standard pipeline flow. Here we simulate the call that main.py would make
    # if it had the dataframe. 
    
    # NOTE: In a real execution, main.py would pass the dataframe to this function.
    # For the sake of this artifact being runnable, we check for a processed CSV.
    processed_data_path = os.path.join("data", "processed", "processed_data.csv")
    
    if os.path.exists(processed_data_path):
        df = pd.read_csv(processed_data_path)
        
        # Ensure we have the necessary columns for plotting
        # We need: predictor, outcome, and if available, predicted values
        # If 'predicted' is missing, we can't make the residual plot without re-running prediction
        # For this task, we assume the regression step added 'predicted' and 'actual' columns
        # or we use the raw columns.
        
        output_dir = "data/processed"
        
        # Try to find columns
        x_col = None
        y_col = None
        
        # Common column names from previous tasks
        if 'perceived_social_validation' in df.columns:
            x_col = 'perceived_social_validation'
        elif 'engagement_count' in df.columns:
            x_col = 'engagement_count'
            
        if 'self_perception' in df.columns:
            y_col = 'self_perception'
        elif 'self_esteem_score' in df.columns:
            y_col = 'self_esteem_score'
        
        if x_col and y_col:
            # Create scatter plot
            create_scatter_plot(
                df=df, 
                x_col=x_col, 
                y_col=y_col, 
                title="Scatter Plot: Perceived Social Validation vs Self-Perception", 
                filename=os.path.join(output_dir, "scatter_plot.png")
            )
            
            # For residual plot, we need predicted values. 
            # If the model was saved in model_results.json, we could re-predict.
            # But for simplicity in this script, we check if 'predicted' exists.
            if 'predicted' in df.columns and 'actual' in df.columns:
                create_residual_plot(
                    df=df,
                    predicted_col='predicted',
                    actual_col='actual',
                    title="Residual Diagnostic Plot",
                    filename=os.path.join(output_dir, "residuals.png")
                )
            else:
                logger.warning("Missing 'predicted' or 'actual' columns in processed data. Skipping residual plot generation.")
                logger.info("To generate residual plots, ensure the regression step adds these columns to the processed data.")
        else:
            logger.error(f"Required columns not found in {processed_data_path}.")
    else:
        logger.error(f"Processed data file not found at {processed_data_path}. Cannot generate plots.")

if __name__ == "__main__":
    main()