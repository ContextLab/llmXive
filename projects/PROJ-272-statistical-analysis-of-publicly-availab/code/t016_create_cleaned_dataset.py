"""
Task T016: Create Cleaned Dataset

Implements the creation of the intermediate cleaned dataset in `data/interim/cleaned_adress.csv`.
This task depends on T014 (Filter Records) and T015 (Metadata Extraction).

It loads the raw data, applies the filtering logic (T014) and metadata extraction (T015),
and writes the final cleaned dataset. It also generates a derivation log.
"""
import logging
import os
import json
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

from config import get_path, ensure_dirs
from utils import get_logger, normalize_text, validate_text_length
from ingestion import (
    count_raw_records_from_csv,
    clean_transcript_text,
    parse_cognitive_status,
    extract_metadata_and_log_exclusions
)

# Configure logger
logger = get_logger(__name__)

def load_interim_records(raw_path: Path) -> pd.DataFrame:
    """
    Load raw records from the specified CSV path.
    Expected columns based on ADReSS structure: 'transcript', 'label' (or similar).
    """
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_path}")
    
    # Attempt to load with common delimiters if csv fails
    try:
        df = pd.read_csv(raw_path)
    except Exception:
        # Fallback for TSV if CSV fails, though ADReSS is usually CSV
        df = pd.read_csv(raw_path, sep='\t')
    
    logger.info(f"Loaded {len(df)} raw records from {raw_path}")
    return df

def apply_t014_t015_logic(df: pd.DataFrame) -> tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Apply T014 (Filter) and T015 (Metadata Extraction) logic.
    
    Returns:
        tuple: (cleaned_df, exclusion_log)
    """
    exclusion_log = []
    valid_records = []
    
    # Ensure required columns exist or normalize names
    # ADReSS typically has 'id', 'label', 'transcript'
    # We map standard names to internal processing
    if 'transcript' not in df.columns and 'text' in df.columns:
        df['transcript'] = df['text']
    
    if 'label' not in df.columns and 'diagnosis' in df.columns:
        df['label'] = df['diagnosis']

    for idx, row in df.iterrows():
        record_id = row.get('id', idx)
        text_raw = row.get('transcript', "")
        label_raw = row.get('label', "")
        
        # T015: Parse Cognitive Status
        label_clean = parse_cognitive_status(label_raw)
        
        # T013b: UTF-8 Normalization
        text_clean = normalize_text(text_raw)
        
        # T013a: Remove Annotations (handled in clean_transcript_text usually, but explicit here)
        text_clean = clean_transcript_text(text_clean)
        
        # T014: Filter Records
        # Condition 1: Label is null or invalid
        if label_clean is None or label_clean == "":
            exclusion_log.append({
                "id": record_id,
                "reason": "NULL_LABEL",
                "original_label": label_raw
            })
            continue
        
        # Condition 2: Text length < 50 words
        word_count = len(text_clean.split())
        if word_count < 50:
            exclusion_log.append({
                "id": record_id,
                "reason": "TEXT_TOO_SHORT",
                "word_count": word_count,
                "threshold": 50
            })
            continue
        
        # If passed all checks
        valid_records.append({
            "participant_id": record_id,
            "label": label_clean,
            "text": text_clean,
            "word_count": word_count
        })
    
    logger.info(f"Filtered {len(df) - len(valid_records)} records. Remaining: {len(valid_records)}")
    
    return pd.DataFrame(valid_records), exclusion_log

def write_cleaned_dataset(df: pd.DataFrame, output_path: Path, exclusion_log: List[Dict[str, Any]]) -> None:
    """
    Write the cleaned dataset to CSV and log exclusions.
    """
    ensure_dirs(output_path)
    
    # Write CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Cleaned dataset written to {output_path}")
    
    # Write Exclusion Log (T014 requirement)
    exclusion_log_path = output_path.parent / "exclusions.log"
    with open(exclusion_log_path, 'w', encoding='utf-8') as f:
        for entry in exclusion_log:
            f.write(json.dumps(entry) + "\n")
    logger.info(f"Exclusion log written to {exclusion_log_path}")

def generate_derivation_log(output_path: Path) -> None:
    """
    Generate a derivation log documenting the pipeline steps for T016.
    """
    log_data = {
        "task_id": "T016",
        "description": "Create Cleaned Dataset",
        "input_source": "Raw ADReSS dataset (processed by T012, T013a, T013b)",
        "dependencies": ["T014", "T015"],
        "steps": [
            "1. Load raw records.",
            "2. Normalize text to UTF-8 (T013b).",
            "3. Remove non-verbal annotations (T013a).",
            "4. Parse cognitive status labels (T015).",
            "5. Filter records with null labels (T014).",
            "6. Filter records with < 50 words (T014).",
            "7. Write cleaned dataset to data/interim/cleaned_adress.csv."
        ],
        "output_file": str(output_path),
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    log_path = output_path.parent / "derivation_log.json"
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Derivation log written to {log_path}")

def main():
    """
    Main entry point for T016.
    """
    # Paths
    # Assuming raw data is in data/raw/ or data/interim/raw.csv based on T012
    # We look for the most recent raw input or use config
    raw_path = get_path("data/raw", "adress_raw.csv") # Fallback if specific name unknown
    if not raw_path.exists():
        # Try standard ADReSS naming if config path fails
        possible_paths = [
            get_path("data/raw", "ADReSS.csv"),
            get_path("data/raw", "adress.csv"),
            get_path("data/interim", "raw_records.csv")
        ]
        for p in possible_paths:
            if p.exists():
                raw_path = p
                break
    
    if not raw_path.exists():
        # If still not found, try to find ANY csv in data/raw
        raw_dir = get_path("data/raw")
        if raw_dir.exists():
            csv_files = list(raw_dir.glob("*.csv"))
            if csv_files:
                raw_path = csv_files[0]
            else:
                raise FileNotFoundError("No raw CSV data found in data/raw/")
        else:
            raise FileNotFoundError("No raw data source found.")

    output_dir = get_path("data/interim")
    output_path = output_dir / "cleaned_adress.csv"

    logger.info(f"Starting T016. Input: {raw_path}, Output: {output_path}")

    # 1. Load
    df = load_interim_records(raw_path)

    # 2. Apply Logic (T014 + T015)
    cleaned_df, exclusions = apply_t014_t015_logic(df)

    # 3. Write
    write_cleaned_dataset(cleaned_df, output_path, exclusions)

    # 4. Derivation Log
    generate_derivation_log(output_path)

    logger.info("T016 Completed successfully.")

if __name__ == "__main__":
    main()
