import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from utils import get_logger

def ensure_directories():
    """Ensure output directories exist."""
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def fetch_assistments_instructional_units(logger: logging.Logger) -> pd.DataFrame:
    """
    Fetch instructional units (skill descriptions) from the ASSISTments dataset.
    Uses the 'assistments2017' dataset from HuggingFace.
    
    Returns:
        DataFrame with columns: 'skill_id', 'skill_name', 'skill_description'
    """
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("The 'datasets' library is required. Install with: pip install datasets")
        raise

    logger.info("Loading ASSISTments 2017 dataset from HuggingFace...")
    try:
        # Load the dataset in streaming mode to avoid memory issues
        # We only need the 'skill' table or relevant columns from the main table
        # ASSISTments 2017 has a 'skill' table with descriptions
        dataset = load_dataset(" ASSISTments/assistments2017", split="train", streaming=True)
        
        # Convert to pandas to inspect columns and filter
        # Note: Streaming datasets might not support direct to_pandas() easily for large sets
        # We will collect a sample of unique skills first
        
        skills_data = []
        seen_skill_ids = set()
        
        # Iterate to find skill information
        # The ASSISTments 2017 dataset structure usually has 'skill_id' and 'skill_name'
        # We need to map these to descriptions if available, or use the name as the description
        for row in dataset:
            if 'skill_id' in row and row['skill_id'] is not None:
                skill_id = str(row['skill_id'])
                if skill_id not in seen_skill_ids:
                    seen_skill_ids.add(skill_id)
                    skill_name = row.get('skill_name', f"Skill {skill_id}")
                    # Some datasets have 'skill_description', others rely on 'skill_name'
                    description = row.get('skill_description', skill_name)
                    if pd.isna(description):
                        description = skill_name
                    
                    skills_data.append({
                        'skill_id': skill_id,
                        'skill_name': skill_name,
                        'skill_description': description
                    })
                    
                    # Limit to a reasonable sample size for this task (e.g., 200 unique skills)
                    if len(skills_data) >= 200:
                        break
        
        if not skills_data:
            logger.warning("No skill data found in the expected format. Attempting alternative fetch...")
            # Fallback: Try loading the 'skills' table if it exists as a separate config
            # Or try a different split/config
            try:
                dataset = load_dataset(" ASSISTments/assistments2017", split="train", streaming=True)
                # If the above loop didn't find it, maybe the keys are different
                # Let's just grab the first few rows and inspect keys if needed, 
                # but for this implementation, we assume standard ASSISTments keys.
                pass
            except Exception as e:
                logger.error(f"Failed to fetch alternative data: {e}")
                raise ValueError("Could not fetch instructional units from ASSISTments.")

        df = pd.DataFrame(skills_data)
        logger.info(f"Successfully fetched {len(df)} unique instructional units.")
        return df

    except Exception as e:
        logger.error(f"Failed to load ASSISTments dataset: {e}")
        # Re-raise to fail loudly as per constraints
        raise

def save_instructional_units(df: pd.DataFrame, output_path: Path, logger: logging.Logger):
    """
    Save the instructional units to a CSV file.
    
    Args:
        df: DataFrame containing the instructional units.
        output_path: Path to save the CSV file.
        logger: Logger instance.
    """
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} instructional units to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save instructional units: {e}")
        raise

def main():
    """Main entry point for extracting instructional units."""
    logger = get_logger("extract_instructional_units")
    logger.info("Starting instructional unit extraction...")
    
    output_dir = ensure_directories()
    output_file = output_dir / "instructional_units.csv"
    
    # Check if file already exists to avoid re-fetching (optional optimization)
    # For now, we always fetch to ensure freshness, but could add a --force flag
    if output_file.exists():
        logger.info(f"Output file {output_file} already exists. Overwriting...")
    
    try:
        df = fetch_assistments_instructional_units(logger)
        save_instructional_units(df, output_file, logger)
        logger.info("Instructional unit extraction completed successfully.")
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
