import logging
import os
import sys
from typing import List, Dict, Any, Optional
import pandas as pd
from datasets import load_dataset
import itertools
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

DATASET_NAME = "matsci/glass-forming-ability"
PROJECT_ROOT = "projects/PROJ-510-predicting-the-glass-forming-region-of-a"
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
OUTPUT_FILE = os.path.join(DATA_DIR, "processed_alloys.csv")
SAMPLING_LOG = os.path.join(DATA_DIR, "sampling_log.txt")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)

def load_glass_data() -> pd.DataFrame:
    """
    Load the glass forming ability dataset from Hugging Face.
    Uses streaming to handle large datasets.
    """
    logger.info(f"Attempting to load dataset: {DATASET_NAME}")
    try:
        # Use streaming to avoid memory issues
        dataset = load_dataset(DATASET_NAME, streaming=True)
        
        # Get the first split (usually 'train')
        split_name = list(dataset.keys())[0]
        logger.info(f"Using split: {split_name}")
        
        # Convert to dataframe (streaming)
        # Note: load_dataset with streaming returns an iterable, we need to convert to list then DF
        # For very large datasets, we might want to sample during iteration
        data_list = []
        count = 0
        
        # Iterate through the dataset
        for item in dataset[split_name]:
            data_list.append(item)
            count += 1
            
            # Optional: Log progress every 10k items if needed, but for now just count
            if count % 10000 == 0:
                logger.info(f"Loaded {count} items...")

        if not data_list:
            raise ValueError("Dataset is empty.")

        df = pd.DataFrame(data_list)
        logger.info(f"Successfully loaded {len(df)} rows.")
        return df

    except Exception as e:
        logger.error(f"Failed to load dataset {DATASET_NAME}: {str(e)}")
        # CRITICAL: Fail loudly, do not fallback to synthetic data
        raise ValueError(f"Data fetch failed: {DATASET_NAME} unavailable. Error: {str(e)}")

def filter_ternary_alloys(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the dataframe to keep only ternary alloys (3 elements).
    Assumes 'composition' column contains strings like "A_B_C" or "A B C".
    """
    logger.info("Filtering for ternary alloys...")
    
    def count_elements(comp_str):
        if not isinstance(comp_str, str):
            return 0
        # Handle various separators: space, underscore, comma
        comp_str = comp_str.replace(',', ' ').replace('_', ' ')
        parts = comp_str.split()
        # Filter out non-element tokens if any (simple heuristic: keep if starts with capital)
        elements = [p for p in parts if p and p[0].isupper()]
        return len(elements)

    df['element_count'] = df['composition'].apply(count_elements)
    ternary_df = df[df['element_count'] == 3].copy()
    logger.info(f"Found {len(ternary_df)} ternary alloys.")
    return ternary_df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the dataframe: remove rows with missing critical_cooling_rate or other essential fields.
    """
    logger.info("Cleaning data...")
    required_cols = ['composition', 'critical_cooling_rate']
    # Check if columns exist, if not, try to find similar ones or fail
    for col in required_cols:
        if col not in df.columns:
            # Try to find a column with 'ccr' or 'cooling' in name
            matches = [c for c in df.columns if 'ccr' in c.lower() or 'cooling' in c.lower()]
            if matches:
                logger.warning(f"Column '{col}' not found. Using '{matches[0]}' instead.")
                df = df.rename(columns={matches[0]: col})
            else:
                raise ValueError(f"Required column '{col}' not found in dataset.")
    
    # Drop rows with NaN in critical columns
    initial_count = len(df)
    df = df.dropna(subset=required_cols)
    dropped = initial_count - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows due to missing values in required columns.")
    
    return df

def validate_critical_cooling_rate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure critical_cooling_rate has non-zero variance and >= 500 entries.
    """
    logger.info("Validating critical_cooling_rate...")
    
    if len(df) < 500:
        raise ValueError(f"Data availability error: {len(df)} valid entries, expected >= 500")
    
    if df['critical_cooling_rate'].var() == 0:
        raise ValueError("Data availability error: zero variance in critical_cooling_rate")
    
    logger.info("Validation passed.")
    return df

def log_sampling_info(total: int, sampled: int, status: str):
    """Log sampling information to a file."""
    with open(SAMPLING_LOG, 'w') as f:
        f.write(f"Total rows: {total}\n")
        f.write(f"Sampled rows: {sampled}\n")
        f.write(f"Status: {status}\n")
        f.write(f"Random Seed: 42\n")
    logger.info(f"Sampling status: {status}. Log written to {SAMPLING_LOG}")

def run_ingestion():
    """Main ingestion pipeline."""
    try:
        # 1. Load Data
        df = load_glass_data()
        
        # 2. Filter Ternary
        df = filter_ternary_alloys(df)
        
        # 3. Clean Data
        df = clean_data(df)
        
        # 4. Validate
        df = validate_critical_cooling_rate(df)
        
        # 5. Sampling Logic (if > 10k)
        target_max = 10000
        if len(df) > target_max:
            logger.info(f"Dataset size ({len(df)}) > {target_max}. Sampling...")
            random.seed(42)
            # Use itertools.islice for sampling
            indices = random.sample(range(len(df)), target_max)
            df = df.iloc[indices].reset_index(drop=True)
            log_sampling_info(len(df) + (len(df) - target_max), len(df), "SAMPLED")
        else:
            log_sampling_info(len(df), len(df), "FULL")

        # 6. Save to CSV
        df.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"Saved processed data to {OUTPUT_FILE}")
        
        return df

    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_ingestion()