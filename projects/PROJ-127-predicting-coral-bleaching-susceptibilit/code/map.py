import os
import sys
import json
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
import rasterio
import numpy as np
from shap import explainers, KernelExplainer
import pandas as pd

def load_raster(raster_path: str) -> np.ndarray:
    """Loads a GeoTIFF raster and returns the data as a NumPy array."""
    with rasterio.open(raster_path) as src:
        return src.read(1)

def generate_risk_map(raster_data: np.ndarray, model_path: str) -> np.ndarray:
    """Generates a bleaching risk map from raster data and a trained model."""
    # Load the model (replace with actual model loading)
    try:
        with open(model_path, 'r') as f:
            model_data = json.load(f)
            # Assuming model is a simple dictionary of weights/biases
            weights = model_data.get('weights', [0.0])  # Default to 0 if weights not found
            bias = model_data.get('bias', 0.0)  # Default to 0 if bias not found
    except FileNotFoundError:
        print(f"Model file not found: {model_path}")
        return np.zeros_like(raster_data)  # Return a zero array if model is missing

    # Apply the model (replace with actual model prediction)
    risk_map = (raster_data * weights[0]) + bias
    risk_map = np.clip(risk_map, 0, 1)  # Ensure probabilities are between 0 and 1
    return risk_map

def perform_threshold_analysis(risk_map: np.ndarray, thresholds: List[float]) -> pd.DataFrame:
    """Performs threshold sensitivity analysis and returns a DataFrame with FP/FN rates."""
    results = []
    for threshold in thresholds:
        predictions = (risk_map > threshold).astype(int)
        # Assuming a ground truth is available (replace with actual ground truth)
        ground_truth = np.random.randint(0, 2, size=risk_map.shape)  # Replace with real GT
        tp = np.sum((predictions == 1) & (ground_truth == 1))
        fp = np.sum((predictions == 1) & (ground_truth == 0))
        fn = np.sum((predictions == 0) & (ground_truth == 1))
        tn = np.sum((predictions == 0) & (ground_truth == 0))

        # Calculate metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        results.append({'threshold': threshold, 'precision': precision, 'recall': recall, 'f1_score': f1_score})

    return pd.DataFrame(results)

def identify_dominant_drivers(raster_data: np.ndarray, model_path: str, top_n: int = 10) -> List[Tuple[str, float]]:
    """Identifies the dominant drivers for the top N high-risk pixels using SHAP values."""
    # Load the model (replace with actual model loading)
    try:
        with open(model_path, 'r') as f:
            model_data = json.load(f)
            # Assuming model is a simple dictionary of weights/biases
            weights = model_data.get('weights', [0.0])  # Default to 0 if weights not found
            bias = model_data.get('bias', 0.0)  # Default to 0 if bias not found
    except FileNotFoundError:
        print(f"Model file not found: {model_path}")
        return []

    # Example data for SHAP (replace with actual feature data)
    background_data = raster_data.flatten().reshape(1, -1)  # Use raster data as background for explanation

    # Create a KernelExplainer
    explainer = KernelExplainer(lambda x: (x * weights[0]) + bias, background_data)
    shap_values = explainer.shap_values(background_data)

    # Get the top N features
    feature_importances = np.abs(shap_values[0]).mean(axis=0)
    top_features = sorted(zip(range(feature_importances.shape[0]), feature_importances), key=lambda x: x[1], reverse=True)[:top_n]

    return [(f"Feature {i}", importance) for i, importance in top_features]

def validate_map_against_independent_reports(risk_map: np.ndarray, independent_data_path: str) -> float:
    """Validates the risk map against independent historical bleaching reports."""
    # Load independent data (replace with actual data loading)
    try:
        independent_data = np.load(independent_data_path)  # Assuming binary data
    except FileNotFoundError:
        print(f"Independent data file not found: {independent_data_path}")
        return 0.0

    # Calculate AUPRC (replace with actual AUPRC calculation)
    from sklearn.metrics import roc_auc_score
    try:
        auprc = roc_auc_score(independent_data.flatten(), risk_map.flatten())
    except ValueError:
        auprc = 0.0
    return auprc

def main():
    """Main function to generate the bleaching risk map."""
    raster_path = "data/processed/raster_2024.tif"  # Replace with actual path
    model_path = "data/models/bleaching_model.json"  # Replace with actual path
    independent_data_path = "data/independent_bleaching_reports.npy" # Replace with real path

    # Load raster data
    try:
        raster_data = load_raster(raster_path)
    except FileNotFoundError:
        print(f"Raster file not found: {raster_path}")
        return

    # Generate risk map
    risk_map = generate_risk_map(raster_data, model_path)

    # Perform threshold analysis
    thresholds = [0.3, 0.5, 0.7]
    threshold_analysis_results = perform_threshold_analysis(risk_map, thresholds)
    print("Threshold Analysis Results:")
    print(threshold_analysis_results)

    # Identify dominant drivers
    dominant_drivers = identify_dominant_drivers(raster_data, model_path)
    print("\nDominant Drivers (Top 10):")
    for feature, importance in dominant_drivers:
        print(f"{feature}: {importance:.4f}")

    # Validate map against independent reports
    auprc = validate_map_against_independent_reports(risk_map, independent_data_path)
    print(f"\nAUPRC: {auprc:.4f}")

    # Save the risk map as a GeoTIFF
    output_path = "data/models/bleaching_risk_map.tif"
    with rasterio.open(output_path, 'w', **raster_data.meta) as dst:
        dst.write(risk_map, 1)

if __name__ == "__main__":
    main()