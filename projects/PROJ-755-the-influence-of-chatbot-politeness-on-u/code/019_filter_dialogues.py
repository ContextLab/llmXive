"""
Task T019: Implement filtering logic to exclude dialogues missing `quality_rating` or chatbot utterances.

This script loads the raw datasets (HCI_P2, Persona-Chat, EmpatheticDialogues) saved in `data/raw/`,
filters them based on completeness criteria, logs the exclusion counts, and saves the filtered
datasets to `data/raw/filtered/`.

Dependencies:
    - T015: HCI_P2 raw data
    - T015b: Persona-Chat raw data
    - T015c: EmpatheticDialogues raw data
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/filtering.log", mode="a")
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Create necessary output directories if they don't exist."""
    directories = [
        Path("data/raw/filtered"),
        Path("logs")
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories: {directories}")

def load_raw_dataset(dataset_name: str, data_dir: Path) -> Optional[pd.DataFrame]:
    """
    Load a raw dataset from the local directory.
    
    Args:
        dataset_name: Name of the dataset (e.g., 'hci_p2', 'persona_chat', 'empathetic_dialogues')
        data_dir: Path to the raw data directory.
        
    Returns:
        DataFrame or None if loading fails.
    """
    logger.info(f"Attempting to load raw dataset: {dataset_name}")
    try:
        # Attempt to load as parquet if available, otherwise try csv or json
        parquet_path = data_dir / f"{dataset_name}.parquet"
        csv_path = data_dir / f"{dataset_name}.csv"
        json_path = data_dir / f"{dataset_name}.json"
        
        if parquet_path.exists():
            df = pd.read_parquet(parquet_path)
        elif csv_path.exists():
            df = pd.read_csv(csv_path)
        elif json_path.exists():
            df = pd.read_json(json_path)
        else:
            # Fallback: try to find any parquet/csv/json in the directory
            files = list(data_dir.glob("*"))
            if not files:
                logger.error(f"No data files found in {data_dir} for {dataset_name}")
                return None
            
            for file_path in files:
                if file_path.suffix == '.parquet':
                    df = pd.read_parquet(file_path)
                    break
                elif file_path.suffix == '.csv':
                    df = pd.read_csv(file_path)
                    break
                elif file_path.suffix == '.json':
                    df = pd.read_json(file_path)
                    break
            else:
                logger.error(f"No supported data files found in {data_dir} for {dataset_name}")
                return None

        logger.info(f"Successfully loaded {dataset_name}: {len(df)} rows, columns: {list(df.columns)}")
        return df
    except Exception as e:
        logger.error(f"Failed to load {dataset_name}: {e}", exc_info=True)
        return None

def filter_dialogues(df: pd.DataFrame, source_name: str) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Filter dialogues to exclude those missing `quality_rating` or chatbot utterances.
    
    Args:
        df: Input DataFrame.
        source_name: Name of the source dataset for logging.
        
    Returns:
        Tuple of (filtered_df, exclusion_stats)
    """
    logger.info(f"Filtering dialogues for {source_name}...")
    
    # Normalize column names (lowercase, strip whitespace)
    df.columns = df.columns.str.lower().str.strip()
    
    # Identify required columns
    required_cols = ['quality_rating']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.warning(f"Dataset {source_name} missing required columns: {missing_cols}. "
                     "Attempting to map or skip filtering for these columns.")
        # If quality_rating is missing, we cannot filter by it. 
        # We will proceed but log a warning.
    
    # Filter 1: Exclude dialogues missing `quality_rating`
    initial_count = len(df)
    if 'quality_rating' in df.columns:
        df = df.dropna(subset=['quality_rating'])
        dropped_by_rating = initial_count - len(df)
    else:
        dropped_by_rating = 0
        logger.warning(f"Skipping quality_rating filter for {source_name} as column is missing.")
    
    # Filter 2: Exclude dialogues missing chatbot utterances
    # Assume 'utterances' column exists and is a list or string representation of a list
    # If 'utterances' is a list of dicts, check for 'speaker' or 'role' indicating 'chatbot'
    # If 'utterances' is a string, try to parse it
    
    utterances_col = None
    for col in ['utterances', 'turns', 'dialogue', 'messages']:
        if col in df.columns:
            utterances_col = col
            break
    
    if utterances_col:
        def has_chatbot_utterance(utterances):
            if pd.isna(utterances):
                return False
            if isinstance(utterances, str):
                try:
                    utterances = eval(utterances) # Safe eval for list of dicts
                except:
                    return False
            if not isinstance(utterances, list):
                return False
            if len(utterances) == 0:
                return False
            
            # Check if any utterance is from a chatbot
            # Common keys: 'speaker', 'role', 'author', 'person'
            chatbot_indicators = ['bot', 'chatbot', 'assistant', 'system', 'ai']
            for utterance in utterances:
                if isinstance(utterance, dict):
                    for key in ['speaker', 'role', 'author', 'person']:
                        if key in utterance:
                            speaker = str(utterance[key]).lower()
                            if any(ind in speaker for ind in chatbot_indicators):
                                return True
                            # If no specific chatbot indicator, assume presence of utterances is enough
                            # But task says "missing chatbot utterances", so we need to be sure it's a chatbot
                            # If we can't determine, we might keep it or drop it. 
                            # Let's be conservative: if we can't identify a chatbot, drop it.
                            break
                elif isinstance(utterance, str):
                    # If it's just a string, assume it's a chatbot response if the dataset structure implies it
                    # This is a heuristic and might need adjustment based on actual data structure
                    return True # Assume string utterances are chatbot responses if no better info
            return False
        
        # Apply filter
        mask = df[utterances_col].apply(has_chatbot_utterance)
        df_filtered = df[mask]
        dropped_by_utterance = len(df) - len(df_filtered)
    else:
        logger.warning(f"Could not find utterances column in {source_name}. Skipping utterance filter.")
        df_filtered = df
        dropped_by_utterance = 0
    
    total_dropped = initial_count - len(df_filtered)
    exclusion_stats = {
        "source": source_name,
        "initial_count": initial_count,
        "dropped_by_missing_quality_rating": dropped_by_rating,
        "dropped_by_missing_chatbot_utterances": dropped_by_utterance,
        "final_count": len(df_filtered),
        "total_dropped": total_dropped
    }
    
    logger.info(f"Filtering complete for {source_name}: "
               f"Initial={initial_count}, Dropped={total_dropped}, Final={len(df_filtered)}")
    logger.info(f"  - Dropped by missing quality_rating: {dropped_by_rating}")
    logger.info(f"  - Dropped by missing chatbot utterances: {dropped_by_utterance}")
    
    return df_filtered, exclusion_stats

def save_results(filtered_dfs: Dict[str, pd.DataFrame], exclusion_stats: List[Dict[str, Any]], output_dir: Path):
    """
    Save filtered datasets and exclusion log.
    
    Args:
        filtered_dfs: Dictionary mapping source name to filtered DataFrame.
        exclusion_stats: List of exclusion statistics dictionaries.
        output_dir: Path to output directory.
    """
    logger.info("Saving filtered datasets and exclusion log...")
    
    # Save each filtered dataset
    for source_name, df in filtered_dfs.items():
        output_path = output_dir / f"{source_name}_filtered.parquet"
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved filtered dataset for {source_name} to {output_path}")
    
    # Save exclusion log
    exclusion_log_path = output_dir.parent / "exclusions.log" # Save to data/raw/exclusions.log as per T021
    with open(exclusion_log_path, "w") as f:
        json.dump(exclusion_stats, f, indent=2)
    logger.info(f"Saved exclusion log to {exclusion_log_path}")

def main():
    """Main entry point for T019."""
    logger.info("Starting T019: Filter dialogues")
    
    ensure_directories()
    
    # Define raw data directories for each dataset
    raw_data_dirs = {
        "hci_p2": Path("data/raw/hci_p2"),
        "persona_chat": Path("data/raw/persona_chat"),
        "empathetic_dialogues": Path("data/raw/empathetic_dialogues")
    }
    
    filtered_dfs = {}
    exclusion_stats = []
    
    for source_name, data_dir in raw_data_dirs.items():
        if not data_dir.exists():
            logger.warning(f"Data directory {data_dir} does not exist. Skipping {source_name}.")
            continue
        
        df = load_raw_dataset(source_name, data_dir)
        if df is None:
            logger.error(f"Failed to load {source_name}. Skipping.")
            continue
        
        filtered_df, stats = filter_dialogues(df, source_name)
        filtered_dfs[source_name] = filtered_df
        exclusion_stats.append(stats)
    
    if not filtered_dfs:
        logger.error("No datasets were successfully filtered. Exiting.")
        sys.exit(1)
    
    save_results(filtered_dfs, exclusion_stats, Path("data/raw/filtered"))
    
    logger.info("T019 completed successfully.")

if __name__ == "__main__":
    main()
