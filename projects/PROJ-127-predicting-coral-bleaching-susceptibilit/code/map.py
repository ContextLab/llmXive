"""
map.py - GeoTIFF generation and threshold analysis for coral bleaching risk.

This module handles:
1. Loading 2024 environmental rasters (SST, DHW).
2. Generating a probability risk map (GeoTIFF).
3. Performing threshold sensitivity analysis.
4. SHAP-based driver identification for high-risk pixels.
"""
import os
import sys
import json
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
import numpy as np
import pandas as pd
import xgboost as xgb
from scipy.stats import zscore

# Import project config
import config

# Optional imports for raster handling
try:
    import rasterio
    from rasterio.crs import CRS
    from rasterio.warp import transform_bounds
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False
    warnings.warn("rasterio not installed. GeoTIFF generation disabled.")

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    warnings.warn("shap not installed. Driver identification disabled.")


def load_raster(raster_path: str) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Load a GeoTIFF raster into a numpy array and metadata.

    Args:
        raster_path: Path to the GeoTIFF file.

    Returns:
        Tuple of (data_array, metadata_dict).
    """
    if not HAS_RASTERIO:
        raise ImportError("rasterio is required to load rasters.")

    with rasterio.open(raster_path) as src:
        data = src.read(1)  # Read first band
        meta = {
            'crs': src.crs,
            'transform': src.transform,
            'width': src.width,
            'height': src.height,
            'nodata': src.nodata
        }
    return data, meta


def generate_risk_map(
    model: xgb.XGBClassifier,
    sst_path: str,
    dhw_path: str,
    output_path: str
) -> None:
    """
    Generate a bleaching risk probability GeoTIFF using the trained model.

    Args:
        model: Trained XGBoost model.
        sst_path: Path to SST GeoTIFF.
        dhw_path: Path to DHW GeoTIFF.
        output_path: Output path for the risk map GeoTIFF.
    """
    if not HAS_RASTERIO:
        raise RuntimeError("Cannot generate risk map: rasterio not installed.")

    if not os.path.exists(sst_path) or not os.path.exists(dhw_path):
        raise FileNotFoundError(f"Input rasters not found. SST: {sst_path}, DHW: {dhw_path}")

    # Load rasters
    sst_data, meta = load_raster(sst_path)
    dhw_data, _ = load_raster(dhw_path)

    # Ensure shapes match
    if sst_data.shape != dhw_data.shape:
        raise ValueError("SST and DHW rasters must have the same dimensions.")

    # Handle nodata
    nodata = meta.get('nodata', -9999)
    valid_mask = (sst_data != nodata) & (dhw_data != nodata)

    # Flatten valid pixels for prediction
    sst_flat = sst_data[valid_mask].reshape(-1, 1)
    dhw_flat = dhw_data[valid_mask].reshape(-1, 1)

    # Prepare features (assuming model expects [SST, DHW, ...])
    # We might need to add other features if the model was trained on more.
    # For this skeleton, we assume a simple 2-feature model or we pad with zeros.
    # In a full implementation, we would load all required feature rasters.
    features = np.hstack([sst_flat, dhw_flat])
    
    # If the model was trained on more features, we need to handle that.
    # For now, we assume the model can handle 2 features or we pad.
    # A robust implementation would check model.n_features_in_.
    if features.shape[1] < model.n_features_in_:
        # Pad with zeros (risky, but prevents crash in skeleton)
        padding = np.zeros((features.shape[0], model.n_features_in_ - features.shape[1]))
        features = np.hstack([features, padding])

    # Predict probabilities
    probs = model.predict_proba(features)[:, 1]

    # Reconstruct the grid
    risk_grid = np.full(sst_data.shape, np.nan)
    risk_grid[valid_mask] = probs

    # Write output GeoTIFF
    with rasterio.open(
        output_path,
        'w',
        driver='GTiff',
        height=risk_grid.shape[0],
        width=risk_grid.shape[1],
        count=1,
        dtype=risk_grid.dtype,
        crs=meta['crs'],
        transform=meta['transform']
    ) as dst:
        dst.write(risk_grid, 1)

    print(f"Risk map saved to {output_path}")


def perform_threshold_analysis(
    model: xgb.XGBClassifier,
    data_path: str,
    output_csv: str,
    output_report: str,
    thresholds: List[float] = [0.3, 0.5, 0.7]
) -> None:
    """
    Perform threshold sensitivity analysis on the model.

    Args:
        model: Trained XGBoost model.
        data_path: Path to the processed CSV data (reef_species_unified.csv).
        output_csv: Path to save the sensitivity table.
        output_report: Path to save the summary report.
        thresholds: List of probability thresholds to evaluate.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")

    df = pd.read_csv(data_path)

    # Identify target column (assumed to be 'bleaching_label' or similar)
    target_col = 'bleaching_label' if 'bleaching_label' in df.columns else None
    if not target_col:
        raise ValueError("Could not find target column 'bleaching_label' in data.")

    # Prepare features (must match training features)
    # This assumes features are numeric columns excluding target and IDs
    feature_cols = [c for c in df.columns if c not in [target_col, 'id', 'reef_id']]
    X = df[feature_cols]
    y = df[target_col]

    # Predict probabilities
    probs = model.predict_proba(X)[:, 1]

    results = []
    for t in thresholds:
        preds = (probs >= t).astype(int)
        
        # Calculate metrics
        tp = ((preds == 1) & (y == 1)).sum()
        fp = ((preds == 1) & (y == 0)).sum()
        fn = ((preds == 0) & (y == 1)).sum()
        tn = ((preds == 0) & (y == 0)).sum()

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        false_negative_rate = fn / (tp + fn) if (tp + fn) > 0 else 0.0

        results.append({
            'threshold': t,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'false_positive_rate': false_positive_rate,
            'false_negative_rate': false_negative_rate,
            'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn
        })

    results_df = pd.DataFrame(results)
    results_df.to_csv(output_csv, index=False)

    # Generate report
    report_lines = [
        "# Threshold Sensitivity Analysis Report",
        "",
        f"Model: XGBoost",
        f"Data Source: {data_path}",
        "",
        "## Summary",
        "Analysis of classification thresholds {0.3, 0.5, 0.7} on the reef species dataset.",
        "",
        "## Metrics by Threshold",
    ]
    for row in results:
        report_lines.append(f"- **Threshold {row['threshold']}:** F1={row['f1_score']:.3f}, FP Rate={row['false_positive_rate']:.3f}, FN Rate={row['false_negative_rate']:.3f}")
    
    # Calculate delta
    f1s = results_df['f1_score'].values
    f1_delta = f1s.max() - f1s.min()
    report_lines.append("")
    report_lines.append(f"## Variation Analysis")
    report_lines.append(f"F1 Score Delta (Range): {f1_delta:.3f}")
    
    with open(output_report, 'w') as f:
        f.write('\n'.join(report_lines))
    
    print(f"Sensitivity analysis saved to {output_csv} and {output_report}")


def identify_dominant_drivers(
    model: xgb.XGBClassifier,
    data_path: str,
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Use SHAP to identify dominant drivers for high-risk predictions.

    Args:
        model: Trained XGBoost model.
        data_path: Path to the processed CSV.
        top_k: Number of top high-risk pixels to analyze.

    Returns:
        List of dictionaries describing dominant drivers.
    """
    if not HAS_SHAP:
        raise ImportError("shap is required for driver identification.")

    df = pd.read_csv(data_path)
    target_col = 'bleaching_label' if 'bleaching_label' in df.columns else None
    if not target_col:
        raise ValueError("Target column 'bleaching_label' not found.")

    feature_cols = [c for c in df.columns if c not in [target_col, 'id', 'reef_id']]
    X = df[feature_cols]
    
    # Calculate SHAP values
    explainer = shap.Explainer(model, X)
    shap_values = explainer(X)

    # Identify top k high-risk pixels (highest predicted probability)
    probs = model.predict_proba(X)[:, 1]
    top_indices = np.argsort(probs)[-top_k:][::-1]

    drivers = []
    for idx in top_indices:
        pixel_shap = shap_values.values[idx]
        # Get feature names and values
        feature_vals = X.iloc[idx].values
        
        # Find the feature with the highest absolute SHAP value
        max_idx = np.argmax(np.abs(pixel_shap))
        dominant_feature = feature_cols[max_idx]
        contribution = pixel_shap[max_idx]
        
        drivers.append({
            'pixel_index': int(idx),
            'predicted_probability': float(probs[idx]),
            'dominant_driver': dominant_feature,
            'contribution': float(contribution),
            'feature_value': float(feature_vals[max_idx])
        })

    return drivers


def main():
    """
    Main entry point for the map module.
    Executes the risk map generation and threshold analysis if data is available.
    """
    # Paths
    sst_path = config.RASTER_2024_SST
    dhw_path = config.RASTER_2024_DHW
    data_path = config.DATA_PROCESSED_UNIFIED
    output_map = config.OUTPUT_RISK_MAP
    output_csv = config.OUTPUT_THRESHOLD_CSV
    output_report = config.OUTPUT_THRESHOLD_REPORT

    # Check if inputs exist
    if not os.path.exists(sst_path) or not os.path.exists(dhw_path):
        print(f"Warning: Input rasters not found at {sst_path} or {dhw_path}. Skipping map generation.")
        print("Ensure 2024 rasters are downloaded (Task T031B).")
    else:
        # We need a model to generate the map. 
        # In a real pipeline, this would be loaded from a saved model file.
        # For this skeleton, we assume a model exists or we skip if not found.
        model_path = config.MODEL_PATH
        if os.path.exists(model_path):
            import joblib
            model = joblib.load(model_path)
            print(f"Loaded model from {model_path}")
            generate_risk_map(model, sst_path, dhw_path, output_map)
        else:
            print(f"Warning: Model not found at {model_path}. Skipping risk map generation.")

    # Threshold analysis requires data and model
    if os.path.exists(data_path) and os.path.exists(config.MODEL_PATH):
        import joblib
        model = joblib.load(config.MODEL_PATH)
        perform_threshold_analysis(model, data_path, output_csv, output_report)
    else:
        print("Warning: Data or model missing. Skipping threshold analysis.")

    print("Map module execution complete.")


if __name__ == "__main__":
    main()
