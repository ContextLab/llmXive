import os
import time
import logging
from datetime import datetime
from pathlib import Path
import requests
import pandas as pd
import json

from config import DATA_DIR, RND_SEED
from logging_config import get_logger

# Ensure directories exist
RAW_DIR = DATA_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)

def fetch_occurrences(species_name, year_start, year_end, max_results=10000):
    """
    Fetch occurrence data from GBIF API for a specific species and year range.
    Implements pagination to handle large datasets.
    """
    url = "https://api.gbif.org/v1/occurrence/search"
    params = {
        "scientificName": species_name,
        "year": f"{year_start},{year_end}",
        "limit": 1000,  # GBIF max per request
        "offset": 0,
        "hasCoordinate": True,
        "hasGeospatialIssue": False
    }

    all_records = []
    total_count = 0
    fetched_count = 0

    logger.info(f"Fetching occurrences for {species_name} ({year_start}-{year_end})")

    while True:
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "results" not in data:
                logger.warning(f"No results key in response for {species_name}")
                break

            records = data["results"]
            if not records:
                break

            all_records.extend(records)
            fetched_count += len(records)
            total_count = data.get("count", 0)

            logger.debug(f"Fetched {fetched_count} records (total available: {total_count})")

            if fetched_count >= total_count or fetched_count >= max_results:
                break

            params["offset"] += params["limit"]
            time.sleep(1)  # Rate limiting

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data: {e}")
            break

    logger.info(f"Total records fetched: {len(all_records)}")
    return all_records

def add_metadata_columns(df, source_identifier, original_dataset_name):
    """
    Add Constitution Principle VI metadata columns to the DataFrame.
    """
    timestamp = datetime.now().isoformat()
    df["source_identifier"] = source_identifier
    df["download_timestamp"] = timestamp
    df["original_dataset_name"] = original_dataset_name
    return df

def derive_effort_data(occurrence_df, grid_size=0.1):
    """
    Derive target-group effort data (all-observer density) from occurrence data.
    This serves as a bias proxy for bias correction.
    """
    if occurrence_df.empty:
        logger.warning("Empty occurrence dataframe, returning empty effort data")
        return pd.DataFrame()

    # Simplified effort derivation: count records per grid cell
    occurrence_df["grid_lon"] = (occurrence_df["decimalLongitude"] / grid_size).round() * grid_size
    occurrence_df["grid_lat"] = (occurrence_df["decimalLatitude"] / grid_size).round() * grid_size

    effort = occurrence_df.groupby(["grid_lon", "grid_lat"]).size().reset_index(name="record_count")
    effort["grid_lon"] = effort["grid_lon"].astype(float)
    effort["grid_lat"] = effort["grid_lat"].astype(float)

    logger.info(f"Derived effort data with {len(effort)} grid cells")
    return effort

def main():
    """
    Main function to download historical occurrence data (1970-2000)
    with metadata columns as per Constitution Principle VI.
    """
    # Example species for demonstration - in real use, iterate over species list
    species_list = ["Turdus migratorius", "Setophaga ruticilla", "Cardinalis cardinalis"]
    
    output_file = RAW_DIR / "occurrence_1970_2000.csv"
    
    all_occurrences = []
    
    for species in species_list:
        records = fetch_occurrences(species, 1970, 2000, max_results=50000)
        
        if not records:
            logger.warning(f"No records found for {species}")
            continue
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Standardize column names for GBIF response
        if "decimalLatitude" in df.columns:
            df["latitude"] = df["decimalLatitude"]
        if "decimalLongitude" in df.columns:
            df["longitude"] = df["decimalLongitude"]
        
        # Add metadata columns (Constitution Principle VI)
        df = add_metadata_columns(
            df,
            source_identifier=f"GBIF_{species}_1970_2000",
            original_dataset_name="GBIF Occurrence Download"
        )
        
        all_occurrences.append(df)
        logger.info(f"Processed {len(df)} records for {species}")
    
    if all_occurrences:
        combined_df = pd.concat(all_occurrences, ignore_index=True)
        combined_df.to_csv(output_file, index=False)
        logger.info(f"Saved combined occurrence data to {output_file}")
        print(f"Download complete. Saved {len(combined_df)} records to {output_file}")
    else:
        logger.error("No occurrence data downloaded")
        raise RuntimeError("Failed to download any occurrence data")

def main_effort():
    """
    Main function to derive effort data from historical occurrence data.
    """
    input_file = RAW_DIR / "occurrence_1970_2000.csv"
    output_file = RAW_DIR / "effort_data.csv"
    
    if not input_file.exists():
        logger.error(f"Input file {input_file} does not exist. Run main() first.")
        raise FileNotFoundError(f"Input file {input_file} not found")
    
    occurrence_df = pd.read_csv(input_file)
    effort_df = derive_effort_data(occurrence_df)
    
    if not effort_df.empty:
        effort_df.to_csv(output_file, index=False)
        logger.info(f"Saved effort data to {output_file}")
        print(f"Effort data derived. Saved {len(effort_df)} grid cells to {output_file}")
    else:
        logger.warning("No effort data could be derived")

if __name__ == "__main__":
    main()
    # Uncomment to also generate effort data
    # main_effort()
