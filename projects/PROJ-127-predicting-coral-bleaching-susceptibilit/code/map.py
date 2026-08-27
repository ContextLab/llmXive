import os
import sys
import json
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union

import numpy as np
import pandas as pd
import xgboost as xgb
import rasterio
from rasterio.warp import calculate_default_transform, transform_bounds
from rasterio.features import geometry_mask
from shapely.geometry import mapping
import geopandas as gpd

import config
from train import load_data

def load_raster(path: Path) -> Tuple[np.ndarray, dict]:
    """
    Load a single band raster file.
    Returns (data_array, profile_dict).
    """
    if not path.exists():
        raise FileNotFoundError(f"Raster file not found: {path}")
    
    with rasterio.open(path) as src:
        data = src.read(1).astype(np.float32)
        profile = src.profile
        # Handle nodata values
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
    return data, profile

def generate_risk_map(model: xgb.Booster, raster_paths: Dict[str, Path], output_path: Path) -> None:
    """
    Load environmental rasters, predict bleaching risk, and save as GeoTIFF.
    
    Args:
        model: Trained XGBoost model.
        raster_paths: Dictionary mapping feature names to raster file paths.
                      Expected keys: 'sst', 'dhw', 'thermal_tolerance', etc.
        output_path: Path to save the output risk map GeoTIFF.
    """
    # Load all rasters and verify they have the same shape and transform
    raster_data = {}
    base_profile = None
    base_shape = None
    
    for key, path in raster_paths.items():
        if not path.exists():
            raise FileNotFoundError(f"Required raster missing for feature '{key}': {path}")
        
        data, profile = load_raster(path)
        
        if base_shape is None:
            base_shape = data.shape
            base_profile = profile
        else:
            if data.shape != base_shape:
                raise ValueError(f"Shape mismatch for {key}: {data.shape} vs {base_shape}")
            # In a real scenario, we might reproject here if transforms differ
            # For now, we assume they are aligned as per project design
        
        raster_data[key] = data

    # Prepare feature matrix for prediction
    # Stack rasters into a 2D array (n_samples, n_features)
    # We flatten the rasters
    n_rows, n_cols = base_shape
    n_samples = n_rows * n_cols
    
    # Create a DataFrame for prediction
    feature_names = list(raster_paths.keys())
    X_flat = np.column_stack([raster_data[f].flatten() for f in feature_names])
    
    # Handle NaNs: We'll predict on valid data and mask invalid later
    valid_mask = ~np.any(np.isnan(X_flat), axis=1)
    X_valid = X_flat[valid_mask]
    
    if len(X_valid) == 0:
        raise ValueError("No valid data points found in rasters for prediction.")
    
    # Predict using XGBoost
    # XGBoost expects a DMatrix or array
    preds = model.predict(xgb.DMatrix(X_valid))
    
    # Reconstruct the full prediction map
    full_preds = np.full(n_samples, np.nan, dtype=np.float32)
    full_preds[valid_mask] = preds
    
    risk_map = full_preds.reshape(base_shape)
    
    # Ensure probabilities are clipped to [0, 1]
    risk_map = np.clip(risk_map, 0.0, 1.0)
    
    # Create output profile
    out_profile = base_profile.copy()
    out_profile.update({
        'driver': 'GTiff',
        'dtype': 'float32',
        'count': 1,
        'compress': 'lzw'
    })
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with rasterio.open(output_path, 'w', **out_profile) as dst:
        dst.write(risk_map, 1)
    
    print(f"Risk map generated and saved to: {output_path}")

def perform_threshold_analysis(model, X, y, thresholds: List[float]) -> pd.DataFrame:
    """
    Perform threshold sensitivity analysis.
    
    Args:
        model: Trained model.
        X: Feature matrix.
        y: True labels.
        thresholds: List of cutoff thresholds to evaluate.
        
    Returns:
        DataFrame with threshold, TP, FP, TN, FN, Precision, Recall, F1.
    """
    preds = model.predict(xgb.DMatrix(X))
    results = []
    
    for thresh in thresholds:
        binary_preds = (preds >= thresh).astype(int)
        
        tp = ((binary_preds == 1) & (y == 1)).sum()
        fp = ((binary_preds == 1) & (y == 0)).sum()
        tn = ((binary_preds == 0) & (y == 0)).sum()
        fn = ((binary_preds == 0) & (y == 1)).sum()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        results.append({
            'threshold': thresh,
            'tp': int(tp),
            'fp': int(fp),
            'tn': int(tn),
            'fn': int(fn),
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'fp_rate': fp / (fp + tn) if (fp + tn) > 0 else 0.0,
            'fn_rate': fn / (tp + fn) if (tp + fn) > 0 else 0.0
        })
    
    return pd.DataFrame(results)

def identify_dominant_drivers(model, X: np.ndarray, indices: List[int], feature_names: List[str]) -> pd.DataFrame:
    """
    Identify dominant drivers for specific pixels using permutation importance locally.
    Note: For a full SHAP analysis, the 'shap' library would be required.
    Here we use a simplified local perturbation approach to estimate driver impact.
    
    Args:
        model: Trained model.
        X: Full feature matrix.
        indices: List of row indices (pixels) to analyze.
        feature_names: Names of features corresponding to X columns.
        
    Returns:
        DataFrame with pixel index, feature, and impact score.
    """
    if len(indices) == 0:
        return pd.DataFrame(columns=['pixel_index', 'feature', 'impact'])
    
    X_subset = X[indices]
    base_preds = model.predict(xgb.DMatrix(X_subset))
    
    impacts = []
    for i, row_idx in enumerate(indices):
        x_sample = X_subset[i].copy().reshape(1, -1)
        base_pred = base_preds[i]
        
        for j, feat_name in enumerate(feature_names):
            # Perturb feature j by 10% of its range (approx)
            # Using a small epsilon for local sensitivity
            x_perturbed = x_sample.copy()
            x_perturbed[0, j] += 0.1 * (x_sample.max() - x_sample.min()) if (x_sample.max() - x_sample.min()) > 0 else 0.1
            
            perturbed_pred = model.predict(xgb.DMatrix(x_perturbed))[0]
            impact = abs(perturbed_pred - base_pred)
            
            impacts.append({
                'pixel_index': int(row_idx),
                'feature': feat_name,
                'impact': float(impact)
            })
    
    return pd.DataFrame(impacts)

def main():
    """
    Main function to execute the risk mapping pipeline.
    1. Loads the trained model from data/models.
    2. Loads 2024 environmental rasters specified in config.
    3. Generates the risk map.
    4. Performs threshold analysis if validation data is available.
    """
    print("Starting Risk Mapping Pipeline (T030)...")
    
    # Paths
    model_path = Path(config.MODEL_PATH) / "best_model.json"
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Run training first.")
    
    # Load model
    model = xgb.Booster()
    model.load_model(str(model_path))
    
    # Define 2024 Raster inputs
    # These paths should be populated by T031B. We assume config provides them or we construct them.
    # Assuming config has variables like RASTER_2024_SST, RASTER_2024_DHW, etc.
    # If not explicitly in config, we try to infer from common patterns or fail.
    
    # Check for required rasters in config
    required_features = ['sst', 'dhw', 'thermal_tolerance']
    raster_paths = {}
    
    # Attempt to load from config attributes if they exist, otherwise raise error
    # This assumes T031B has populated config with these paths or we use default patterns
    # For robustness, we check if the attributes exist
    for feat in required_features:
        attr_name = f"RASTER_2024_{feat.upper()}"
        if hasattr(config, attr_name):
            path_str = getattr(config, attr_name)
            if path_str:
                raster_paths[feat] = Path(path_str)
            else:
                raise ValueError(f"Config attribute {attr_name} is empty. Raster {feat} missing.")
        else:
            # Fallback to a standard path if not explicitly defined in config but expected
            # This is a heuristic; in a strict pipeline, T031B should set these in config
            fallback = Path(config.DATA_PROCESSED) / f"2024_{feat}.tif"
            if fallback.exists():
                raster_paths[feat] = fallback
            else:
                raise FileNotFoundError(f"Raster for '{feat}' not found. Check config.{attr_name} or fallback at {fallback}.")

    # Output path
    output_path = Path(config.MODEL_OUTPUT) / "bleaching_risk_map.tif"
    
    try:
        generate_risk_map(model, raster_paths, output_path)
    except Exception as e:
        print(f"Error generating risk map: {e}")
        sys.exit(1)

    # Optional: Threshold Analysis if we have processed data
    # We load the unified dataset to get X and y for analysis
    unified_path = Path(config.DATA_PROCESSED) / "reef_species_unified.csv"
    if unified_path.exists():
        print("Performing threshold sensitivity analysis...")
        try:
            df = pd.read_csv(unified_path)
            # Filter for valid rows
            cols = required_features + ['bleaching_label']
            if not all(c in df.columns for c in cols):
                # Try to find feature columns that exist
                avail_cols = [c for c in required_features if c in df.columns]
                if len(avail_cols) == 0:
                    warnings.warn("No feature columns found for threshold analysis.")
                else:
                    X = df[avail_cols].dropna()
                    y = df.loc[X.index, 'bleaching_label']
                    if len(X) > 0 and 'bleaching_label' in df.columns:
                        thresholds = [0.3, 0.5, 0.7]
                        thresh_df = perform_threshold_analysis(model, X.values, y.values, thresholds)
                        
                        thresh_out = Path(config.DATA_PROCESSED) / "threshold_sensitivity.csv"
                        thresh_df.to_csv(thresh_out, index=False)
                        print(f"Threshold sensitivity report saved to {thresh_out}")
                        
                        # Generate simple report
                        report_path = Path(config.DATA_PROCESSED) / "sensitivity_report.md"
                        with open(report_path, 'w') as f:
                            f.write("# Threshold Sensitivity Analysis\n\n")
                            f.write(f"Analyzed {len(X)} data points.\n\n")
                            f.write(thresh_df.to_markdown(index=False))
                        print(f"Sensitivity report saved to {report_path}")
        except Exception as e:
            warnings.warn(f"Could not perform threshold analysis: {e}")
    else:
        warnings.warn(f"Unified dataset not found at {unified_path}. Skipping threshold analysis.")

    print("Risk Mapping Pipeline completed.")

if __name__ == "__main__":
    main()
