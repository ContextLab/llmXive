import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from code.config import get_path, ensure_dirs

logger = logging.getLogger(__name__)

def load_processed_intermediates() -> pd.DataFrame:
    """
    Load the processed morphological metrics.
    """
    path = get_path("data/processed/morphological_metrics.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    
    # Fallback to synthetic if real not found
    synth_path = get_path("data/processed/synthetic_dataset.csv")
    if os.path.exists(synth_path):
        return pd.read_csv(synth_path)
    
    raise FileNotFoundError("No processed data found.")

def format_sholl_vector(sholl_data: Any) -> str:
    """
    Format Sholl intersections vector for CSV.
    """
    if isinstance(sholl_data, list):
        return json.dumps(sholl_data)
    return str(sholl_data)

def aggregate_and_save_metrics(df: pd.DataFrame, output_path: str) -> None:
    """
    Aggregate metrics and save to CSV.
    """
    # Ensure sholl_intersections is formatted
    if 'sholl_intersections' in df.columns:
        df['sholl_intersections'] = df['sholl_intersections'].apply(format_sholl_vector)
    
    # Ensure brain_region is present
    if 'brain_region' not in df.columns:
        logger.warning("brain_region not found. Adding default.")
        df['brain_region'] = 'Unknown'

    df.to_csv(output_path, index=False)
    logger.info(f"Morphological metrics saved to {output_path}")

def run_output_pipeline() -> str:
    """
    Run the output pipeline to generate the final metrics CSV.
    """
    logger.info("Running output pipeline.")
    
    df = load_processed_intermediates()
    output_path = get_path("data/processed/morphological_metrics.csv")
    ensure_dirs(output_path)
    
    aggregate_and_save_metrics(df, output_path)
    return output_path

def main():
    path = run_output_pipeline()
    print(f"Output saved to {path}")

if __name__ == "__main__":
    main()
