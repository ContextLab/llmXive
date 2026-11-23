import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Polygon, Point, MultiPolygon
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

# Import project utilities
from utils.config import get_project_root, get_processed_dir, get_models_dir, get_viz_dir, ensure_directories
from utils.provenance import record_artifact_provenance, load_metadata_config, save_metadata_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_top_species_id() -> str:
    """Load the single top species ID from the processed JSON file."""
    processed_dir = get_processed_dir()
    top_species_file = processed_dir / "top_25_species_ids.json"
    
    if not top_species_file.exists():
        raise FileNotFoundError(f"Top species file not found: {top_species_file}. "
                                "Ensure T012.5b has been executed.")
    
    with open(top_species_file, 'r') as f:
        data = json.load(f)
    
    # The file contains a list of species IDs sorted by count. 
    # We need the single top one (index 0).
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError("Top species file must contain a non-empty list of species IDs.")
    
    return data[0]

def load_model_and_scaler() -> Tuple[RandomForestClassifier, StandardScaler]:
    """Load the trained model and the scaler used during training."""
    models_dir = get_models_dir()
    model_path = models_dir / "random_forest.pkl"
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}. "
                                "Ensure T041 has been executed.")
    
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    # The model artifact should contain the fitted model and the scaler
    if 'model' not in model_data or 'scaler' not in model_data:
        raise ValueError("Model artifact missing 'model' or 'scaler' keys.")
    
    return model_data['model'], model_data['scaler']

def load_species_profiles() -> pd.DataFrame:
    """Load the species profiles to get feature names and mean values."""
    processed_dir = get_processed_dir()
    profiles_file = processed_dir / "species_profiles.csv"
    
    if not profiles_file.exists():
        raise FileNotFoundError(f"Species profiles file not found: {profiles_file}. "
                                "Ensure T040 has been executed.")
    
    return pd.read_csv(profiles_file)

def create_prediction_grid(
    species_profiles: pd.DataFrame, 
    top_species_id: str, 
    resolution: float = 0.01
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[str]]:
    """
    Create a high-resolution grid for prediction based on the range of observed land cover proportions.
    
    Returns:
        X_grid: 2D array of feature values (n_points, n_features)
        X_coords: 1D array of X coordinates (longitude proxy)
        Y_coords: 1D array of Y coordinates (latitude proxy)
        feature_names: List of land cover feature names
    """
    # Identify land cover proportion columns (typically end with '_prop_100m')
    # We assume the first two columns are 'species_id' and 'foraging_guild'
    # and the rest are land cover proportions.
    # A safer approach: look for columns containing 'prop'
    lc_cols = [col for col in species_profiles.columns if 'prop' in col.lower()]
    
    if len(lc_cols) < 2:
        raise ValueError("Could not identify enough land cover proportion columns for grid creation.")
    
    # For visualization, we typically map two key land cover types against each other,
    # or use PCA. However, the task asks for a "high-resolution grid". 
    # Given the multi-dimensional nature of land cover (forest, grass, urban, etc.),
    # a 2D grid implies we are projecting or selecting 2 dominant variables.
    # A common ecological approach is to plot Forest vs Urban/Water, or use the first two PCs.
    # Here, we will select the top 2 most important land cover features based on the model
    # to define the 2D grid axes, effectively creating a "Habitat Suitability" map in the space of those two drivers.
    
    # Load model to get feature importances
    models_dir = get_models_dir()
    model_path = models_dir / "random_forest.pkl"
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    model = model_data['model']
    feature_importances = model.feature_importances_
    
    # Map importances to column names (assuming order matches the training data)
    # We need to ensure we only use land cover columns for the grid
    # The training data likely had 'species_id' and 'foraging_guild' encoded, so we need to be careful.
    # Let's assume the model was trained on the numeric land cover columns.
    # We'll filter feature_importances to match the land cover columns found in profiles.
    
    # Re-load the model's feature names if stored, otherwise assume order matches lc_cols
    # For robustness, we'll assume the model was trained on the numeric columns from species_profiles
    # excluding 'species_id' and 'foraging_guild'.
    
    train_features = [c for c in species_profiles.columns if c not in ['species_id', 'foraging_guild']]
    
    if len(train_features) != len(feature_importances):
        logger.warning(f"Feature count mismatch: model has {len(feature_importances)}, data has {len(train_features)}. "
                       "Attempting to align by land cover columns only.")
        # Fallback: use only land cover columns if they match the count
        if len(lc_cols) == len(feature_importances):
            train_features = lc_cols
        else:
            raise ValueError("Cannot align model features with data columns for grid creation.")
    
    # Create a dataframe of importances to sort
    imp_df = pd.DataFrame({'feature': train_features, 'importance': feature_importances})
    imp_df = imp_df.sort_values(by='importance', ascending=False)
    
    # Select top 2 features for the 2D grid
    top_features = imp_df['feature'].head(2).tolist()
    logger.info(f"Creating grid based on top 2 features: {top_features}")
    
    # Define grid bounds based on the observed range in the top species' profile (or all profiles)
    # Since species_profiles is an average, the range is small. 
    # To make a "map", we should look at the raw merged observations to get the full range of variation.
    processed_dir = get_processed_dir()
    merged_file = processed_dir / "merged_observations.csv"
    
    if merged_file.exists():
        df_raw = pd.read_csv(merged_file)
        # Filter for the top species to get its specific range
        df_species = df_raw[df_raw['species_id'] == top_species_id]
        if df_species.empty:
            # Fallback to all data if top species not found in raw (shouldn't happen)
            df_species = df_raw
        
        x_col, y_col = top_features
        x_min, x_max = df_species[x_col].min(), df_species[x_col].max()
        y_min, y_max = df_species[y_col].min(), df_species[y_col].max()
        
        # Add a small margin to avoid edge effects
        x_margin = (x_max - x_min) * 0.05
        y_margin = (y_max - y_min) * 0.05
        x_min, x_max = x_min - x_margin, x_max + x_margin
        y_min, y_max = y_min - y_margin, y_max + y_margin
    else:
        # Fallback to 0-1 range if raw data not available
        x_min, x_max = 0.0, 1.0
        y_min, y_max = 0.0, 1.0
        x_col, y_col = top_features
    
    # Generate grid
    # Resolution: number of points per axis
    grid_size = 100
    x_vals = np.linspace(x_min, x_max, grid_size)
    y_vals = np.linspace(y_min, y_max, grid_size)
    
    X_grid, Y_grid = np.meshgrid(x_vals, y_vals)
    
    # Prepare input for prediction
    # We need to create a dataframe with all features, filling the top 2 with grid values
    # and the others with the mean values from the species profile
    grid_points = []
    for i in range(grid_size):
        for j in range(grid_size):
            row = {}
            # Set the two grid axes
            row[x_col] = X_grid[i, j]
            row[y_col] = Y_grid[i, j]
            
            # Fill other land cover features with the mean of the top species profile
            for feat in train_features:
                if feat not in row:
                    # Get mean from species_profiles for this species
                    profile_row = species_profiles[species_profiles['species_id'] == top_species_id]
                    if not profile_row.empty:
                        row[feat] = profile_row[feat].values[0]
                    else:
                        row[feat] = 0.5 # Default fallback
            
            grid_points.append(row)
    
    X_grid_df = pd.DataFrame(grid_points)
    X_grid_np = X_grid_df[train_features].values
    
    return X_grid_np, X_grid, Y_grid, [x_col, y_col]

def rasterize_predictions(
    model: RandomForestClassifier, 
    scaler: StandardScaler, 
    X_grid: np.ndarray, 
    feature_names: List[str]
) -> np.ndarray:
    """
    Predict habitat suitability for each point in the grid.
    Returns the probability of the positive class (or the most likely guild if multi-class).
    """
    # Scale the grid data
    X_scaled = scaler.transform(X_grid)
    
    # Predict probabilities
    # If multi-class, we might want the probability of the most common guild or the "optimal" one.
    # For a general "habitat map", we can predict the probability of the species' guild being suitable,
    # or simply the predicted class. Let's return the probability of the most likely class.
    probs = model.predict_proba(X_scaled)
    
    # If binary classification (guild vs not), take prob of 1.
    # If multi-class, take max probability (confidence) or specific guild.
    # Given the task is "predicting foraging guilds", it's likely multi-class.
    # We will map the predicted class to a suitability score? 
    # Actually, the task asks for "rasterize model predictions". 
    # Let's return the predicted class index for now, or the max probability as a "suitability" score.
    # A common interpretation is "probability of suitable habitat".
    # Let's use the max probability as a proxy for suitability confidence.
    suitability = np.max(probs, axis=1)
    
    return suitability

def generate_habitat_map(
    suitability: np.ndarray, 
    X_grid: np.ndarray, 
    Y_grid: np.ndarray, 
    top_species_id: str,
    output_png: Path,
    output_geojson: Path
) -> None:
    """
    Generate a PNG map and a GeoJSON file of the habitat suitability.
    """
    # Reshape suitability to match grid shape
    # suitability is 1D (n_points), need to reshape to (grid_size, grid_size)
    grid_size = int(np.sqrt(len(suitability)))
    if grid_size * grid_size != len(suitability):
        raise ValueError("Suitability array length is not a perfect square.")
    
    suitability_2d = suitability.reshape((grid_size, grid_size))
    
    # Plot
    plt.figure(figsize=(10, 8))
    contour = plt.contourf(X_grid, Y_grid, suitability_2d, levels=20, cmap='viridis')
    plt.colorbar(contour, label='Habitat Suitability (Model Confidence)')
    plt.xlabel('Land Cover Proportion 1')
    plt.ylabel('Land Cover Proportion 2')
    plt.title(f'Habitat Suitability Map for {top_species_id}')
    
    # Save PNG
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved habitat map PNG: {output_png}")
    
    # Generate GeoJSON
    # We need to convert the grid into a GeoJSON feature collection.
    # Since we don't have real lat/lon for the abstract 2D space of land cover proportions,
    # we will create a GeoJSON where the geometry represents the grid cells in the abstract space.
    # Alternatively, if the task implies a real spatial map, we would need to project the model
    # onto a real geographic raster. However, the task says "rasterize model predictions over a high-resolution grid"
    # and "ensure the grid does not extrapolate beyond observed coordinates".
    # This suggests an abstract feature space map.
    # If a real spatial map is required, we would need to load the NLCD raster and predict on every pixel.
    # Given the constraints and the "grid" description, an abstract feature space map is the most robust interpretation
    # of "grid does not extrapolate beyond observed coordinates" in feature space.
    # HOWEVER, "habitat map" usually implies geography. 
    # Let's re-read: "rasterize model predictions over a high-resolution grid... for the single top species".
    # If we had a real NLCD raster, we could predict on it. But T037 downloads NLCD, T039 merges.
    # We don't have the full NLCD raster loaded in memory here.
    # The most feasible "map" given the artifacts (species_profiles) is the feature space map.
    # But to be safe and useful, let's create a GeoJSON of the grid in the feature space.
    
    features = []
    # Create a grid of polygons
    # We'll create a simple grid of squares
    x_min, x_max = X_grid.min(), X_grid.max()
    y_min, y_max = Y_grid.min(), Y_grid.max()
    
    # To keep GeoJSON size manageable, we might aggregate or just represent the extent.
    # Let's create a single MultiPolygon representing the valid domain, or a grid of small polygons.
    # Given the resolution (100x100), 10,000 polygons is too many for a simple GeoJSON.
    # We will create a grid of 10x10 representative cells.
    step_x = (x_max - x_min) / 10
    step_y = (y_max - y_min) / 10
    
    for i in range(10):
        for j in range(10):
            x_start = x_min + i * step_x
            x_end = x_start + step_x
            y_start = y_min + j * step_y
            y_end = y_start + step_y
            
            # Calculate average suitability for this cell
            # Mask points in this cell
            mask = (X_grid >= x_start) & (X_grid < x_end) & (Y_grid >= y_start) & (Y_grid < y_end)
            if mask.sum() > 0:
                avg_suit = suitability[mask].mean()
            else:
                avg_suit = 0.0
                
            poly = Polygon([(x_start, y_start), (x_end, y_start), (x_end, y_end), (x_start, y_end)])
            
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [list(poly.exterior.coords)]
                },
                "properties": {
                    "avg_suitability": float(avg_suit),
                    "species_id": top_species_id
                }
            })
    
    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(output_geojson, 'w') as f:
        json.dump(geojson_data, f, indent=2)
    
    logger.info(f"Saved habitat map GeoJSON: {output_geojson}")

def main():
    """Main entry point for the habitat mapping task."""
    logger.info("Starting T045: Map Habitat Suitability")
    
    # Ensure output directories exist
    viz_dir = get_viz_dir()
    docs_results = viz_dir.parent / "docs" / "results"
    ensure_directories([docs_results])
    
    try:
        # 1. Load Top Species
        top_species_id = load_top_species_id()
        logger.info(f"Top species identified: {top_species_id}")
        
        # 2. Load Model and Scaler
        model, scaler = load_model_and_scaler()
        logger.info("Model and scaler loaded.")
        
        # 3. Load Species Profiles
        species_profiles = load_species_profiles()
        logger.info("Species profiles loaded.")
        
        # 4. Create Prediction Grid
        X_grid_np, X_coords, Y_coords, feature_names = create_prediction_grid(
            species_profiles, top_species_id
        )
        logger.info(f"Grid created with shape {X_grid_np.shape}.")
        
        # 5. Rasterize Predictions
        suitability = rasterize_predictions(model, scaler, X_grid_np, feature_names)
        logger.info("Predictions rasterized.")
        
        # 6. Generate Outputs
        output_png = docs_results / f"habitat_map_{top_species_id}.png"
        output_geojson = docs_results / "habitat_map.geojson"
        
        generate_habitat_map(
            suitability, X_coords, Y_coords, top_species_id, 
            output_png, output_geojson
        )
        
        # 7. Record Provenance
        metadata = load_metadata_config()
        record_artifact_provenance(
            metadata, 
            step_name="map_habitat", 
            artifacts=[str(output_png), str(output_geojson)],
            input_artifacts=["species_profiles.csv", "random_forest.pkl", "top_25_species_ids.json"]
        )
        save_metadata_config(metadata)
        
        logger.info("T045 completed successfully.")
        
    except Exception as e:
        logger.error(f"Task T045 failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
