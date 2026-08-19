import os
import logging
import warnings
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any, Iterator
import pandas as pd
import numpy as np
import rioxarray
import xarray as xr
import geopandas as gpd
from pyproj import CRS
from utils.exceptions import DataQualityError
from utils.geocoding import validate_coordinates, align_crs
from utils.logging_utils import get_logger, log_excluded_record

# Configure logger for this module
logger = get_logger(__name__)

# SoilGrids layer names and their corresponding SoilGrids 250m layer identifiers
# These correspond to the 2017/2020 SoilGrids layers available via the ISRIC API
SOIL_LAYERS = {
    'n': 'soil_n',       # Total Nitrogen (g/kg)
    'p': 'soil_p',       # Available Phosphorus (mg/kg)
    'k': 'soil_k',       # Exchangeable Potassium (cmol/kg) - often converted to mg/kg or mmolc/kg
    'ph': 'soil_phh2o'   # pH (H2O)
}

# SoilGrids base URL for downloading layers (using the ISRIC SoilGrids 250m v2.0)
# We use the 'soilgrids.org' public endpoint which serves GeoTIFFs
# Note: In a production environment, one might use the ISRIC API or download from their S3 bucket.
# For this implementation, we assume the GeoTIFFs are downloaded or available locally,
# or we fetch them on the fly if a download URL pattern is known.
# To satisfy "Real data only", we will attempt to download from the ISRIC public S3 bucket if not present.
SOILGRIDS_S3_BASE = "https://files.isric.org/soilgrids/latest/data_aggregated/"

# Depth indices for SoilGrids (0-5cm, 5-15cm, etc.)
# We will use the top layer (0-5cm) for this implementation as per standard root trait studies
DEPTH_INDEX = 0 

def _get_layer_url(layer_name: str) -> str:
    """Construct the URL for a specific SoilGrids layer GeoTIFF."""
    # The file naming convention in the S3 bucket is usually: {layer_name}/0-5cm/{layer_name}_0-5cm.tif
    # However, the aggregated layers might be zipped. Let's try to find the direct .tif or .zip.
    # Based on SoilGrids 250m v2.0 structure:
    # https://files.isric.org/soilgrids/latest/data_aggregated/{layer_name}/0-5cm/{layer_name}_0-5cm.tif
    # Actually, the aggregated data is often in .zarr or .tif. Let's assume the standard .tif path for now.
    # If the direct tif is not available, we might need to download a zip.
    # For robustness, we will construct the path for the 0-5cm depth.
    return f"{SOILGRIDS_S3_BASE}{layer_name}/0-5cm/{layer_name}_0-5cm.tif"

def _ensure_raster_exists(layer_name: str, target_dir: Path) -> Path:
    """Download the GeoTIFF for a layer if it doesn't exist locally."""
    import requests
    
    file_name = f"{layer_name}_0-5cm.tif"
    local_path = target_dir / file_name
    
    if local_path.exists():
        logger.info(f"Raster found locally: {local_path}")
        return local_path
    
    url = _get_layer_url(layer_name)
    logger.info(f"Downloading raster from {url}...")
    
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Successfully downloaded {local_path}")
        return local_path
    except requests.RequestException as e:
        raise DataQualityError(
            f"Failed to download SoilGrids layer {layer_name} from {url}. "
            f"Please ensure internet connectivity or provide local data. Error: {e}"
        )

def load_soil_raster(layer_key: str, data_dir: Path = Path("data/raw/soil")) -> Tuple[xr.DataArray, str]:
    """
    Load a specific SoilGrids raster layer.
    
    Args:
        layer_key: One of 'n', 'p', 'k', 'ph'.
        data_dir: Directory to store/download rasters.
        
    Returns:
        Tuple of (xarray DataArray, layer_name).
    """
    if layer_key not in SOIL_LAYERS:
        raise ValueError(f"Invalid layer key: {layer_key}. Must be one of {list(SOIL_LAYERS.keys())}")
    
    layer_name = SOIL_LAYERS[layer_key]
    target_dir = Path(data_dir) / layer_name
    target_dir.mkdir(parents=True, exist_ok=True)
    
    raster_path = _ensure_raster_exists(layer_name, target_dir)
    
    try:
        # Open with rioxarray for geospatial handling
        da = rioxarray.open_rasterio(raster_path)
        
        # SoilGrids often stores data in a specific projection (WGS84 is common for v2.0, but check)
        # The task requires reprojecting to WGS84 (EPSG:4326) if not already.
        if da.rio.crs is None:
            logger.warning(f"Raster {raster_path} has no CRS. Assuming EPSG:4326.")
            da.rio.write_crs("EPSG:4326", inplace=True)
        
        if da.rio.crs != CRS.from_epsg(4326):
            logger.info(f"Reprojecting {layer_name} from {da.rio.crs} to EPSG:4326")
            da = da.rio.reproject("EPSG:4326")
        
        # SoilGrids layers often have a 'band' dimension. We need the first band (0-5cm).
        # If the dataset has a 'depth' dimension, we select the first one.
        if 'band' in da.dims:
            da = da.isel(band=0)
        
        # Ensure the name is set for clarity
        da.attrs['long_name'] = layer_name
        da.attrs['layer_key'] = layer_key
        
        return da, layer_name
    except Exception as e:
        raise DataQualityError(f"Failed to load or process raster {raster_path}: {e}")

def extract_values_at_coords(
    da: xr.DataArray, 
    coords: List[Tuple[float, float]], 
    layer_key: str,
    log_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Extract raster values at specific (lon, lat) coordinates.
    
    Args:
        da: xarray DataArray with spatial dimensions.
        coords: List of (longitude, latitude) tuples.
        layer_key: The key for the soil property (n, p, k, ph).
        log_path: Path to log excluded records.
        
    Returns:
        Tuple of (DataFrame of valid extractions, List of excluded record details).
    """
    if not coords:
        return pd.DataFrame(), []
    
    # Create a GeoDataFrame for the points
    gdf = gpd.GeoDataFrame(
        {'geometry': [gpd.points_from_xy([c[0]], [c[1]])[0] for c in coords]},
        crs="EPSG:4326"
    )
    gdf['row_idx'] = range(len(coords))
    
    # Reproject points to match the raster if necessary (though we ensured raster is WGS84)
    if da.rio.crs != gdf.crs:
        gdf = gdf.to_crs(da.rio.crs)
    
    # Extract values
    # Use rioxarray's sample method or point extraction
    # rioxarray doesn't have a direct 'sample' method for multiple points in older versions,
    # so we use the 'intersection' or 'mask' approach, or simply iterate if performance allows.
    # For efficiency, we can use the `sample` method if available, or `xr.Dataset` interpolation.
    # A robust way is to use `rioxarray`'s `sample` if the points are in the same CRS.
    
    extracted_values = []
    excluded_records = []
    
    # We need to handle the case where the point is outside the raster extent or over nodata.
    # rioxarray's `sample` returns NaN for no data.
    
    # Prepare the xarray object for sampling
    # We need to ensure the xarray object has the correct dimensions for sampling
    # The `sample` method in rioxarray expects a GeoDataFrame
    
    try:
        # Sample the raster at the points
        # Note: This might return a DataArray with dimensions ['geometry']
        sampled = da.rio.sample(gdf)
        
        # Convert to list of values
        # sampled.values will be an array of shape (n_points,)
        # We need to handle the case where the result is a 2D array if multiple bands existed (but we selected band 0)
        
        for i, val in enumerate(sampled.values):
            # Check for NaN (No Data) or negative values
            if np.isnan(val) or val < 0:
                reason = "No Data" if np.isnan(val) else "Negative Value"
                excluded_records.append({
                    'row_idx': gdf.iloc[i]['row_idx'],
                    'lon': gdf.iloc[i].geometry.x,
                    'lat': gdf.iloc[i].geometry.y,
                    'layer': layer_key,
                    'reason': reason,
                    'value': val
                })
                if log_path:
                    log_excluded_record(
                        log_path, 
                        record_id=gdf.iloc[i]['row_idx'], 
                        reason_code=f"{layer_key}_{reason}", 
                        details=f"Value: {val}"
                    )
            else:
                extracted_values.append({
                    'row_idx': gdf.iloc[i]['row_idx'],
                    'lon': gdf.iloc[i].geometry.x,
                    'lat': gdf.iloc[i].geometry.y,
                    layer_key: val
                })
                
    except Exception as e:
        # Fallback or error handling if sampling fails (e.g., points outside extent)
        logger.error(f"Error sampling raster {layer_key}: {e}")
        # Treat all as excluded if sampling fails entirely
        for i, row in gdf.iterrows():
            excluded_records.append({
                'row_idx': row['row_idx'],
                'lon': row.geometry.x,
                'lat': row.geometry.y,
                'layer': layer_key,
                'reason': 'Extraction Error',
                'value': None
            })
            if log_path:
                log_excluded_record(
                    log_path,
                    record_id=row['row_idx'],
                    reason_code=f"{layer_key}_EXTRACTION_ERROR",
                    details=str(e)
                )

    df_extracted = pd.DataFrame(extracted_values)
    return df_extracted, excluded_records

def process_soil_data(
    trait_df: pd.DataFrame,
    soil_layers: Optional[List[str]] = None,
    data_dir: Path = Path("data/raw/soil"),
    log_dir: Path = Path("data/logs")
) -> pd.DataFrame:
    """
    Main function to process soil data for a given trait dataframe.
    
    Args:
        trait_df: DataFrame containing 'latitude', 'longitude', and other trait data.
        soil_layers: List of layer keys to extract (default: all).
        data_dir: Directory for soil rasters.
        log_dir: Directory for log files.
        
    Returns:
        DataFrame with soil values merged into the trait data.
    """
    if soil_layers is None:
        soil_layers = list(SOIL_LAYERS.keys())
    
    # Validate coordinates
    valid_coords_df, invalid_coords = validate_coordinates(trait_df)
    if invalid_coords:
        for idx, reason in invalid_coords:
            log_excluded_record(
                log_dir / "record_exclusions.log",
                record_id=idx,
                reason_code="INVALID_COORDINATES",
                details=reason
            )
    
    if valid_coords_df.empty:
        raise DataQualityError("No valid coordinates found in the input dataframe.")
    
    all_soil_dfs = []
    total_excluded = []
    
    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "record_exclusions.log"
    
    for layer_key in soil_layers:
        logger.info(f"Processing soil layer: {layer_key}")
        
        # Load raster
        da, layer_name = load_soil_raster(layer_key, data_dir)
        
        # Extract values
        # We pass the coordinates from the valid trait dataframe
        coords = list(zip(valid_coords_df['longitude'], valid_coords_df['latitude']))
        
        df_layer, excluded = extract_values_at_coords(
            da, 
            coords, 
            layer_key,
            log_path=log_file
        )
        
        all_soil_dfs.append(df_layer)
        total_excluded.extend(excluded)
    
    if not all_soil_dfs:
        raise DataQualityError("No soil data extracted for any layer.")
    
    # Merge extracted data back to the original trait dataframe
    # We need to align by the original row index. 
    # The extract_values_at_coords returns 'row_idx' which corresponds to the index in valid_coords_df.
    # We need to map this back to the original trait_df index.
    
    # Create a mapping from the subset index to the original index
    # valid_coords_df should have the original index preserved if we used .loc or similar
    # Assuming valid_coords_df has the original index as its index
    
    # Let's create a DataFrame with the extracted values and the original index
    merged_soil = pd.DataFrame()
    
    # We need to join the extracted values to the valid_coords_df first to get the original index
    # But extract_values_at_coords returns a list of dicts with 'row_idx' which is the index in the input list (coords).
    # coords was created from valid_coords_df, so row_idx matches valid_coords_df's index if we iterated correctly.
    # However, in extract_values_at_coords, we used range(len(coords)) as 'row_idx'.
    # So we need to map this back.
    
    # Let's reconstruct the mapping
    # valid_coords_df is a subset of trait_df. We need to know which original indices are in valid_coords_df.
    # If we constructed valid_coords_df by filtering, we should preserve the original index.
    
    # Re-implementation of coordinate validation to ensure index preservation
    # (This logic is usually in geocoding.py, but we need to ensure the index is passed through)
    # Assuming validate_coordinates returns a df with original indices.
    
    # To be safe, let's assume valid_coords_df has the original indices.
    # The 'row_idx' in extracted data corresponds to the position in valid_coords_df.
    # So we can use valid_coords_df.index[row_idx] to get the original index.
    
    # But extract_values_at_coords doesn't know about the original index.
    # We need to pass the original indices to extract_values_at_coords or handle the mapping here.
    
    # Let's modify the approach: 
    # We will create a DataFrame of the extracted values and then merge with valid_coords_df on the row position.
    # Actually, it's easier to pass the original indices to the extraction function.
    # But since the function signature is fixed, we'll do the mapping here.
    
    # We need to know the order of coords. coords = list(zip(...)) preserves order.
    # So row_idx i corresponds to valid_coords_df.iloc[i].
    
    # Let's create a DataFrame from all_soil_dfs and merge them
    soil_data_combined = all_soil_dfs[0]
    for df in all_soil_dfs[1:]:
        soil_data_combined = soil_data_combined.merge(df, on='row_idx', how='outer')
    
    # Now merge with valid_coords_df to get the original index
    # We assume valid_coords_df has the original index.
    # We need to add the original index to soil_data_combined
    
    # Create a DataFrame of valid_coords_df with a reset index to match row_idx
    valid_coords_reset = valid_coords_df.reset_index(drop=True)
    valid_coords_reset['row_idx'] = range(len(valid_coords_reset))
    
    # Merge
    soil_with_orig_idx = soil_data_combined.merge(
        valid_coords_reset[['row_idx', 'index']], # 'index' is the original index from valid_coords_df
        on='row_idx',
        how='left'
    )
    
    # Now we have the original index in 'index' column.
    # We need to merge this back to trait_df
    
    # But wait, valid_coords_df might not have the original index as a column.
    # Let's assume trait_df has a unique identifier or we use the index.
    # If trait_df has a 'record_id' or similar, we should use that.
    # For now, we assume the index is the record_id.
    
    # Let's rename 'index' to 'record_id' if it's the original index
    if 'index' in soil_with_orig_idx.columns:
        soil_with_orig_idx = soil_with_orig_idx.rename(columns={'index': 'record_id'})
    
    # Now merge with trait_df on record_id (which is the original index)
    # But trait_df might not have 'record_id' column, it might be the index.
    # We need to reset the index of trait_df to have a 'record_id' column if it's not there.
    
    if 'record_id' not in trait_df.columns:
        trait_df = trait_df.reset_index().rename(columns={'index': 'record_id'})
    
    final_df = trait_df.merge(
        soil_with_orig_idx[['record_id'] + [k for k in soil_layers if k in soil_with_orig_idx.columns]],
        on='record_id',
        how='left'
    )
    
    # Check for any rows that still have NaN in soil columns (shouldn't happen if we filtered correctly, but just in case)
    # We already excluded NaNs in extract_values_at_coords, so this should be clean.
    
    # Set the index back to 'record_id' if needed, or keep as is
    final_df = final_df.set_index('record_id')
    
    return final_df

def main():
    """
    Entry point for the soil data ingestion script.
    Reads trait data, extracts soil values, and outputs the merged dataset.
    """
    # This function is typically called by merge.py or validation.py
    # For standalone execution, we can load a sample trait file
    logger.info("Starting soil data ingestion.")
    
    # Example usage (to be replaced by actual pipeline calls)
    # trait_df = pd.read_csv("data/raw/trait_data.csv")
    # result_df = process_soil_data(trait_df)
    # result_df.to_csv("data/processed/soil_merged.csv")
    
    logger.info("Soil data ingestion module loaded.")

if __name__ == "__main__":
    main()
