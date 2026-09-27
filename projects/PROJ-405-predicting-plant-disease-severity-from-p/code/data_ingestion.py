import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import json

# Import local utilities
from config import ensure_dirs, get_path, get_env_or_fail
from utils.logging_config import get_logger
from utils.feature_extraction import extract_lesion_area_ratio, extract_necrosis_color_index, extract_texture_entropy
from weather_linker import fetch_historical_weather, get_weather_for_record

# Initialize logger
logger = get_logger(__name__)

def get_image_paths(root_dir: str) -> List[Path]:
    """
    Recursively find all image files in the given root directory.
    """
    root_path = Path(root_dir)
    if not root_path.exists():
        raise FileNotFoundError(f"Root directory not found: {root_path}")
    
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    image_paths = []
    
    for ext in valid_extensions:
        image_paths.extend(root_path.rglob(f'*{ext}'))
        image_paths.extend(root_path.rglob(f'*{ext.upper()}'))
    
    return sorted(list(set(image_paths)))

def extract_metadata_from_path(image_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from image path.
    Expected format: .../PlantVillage/PlantVillage_Dataset/.../{Crop}_{Disease}/...
    Returns: dict with 'image_path', 'disease_label', 'location_lat', 'location_lon', 'image_date'
    """
    parts = image_path.parts
    metadata = {
        'image_path': str(image_path),
        'disease_label': None,
        'location_lat': None,
        'location_lon': None,
        'image_date': None
    }
    
    # Heuristic: Look for crop/disease in path
    # Assuming structure like: .../PlantVillage_Dataset/Crop_Disease/Image.jpg
    # Or standard PlantVillage: .../Apple___Apple_scab/...
    for i, part in enumerate(parts):
        if '___' in part:
            # Format: Crop___Disease
            metadata['disease_label'] = part
            break
        
        # Check for lat/lon in filename if present (e.g., 45.123_-122.456.jpg)
        if part.endswith('.jpg') or part.endswith('.png'):
            stem = part.rsplit('.', 1)[0]
            if '_' in stem and stem.count('_') >= 2:
                try:
                    # Try to parse lat_lon_date from filename
                    # Format: lat_lon.jpg or lat_lon_date.jpg
                    stem_parts = stem.split('_')
                    if len(stem_parts) >= 2:
                        lat_str = stem_parts[-2]
                        lon_str = stem_parts[-1]
                        # Remove date part if exists (last part might be date or lon)
                        # Simple heuristic: if last part is numeric, it's lon
                        if lon_str.replace('.', '').replace('-', '').isdigit():
                            metadata['location_lon'] = float(lon_str)
                            if lat_str.replace('.', '').replace('-', '').isdigit():
                                metadata['location_lat'] = float(lat_str)
                    elif len(stem_parts) >= 1:
                        # Fallback: try to parse just lat/lon from filename
                        if stem_parts[0].replace('.', '').replace('-', '').isdigit():
                            metadata['location_lat'] = float(stem_parts[0])
                        if len(stem_parts) > 1 and stem_parts[1].replace('.', '').replace('-', '').isdigit():
                            metadata['location_lon'] = float(stem_parts[1])
                except ValueError:
                    pass
    
    # If disease_label is still None, try to infer from parent directories
    if metadata['disease_label'] is None:
        parent = image_path.parent
        if parent.name and '___' in parent.name:
            metadata['disease_label'] = parent.name
        elif parent.parent.name and '___' in parent.parent.name:
            metadata['disease_label'] = parent.parent.name
    
    return metadata

def process_image_features(image_path: Path) -> Optional[Dict[str, float]]:
    """
    Extract visual features from a single image.
    Returns dict with 'lesion_area_ratio', 'necrosis_color_index', 'texture_entropy'
    or None if extraction fails.
    """
    try:
        lesion_ratio = extract_lesion_area_ratio(str(image_path))
        necrosis_index = extract_necrosis_color_index(str(image_path))
        texture_ent = extract_texture_entropy(str(image_path))
        
        return {
            'lesion_area_ratio': lesion_ratio,
            'necrosis_color_index': necrosis_index,
            'texture_entropy': texture_ent
        }
    except Exception as e:
        logger.warning(f"Failed to extract features from {image_path}: {e}")
        return None

def run_feature_extraction_pipeline(image_paths: List[Path], batch_size: int = 100) -> pd.DataFrame:
    """
    Run feature extraction on all images in batches to manage memory.
    """
    records = []
    
    for i, image_path in enumerate(image_paths):
        logger.info(f"Processing image {i+1}/{len(image_paths)}: {image_path.name}")
        
        # Extract metadata
        metadata = extract_metadata_from_path(image_path)
        
        # Extract visual features
        features = process_image_features(image_path)
        
        if features is None:
            logger.warning(f"Skipping {image_path} due to feature extraction failure")
            continue
        
        # Combine metadata and features
        record = {**metadata, **features}
        records.append(record)
        
        # Log progress
        if (i + 1) % batch_size == 0:
            logger.info(f"Processed {i+1} images")
    
    if not records:
        logger.error("No valid records extracted from images")
        return pd.DataFrame()
    
    return pd.DataFrame(records)

def filter_records_with_location(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out records that do not have valid location coordinates.
    """
    valid_mask = df['location_lat'].notna() & df['location_lon'].notna()
    filtered_df = df[valid_mask].copy()
    
    excluded_count = len(df) - len(filtered_df)
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} records with missing location metadata")
    
    return filtered_df

def merge_weather_and_features(df_features: pd.DataFrame, weather_cache: Optional[Dict] = None) -> pd.DataFrame:
    """
    Fetch weather data for each record and merge with image features.
    Uses a cache to avoid redundant API calls for the same location/date.
    """
    if df_features.empty:
        logger.warning("No features to merge with weather data")
        return df_features
    
    weather_records = []
    cache = weather_cache if weather_cache else {}
    
    for idx, row in df_features.iterrows():
        lat = row['location_lat']
        lon = row['location_lon']
        # Use image_date if available, otherwise use a default recent date
        # Since PlantVillage images often don't have precise dates, we might use a placeholder
        # For now, assume we need to fetch weather for the location regardless of date
        # In a real scenario, we'd parse the date from filename or metadata
        
        date_str = row.get('image_date')
        if date_str is None:
            # Use a default date (e.g., today or a representative date)
            # For PlantVillage, we might not have specific dates, so we fetch for the location
            # and use mean values or a representative period
            logger.info(f"No date for {row['image_path']}, fetching weather for location only")
            weather_data = get_weather_for_record(lat, lon, None, cache)
        else:
            weather_data = get_weather_for_record(lat, lon, date_str, cache)
        
        if weather_data is None:
            logger.warning(f"Failed to fetch weather for {row['image_path']} (lat={lat}, lon={lon})")
            # Exclude record if weather cannot be fetched (per T015)
            continue
        
        # Merge weather data into the record
        record = row.to_dict()
        record.update(weather_data)
        weather_records.append(record)
    
    if not weather_records:
        logger.error("No weather data successfully merged")
        return pd.DataFrame()
    
    return pd.DataFrame(weather_records)

def main():
    """
    Main entry point for the data ingestion pipeline.
    Orchestrates: Download -> Extract -> Link -> Merge
    """
    logger.info("Starting data ingestion pipeline (T016: Merge features and weather)")
    
    # Get paths
    data_root = get_path('data_raw')
    processed_dir = get_path('data_processed')
    ensure_dirs(processed_dir)
    
    output_path = processed_dir / 'unified_analysis.csv'
    
    # Get image paths
    logger.info(f"Scanning for images in {data_root}")
    try:
        image_paths = get_image_paths(data_root)
        logger.info(f"Found {len(image_paths)} images")
    except FileNotFoundError as e:
        logger.error(f"Data root not found: {e}")
        # Try to create a minimal dataset for testing if data_raw doesn't exist
        # In a real scenario, this should fail loudly
        raise RuntimeError(f"Cannot proceed without data directory: {data_root}")
    
    if not image_paths:
        logger.error("No images found in data directory")
        return
    
    # Run feature extraction
    logger.info("Running feature extraction pipeline")
    df_features = run_feature_extraction_pipeline(image_paths)
    
    if df_features.empty:
        logger.error("Feature extraction produced no valid records")
        return
    
    logger.info(f"Extracted features for {len(df_features)} images")
    
    # Filter records with location
    logger.info("Filtering records with location metadata")
    df_filtered = filter_records_with_location(df_features)
    
    if df_filtered.empty:
        logger.error("No records with valid location metadata")
        return
    
    logger.info(f"Retained {len(df_filtered)} records with location data")
    
    # Merge with weather data
    logger.info("Merging with weather data")
    df_unified = merge_weather_and_features(df_filtered)
    
    if df_unified.empty:
        logger.error("Weather merging produced no valid records")
        return
    
    logger.info(f"Successfully merged {len(df_unified)} records")
    
    # Save to CSV
    logger.info(f"Saving unified dataset to {output_path}")
    df_unified.to_csv(output_path, index=False)
    
    # Log summary
    logger.info(f"Pipeline complete. Output: {output_path}")
    logger.info(f"Columns: {list(df_unified.columns)}")
    logger.info(f"Shape: {df_unified.shape}")
    
    return output_path

if __name__ == '__main__':
    main()