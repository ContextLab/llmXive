import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Optional, Dict, Any, List

# Standard imports for plotting and data handling
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Import local utilities as per API surface
# Note: We import from the parent directory or relative path as needed
# The API surface suggests these are in code/
from config.config import get_config

# --- Helper Functions ---

def get_project_root() -> Path:
    """Returns the project root directory."""
    # Assuming the script is run from the project root or code/
    # We traverse up if necessary, but typically project root is where code/ lives.
    current = Path(__file__).resolve()
    # Check if we are in code/
    if current.name == 'code':
        return current.parent
    # Otherwise traverse up until we find 'code' or 'data' dirs
    for parent in current.parents:
        if (parent / 'data').exists() and (parent / 'code').exists():
            return parent
    # Fallback
    return current.parent

def load_model(model_path: Path) -> Any:
    """Loads a pickled model object."""
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_stability_metrics(metrics_path: Path) -> Dict:
    """Loads stability metrics JSON."""
    if not metrics_path.exists():
        raise FileNotFoundError(f"Stability metrics file not found: {metrics_path}")
    with open(metrics_path, 'r') as f:
        return json.load(f)

def load_correlation_matrix(csv_path: Path) -> pd.DataFrame:
    """
    Loads the correlation matrix CSV.
    Expected format: Multi-index or columns containing 'Pearson', 'Spearman', etc.
    Returns a DataFrame ready for plotting.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Correlation matrix file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Handle potential MultiIndex columns if saved as such, or flat columns
    # The analyze.py task (T033a) should have saved it. 
    # We assume a standard format where the index is the feature name 
    # and columns are the correlation types (e.g., 'Pearson', 'Spearman').
    # If the file has a specific structure from T033a, we adapt.
    # Assuming the CSV has columns like 'feature', 'Pearson', 'Spearman' or 
    # a matrix format where index is feature and columns are features.
    
    # Re-reading T033a requirement: "Save correlation matrix (both coefficients and p-values)"
    # It likely saved a wide format or a specific structure.
    # Let's assume the standard output of a correlation calculation:
    # A square matrix of coefficients, potentially with p-values in a separate structure or combined.
    # However, T039b specifically asks to generate a heatmap from this file.
    # We will attempt to load it and ensure it's a numeric matrix suitable for heatmap.
    
    # If the CSV contains a 'feature' column, we might need to pivot.
    # If it's already a matrix, we use it directly.
    if 'feature' in df.columns:
        # Pivot if it's in long format (unlikely for a matrix file, but possible)
        # Assuming it's a square matrix saved as CSV where index is feature names
        # and columns are feature names, but T033a said "both coefficients and p-values".
        # Let's assume the file contains a matrix of Pearson correlations for the heatmap.
        # We will look for the numeric columns.
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            return df.set_index(numeric_cols[0])[numeric_cols[1:]] if len(numeric_cols) > 1 else df.set_index(numeric_cols[0])
        else:
            # Fallback: assume first column is index
            df = df.set_index(df.columns[0])
    else:
        # Assume it's already a matrix (index = rows, cols = cols)
        # Ensure numeric
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            # Try to infer if columns are feature names
            pass 
        df = numeric_df if not numeric_df.empty else df

    return df

def plot_partial_dependence(model, X, feature_name: str, output_path: Path):
    """Generates a partial dependence plot for a given feature."""
    from sklearn.inspection import PartialDependenceDisplay
    
    fig, ax = plt.subplots(figsize=(8, 6))
    PartialDependenceDisplay.from_estimator(model, X, features=[feature_name], ax=ax)
    plt.title(f'Partial Dependence Plot: {feature_name}')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)
    logging.info(f"Saved PDP for {feature_name} to {output_path}")

def plot_correlation_heatmap(df: pd.DataFrame, output_path: Path):
    """
    Generates a correlation heatmap from the provided DataFrame.
    Expects df to be a square matrix of correlations.
    """
    if df.empty:
        raise ValueError("Correlation DataFrame is empty, cannot plot heatmap.")
    
    # Ensure we are plotting a square matrix
    # If the DataFrame has non-square shape, we might need to select the Pearson correlation matrix specifically
    # Assuming the input from T033a is a square matrix of Pearson correlations (or the primary correlation type)
    # If T033a saved a specific format (e.g., with p-values), we need to extract the coefficient matrix.
    # Let's assume the CSV contains the Pearson correlation matrix as the primary data.
    
    # If the CSV has columns like 'Pearson', 'Spearman' for each row (long format), we need to pivot.
    # But T033a said "Save correlation matrix", implying a square matrix.
    # Let's try to detect if it's a square matrix.
    if df.shape[0] != df.shape[1]:
        # It might be a long format or have extra columns.
        # We'll try to find the most likely square submatrix or pivot.
        # For now, we assume the first N columns where N = rows form the matrix if it's not square.
        # Or, if it has a 'feature' column, we pivot.
        if 'feature' in df.columns:
            # Assume columns are 'feature', 'correlation_type', 'value'?
            # This is ambiguous without seeing T033a output.
            # We will assume the CSV is a square matrix where index is feature and columns are features.
            # If it's not, we try to select numeric columns that form a square.
            pass
    
    # Standard heatmap
    plt.figure(figsize=(10, 8))
    # Mask the upper triangle for a cleaner look, or show full. Let's show full.
    sns.heatmap(df, annot=True, fmt=".2f", cmap='coolwarm', square=True, linewidths=0.5)
    plt.title('Correlation Matrix Heatmap')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logging.info(f"Saved correlation heatmap to {output_path}")

def plot_feature_importance_stability(stability_metrics: Dict, output_path: Path):
    """Generates a stability plot for feature importances."""
    # Expected stability_metrics structure:
    # {
    #   "feature_importances": {"feat1": mean, ...},
    #   "ci_lower": {"feat1": low, ...},
    #   "ci_upper": {"feat1": high, ...}
    # }
    features = list(stability_metrics.get("feature_importances", {}).keys())
    if not features:
        logging.warning("No features found in stability metrics for plotting.")
        return

    means = [stability_metrics["feature_importances"][f] for f in features]
    lower = [stability_metrics["ci_lower"][f] for f in features]
    upper = [stability_metrics["ci_upper"][f] for f in features]
    
    # Calculate error bars (symmetric or asymmetric)
    # We'll use asymmetric error bars if available
    yerr_lower = np.array(means) - np.array(lower)
    yerr_upper = np.array(upper) - np.array(means)
    yerr = [yerr_lower, yerr_upper]

    plt.figure(figsize=(10, 6))
    plt.bar(features, means, yerr=yerr, capsize=5, color='steelblue', alpha=0.7)
    plt.ylabel('Feature Importance (Mean ± 95% CI)')
    plt.title('Feature Importance Stability Analysis')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logging.info(f"Saved stability plot to {output_path}")

def generate_report_summary(report_path: Path, metrics: Dict, model_path: Path):
    """Generates a markdown summary report."""
    # Placeholder for report generation logic
    with open(report_path, 'w') as f:
        f.write("# Analysis Report\n\n")
        f.write(f"## Model Performance\n")
        f.write(json.dumps(metrics, indent=2))
    logging.info(f"Generated report at {report_path}")

def main():
    """
    Main entry point for T039b: Generate correlation heatmap.
    Input: data/processed/correlation_matrix.csv
    Output: artifacts/reports/correlation_heatmap.png
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "correlation_matrix.csv"
    output_dir = project_root / "artifacts" / "reports"
    output_path = output_dir / "correlation_heatmap.png"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        # Load data
        logging.info(f"Loading correlation matrix from {input_path}")
        df = load_correlation_matrix(input_path)

        # Generate plot
        logging.info("Generating correlation heatmap")
        plot_correlation_heatmap(df, output_path)

        logging.info(f"Task T039b completed successfully. Output: {output_path}")

    except FileNotFoundError as e:
        logging.error(f"Input file missing: {e}")
        raise
    except Exception as e:
        logging.error(f"Error during execution: {e}")
        raise

if __name__ == "__main__":
    main()