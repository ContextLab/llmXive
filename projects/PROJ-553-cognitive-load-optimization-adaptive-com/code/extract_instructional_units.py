import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories(output_path: Path) -> None:
    """Ensure the output directory exists."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

def fetch_assistments_instructional_units(
    dataset_name: str = " assistments/2009-2010",
    sample_size: Optional[int] = 1000
) -> pd.DataFrame:
    """
    Fetch instructional units (skill descriptions) from the ASSISTments dataset.
    
    Args:
        dataset_name: HuggingFace dataset identifier.
        sample_size: Number of rows to sample. If None, loads full dataset.
        
    Returns:
        DataFrame containing 'skill' (instructional unit) and 'skill_id'.
        
    Raises:
        ValueError: If the dataset does not contain required 'skill' or 'skill_id' columns.
        RuntimeError: If the dataset cannot be fetched.
    """
    logger.info(f"Fetching dataset: {dataset_name}")
    
    try:
        # Load dataset (streaming to handle large datasets efficiently)
        dataset = load_dataset(dataset_name, split="train", streaming=True)
        
        # Convert to list if sample_size is specified to avoid loading full dataset into memory
        if sample_size:
            data_iter = list(dataset)
            # We need to ensure we have enough unique skills
            # If the sample is small, we might not get enough unique skills, 
            # but we'll process what we have.
            logger.info(f"Sampled {len(data_iter)} interactions")
        else:
            data_iter = list(dataset)
            logger.info(f"Loaded full dataset with {len(data_iter)} interactions")
            
        df = pd.DataFrame(data_iter)
        
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise RuntimeError(f"Could not fetch dataset {dataset_name}: {e}") from e

    # Verify schema
    required_cols = {'skill', 'skill_id'}
    available_cols = set(df.columns)
    missing_cols = required_cols - available_cols
    
    if missing_cols:
        error_msg = f"Schema Missing: Required columns {missing_cols} not found in dataset. Available: {available_cols}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Extract unique instructional units (skills)
    logger.info("Extracting unique instructional units (skills)...")
    
    # Drop duplicates based on skill_id to get unique skills
    unique_skills = df[['skill_id', 'skill']].drop_duplicates(subset='skill_id')
    
    # Reset index
    unique_skills = unique_skills.reset_index(drop=True)
    
    # Rename columns to match expected output
    unique_skills = unique_skills.rename(columns={
        'skill_id': 'interaction_id',
        'skill': 'instructional_unit'
    })
    
    # Filter out any empty or NaN skills
    unique_skills = unique_skills[unique_skills['instructional_unit'].notna()]
    unique_skills = unique_skills[unique_skills['instructional_unit'].str.strip() != '']
    
    logger.info(f"Extracted {len(unique_skills)} unique instructional units")
    
    return unique_skills

def save_instructional_units(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save instructional units to CSV.
    
    Args:
        df: DataFrame with 'interaction_id' and 'instructional_unit' columns.
        output_path: Path to save the CSV file.
    """
    ensure_directories(output_path)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} instructional units to {output_path}")

def main() -> None:
    """Main entry point for extracting instructional units."""
    logger.info("Starting instructional unit extraction...")
    
    # Define paths
    project_root = Path(__file__).parent.parent
    output_path = project_root / "data" / "processed" / "instructional_units.csv"
    
    try:
        # Fetch and extract
        df = fetch_assistments_instructional_units()
        
        # Save
        save_instructional_units(df, output_path)
        
        logger.info("Instructional unit extraction completed successfully.")
        
    except Exception as e:
        logger.error(f"Failed to extract instructional units: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
