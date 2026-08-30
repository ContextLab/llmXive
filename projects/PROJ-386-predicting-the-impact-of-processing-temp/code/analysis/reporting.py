import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.inspection import PartialDependenceDisplay
from sklearn.ensemble import RandomForestRegressor

from config import get_config, ensure_dirs
from analysis.diagnostics import load_rf_model_artifact, load_collinearity_report

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler('data/artifacts/reporting.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

def load_processed_data() -> pd.DataFrame:
    """
    Load the preprocessed data from the expected location.
    Expects data/processed/preprocessed_data.csv based on pipeline conventions.
    """
    config = get_config()
    data_path = config['paths']['processed_data']
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data not found at {data_path}. "
                                "Run preprocessing pipeline first.")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded preprocessed data with shape: {df.shape}")
    return df

def get_median_compositions(df: pd.DataFrame, target_elements: List[str]) -> Dict[str, float]:
    """
    Calculate median composition for specific elements to use in PDP.
    """
    median_vals = {}
    for elem in target_elements:
        if elem in df.columns:
            median_vals[elem] = df[elem].median()
        else:
            logger.warning(f"Element {elem} not found in data columns.")
            median_vals[elem] = 0.0
    return median_vals

def generate_partial_dependence_plots(
    model: RandomForestRegressor,
    features: List[str],
    X: pd.DataFrame,
    output_path: str
) -> None:
    """
    Generate Partial Dependence Plots (PDP) for specific features.
    Visualizes Grain Size vs. Temp for specific compositions (held constant at median).
    
    Args:
        model: Trained Random Forest model
        features: List of feature names to plot (e.g., ['Temperature', 'Temp_Mg'])
        X: Feature dataframe used for training (contains all features)
        output_path: Path to save the figure
    """
    if not features:
        raise ValueError("At least one feature must be provided for PDP.")
    
    # Determine target variable (assumed to be 'Grain_Size' or 'residual_grain_size')
    # Based on US2 residualization, the target is likely residuals or original grain size
    # We assume the model was trained on residuals or the target is known.
    # For visualization, we plot the partial dependence on the target scale.
    
    target_col = 'Grain_Size'
    if target_col not in X.columns:
        # Fallback if residuals are used as target, but we want to plot on original scale?
        # The PDP shows the effect on the predicted target.
        # If model predicts residuals, PDP shows effect on residuals.
        # Let's assume the model predicts 'Grain_Size' or 'residual_grain_size'.
        # We will use the first column that looks like a target if 'Grain_Size' is missing.
        potential_targets = [c for c in X.columns if 'Grain' in c or 'Size' in c]
        if potential_targets:
            target_col = potential_targets[0]
        else:
            target_col = X.columns[-1] # Fallback to last column
    
    logger.info(f"Generating PDP for features: {features}")
    logger.info(f"Using target column: {target_col}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Set plot style
    sns.set(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    # Create PDP display
    # Note: PartialDependenceDisplay.from_estimator is sklearn >= 1.0
    # If older sklearn, use PartialDependenceDisplay
    try:
        # Attempt to use the modern API
        display = PartialDependenceDisplay.from_estimator(
            model,
            X,
            features=features,
            ax=ax,
            kind='average'
        )
    except Exception as e:
        logger.warning(f"Error using from_estimator: {e}. Attempting manual calculation.")
        # Fallback: Manual calculation if API differs
        # This is a simplified manual PDP for single features
        for feature in features:
            if feature in X.columns:
                feature_vals = np.linspace(X[feature].min(), X[feature].max(), 10)
                predictions = []
                for val in feature_vals:
                    X_temp = X.copy()
                    X_temp[feature] = val
                    preds = model.predict(X_temp)
                    predictions.append(np.mean(preds))
                ax.plot(feature_vals, predictions, label=feature)
        
        ax.set_xlabel('Feature Value')
        ax.set_ylabel('Partial Dependence (Predicted Grain Size)')
        ax.legend()

    plt.title(f'Partial Dependence Plot: Grain Size vs. {", ".join(features)}')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    
    logger.info(f"Partial Dependence Plot saved to: {output_path}")

def run_reporting_pipeline() -> Dict[str, Any]:
    """
    Main pipeline function for T033:
    1. Load processed data and RF model.
    2. Identify key features (Temperature, Interaction terms).
    3. Generate Partial Dependence Plots visualizing Grain Size vs. Temp.
    4. Save plot to data/artifacts/.
    """
    config = get_config()
    output_dir = config['paths']['artifacts']
    ensure_dirs([output_dir])

    # 1. Load Model
    logger.info("Loading RF model artifact...")
    model, feature_names = load_rf_model_artifact()
    if model is None:
        raise RuntimeError("Failed to load RF model. Ensure T030 completed successfully.")
    
    # 2. Load Data
    logger.info("Loading preprocessed data...")
    df = load_processed_data()
    
    # Ensure feature names match columns
    # The model might have been trained on a subset or transformed names.
    # We assume feature_names from the model artifact matches the dataframe columns used for training.
    # If not, we align them.
    available_features = [f for f in feature_names if f in df.columns]
    if not available_features:
        raise ValueError(f"No model features found in dataframe. Columns: {df.columns}, Model features: {feature_names}")
    
    X = df[available_features]

    # 3. Define Features for PDP
    # Prioritize 'Temperature' and interaction terms involving Temperature
    temp_feature = 'Temperature'
    if temp_feature not in available_features:
        # Try variations
        for f in available_features:
            if 'temp' in f.lower() or 'Temp' in f:
                temp_feature = f
                break
    
    interaction_features = [f for f in available_features if 'Temp' in f and f != temp_feature]
    
    # If no specific temp feature found, just use the first one or raise
    if temp_feature not in available_features:
        logger.warning("Could not identify a 'Temperature' feature. Using first available feature.")
        temp_feature = available_features[0]

    features_to_plot = [temp_feature]
    if interaction_features:
        features_to_plot.extend(interaction_features[:2]) # Limit to top 2 interactions for clarity

    logger.info(f"Generating PDP for: {features_to_plot}")

    # 4. Generate Plot
    output_path = os.path.join(output_dir, 'partial_dependence_temp.png')
    generate_partial_dependence_plots(model, features_to_plot, X, output_path)

    # 5. Log Summary
    summary = {
        "task_id": "T033",
        "status": "completed",
        "plot_path": output_path,
        "features_plotted": features_to_plot,
        "model_features_used": available_features
    }
    
    logger.info(f"Reporting pipeline completed. Summary: {json.dumps(summary, indent=2)}")
    return summary

def main():
    parser = argparse.ArgumentParser(description="Generate Partial Dependence Plots (T033)")
    parser.add_argument('--output-dir', type=str, default=None, help="Override output directory")
    args = parser.parse_args()

    if args.output_dir:
        config = get_config()
        config['paths']['artifacts'] = args.output_dir

    try:
        run_reporting_pipeline()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
