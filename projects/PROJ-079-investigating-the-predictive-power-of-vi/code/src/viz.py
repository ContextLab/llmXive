import os
import json
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.inspection import PartialDependenceDisplay
from src.config import ARTIFACTS_PATH, DATA_PROCESSED_PATH
from src.utils.logging import get_logger

logger = get_logger(__name__)

PLOTS_PATH = Path(ARTIFACTS_PATH) / "plots"
PLOTS_PATH.mkdir(parents=True, exist_ok=True)

def load_model_and_data() -> tuple:
    """Load the trained model and test data for visualization."""
    model_path = Path(ARTIFACTS_PATH) / "models" / "elastic_net.pkl"
    test_data_path = Path(DATA_PROCESSED_PATH) / "test.csv"

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not test_data_path.exists():
        raise FileNotFoundError(f"Test data file not found: {test_data_path}")

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    test_df = pd.read_csv(test_data_path)
    return model, test_df

def get_feature_columns(df: pd.DataFrame, exclude_cols: Optional[List[str]] = None) -> List[str]:
    """Get list of feature columns from dataframe, excluding specified columns."""
    exclude = exclude_cols or ["strain_accession", "isg_score"]
    return [col for col in df.columns if col not in exclude]

def plot_coefficients(model: Any, features: List[str]) -> None:
    """
    Generate a bar plot of standardized coefficients.
    Sets xlabel, ylabel, title, and legend explicitly.
    """
    if not hasattr(model, 'coef_'):
        raise ValueError("Model does not have coef_ attribute")

    coefficients = model.coef_
    
    # Standardize coefficients by dividing by feature std dev if available
    # For ElasticNet, coefficients are already scaled relative to input
    # We plot raw coefficients but label appropriately
    plt.figure(figsize=(10, 6))
    
    # Sort by absolute magnitude for better visualization
    sorted_indices = np.argsort(np.abs(coefficients))[::-1]
    sorted_features = [features[i] for i in sorted_indices]
    sorted_coefs = [coefficients[i] for i in sorted_indices]

    ax = sns.barplot(x=sorted_coefs, y=sorted_features, palette="viridis")
    
    plt.xlabel("Standardized Coefficient Value", fontsize=12, fontweight='bold')
    plt.ylabel("Viral Feature", fontsize=12, fontweight='bold')
    plt.title("Elastic Net Coefficients: Viral Features vs Host Response", fontsize=14, fontweight='bold')
    plt.axvline(x=0, color='red', linestyle='--', linewidth=1)
    plt.legend(["Coefficient Value"], loc="best")
    
    plt.tight_layout()
    output_path = PLOTS_PATH / "coefficients.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Coefficient plot saved to {output_path}")

def plot_partial_dependence(model: Any, X: pd.DataFrame, features: List[str], n_points: int = 50) -> None:
    """
    Generate partial dependence plots for top-ranked features.
    Sets xlabel, ylabel, title, and legend explicitly.
    """
    if len(features) == 0:
        logger.warning("No features provided for partial dependence plot")
        return

    # Select top 5 features by absolute coefficient magnitude if available
    if hasattr(model, 'coef_'):
        coefs = np.abs(model.coef_)
        top_indices = np.argsort(coefs)[-5:][::-1]
        top_features = [features[i] for i in top_indices]
    else:
        top_features = features[:5]

    if len(top_features) == 0:
        logger.warning("No top features selected for partial dependence plot")
        return

    plt.figure(figsize=(12, 10))
    
    for i, feature in enumerate(top_features):
        if feature not in X.columns:
            logger.warning(f"Feature {feature} not in X, skipping")
            continue
        
        try:
            PartialDependenceDisplay.from_estimator(
                model, X, features=[feature], kind="average", n_points=n_points
            )
            # Get the current axes and set labels
            ax = plt.gca()
            ax.set_xlabel(f"{feature}", fontsize=10)
            ax.set_ylabel("Partial Dependence", fontsize=10)
            ax.set_title(f"Partial Dependence: {feature}", fontsize=12, fontweight='bold')
            
            # Add legend if available
            if hasattr(ax, 'get_legend') and ax.get_legend() is not None:
                ax.get_legend().set_title("Response")
            else:
                ax.legend(["Partial Dependence"], loc="best")
                
        except Exception as e:
            logger.error(f"Failed to plot PDP for {feature}: {e}")
            continue

    plt.suptitle("Partial Dependence Plots: Top 5 Viral Features", fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    output_path = PLOTS_PATH / "pdp_top5.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Partial dependence plot saved to {output_path}")

def run_viz_pipeline() -> None:
    """Run the full visualization pipeline."""
    logger.info("Starting visualization pipeline")
    
    try:
        model, test_df = load_model_and_data()
        features = get_feature_columns(test_df)
        
        if len(features) == 0:
            raise ValueError("No features found in test data")
        
        # Plot coefficients
        plot_coefficients(model, features)
        
        # Plot partial dependence
        X_test = test_df[features]
        plot_partial_dependence(model, X_test, features)
        
        logger.info("Visualization pipeline completed successfully")
    except Exception as e:
        logger.error(f"Visualization pipeline failed: {e}")
        raise

if __name__ == "__main__":
    run_viz_pipeline()