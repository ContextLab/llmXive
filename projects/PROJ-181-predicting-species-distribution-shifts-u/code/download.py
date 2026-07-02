import os
import time
import logging
from datetime import datetime
from pathlib import Path
import requests
import pandas as pd

# Import project configuration and utilities
from config import DATA_RAW_DIR, RND_SEED
from utils.data_utils import validate_coordinates, handle_missing_values

# Setup logger
from logging_config import setup_logger, get_logger
logger = get_logger(__name__)

GBIF_API_BASE = "https://api.gbif.org/v1/occurrence/search"
USER_AGENT = "llmXive-species-distribution-project"

def fetch_occurrences(year_start, year_end, output_path, species_limit=None, max_records=50000):
    """
    Fetch occurrence data from GBIF for a specific year range.
    
    Args:
        year_start (int): Start year for occurrence records.
        year_end (int): End year for occurrence records.
        output_path (str): Path to save the CSV output.
        species_limit (int, optional): Limit number of species to fetch (for testing).
        max_records (int): Maximum number of records to fetch per species.
    """
    logger.info(f"Fetching occurrences from {year_start} to {year_end}...")
    
    # We will fetch for a representative set of North American bird species
    # In a full implementation, this would iterate over a list of species from a config or spec
    # For now, we fetch a general dataset or specific common species to ensure real data
    # Using a generic query for "Aves" (Birds) in North America for the time range
    # Note: GBIF API requires a valid email in User-Agent for high volume, but we use a generic one for demo
    
    params = {
        "taxonKey": 212,  # Aves (Birds)
        "country": "US",  # Focusing on US for North America sample, can add CA, MX
        "year": f"{year_start},{year_end}",
        "hasCoordinate": "true",
        "typeStatus": "holotype", # Filter for better quality, or remove to get more data
        "limit": 1000, # Page size
        "offset": 0
    }
    
    all_records = []
    total_fetched = 0
    
    # Simple pagination loop for a single species/taxon query
    # In a real robust system, we would handle multiple species and complex pagination
    while total_fetched < max_records:
        try:
            response = requests.get(GBIF_API_BASE, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'results' not in data or not data['results']:
                break
                
            for record in data['results']:
                if record.get('decimalLatitude') and record.get('decimalLongitude'):
                    all_records.append(record)
            
            total_fetched += len(data['results'])
            if len(data['results']) < 1000:
                break # Last page
                
            params['offset'] += 1000
            time.sleep(0.5) # Rate limiting
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data: {e}")
            break

    if not all_records:
        logger.warning("No records fetched. Creating empty dataframe with expected schema.")
        df = pd.DataFrame(columns=[
            'decimalLatitude', 'decimalLongitude', 'scientificName', 
            'eventDate', 'basisOfRecord', 'source_identifier', 
            'download_timestamp', 'original_dataset_name'
        ])
    else:
        df = pd.DataFrame(all_records)
        # Standardize column names to expected schema if they differ
        # GBIF returns 'decimalLatitude', 'decimalLongitude', 'scientificName', 'eventDate', 'basisOfRecord'
        # We map them directly if they exist
        required_cols = ['decimalLatitude', 'decimalLongitude', 'scientificName', 'eventDate', 'basisOfRecord']
        existing_cols = [c for c in required_cols if c in df.columns]
        if len(existing_cols) != len(required_cols):
            logger.warning(f"Missing expected columns in GBIF response: {set(required_cols) - set(existing_cols)}")
        
        df = df[existing_cols]

    # Add metadata columns (Constitution Principle VI)
    df = add_metadata_columns(df, source_identifier="GBIF-AVES-US", original_dataset_name="GBIF Occurrence Download")
    
    # Validate and clean coordinates
    df = validate_coordinates(df)
    
    # Handle missing values
    df = handle_missing_values(df)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} records to {output_path}")
    
    return df

def add_metadata_columns(df, source_identifier="GBIF-AVES-US", original_dataset_name="GBIF Occurrence Download"):
    """
    Add required metadata columns to the dataframe as per Constitution Principle VI.
    
    Args:
        df (pd.DataFrame): The occurrence dataframe.
        source_identifier (str): Unique identifier for the data source.
        original_dataset_name (str): Name of the original dataset.
        
    Returns:
        pd.DataFrame: DataFrame with added metadata columns.
    """
    df['source_identifier'] = source_identifier
    df['download_timestamp'] = datetime.utcnow().isoformat()
    df['original_dataset_name'] = original_dataset_name
    return df

def derive_effort_data(input_path, output_path):
    """
    Derive "target-group effort data" as all-observer density from the historical GBIF dataset.
    
    This function reads the historical occurrence data (T010), groups by spatial grid cells,
    and counts the total number of observations per cell. This serves as a bias proxy for
    sampling effort, independent of specific species presence.
    
    Args:
        input_path (str): Path to the historical occurrence CSV (e.g., occurrence_1970_2000.csv).
        output_path (str): Path to save the effort data CSV.
    """
    logger.info(f"Deriving effort data from {input_path}...")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load historical data
    df = pd.read_csv(input_path)
    
    if df.empty:
        logger.warning("Input data is empty. Creating empty effort data file.")
        effort_df = pd.DataFrame(columns=['grid_cell_id', 'observation_count', 'lat_center', 'lon_center'])
    else:
        # Filter for valid coordinates
        valid_df = df.dropna(subset=['decimalLatitude', 'decimalLongitude'])
        
        if valid_df.empty:
            logger.warning("No valid coordinates found in input data.")
            effort_df = pd.DataFrame(columns=['grid_cell_id', 'observation_count', 'lat_center', 'lon_center'])
        else:
            # Create spatial grid cells (0.1 degree resolution for effort density)
            # This is a coarse grid to aggregate observer effort
            bin_size = 0.1
            valid_df['grid_lat'] = (valid_df['decimalLatitude'] / bin_size).astype(int) * bin_size
            valid_df['grid_lon'] = (valid_df['decimalLongitude'] / bin_size).astype(int) * bin_size
            
            # Group by grid cell and count observations
            effort_df = valid_df.groupby(['grid_lat', 'grid_lon']).agg(
                observation_count=('decimalLatitude', 'count'),
                lat_center=('decimalLatitude', 'mean'),
                lon_center=('decimalLongitude', 'mean')
            ).reset_index()
            
            # Create a unique ID for each grid cell
            effort_df['grid_cell_id'] = effort_df['grid_lat'].astype(str) + "_" + effort_df['grid_lon'].astype(str)
            
            # Reorder columns
            effort_df = effort_df[['grid_cell_id', 'observation_count', 'lat_center', 'lon_center']]
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    effort_df.to_csv(output_path, index=False)
    logger.info(f"Saved effort data ({len(effort_df)} grid cells) to {output_path}")
    
    return effort_df

def main():
    """Main entry point for downloading recent occurrence data (2005-2020)."""
    logger.info("Starting download of recent occurrence data (2005-2020)...")
    
    output_path = DATA_RAW_DIR / "occurrence_2005_2020.csv"
    
    # Fetch data for the 2005-2020 range
    df = fetch_occurrences(
        year_start=2005,
        year_end=2020,
        output_path=output_path,
        max_records=10000 # Limit for this specific task to ensure speed
    )
    
    logger.info("Download complete.")

def main_effort():
    """Main entry point for deriving target-group effort data from historical occurrences."""
    logger.info("Starting derivation of target-group effort data...")
    
    input_path = DATA_RAW_DIR / "occurrence_1970_2000.csv"
    output_path = DATA_RAW_DIR / "effort_data.csv"
    
    derive_effort_data(input_path, output_path)
    
    logger.info("Effort data derivation complete.")

if __name__ == "__main__":
    # Check if running as main script for effort data
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "effort":
        main_effort()
    else:
        main()