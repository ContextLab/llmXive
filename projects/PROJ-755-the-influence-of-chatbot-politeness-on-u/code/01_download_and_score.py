import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure the parent directory is in the path for relative imports if running as script
# However, standard practice in this project seems to be running from root with code/ in path
# or using absolute imports from the package root. We will assume standard execution context.
# The prompt implies we are extending this file.

import pandas as pd

# Import existing utilities from the project structure
# Based on the API surface, we assume these exist in code/utils
try:
    from utils.data_integrity import compute_file_checksum
except ImportError:
    # Fallback if running directly without path setup, though unlikely in pipeline
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories(output_dir: Path) -> None:
    """Ensure required output directories exist."""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir.parent / "raw").mkdir(parents=True, exist_ok=True)

def load_dataset_with_check(path: Path) -> pd.DataFrame:
    """
    Load a dataset from parquet or csv with basic checks.
    This is a placeholder for the actual loading logic which might be in a utility.
    Since T016 handles merging, we assume the input here is the merged or primary dataset.
    """
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")
    
    suffix = path.suffix.lower()
    if suffix == '.parquet':
        return pd.read_parquet(path)
    elif suffix in ['.csv', '.tsv']:
        return pd.read_csv(path, sep='\t' if suffix == '.tsv' else ',')
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

def validate_and_preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Basic validation and preprocessing.
    Ensures required columns exist and handles basic types.
    """
    required_cols = ['user_id', 'dialogue_id', 'utterance', 'speaker']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.warning(f"Missing columns in input dataset: {missing}. Attempting to proceed with available columns.")
    
    # Ensure string types for text columns
    text_cols = ['utterance']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)
    
    return df

def extract_utterances(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract utterances and prepare for scoring.
    This might involve grouping or flattening if data is nested.
    Assuming flat structure for now based on typical parquet exports from HF datasets.
    """
    # If the data is already flat (one row per utterance), this might be a pass-through
    # or a renaming step.
    return df.copy()

def filter_dialogues(df: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    """
    Filter dialogues missing 'quality_rating' or chatbot utterances.
    
    Logic:
    1. Exclude rows where 'quality_rating' is missing (NaN) or not present in the dataset.
       Note: Per T016/T012, if the dataset was merged because HCI_P2 lacked fields,
       we still need to ensure we only keep rows with a valid quality rating for analysis.
    2. Identify 'chatbot' utterances. The 'speaker' column is used to identify the bot.
       We assume 'chatbot', 'bot', 'assistant', or 'system' are valid bot identifiers.
       We exclude dialogues that have NO chatbot utterances at all.
    3. Log counts of excluded dialogues to 'data/raw/exclusions.log'.
    4. Return the filtered dataframe.
    """
    if df.empty:
        logger.warning("Input dataframe is empty. Returning empty dataframe.")
        return df

    original_count = len(df)
    logger.info(f"Starting filtering on {original_count} rows.")

    # 1. Filter for quality_rating
    if 'quality_rating' not in df.columns:
        logger.error("CRITICAL: 'quality_rating' column is missing. Cannot filter. Exiting.")
        raise ValueError("Missing required column 'quality_rating'.")
    
    # Remove rows with NaN in quality_rating
    pre_quality_count = len(df)
    df = df.dropna(subset=['quality_rating'])
    dropped_quality = pre_quality_count - len(df)
    if dropped_quality > 0:
        logger.info(f"Dropped {dropped_quality} rows due to missing 'quality_rating'.")
    
    # 2. Filter for chatbot utterances
    # We need to identify dialogues that contain at least one chatbot utterance.
    # First, identify bot speakers.
    bot_keywords = ['chatbot', 'bot', 'assistant', 'system', 'ai']
    
    # Normalize speaker column to lower case for matching
    if 'speaker' in df.columns:
        df['speaker_lower'] = df['speaker'].astype(str).str.lower()
        # Create a mask for bot utterances
        bot_mask = df['speaker_lower'].apply(lambda x: any(k in x for k in bot_keywords))
        
        # Identify dialogue_ids that have at least one bot utterance
        valid_dialogue_ids = df[bot_mask]['dialogue_id'].unique()
        
        # Filter the dataframe to keep only rows belonging to these dialogue_ids
        pre_bot_count = len(df)
        df = df[df['dialogue_id'].isin(valid_dialogue_ids)]
        dropped_bot = pre_bot_count - len(df)
        
        if dropped_bot > 0:
            logger.info(f"Dropped {dropped_bot} rows belonging to dialogues without chatbot utterances.")
    else:
        logger.warning("Column 'speaker' not found. Cannot filter by chatbot utterances. Proceeding with quality_rating filter only.")

    # 3. Logging
    final_count = len(df)
    total_dropped = original_count - final_count
    
    log_entry = {
        "task": "T017_FilterDialogues",
        "input_rows": original_count,
        "dropped_missing_quality_rating": dropped_quality,
        "dropped_no_chatbot_utterances": dropped_bot,
        "final_rows": final_count,
        "exclusion_rate": total_dropped / original_count if original_count > 0 else 0
    }
    
    log_path = output_dir.parent / "raw" / "exclusions.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    logger.info(f"Filtering complete. Final rows: {final_count}. Log written to {log_path}")
    
    if 'speaker_lower' in df.columns:
        df = df.drop(columns=['speaker_lower'])

    return df

def main():
    """
    Main entry point for T017.
    Expects the merged or primary dataset to be at:
    data/processed/merged_dialogues.parquet OR data/processed/scored_dialogues.parquet
    depending on the flow.
    Based on T016, if HCI_P2 is full, it goes to scored_dialogues. If partial, merged_dialogues.
    We check for the existence of the merged file first, then the scored file (if T016 skipped merge).
    However, T017 is part of US1 which happens BEFORE T018 (scoring).
    So we expect the input to be the raw/merged data BEFORE scoring.
    
    Input: data/processed/merged_dialogues.parquet (if merge happened)
           OR data/raw/hci_p2/... (if no merge needed, but T016 says it saves to processed)
    
    Let's assume T016 produces 'data/processed/merged_dialogues.parquet' if merge occurred.
    If no merge occurred (HCI_P2 full), T016 might have saved directly to 'data/processed/scored_dialogues.parquet'?
    Wait, T018 is scoring. T017 is filtering.
    The flow is: Download -> Merge (T016) -> Filter (T017) -> Score (T018).
    
    So input for T017 is the output of T016.
    T016 output: 'data/processed/merged_dialogues.parquet' (if merge) or 'data/processed/scored_dialogues.parquet' (if no merge? No, that's T020).
    Actually, T016 description says: "Save processed data to ... scored_dialogues.parquet (if HCI_P2 only)".
    Wait, T016 says: "If status: full, DO NOT MERGE. Use HCI_P2 only."
    And T016 deliverable: "scored_dialogues.parquet (if HCI_P2 only)".
    This is confusing naming. T016 is "conditional merging".
    If no merge, it likely just copies/renames the HCI_P2 data to the processed folder.
    Let's look for 'data/processed/merged_dialogues.parquet' first. If not found, look for 'data/processed/scored_dialogues.parquet' (from T016's 'no merge' path).
    Actually, T016 says: "Store all datasets separately...".
    Let's assume the input to T017 is the unified dataframe available in 'data/processed/'.
    We will try to load 'data/processed/merged_dialogues.parquet'. If not found, try 'data/processed/scored_dialogues.parquet' (assuming T016 put it there in the no-merge case).
    """
    project_root = Path(__file__).resolve().parent.parent
    processed_dir = project_root / "data" / "processed"
    
    input_file = None
    possible_inputs = [
        processed_dir / "merged_dialogues.parquet",
        processed_dir / "scored_dialogues.parquet" # In case T016 named it this even before scoring
    ]
    
    for p in possible_inputs:
        if p.exists():
            input_file = p
            break
    
    if not input_file:
        # Fallback: Check raw directories if T016 didn't save to processed yet?
        # T016 says: "Save processed data to ...". So it should be in processed.
        logger.error("No input file found in data/processed/. T016 might not have completed.")
        sys.exit(1)
    
    logger.info(f"Loading input dataset from {input_file}")
    df = load_dataset_with_check(input_file)
    
    # Preprocess
    df = validate_and_preprocess(df)
    
    # Filter
    df_filtered = filter_dialogues(df, processed_dir)
    
    # Save the filtered result
    # Where should it go? T018 needs it.
    # T018 says: "Implement batched inference... to score utterances."
    # It likely loads the filtered data.
    # Let's save it as 'data/processed/filtered_dialogues.parquet' or overwrite the input?
    # T018 description doesn't specify the input filename, but T020 says "Save processed data to ... scored_dialogues.parquet".
    # So T017 should output something that T018 can read.
    # Let's save to 'data/processed/filtered_dialogues.parquet' to be safe, or overwrite 'merged_dialogues.parquet'.
    # Given T016's ambiguity, let's overwrite the input file to keep the pipeline linear.
    # Or better: Save to a specific filtered file and let T018 read that.
    # Let's save to 'data/processed/filtered_dialogues.parquet'.
    
    output_file = processed_dir / "filtered_dialogues.parquet"
    df_filtered.to_parquet(output_file, index=False)
    logger.info(f"Filtered data saved to {output_file}")

if __name__ == "__main__":
    main()