import os
import sys
import json
import logging
import time
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
import shap
from sklearn.ensemble import RandomForestRegressor

# Import memory profiling utilities
from memory_profiler import profile_memory, ensure_results_directory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_descriptor_schema(schema_path: str) -> Dict[str, Any]:
    """Load the descriptor schema from JSON file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return json.load(f)

def generate_physics_inspired_weights(schema: Dict[str, Any]) -> np.ndarray:
    """
    Generate physics-inspired weights for synthetic data.
    Weight for 'mean_atomic_number' is derived from a scaling factor, others negligible.
    """
    feature_count = schema.get('feature_count', 0)
    feature_names = schema.get('features', [])
    
    weights = np.zeros(feature_count)
    if 'mean_atomic_number' in feature_names:
        idx = feature_names.index('mean_atomic_number')
        # Physics-inspired: weight proportional to atomic number importance
        weights[idx] = 1.0 / 10.0 # Scaling factor
    else:
        # Fallback: assign random small weights if specific feature not found
        logger.warning("mean_atomic_number not found in schema. Assigning random weights.")
        weights = np.random.rand(feature_count) * 0.01
    
    return weights

def generate_synthetic_target(X: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Generate synthetic target based on known weights."""
    alpha = 0.1
    beta = 0.05
    target = np.dot(X, weights) + alpha * np.sum(X**2, axis=1) + beta * np.sum(X * np.roll(X, 1, axis=1), axis=1)
    return target

def generate_synthetic_dataset(schema_path: str, n_samples: int = 1000, seed: int = 42) -> pd.DataFrame:
    """Generate a synthetic dataset with known ground truth."""
    np.random.seed(seed)
    schema = load_descriptor_schema(schema_path)
    weights = generate_physics_inspired_weights(schema)
    
    feature_count = len(weights)
    X = np.random.randn(n_samples, feature_count)
    y = generate_synthetic_target(X, weights)
    
    df = pd.DataFrame(X, columns=schema.get('features', [f'feature_{i}' for i in range(feature_count)]))
    df['target'] = y
    df['known_weights'] = weights.tolist()
    
    return df

def save_ground_truth(df: pd.DataFrame, output_path: str):
    """Save synthetic ground truth to parquet."""
    df.to_parquet(output_path)
    logger.info(f"Synthetic ground truth saved to {output_path}")

@profile_memory(output_path="results/memory_profile.csv")
def run_shap_analysis(
    model_path: str, 
    data_path: str, 
    output_dir: str, 
    model_type: str = 'rf'
):
    """
    Compute SHAP values for a trained model and save results.
    Decorated with memory profiler.
    """
    ensure_results_directory()
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Loading model from {model_path}")
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
        model = model_data['model']
        scaler = model_data.get('scaler', None)
    
    logger.info(f"Loading data from {data_path}")
    df = pd.read_parquet(data_path)
    
    # Assume all columns except 'target' are features
    feature_cols = [c for c in df.columns if c != 'target' and c != 'known_weights']
    X = df[feature_cols].values
    
    if scaler:
        X = scaler.transform(X)
    
    logger.info(f"Computing SHAP values for {model_type} model...")
    # Use a background sample for SHAP if dataset is large
    background = shap.sample(X, min(100, len(X)))
    explainer = shap.Explainer(model, background)
    shap_values = explainer(X)
    
    # Save SHAP values
    output_file = os.path.join(output_dir, f"shap_{model_type}.npy")
    np.save(output_file, shap_values.values)
    logger.info(f"SHAP values saved to {output_file}")
    
    return shap_values

def main():
    """Entry point for SHAP analysis."""
    # Default paths
    schema_path = "data/processed/descriptor_schema.json"
    model_path = "results/models/target_property_rf.pkl" # Example path
    data_path = "data/processed/descriptors.parquet"
    output_dir = "results/shap_analysis"
    
    # Generate synthetic data if needed
    synthetic_path = os.path.join("data/synthetic", "ground_truth.parquet")
    os.makedirs(os.path.dirname(synthetic_path), exist_ok=True)
    if not os.path.exists(synthetic_path):
        logger.info("Generating synthetic ground truth...")
        df_synthetic = generate_synthetic_dataset(schema_path)
        save_ground_truth(df_synthetic, synthetic_path)
    
    # Run SHAP analysis
    run_shap_analysis(model_path, data_path, output_dir)

if __name__ == "__main__":
    main()
