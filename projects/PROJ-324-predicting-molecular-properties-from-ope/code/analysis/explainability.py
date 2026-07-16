import os
import sys
import pickle
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
import shap

from seed_manager import set_global_seed
from logging_utils import setup_logger

# Configure logging
logger = setup_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DERIVED_DIR = DATA_DIR / "derived"
MODEL_PATH = DERIVED_DIR / "final_model.pkl"
FINGERPRINTS_PATH = DERIVED_DIR / "fingerprints.parquet"
INTERACTION_OUTPUT_PATH = DERIVED_DIR / "shap_interactions.png"
INTERACTION_SUMMARY_PATH = DERIVED_DIR / "shap_interaction_summary.csv"

def load_model(model_path: Path = MODEL_PATH) -> RandomForestRegressor:
    """Load the trained Random Forest model from disk."""
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    logger.info(f"Loaded model from {model_path}")
    return model

def load_fingerprints_data(fingerprints_path: Path = FINGERPRINTS_PATH) -> Tuple[pd.DataFrame, pd.Series]:
    """Load fingerprints and target values from the processed dataset."""
    if not fingerprints_path.exists():
        raise FileNotFoundError(f"Fingerprints data not found at {fingerprints_path}")
    
    df = pd.read_parquet(fingerprints_path)
    
    # Assuming the last column is the target variable (e.g., logP)
    # and the rest are fingerprint bits
    fingerprint_cols = [col for col in df.columns if col.startswith('fp_')]
    target_col = [col for col in df.columns if col not in fingerprint_cols][0]
    
    X = df[fingerprint_cols]
    y = df[target_col]
    
    logger.info(f"Loaded fingerprints data with {X.shape[1]} features and {X.shape[0]} samples")
    return X, y

def calculate_shap_interactions(
    model: RandomForestRegressor,
    X: pd.DataFrame,
    sample_size: int = 1000,
    seed: int = 42
) -> np.ndarray:
    """
    Calculate SHAP interaction values for the model.
    
    Args:
        model: Trained Random Forest model
        X: Feature matrix (fingerprints)
        sample_size: Number of samples to use for SHAP calculation (for performance)
        seed: Random seed for reproducibility
    
    Returns:
        SHAP interaction values array
    """
    set_global_seed(seed)
    
    # Sample data if dataset is too large for SHAP computation
    if X.shape[0] > sample_size:
        logger.info(f"Sampling {sample_size} rows from {X.shape[0]} for SHAP calculation")
        X_sample = X.sample(n=sample_size, random_state=seed)
    else:
        X_sample = X
    
    # Create SHAP explainer
    explainer = shap.TreeExplainer(model)
    
    # Calculate interaction values
    logger.info("Calculating SHAP interaction values...")
    shap_interaction_values = explainer.shap_interaction_values(X_sample)
    
    logger.info(f"SHAP interaction values shape: {shap_interaction_values.shape}")
    return shap_interaction_values

def save_interaction_summary(
    shap_interaction_values: np.ndarray,
    feature_names: List[str],
    output_path: Path = INTERACTION_SUMMARY_PATH,
    top_n: int = 50
) -> pd.DataFrame:
    """
    Save the top interacting feature pairs to a CSV file.
    
    Args:
        shap_interaction_values: SHAP interaction values array
        feature_names: List of feature names
        output_path: Path to save the summary CSV
        top_n: Number of top interactions to save
    
    Returns:
        DataFrame of top interactions
    """
    # Aggregate interaction values (absolute mean) across samples
    # Shape: (n_samples, n_features, n_features)
    interaction_strengths = np.abs(shap_interaction_values).mean(axis=0)
    
    # Create a list of all unique pairs
    pairs = []
    for i in range(len(feature_names)):
        for j in range(i + 1, len(feature_names)):
            strength = interaction_strengths[i, j]
            pairs.append({
                'feature_1': feature_names[i],
                'feature_2': feature_names[j],
                'interaction_strength': strength
            })
    
    df_pairs = pd.DataFrame(pairs)
    
    # Sort by interaction strength
    df_pairs = df_pairs.sort_values('interaction_strength', ascending=False)
    
    # Select top N
    top_interactions = df_pairs.head(top_n)
    
    # Save to CSV
    top_interactions.to_csv(output_path, index=False)
    logger.info(f"Saved top {top_n} interactions to {output_path}")
    
    return top_interactions

def generate_interaction_heatmap(
    shap_interaction_values: np.ndarray,
    feature_names: List[str],
    output_path: Path = INTERACTION_OUTPUT_PATH,
    top_n: int = 20
) -> None:
    """
    Generate and save a heatmap of top interacting fingerprint bit pairs.
    
    Args:
        shap_interaction_values: SHAP interaction values array
        feature_names: List of feature names
        output_path: Path to save the heatmap PNG
        top_n: Number of top features to include in the heatmap
    """
    # Aggregate interaction values
    interaction_strengths = np.abs(shap_interaction_values).mean(axis=0)
    
    # Identify top N features by total interaction strength
    # Sum over both axes (symmetric matrix)
    total_strength = interaction_strengths.sum(axis=1)
    top_indices = np.argsort(total_strength)[-top_n:]
    top_indices = np.sort(top_indices)
    
    # Subset the interaction matrix
    subset_matrix = interaction_strengths[np.ix_(top_indices, top_indices)]
    subset_features = [feature_names[i] for i in top_indices]
    
    # Create DataFrame for plotting
    heatmap_df = pd.DataFrame(subset_matrix, index=subset_features, columns=subset_features)
    
    # Create the heatmap
    plt.figure(figsize=(12, 10))
    sns.heatmap(
        heatmap_df,
        annot=False,
        cmap='YlOrRd',
        cbar_kws={'label': 'Mean |SHAP Interaction Value|'},
        linewidths=0.5,
        square=True
    )
    
    plt.title(f'Top {top_n} Interacting Fingerprint Bit Pairs (SHAP Interaction Values)')
    plt.xlabel('Fingerprint Bit')
    plt.ylabel('Fingerprint Bit')
    
    # Save the plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved interaction heatmap to {output_path}")

def main():
    """Main function to run SHAP interaction analysis."""
    try:
        # Ensure output directory exists
        DERIVED_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load model
        model = load_model()
        
        # Load fingerprints data
        X, y = load_fingerprints_data()
        
        # Calculate SHAP interaction values
        shap_interaction_values = calculate_shap_interactions(model, X)
        
        # Get feature names
        feature_names = [f"fp_{i}" for i in range(X.shape[1])]
        
        # Save interaction summary
        save_interaction_summary(shap_interaction_values, feature_names)
        
        # Generate and save heatmap
        generate_interaction_heatmap(shap_interaction_values, feature_names)
        
        logger.info("SHAP interaction analysis completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during SHAP interaction analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()