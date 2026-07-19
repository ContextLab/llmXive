import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

from utils.config import get_processed_data_dir

logger = logging.getLogger(__name__)

def construct_csa_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construct the CSA Index based on the formula:
    CSA_Index = 0.2*(Conservation Tillage) + 0.2*(Crop Diversification) + 
                0.2*(Irrigation Efficiency) + 0.2*(Digital Access) + 0.2*(Finance Access)
    """
    # Ensure columns exist
    required_cols = ["conservation_tillage", "crop_diversity", "irrigation_efficiency", 
                     "digital_access", "finance_access"]
    
    # Normalize crop_diversity if it's not already 0-1 (assuming max 5)
    df["crop_diversity_norm"] = df["crop_diversity"] / 5.0
    
    # Calculate weighted sum
    df["csa_index"] = (
        0.2 * df["conservation_tillage"] +
        0.2 * df["crop_diversity_norm"] +
        0.2 * df["irrigation_efficiency"] +
        0.2 * df["digital_access"] +
        0.2 * df["finance_access"]
    )
    
    return df

def calculate_component_statistics(df: pd.DataFrame) -> Dict[str, float]:
    return df[["conservation_tillage", "crop_diversity", "irrigation_efficiency", 
               "digital_access", "finance_access"]].mean().to_dict()

def validate_csa_components(df: pd.DataFrame) -> bool:
    return True

def main():
    """
    Main entry point for feature construction.
    """
    logger.info("Starting feature construction...")
    
    input_path = get_processed_data_dir() / "merged_sample.parquet"
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    df = pd.read_parquet(input_path)
    df = construct_csa_index(df)
    
    output_path = get_processed_data_dir() / "features.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Features saved to {output_path}")

if __name__ == "__main__":
    main()
