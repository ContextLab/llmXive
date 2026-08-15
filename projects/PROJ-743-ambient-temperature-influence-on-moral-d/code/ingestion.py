import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import pandas as pd
from config import get_path_env_override

def ensure_exclusion_log_exists(log_file_path: str):
    """Ensures the exclusion log file exists and has a header."""
    if not os.path.exists(log_file_path):
        with open(log_file_path, 'w') as f:
            f.write("record_id,reason\n")

def load_moral_machine_dataset(data_path: str) -> pd.DataFrame:
    """Loads the Moral Machine dataset from a CSV file."""
    try:
        df = pd.read_csv(data_path)
        return df
    except FileNotFoundError:
        logging.error(f"Moral Machine data not found at {data_path}")
        raise

def filter_invalid_records(df: pd.DataFrame) -> pd.DataFrame:
    """Filters records with missing location data or impossible response times."""
    valid_df = df[((df['location_x'].notna()) & (df['location_y'].notna())) &
                   (df['response_time'] >= 0.1) & (df['response_time'] <= 10000)]
    return valid_df

def log_excluded_records(df: pd.DataFrame, log_file_path: str):
    """Logs excluded records with their reasons to a CSV file."""
    ensure_exclusion_log_exists(log_file_path)
    with open(log_file_path, 'a') as f:
        for index, row in df[~df['is_valid']].iterrows():
            f.write(f"{index},{row['reason']}\n")

def fetch_era5_temperature(latitude: float, longitude: float) -> Optional[float]:
    """Placeholder for fetching ERA5 temperature data."""
    # Replace with actual API call to CDS API
    return None  # Implement real logic here. Returning None simulates missing data for interpolation test.

def add_era5_temperature_to_df(df: pd.DataFrame) -> pd.DataFrame:
    """Adds ERA5 temperature data to the DataFrame."""
    df['temperature_celsius'] = df.apply(lambda row: fetch_era5_temperature(row['location_x'], row['location_y']), axis=1)
    return df

def haversine_distance(lat1, lon1, lat2, lon2):
  """Calculates the Haversine distance between two points."""
  from math import radians, cos, sin, sqrt, atan2
  R = 6371  # Radius of Earth in kilometers

  lat1 = radians(lat1)
  lon1 = radians(lon1)
  lat2 = radians(lat2)
  lon2 = radians(lon2)

  dlon = lon2 - lon1
  dlat = lat2 - lat1

  a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
  c = 2 * atan2(sqrt(a), sqrt(1 - a))

  distance = R * c
  return distance

def match_geospatial_records(df: pd.DataFrame, grid_latitude: float, grid_longitude: float, threshold_km: int = 100):
  """Matches records to the nearest ERA5 grid within a threshold."""
  distances = df.apply(lambda row: haversine_distance(row['location_x'], row['location_y'], grid_latitude, grid_longitude), axis=1)
  df['match_quality'] = 'high'  # Default quality
  df.loc[distances > threshold_km, 'match_quality'] = 'low'
  return df

def interpolate_missing_temperature(df: pd.DataFrame):
    """Interpolates missing ERA5 temperature values."""
    df['temperature_celsius'].fillna(method='ffill', inplace=True) # Forward fill for gaps <= 2 hours
    # Check if there are any remaining NaNs after forward fill (gaps > 2 hours)
    missing_values = df[df['temperature_celsius'].isna()]
    if not missing_values.empty:
        exclude_records = missing_values.index
        df.drop(exclude_records, inplace=True)

    return df

def generate_merged_output(df: pd.DataFrame, output_path: str):
  """Generates the merged dataset and saves it to a Parquet file."""
  try:
      df.to_parquet(output_path)
      logging.info(f"Merged dataset saved to {output_path}")
  except Exception as e:
      logging.error(f"Error saving merged dataset: {e}")

def main():
    """Main function for data ingestion and merging."""
    data_path = "data/raw/moral_machine.csv"  # Replace with actual path
    exclusion_log_path = "results/logs/exclusion_log.csv"
    output_path = "data/processed/merged_dataset.parquet"

    df = load_moral_machine_dataset(data_path)
    df['reason'] = 'Unknown' # initialize reason column for filtering in next steps
    df['is_valid'] = True

    # Filter invalid records
    filtered_df = filter_invalid_records(df.copy())  # Create a copy to avoid modifying the original DataFrame
    excluded_records = df[~filtered_df['is_valid']].copy()
    log_excluded_records(excluded_records, exclusion_log_path)

    # Add ERA5 temperature data (placeholder for API call)
    era5_df = add_era5_temperature_to_df(filtered_df.copy()) # Create a copy to avoid modifying the original DataFrame

    # Match geospatial records
    matched_df = match_geospatial_records(era5_df, 48.8566, 2.3522)  # Example coordinates for Paris

    # Interpolate missing temperature values
    interpolated_df = interpolate_missing_temperature(matched_df.copy()) # Create a copy to avoid modifying the original DataFrame

    # Generate merged output
    generate_merged_output(interpolated_df, output_path)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()