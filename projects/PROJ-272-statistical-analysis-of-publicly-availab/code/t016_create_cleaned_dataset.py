import logging
import os
import json
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

from config import get_path, ensure_dirs
from utils import get_logger
from ingestion import clean_transcript_text, parse_cognitive_status

def load_interim_records(input_path: str) -> pd.DataFrame:
    """
    Load the intermediate cleaned transcripts from ingestion step.
    Expects a CSV with at least 'participant_id', 'text', and 'label' columns.
    """
    logger = get_logger("T016")
    logger.info(f"Loading interim records from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records")
    return df

def apply_t014_t015_logic(df: pd.DataFrame, exclusions_log_path: str) -> pd.DataFrame:
    """
    Apply filtering logic from T014 and T015:
    - T014: Filter out records where label is null OR text length < 50 words.
    - T015: Parse cognitive status and generate specific reason codes for exclusions.
    
    Logs excluded records to exclusions_log_path.
    Returns the filtered DataFrame.
    """
    logger = get_logger("T016")
    exclusions = []
    
    # Ensure exclusions log directory exists
    ensure_dirs(exclusions_log_path)
    
    # Parse cognitive status for all records first (T015)
    # Assuming 'label' or a metadata column contains the status info
    # We'll assume the ingestion step already parsed this into a 'cognitive_status' column
    # or we parse it from the raw text/metadata if available.
    # For this implementation, we assume 'label' contains the status string or code.
    
    if 'cognitive_status' not in df.columns:
        # Attempt to parse from label if it's a raw string
        if 'label' in df.columns:
            df['cognitive_status'] = df['label'].apply(lambda x: parse_cognitive_status(str(x)) if pd.notna(x) else None)
        else:
            logger.warning("No 'label' or 'cognitive_status' column found. Creating placeholder.")
            df['cognitive_status'] = None

    filtered_rows = []
    
    for idx, row in df.iterrows():
        reason = None
        
        # T014 Logic: Filter null labels
        if pd.isna(row.get('label')):
            reason = "T014_NULL_LABEL"
        
        # T014 Logic: Filter short text (< 50 words)
        elif 'text' in row:
            text = str(row['text'])
            word_count = len(text.split())
            if word_count < 50:
                reason = f"T014_SHORT_TEXT ({word_count} words)"
        
        # T015 Logic: Validate cognitive status
        if not reason and 'cognitive_status' in df.columns:
            status = row.get('cognitive_status')
            if status is None or status not in ["Control", "MCI", "AD"]:
                reason = f"T015_INVALID_STATUS ({status})"
        
        if reason:
            exclusions.append({
                "participant_id": row.get('participant_id', idx),
                "reason_code": reason,
                "original_label": row.get('label'),
                "text_length": len(str(row.get('text', '')).split()) if 'text' in row else 0
            })
        else:
            filtered_rows.append(row)
    
    # Write exclusions log
    if exclusions:
        with open(exclusions_log_path, 'w', encoding='utf-8') as f:
            for exc in exclusions:
                f.write(json.dumps(exc) + '\n')
        logger.info(f"Logged {len(exclusions)} exclusions to {exclusions_log_path}")
    else:
        logger.info("No exclusions logged.")
    
    return pd.DataFrame(filtered_rows)

def write_cleaned_dataset(df: pd.DataFrame, output_path: str, derivation_log_path: str) -> None:
    """
    Write the final cleaned dataset to CSV and generate a derivation log.
    """
    logger = get_logger("T016")
    
    # Ensure output directory exists
    ensure_dirs(output_path)
    ensure_dirs(derivation_log_path)
    
    # Write CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(df)} records to {output_path}")
    
    # Generate derivation log
    derivation_log = {
        "task_id": "T016",
        "description": "Create intermediate cleaned dataset",
        "input_source": "data/interim/cleaned_transcripts.csv (from T013)",
        "filters_applied": [
            "T014: Exclude null labels",
            "T014: Exclude text < 50 words",
            "T015: Validate cognitive status (Control, MCI, AD)"
        ],
        "output_record_count": len(df),
        "columns": list(df.columns),
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    with open(derivation_log_path, 'w', encoding='utf-8') as f:
        json.dump(derivation_log, f, indent=2)
    logger.info(f"Wrote derivation log to {derivation_log_path}")

def main():
    logger = setup_logging("T016", level=logging.INFO)
    
    # Paths
    input_path = get_path("data/interim/cleaned_transcripts.csv")
    output_path = get_path("data/interim/cleaned_adress.csv")
    exclusions_log_path = get_path("data/interim/exclusions.log")
    derivation_log_path = get_path("data/interim/cleaned_adress.derivation.log")
    
    # Ensure directories
    ensure_dirs(output_path)
    ensure_dirs(exclusions_log_path)
    ensure_dirs(derivation_log_path)
    
    try:
        # 1. Load interim data
        df = load_interim_records(input_path)
        
        # 2. Apply T014/T015 logic
        df_clean = apply_t014_t015_logic(df, exclusions_log_path)
        
        # 3. Write output and derivation log
        write_cleaned_dataset(df_clean, output_path, derivation_log_path)
        
        logger.info("T016 completed successfully.")
        
    except Exception as e:
        logger.error(f"T016 failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
