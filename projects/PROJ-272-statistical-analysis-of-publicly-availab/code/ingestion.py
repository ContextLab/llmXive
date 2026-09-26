import hashlib
import json
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
from config import get_path, DataSourceConfig
from utils import normalize_text, validate_text_length, get_logger

# Constants
MIN_WORD_COUNT = 50
EXCLUSIONS_LOG_PATH = "data/interim/exclusions.log"

def download_file(url: str, dest: Path, retries: int = 3) -> Path:
    """Download a file from a URL with retry logic."""
    logger = get_logger(__name__)
    for attempt in range(retries):
        try:
            # Simple wget-like logic using urllib (standard lib) to avoid extra deps if possible,
            # but requests is standard in this env. Assuming requests is available via requirements.txt.
            import urllib.request
            logger.info(f"Attempting download (attempt {attempt + 1}/{retries}) from {url}")
            urllib.request.urlretrieve(url, dest)
            logger.info(f"Successfully downloaded to {dest}")
            return dest
        except Exception as e:
            logger.warning(f"Download attempt {attempt + 1} failed: {e}")
            if attempt == retries - 1:
                raise ConnectionError(f"ADReSS download failed after {retries} attempts. No synthetic fallback.")
    return dest

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def record_checksums(file_path: Path, output_path: Path) -> Dict[str, str]:
    """Record checksum for a file in a JSON file."""
    checksum = compute_sha256(file_path)
    data = {file_path.name: checksum}
    # Load existing if present
    if output_path.exists():
        with open(output_path, 'r') as f:
            existing = json.load(f)
        existing.update(data)
        data = existing
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    return data

def validate_scope(config: DataSourceConfig) -> None:
    """Validate that the dataset source is ADReSS and not DementiaBank."""
    if config.source != "ADReSS":
        raise ValueError(f"Scope violation: Expected ADReSS, got {config.source}. DementiaBank is explicitly excluded.")

def clean_transcript_text(text: str) -> str:
    """Remove non-verbal annotations and normalize text."""
    # Remove annotations like <laughter>, <pause>, etc.
    text = re.sub(r'<[^>]+>', '', text)
    # Normalize UTF-8 (handled by pandas read_csv usually, but explicit here)
    text = normalize_text(text)
    return text

def parse_cognitive_status(header: str) -> Optional[str]:
    """Parse cognitive status from ADReSS headers."""
    # ADReSS headers usually contain 'control', 'mci', 'ad' or similar
    header_lower = header.lower()
    if 'control' in header_lower:
        return 'Control'
    elif 'mci' in header_lower:
        return 'MCI'
    elif 'ad' in header_lower or 'dementia' in header_lower:
        return 'AD'
    return None

def extract_metadata_and_log_exclusions(df: pd.DataFrame, exclusions_log_path: Path) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Filter records where label is null OR text length < 50 words.
    Log excluded records with reason codes to exclusions_log_path.
    """
    logger = get_logger(__name__)
    exclusions_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    excluded_records = []
    
    # Prepare log file
    with open(exclusions_log_path, 'w', encoding='utf-8') as log_file:
        log_file.write("participant_id,reason,original_label,original_text_length\n")
        
        valid_rows = []
        for idx, row in df.iterrows():
            label = row.get('label')
            text = row.get('text', '')
            pid = row.get('participant_id', f'idx_{idx}')
            
            reason = None
            if pd.isna(label) or label is None:
                reason = "NULL_LABEL"
            else:
                # Count words
                words = str(text).split()
                if len(words) < MIN_WORD_COUNT:
                    reason = "TEXT_TOO_SHORT"
            
            if reason:
                excluded_records.append({
                    'participant_id': pid,
                    'reason': reason,
                    'label': str(label),
                    'text_len': len(str(text).split())
                })
                log_file.write(f"{pid},{reason},{label},{len(str(text).split())}\n")
                logger.debug(f"Excluded {pid}: {reason}")
            else:
                valid_rows.append(idx)
        
        log_file.flush()
    
    logger.info(f"Filtered {len(excluded_records)} records. Exclusions logged to {exclusions_log_path}")
    return df.iloc[valid_rows].reset_index(drop=True), excluded_records

def count_raw_records_from_csv(file_path: Path) -> int:
    """Count total records in raw CSV."""
    if not file_path.exists():
        raise FileNotFoundError(f"Raw file not found: {file_path}")
    return len(pd.read_csv(file_path))

def save_raw_record_count(count: int, output_path: Path) -> None:
    """Save raw record count to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({"raw_count": count}, f)

def validate_dataset_size(df: pd.DataFrame, output_path: Path) -> Dict[str, Any]:
    """Validate dataset size and log low power warnings."""
    logger = get_logger(__name__)
    group_counts = df['label'].value_counts().to_dict()
    
    low_power = False
    for group, count in group_counts.items():
        if count < 15:
            logger.warning(f"Low sample size in group {group}: {count}")
            low_power = True
    
    metadata = {
        "low_power": low_power,
        "group_counts": group_counts
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return metadata

def calculate_valid_label_proportion(total_raw: int, valid_count: int) -> float:
    """Calculate proportion of valid records."""
    if total_raw == 0:
        return 0.0
    return valid_count / total_raw

def save_valid_label_proportion(proportion: float, output_path: Path) -> None:
    """Save valid label proportion to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({"valid_label_proportion": proportion}, f)

def merge_metadata_files(files: List[Path], output_path: Path) -> None:
    """Merge multiple metadata JSON files into one."""
    merged = {}
    for f in files:
        if f.exists():
            with open(f, 'r') as fh:
                merged.update(json.load(fh))
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(merged, f, indent=2)

def main():
    """Main entry point for ingestion pipeline."""
    logger = get_logger(__name__)
    logger.info("Starting ingestion pipeline")
    
    # Load config
    config = DataSourceConfig()
    validate_scope(config)
    
    # Define paths
    raw_path = get_path("data/raw", "adress_raw.csv") # Assuming raw download lands here or specified
    # Note: In a real run, the download step must happen first. 
    # This function assumes raw_path exists as per T012.
    
    if not raw_path.exists():
        logger.error(f"Raw data file not found: {raw_path}")
        # In a real pipeline, this would trigger download logic from T012
        raise FileNotFoundError("Raw data not found. Run download step first.")

    # 1. Count raw records (T012b)
    raw_count = count_raw_records_from_csv(raw_path)
    save_raw_record_count(raw_count, get_path("data/results", "raw_record_count.json"))
    
    # 2. Load and clean
    df = pd.read_csv(raw_path)
    if 'text' in df.columns:
        df['text'] = df['text'].apply(clean_transcript_text)
    
    # 3. Filter records (T014)
    exclusions_path = get_path("data/interim", "exclusions.log")
    df_filtered, excluded_list = extract_metadata_and_log_exclusions(df, exclusions_path)
    
    # 4. Save intermediate cleaned dataset (T016 precursor)
    # The task T014 specifically asks for filtering and logging. 
    # T016 will take this filtered DF and save to cleaned_adress.csv.
    # We save the filtered DF here to be consumed by T016 or main flow.
    interim_path = get_path("data/interim", "cleaned_transcripts.csv")
    df_filtered.to_csv(interim_path, index=False)
    logger.info(f"Saved filtered data to {interim_path}")
    
    # 5. Low power check (T012e)
    validate_dataset_size(df_filtered, get_path("data/results", "metadata_partial_e.json"))
    
    # 6. Success criterion (T012h)
    valid_proportion = calculate_valid_label_proportion(raw_count, len(df_filtered))
    save_valid_label_proportion(valid_proportion, get_path("data/results", "metadata_partial_h.json"))
    
    # 7. Merge metadata (T012g)
    merge_metadata_files([
        get_path("data/results", "metadata_partial_e.json"),
        get_path("data/results", "metadata_partial_h.json")
    ], get_path("data/results", "metadata.json"))
    
    logger.info("Ingestion pipeline completed successfully")

if __name__ == "__main__":
    main()