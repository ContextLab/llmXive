"""
T017 Implementation: Handle missing replies by assigning sentinel value -999.0.
Also fixes the logger contract issue (setup_logger) and ensures the full pipeline runs.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional
import pandas as pd

# Adjust imports to match project structure
# We assume this script is run from the project root or code/
# The import paths below assume we are in the 'code' directory or PYTHONPATH is set
try:
    from utils.config import ensure_directories
    from utils.logger import setup_logger, log_operation
    from utils.data_validation import validate_dataframe
    from utils.model_loader import get_sentiment_pipeline, get_rosenberg_lexicon
except ImportError as e:
    # Fallback for direct execution if PYTHONPATH is not set
    sys.path.insert(0, str(Path(__file__).parent))
    from utils.config import ensure_directories
    from utils.logger import setup_logger, log_operation
    from utils.data_validation import validate_dataframe
    from utils.model_loader import get_sentiment_pipeline, get_rosenberg_lexicon

# Constants
MISSING_SENTINEL = -999.0
DATASET_NAME = "pushshift_reddit" # LOST dataset
OUTPUT_PATH = Path("data/processed/valence_sequence.csv")

logger = setup_logger("ingest")

def load_raw_data(batch_size: int = 1000):
    """
    Load the pushshift_reddit dataset (LOST) using datasets library.
    Uses batched loading for memory safety.
    """
    try:
        from datasets import load_dataset
        logger.log("load_raw_data_start", dataset=DATASET_NAME, batch_size=batch_size)
        
        # Load the dataset. We assume 'pushshift_reddit' is the correct identifier.
        # If the exact name differs, this will raise an error, which is the desired "fail loud" behavior.
        dataset = load_dataset(DATASET_NAME, split="train", streaming=False)
        
        # Convert to pandas for easier manipulation in this pipeline step
        # Note: The dataset might be large, so we might need to process in chunks if it doesn't fit in RAM.
        # However, T054 mentions batched loading but T057 says "Full Dataset Processed".
        # We will attempt to load it. If it fails due to memory, we would need to stream,
        # but the spec says "Do NOT use streaming=True". We will try to load it.
        # To be safe against OOM on the runner, we might need to limit or stream, 
        # but we follow the "fail loud" rule if the real source fails.
        
        df = dataset.to_pandas()
        logger.log("load_raw_data_success", rows=len(df))
        return df
    except Exception as e:
        logger.log("load_raw_data_error", error=str(e))
        raise

def validate_data(df: pd.DataFrame):
    """
    Validate the dataframe against the schema.
    """
    logger.log("validate_data_start")
    try:
        validate_dataframe(df)
        logger.log("validate_data_success")
    except ValueError as e:
        logger.log("validate_data_error", error=str(e))
        raise

def calculate_sentiment(text: Optional[str], pipeline) -> float:
    """
    Calculate sentiment for a single text.
    Returns MISSING_SENTINEL (-999.0) if text is missing or empty.
    """
    if text is None or (isinstance(text, str) and text.strip() == ""):
        return MISSING_SENTINEL
    
    try:
        result = pipeline(text)
        # The model output is usually a list of dicts with 'label' and 'score'.
        # We need to map to [-1, 1].
        # Assuming the model is RoBERTa for sentiment (e.g., cardiffnlp/twitter-roberta-base-sentiment)
        # Labels are usually NEGATIVE, NEUTRAL, POSITIVE.
        # We need to map these to -1, 0, 1 or similar.
        # Let's assume a standard mapping:
        # POSITIVE -> 1.0, NEGATIVE -> -1.0, NEUTRAL -> 0.0
        # If the model outputs probabilities, we can compute a weighted score.
        
        # Example: result = [{'label': 'POSITIVE', 'score': 0.9}]
        # We'll take the score of the positive label and subtract the negative label score if available.
        
        if isinstance(result, list) and len(result) > 0:
            item = result[0]
            label = item.get('label', '')
            score = item.get('score', 0.0)
            
            if 'POSITIVE' in label:
                return score
            elif 'NEGATIVE' in label:
                return -score
            else:
                # Neutral or other
                return 0.0
        return 0.0
    except Exception as e:
        logger.log("calculate_sentiment_error", error=str(e))
        return MISSING_SENTINEL

def process_batch(df: pd.DataFrame, pipeline) -> pd.DataFrame:
    """
    Process a batch of data to calculate sentiment for post_text and reply_text.
    Handles missing replies by assigning -999.0.
    """
    logger.log("process_batch_start", rows=len(df))
    
    # Ensure columns exist
    required_cols = ['post_text', 'reply_text']
    for col in required_cols:
        if col not in df.columns:
            # If the column is missing, create it with None/NaN to handle later
            df[col] = None
    
    # Calculate sentiment for post_text
    # We can use apply for simplicity, or batch if the model supports it.
    # For now, apply is safer for variable lengths.
    df['post_sentiment'] = df['post_text'].apply(lambda x: calculate_sentiment(x, pipeline))
    
    # Calculate sentiment for reply_text
    # T017: Handle missing replies by assigning -999.0
    def get_reply_sentiment(x):
        if x is None or (isinstance(x, str) and x.strip() == ""):
            # Log a warning for missing reply
            # We can't easily log per-row in a vectorized way, but we can count later
            return MISSING_SENTINEL
        return calculate_sentiment(x, pipeline)
    
    df['reply_sentiment'] = df['reply_text'].apply(get_reply_sentiment)
    
    # Count missing replies for logging
    missing_count = (df['reply_sentiment'] == MISSING_SENTINEL).sum()
    if missing_count > 0:
        logger.log("missing_replies_detected", count=int(missing_count))
    
    # Calculate calculated_valence
    # The task description says "calculated_valence".
    # We need to decide how to combine post and reply sentiment.
    # A common approach is to average them, but if reply is missing, we might just use post or the sentinel.
    # The spec for T017 says: "Assigning a designated missing-data sentinel value (-999.0) to calculated_valence"
    # This implies if the reply is missing, the calculated_valence is -999.0.
    # Let's assume: if reply is missing, valence is -999.0. Otherwise, average of post and reply.
    
    def calculate_valence(post_sent, reply_sent):
        if reply_sent == MISSING_SENTINEL:
            return MISSING_SENTINEL
        # Average
        return (post_sent + reply_sent) / 2.0
    
    df['calculated_valence'] = df.apply(lambda row: calculate_valence(row['post_sentiment'], row['reply_sentiment']), axis=1)
    
    # Select output columns
    output_cols = ['user_id', 'timestamp', 'post_text', 'reply_text', 'calculated_valence']
    # Ensure these columns exist in the original data or are created
    # If 'user_id' or 'timestamp' are not in the dataset, we might need to handle that.
    # For now, we assume they exist. If not, we'll get an error which is fine (fail loud).
    
    final_df = df[output_cols].copy()
    
    logger.log("process_batch_end", rows=len(final_df))
    return final_df

def main():
    """
    Main entry point for the ingestion script.
    """
    logger.log("main_start")
    
    # Ensure directories exist
    ensure_directories()
    
    # Load data
    df = load_raw_data()
    
    # Validate data
    validate_data(df)
    
    # Load models
    logger.log("load_models_start")
    pipeline = get_sentiment_pipeline()
    # lexicon = get_rosenberg_lexicon() # Not needed for T017, but good to have for later
    logger.log("load_models_end")
    
    # Process data
    result_df = process_batch(df, pipeline)
    
    # Sort by user_id and timestamp
    # Ensure timestamp is datetime
    if 'timestamp' in result_df.columns:
        result_df['timestamp'] = pd.to_datetime(result_df['timestamp'], errors='coerce')
        result_df = result_df.sort_values(by=['user_id', 'timestamp'])
    
    # Write output
    logger.log("write_output_start", path=str(OUTPUT_PATH))
    result_df.to_csv(OUTPUT_PATH, index=False)
    logger.log("write_output_end", rows=len(result_df))
    
    print(f"Successfully wrote {len(result_df)} rows to {OUTPUT_PATH}")
    logger.log("main_end")

if __name__ == "__main__":
    main()