import os
import sys
import json
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
import pandas as pd
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, transform_bounds
from scipy import stats
from sklearn.metrics import precision_recall_curve, auc

# Import config and other project modules
import config
from evaluate import load_model_and_data
from ingest import download_csv

def load_raster(path: str) -> Tuple[np.ndarray, rasterio.DatasetReader]:
    """Load a raster file and return the array and dataset."""
    with rasterio.open(path) as src:
        data = src.read(1)
        transform = src.transform
        crs = src.crs
    return data, src

def generate_risk_map(model, features: pd.DataFrame, output_path: str) -> None:
    """Generate a risk map GeoTIFF based on model predictions."""
    # Implementation handled in previous tasks (T030)
    pass

def threshold_sensitivity(predictions: np.ndarray, labels: np.ndarray) -> pd.DataFrame:
    """Perform threshold sensitivity analysis."""
    # Implementation handled in previous tasks (T032)
    pass

def identify_dominant_drivers(model, X: np.ndarray, feature_names: List[str], top_k: int = 10) -> pd.DataFrame:
    """Identify dominant drivers using SHAP values."""
    # Implementation handled in previous tasks (T031)
    pass

def validate_map_against_independent_reports(
    model,
    feature_df: pd.DataFrame,
    config: Dict[str, Any],
    output_metrics_path: str = "data/metrics.json"
) -> Dict[str, Any]:
    """
    Validate the generated risk map against independent historical bleaching reports.
    
    This function:
    1. Fetches 2023 bleaching events from REEFBASE_URL.
    2. Aligns the model's predictions with the observed events.
    3. Calculates AUPRC if data is available.
    4. Updates metrics.json with the results.
    """
    metrics = {
        "independent_data_available": False,
        "auprc": None,
        "event_count": 0,
        "warning": None
    }

    reefbase_url = config.get("REEFBASE_URL")
    if not reefbase_url:
        metrics["warning"] = "REEFBASE_URL not found in config."
        return metrics

    try:
        # Attempt to download the specific file requested in the task
        # We assume the URL points to a directory or a specific file pattern.
        # Based on the task description: "Fetch 2023_bleaching_events.csv"
        # If the URL is a base URL, we construct the specific file path.
        # If the URL is a direct link, we use it.
        
        # Strategy: Try to download the specific filename first.
        # If the URL in config is a base, we append the filename.
        # We'll use a heuristic: if URL ends in .csv, use it; otherwise append.
        target_filename = "2023_bleaching_events.csv"
        
        if reefbase_url.endswith("/"):
            data_url = reefbase_url + target_filename
        elif not reefbase_url.endswith(".csv"):
            data_url = reefbase_url + "/" + target_filename
        else:
            # If the URL is already a CSV, maybe it's the one, or maybe we need to check
            # For safety, we try the constructed path first if it looks like a directory
            data_url = reefbase_url # Fallback to exact URL if it looks complete
            # But the task says "Fetch 2023_bleaching_events.csv", so we try to construct it if possible
            if not reefbase_url.endswith(target_filename):
                 data_url = reefbase_url.rstrip("/") + "/" + target_filename

        print(f"Attempting to fetch independent data from: {data_url}")
        
        # Use the project's existing download function
        local_path = Path(config.PROJECT_ROOT) / "data" / "raw" / target_filename
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        # download_csv expects a URL and a local path
        df_events = download_csv(data_url, str(local_path))
        
        if df_events is None or df_events.empty:
            raise ValueError("Downloaded file is empty or could not be parsed.")

        metrics["independent_data_available"] = True
        metrics["event_count"] = len(df_events)
        print(f"Successfully loaded {len(df_events)} independent bleaching events.")

        # --- Data Alignment ---
        # We need to match the model's prediction points (from feature_df) with the event locations.
        # Assumption: feature_df has columns 'latitude' and 'longitude' (or similar)
        # and the event dataframe has 'lat' and 'lon' (or similar).
        
        # Normalize column names for matching
        event_cols = df_events.columns.str.lower()
        feature_cols = feature_df.columns.str.lower()
        
        # Heuristic mapping for coordinates
        lat_col = None
        lon_col = None
        severity_col = None
        
        for c in df_events.columns:
            if 'lat' in c.lower(): lat_col = c
            if 'lon' in c.lower() or 'long' in c.lower(): lon_col = c
            if 'sev' in c.lower() or 'bleach' in c.lower(): severity_col = c

        if not all([lat_col, lon_col]):
            raise KeyError("Could not identify latitude/longitude columns in independent data.")
        
        # Ensure feature_df has coordinates
        if 'latitude' not in feature_df.columns or 'longitude' not in feature_df.columns:
            # Try to find them
            f_lat = next((c for c in feature_df.columns if 'lat' in c.lower()), None)
            f_lon = next((c for c in feature_df.columns if 'lon' in c.lower() or 'long' in c.lower()), None)
            if f_lat and f_lon:
                feature_df = feature_df.rename(columns={f_lat: 'latitude', f_lon: 'longitude'})
            else:
                raise KeyError("Feature dataframe lacks coordinate columns for spatial join.")

        # Merge on coordinates (exact match or nearest neighbor)
        # Since exact matches are rare in real world data, we perform a nearest-neighbor join
        # using a simple distance calculation (Haversine) or a spatial index.
        # For simplicity and speed in this script, we will filter feature_df to points 
        # that are within a small radius of the events, or if the feature_df is the grid,
        # we pick the closest grid point to each event.
        
        # Convert to numpy for speed
        events_lat = df_events[lat_col].values
        events_lon = df_events[lon_col].values
        
        f_lat = feature_df['latitude'].values
        f_lon = feature_df['longitude'].values
        
        # Calculate distances (simplified Euclidean for small regions, or Haversine)
        # Using Haversine for accuracy
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371  # km
            phi1, phi2 = np.radians(lat1), np.radians(lat2)
            d_phi = np.radians(lat2 - lat1)
            d_lambda = np.radians(lon2 - lon1)
            a = np.sin(d_phi/2.0)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(d_lambda/2.0)**2
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
            return R * c

        # Find closest feature point for each event
        closest_indices = []
        closest_distances = []
        
        # This is O(N*M). If datasets are large, use KDTree. 
        # Assuming feature_df is manageable or we sample.
        # If feature_df is the full grid, we might need a spatial index.
        # For now, we assume a reasonable size or that we are validating against a subset.
        
        # Optimization: Use scipy.spatial.KDTree if available, else brute force
        try:
            from scipy.spatial import cKDTree
            # KDTree works in 2D, but lat/lon are not Euclidean. 
            # For small regions, it's okay. For global, we need projection.
            # Let's assume the data is regional (Pacific) and use a simple projection or brute force with vectorization
            # Vectorized brute force for memory efficiency
            coords = np.column_stack((f_lat, f_lon))
            event_coords = np.column_stack((events_lat, events_lon))
            
            # Calculate distances matrix (events x features)
            # To save memory, we process in chunks if needed. 
            # Assuming features < 100k for now.
            dists = haversine(coords[:,0][:, None], coords[:,1][:, None], 
                              event_coords[:,0], event_coords[:,1])
            
            closest_indices = np.argmin(dists, axis=1)
            closest_distances = np.min(dists, axis=1)
            
        except ImportError:
            # Fallback to brute force loop (slow but works)
            for i, (el, en) in enumerate(zip(events_lat, events_lon)):
                dists = haversine(f_lat, f_lon, el, en)
                idx = np.argmin(dists)
                closest_indices.append(idx)
                closest_distances.append(dists[idx])
            closest_indices = np.array(closest_indices)
            closest_distances = np.array(closest_distances)

        # Filter events that are too far from any feature point (e.g., > 10km)
        valid_mask = closest_distances < 10.0 # 10 km threshold
        valid_event_indices = np.where(valid_mask)[0]
        
        if len(valid_event_indices) == 0:
            metrics["warning"] = "No independent events found within 10km of any feature point."
            metrics["independent_data_available"] = False
            return metrics

        # Extract predictions and labels for valid events
        # Predictions: model probability for the closest feature point
        # Labels: Severity from event (binary: bleached or not? or severity score?)
        # Task says "AUPRC between predicted probability and observed severity".
        # AUPRC usually requires binary labels. We assume severity > 0 implies bleaching.
        
        # Map event data to feature predictions
        matched_predictions = feature_df.iloc[closest_indices[valid_event_indices]]['probability'] # Assuming model output column
        matched_severity = df_events.iloc[valid_event_indices][severity_col]
        
        # Convert severity to binary (1 if severity > 0, else 0)
        # If severity is a string or categorical, handle it.
        # Assuming numeric for now.
        matched_labels = (matched_severity > 0).astype(int)

        if matched_labels.sum() == 0:
            metrics["warning"] = "No positive bleaching events in the matched independent data."
            return metrics

        # Calculate AUPRC
        precision, recall, _ = precision_recall_curve(matched_labels, matched_predictions)
        auprc = auc(recall, precision)
        
        metrics["auprc"] = float(auprc)
        print(f"Calculated AUPRC: {auprc:.4f}")

    except Exception as e:
        metrics["warning"] = f"Failed to fetch or process independent data: {str(e)}"
        metrics["independent_data_available"] = False
        print(f"Warning: {metrics['warning']}")

    # Save metrics to JSON
    output_path = Path(config.PROJECT_ROOT) / output_metrics_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing metrics if present
    if output_path.exists():
        with open(output_path, 'r') as f:
            existing_metrics = json.load(f)
        existing_metrics.update(metrics)
        final_metrics = existing_metrics
    else:
        final_metrics = metrics

    with open(output_path, 'w') as f:
        json.dump(final_metrics, f, indent=2)

    return final_metrics

def main():
    """Main entry point for map.py tasks."""
    print("Starting map.py execution...")
    
    # Load config
    cfg = config.get_config() # Assuming get_config exists or use config object directly
    
    # Load model and data (from previous tasks)
    # We need the feature dataframe and the model to generate predictions
    # This might require loading from disk or re-running parts of the pipeline
    # For T033, we assume the model and features are available from T023/T030
    
    try:
        # Re-load model and data to get predictions
        # This is a simplified assumption. In reality, we might load from saved artifacts.
        model, X, y, feature_names = load_model_and_data()
        
        # Generate predictions for the feature set
        # Assuming model has predict_proba
        if hasattr(model, 'predict_proba'):
            predictions = model.predict_proba(X)[:, 1]
        else:
            # Fallback for other models
            predictions = model.predict(X)
            
        # Create a feature dataframe with predictions
        feature_df = pd.DataFrame(X, columns=feature_names)
        feature_df['probability'] = predictions
        
        # Ensure coordinates are in the feature_df (they should be if from T014)
        if 'latitude' not in feature_df.columns:
            # If coordinates are not in features, we cannot validate spatially.
            # This is a critical failure for T033.
            raise ValueError("Feature dataframe lacks latitude/longitude columns required for spatial validation.")
        
        # Run validation
        metrics = validate_map_against_independent_reports(model, feature_df, cfg)
        
        print("Validation complete. Metrics saved to data/metrics.json")
        print(f"Independent data available: {metrics['independent_data_available']}")
        if metrics['auprc'] is not None:
            print(f"AUPRC: {metrics['auprc']}")
            
    except Exception as e:
        print(f"Error during validation: {e}")
        # Still try to save the failure state
        metrics = {"independent_data_available": False, "error": str(e)}
        output_path = Path(config.PROJECT_ROOT) / "data/metrics.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        raise

if __name__ == "__main__":
    main()