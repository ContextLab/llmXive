import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from .logging_config import get_logger

logger = get_logger(__name__)

# Constants for matching
MATCHING_TOLERANCE_DAYS = 30  # Allow 30-day window for date matching
MATCHING_LOCATION_THRESHOLD = 0.05  # Approx 5km tolerance if coordinates differ slightly (optional)

def load_sample_data(filepath: str) -> pd.DataFrame:
    """
    Load sample data from CSV.
    Expected columns: sample_id, gps_latitude, gps_longitude, collection_date, plant_species, soil_type
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Sample data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} sample records from {filepath}")
    
    # Normalize column names to lowercase
    df.columns = df.columns.str.lower().str.strip()
    
    # Ensure date column is datetime
    if 'collection_date' in df.columns:
        df['collection_date'] = pd.to_datetime(df['collection_date'], errors='coerce')
    
    return df

def load_disease_data(filepath: str) -> pd.DataFrame:
    """
    Load disease incidence records from CSV.
    Expected columns: sample_id, gps_latitude, gps_longitude, measurement_date, disease_type, incidence_rate
    Note: Sometimes disease data uses 'sample_id' or 'location_id' as join key, but we match by location+date.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Disease data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} disease records from {filepath}")
    
    # Normalize column names
    df.columns = df.columns.str.lower().str.strip()
    
    # Ensure date column is datetime
    if 'measurement_date' in df.columns:
        df['measurement_date'] = pd.to_datetime(df['measurement_date'], errors='coerce')
    
    return df

def _parse_coordinate(coord: Any) -> Optional[float]:
    """Parse coordinate string or float to float."""
    if pd.isna(coord):
        return None
    try:
        return float(coord)
    except (ValueError, TypeError):
        return None

def _calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth (in km).
    """
    R = 6371.0  # Earth radius in km
    
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    delta_lat = np.radians(lat2 - lat1)
    delta_lon = np.radians(lon2 - lon1)
    
    a = np.sin(delta_lat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    return R * c

def match_samples_to_disease(samples_df: pd.DataFrame, disease_df: pd.DataFrame, 
                             lat_col: str = 'gps_latitude', lon_col: str = 'gps_longitude',
                             sample_date_col: str = 'collection_date', disease_date_col: str = 'measurement_date') -> pd.DataFrame:
    """
    Match samples to disease records based on:
    1. Geographic proximity (GPS coordinates)
    2. Temporal proximity (dates within tolerance)
    
    Strategy:
    - For each disease record, find the closest sample within the date window and location threshold.
    - If multiple samples match, pick the closest one.
    - If no sample matches, the disease record is left unmatched.
    
    Returns:
    DataFrame with matched records containing combined metadata.
    """
    logger.info("Starting sample-disease matching process...")
    
    # Clean coordinates
    samples_df = samples_df.copy()
    disease_df = disease_df.copy()
    
    samples_df['lat'] = samples_df[lat_col].apply(_parse_coordinate)
    samples_df['lon'] = samples_df[lon_col].apply(_parse_coordinate)
    disease_df['lat'] = disease_df[lat_col].apply(_parse_coordinate)
    disease_df['lon'] = disease_df[lon_col].apply(_parse_coordinate)
    
    # Drop rows with invalid coordinates
    valid_samples = samples_df.dropna(subset=['lat', 'lon'])
    valid_disease = disease_df.dropna(subset=['lat', 'lon'])
    
    if len(valid_samples) == 0:
        logger.warning("No valid sample coordinates found. Returning empty match.")
        return pd.DataFrame()
    
    if len(valid_disease) == 0:
        logger.warning("No valid disease coordinates found. Returning empty match.")
        return pd.DataFrame()
    
    matches = []
    
    # Iterate through disease records and find best matching sample
    for _, disease_row in valid_disease.iterrows():
        disease_lat = disease_row['lat']
        disease_lon = disease_row['lon']
        disease_date = disease_row.get(disease_date_col)
        
        if pd.isna(disease_date):
            continue
        
        # Filter samples by date window
        if isinstance(disease_date, pd.Timestamp):
            date_mask = (valid_samples[sample_date_col] >= disease_date - pd.Timedelta(days=MATCHING_TOLERANCE_DAYS)) & \
                        (valid_samples[sample_date_col] <= disease_date + pd.Timedelta(days=MATCHING_TOLERANCE_DAYS))
        else:
            date_mask = pd.Series([False] * len(valid_samples), index=valid_samples.index)
        
        candidates = valid_samples[date_mask].copy()
        
        if candidates.empty:
            continue
        
        # Calculate distance for candidates
        candidates['distance_km'] = candidates.apply(
            lambda row: _calculate_haversine_distance(disease_lat, disease_lon, row['lat'], row['lon']), axis=1
        )
        
        # Filter by distance threshold (e.g., 50km for regional matching if GPS is coarse)
        # Using a generous 50km threshold for soil samples which might be from the same field
        distance_threshold = 50.0 
        candidates = candidates[candidates['distance_km'] <= distance_threshold]
        
        if candidates.empty:
            continue
        
        # Select closest sample
        best_match = candidates.loc[candidates['distance_km'].idxmin()]
        
        # Create merged record
        merged_record = {
            'sample_id': best_match['sample_id'],
            'gps_latitude': disease_lat,
            'gps_longitude': disease_lon,
            'collection_date': best_match[sample_date_col],
            'measurement_date': disease_date,
            'plant_species': best_match.get('plant_species', None),
            'soil_type': best_match.get('soil_type', None),
            'disease_type': disease_row.get('disease_type', None),
            'incidence_rate': disease_row.get('incidence_rate', None),
            'distance_km': best_match['distance_km'],
            'date_diff_days': abs((disease_date - best_match[sample_date_col]).days) if pd.notna(disease_date) and pd.notna(best_match[sample_date_col]) else None
        }
        matches.append(merged_record)
    
    if not matches:
        logger.warning("No matches found between samples and disease records.")
        return pd.DataFrame()
    
    result_df = pd.DataFrame(matches)
    logger.info(f"Successfully matched {len(result_df)} samples to disease records.")
    
    return result_df

def validate_matches(matched_df: pd.DataFrame, min_matches: int = 30) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate the matching results against requirements.
    
    Args:
        matched_df: DataFrame of matched records
        min_matches: Minimum required matched samples (default 30 per task spec)
    
    Returns:
        Tuple of (success: bool, details: dict)
    """
    details = {
        'total_matches': len(matched_df),
        'min_required': min_matches,
        'status': 'pass' if len(matched_df) >= min_matches else 'fail'
    }
    
    if len(matched_df) < min_matches:
        logger.warning(f"Match count {len(matched_df)} is below minimum {min_matches}")
        return False, details
    
    # Check for completeness of critical fields
    critical_fields = ['sample_id', 'plant_species', 'incidence_rate']
    missing_fields = [f for f in critical_fields if f not in matched_df.columns]
    
    if missing_fields:
        details['missing_fields'] = missing_fields
        details['status'] = 'fail'
        return False, details
    
    # Check for non-null values in critical fields
    null_counts = matched_df[critical_fields].isnull().sum()
    if null_counts.any():
        details['null_counts'] = null_counts.to_dict()
        logger.warning(f"Found null values in critical fields: {null_counts[null_counts > 0].to_dict()}")
        # We still pass if we have enough matches, but log the warning
    
    logger.info(f"Validation passed: {len(matched_df)} matches found.")
    return True, details

def run_matching_pipeline(sample_file: str, disease_file: str, output_file: str, min_matches: int = 30) -> bool:
    """
    Run the full matching pipeline: load, match, validate, save.
    
    Args:
        sample_file: Path to sample data CSV
        disease_file: Path to disease data CSV
        output_file: Path for output matched CSV
        min_matches: Minimum required matches
    
    Returns:
        True if pipeline completed successfully and met requirements
    """
    logger.info(f"Running matching pipeline: {sample_file} + {disease_file} -> {output_file}")
    
    try:
        samples_df = load_sample_data(sample_file)
        disease_df = load_disease_data(disease_file)
        
        matched_df = match_samples_to_disease(samples_df, disease_df)
        
        success, details = validate_matches(matched_df, min_matches)
        
        # Save output regardless of validation status (for debugging)
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        matched_df.to_csv(output_file, index=False)
        logger.info(f"Saved matched data to {output_file}")
        
        if not success:
            logger.error(f"Matching validation failed: {details}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        return False

def main():
    """Main entry point for the matching script."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    sample_file = project_root / "data" / "raw" / "emp_agricultural_samples.csv"
    disease_file = project_root / "data" / "raw" / "disease_incidence_records.csv"
    output_file = project_root / "data" / "processed" / "matched_samples.csv"
    
    # Fallback for testing if raw files don't exist yet (should not happen in production)
    if not sample_file.exists():
        logger.error(f"Sample file not found: {sample_file}")
        return 1
    if not disease_file.exists():
        logger.error(f"Disease file not found: {disease_file}")
        return 1
    
    success = run_matching_pipeline(str(sample_file), str(disease_file), str(output_file), min_matches=30)
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
