import logging
import os
import sys
from typing import List, Dict, Any, Optional
import pandas as pd
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_glass_data() -> pd.DataFrame:
    """
    Load the glass-forming ability dataset from HuggingFace.
    Uses the verified source: matsci/glass-forming-ability.
    Fails loudly if the dataset cannot be loaded or lacks required columns.
    """
    logger.info("Loading glass-forming ability dataset from matsci/glass-forming-ability...")
    try:
        # Load the dataset (streaming=False as per T012 constraints for <7GB check)
        dataset = load_dataset("matsci/glass-forming-ability", split="train")
        df = dataset.to_pandas()
        
        # Verify required columns exist
        required_cols = ["composition", "critical_cooling_rate", "glass_forming_label"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in dataset: {missing_cols}")
        
        logger.info(f"Dataset loaded successfully with {len(df)} rows.")
        logger.info(f"Columns: {list(df.columns)}")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise RuntimeError(f"Data ingestion failed: {e}")

def filter_ternary_alloys(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the dataset to include only ternary alloys (exactly 3 elements).
    Excludes rows with missing elemental data or unknown glass-forming labels.
    Logs exclusion counts.
    
    Args:
        df: Input DataFrame with 'composition' and 'glass_forming_label' columns.
        
    Returns:
        Filtered DataFrame containing only valid ternary alloys.
    """
    logger.info("Filtering for ternary alloys (3 elements)...")
    
    initial_count = len(df)
    logger.debug(f"Initial row count: {initial_count}")
    
    # Helper to count elements in composition string
    # Expected format: "Element1_x1 Element2_x2 ..." or similar
    def count_elements(composition_str: str) -> int:
        if not isinstance(composition_str, str) or not composition_str.strip():
            return 0
        # Split by whitespace and count non-empty parts
        parts = composition_str.strip().split()
        # Filter out potential non-element parts if any (simple heuristic: count spaces or known separators)
        # Assuming format like "Fe20Ni20Co60" or "Fe 20 Ni 20 Co 60"
        # If it's a single string without spaces, we need to parse elements.
        # However, based on standard datasets, it's often space-separated or comma-separated.
        # Let's assume space-separated for now, or handle single string if no spaces.
        if len(parts) == 1 and len(composition_str) > 0:
            # Could be "Fe20Ni20Co60" -> need to parse
            # Simple regex to find capital letters followed by optional lowercase
            import re
            elements = re.findall(r'[A-Z][a-z]?', composition_str)
            return len(elements)
        return len(parts)

    # Filter for exactly 3 elements
    ternary_mask = df['composition'].apply(count_elements) == 3
    ternary_df = df[ternary_mask]
    
    count_ternary = len(ternary_df)
    count_non_ternary = initial_count - count_ternary
    logger.info(f"Filtered to ternary alloys: {count_ternary} rows (excluded {count_non_ternary} non-ternary).")
    
    # Exclude rows with missing critical_cooling_rate
    count_missing_ccr = ternary_df['critical_cooling_rate'].isna().sum()
    ternary_df = ternary_df.dropna(subset=['critical_cooling_rate'])
    logger.info(f"Excluded {count_missing_ccr} rows with missing critical_cooling_rate.")
    
    # Exclude rows with missing or unknown glass_forming_label
    # Assuming 'unknown' or NaN or specific string values indicate invalid labels
    # Check for NaN first
    count_missing_label = ternary_df['glass_forming_label'].isna().sum()
    ternary_df = ternary_df.dropna(subset=['glass_forming_label'])
    
    # Check for string 'unknown' if applicable
    if 'glass_forming_label' in ternary_df.columns:
        unknown_mask = ternary_df['glass_forming_label'].astype(str).str.lower() == 'unknown'
        count_unknown_label = unknown_mask.sum()
        ternary_df = ternary_df[~unknown_mask]
    else:
        count_unknown_label = 0
        
    logger.info(f"Excluded {count_missing_label} rows with missing glass_forming_label.")
    logger.info(f"Excluded {count_unknown_label} rows with 'unknown' glass_forming_label.")
    
    final_count = len(ternary_df)
    total_excluded = initial_count - final_count
    
    logger.info(f"Final ternary alloy count: {final_count} (Total excluded: {total_excluded})")
    
    return ternary_df.reset_index(drop=True)

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform additional cleaning on the filtered dataset.
    Ensures data types are correct and removes any remaining anomalies.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Cleaned DataFrame.
    """
    logger.info("Performing data cleaning...")
    
    # Ensure critical_cooling_rate is numeric
    df['critical_cooling_rate'] = pd.to_numeric(df['critical_cooling_rate'], errors='coerce')
    
    # Drop any rows that might have become NaN after coercion
    df = df.dropna(subset=['critical_cooling_rate'])
    
    # Reset index
    df = df.reset_index(drop=True)
    
    logger.info(f"Data cleaning complete. Final shape: {df.shape}")
    return df

def run_ingestion(output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Main entry point for the ingestion pipeline.
    1. Loads the raw dataset.
    2. Filters for ternary alloys.
    3. Cleans the data.
    4. Saves to disk if output_path is provided.
    
    Args:
        output_path: Path to save the processed CSV. Defaults to 'data/processed/processed_alloys.csv'.
        
    Returns:
        The processed DataFrame.
    """
    if output_path is None:
        output_path = os.path.join("data", "processed", "processed_alloys.csv")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Step 1: Load
    raw_df = load_glass_data()
    
    # Step 2: Filter
    filtered_df = filter_ternary_alloys(raw_df)
    
    # Step 3: Clean
    cleaned_df = clean_data(filtered_df)
    
    # Step 4: Save
    cleaned_df.to_csv(output_path, index=False)
    logger.info(f"Processed data saved to {output_path}")
    
    return cleaned_df

if __name__ == "__main__":
    run_ingestion()
