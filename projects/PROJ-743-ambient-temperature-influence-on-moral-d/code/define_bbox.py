import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd

from config import DATA_RAW_DIR, DATA_EXTERNAL_DIR, RESULTS_LOG_DIR

def calculate_bounding_box(df, expand_degrees=2.0):
    valid_df = df.dropna(subset=['latitude', 'longitude'])
    if valid_df.empty:
        raise ValueError("No valid latitude/longitude data found.")

    min_lat, max_lat = valid_df['latitude'].min(), valid_df['latitude'].max()
    min_lon, max_lon = valid_df['longitude'].min(), valid_df['longitude'].max()

    return {
        "min_lat": float(min_lat - expand_degrees),
        "max_lat": float(max_lat + expand_degrees),
        "min_lon": float(min_lon - expand_degrees),
        "max_lon": float(max_lon + expand_degrees),
        "expand_degrees": expand_degrees,
        "source_records": len(valid_df)
    }

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    input_path = DATA_RAW_DIR / "moral_machine.csv.gz"
    output_path = DATA_EXTERNAL_DIR / "bounding_box.json"
    
    DATA_EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_LOG_DIR.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Loading data from {input_path}")
        df = pd.read_csv(input_path, compression='gzip')
        bbox = calculate_bounding_box(df)
        
        with open(output_path, 'w') as f:
            json.dump(bbox, f, indent=2)
        
        logger.info(f"Bounding box saved to {output_path}: {bbox}")
    except Exception as e:
        logger.error(f"Failed to define bounding box: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
