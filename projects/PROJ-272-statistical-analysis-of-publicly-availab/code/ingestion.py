"""
Ingestion module for downloading and preprocessing ADReSS dataset.
"""
import hashlib
import json
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import requests
from tqdm import tqdm
from config import DataSourceConfig, get_path, ensure_dirs
from utils import normalize_text, validate_text_length

# Configure logging
logger = logging.getLogger(__name__)

def download_file(url: str, dest_path: Path, desc: str = "Downloading") -> bool:
    """
    Download a file from a URL with progress bar and retry logic.
    
    Args:
        url: The URL to download from
        dest_path: The destination path
        desc: Description for progress bar
        
    Returns:
        True if successful, False otherwise
    """
    try:
        ensure_dirs(dest_path.parent)
        
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(dest_path, 'wb') as f, tqdm(
            desc=desc,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        logger.info(f"Downloaded {dest_path.name} ({total_size} bytes)")
        return True
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def record_checksums(file_path: Path, checksum_path: Path) -> None:
    """Record file checksums to a JSON file."""
    checksums = {}
    if checksum_path.exists():
        with open(checksum_path, 'r') as f:
            checksums = json.load(f)
    
    checksums[file_path.name] = compute_sha256(file_path)
    
    with open(checksum_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def validate_scope(config: DataSourceConfig) -> None:
    """
    Validate that the dataset source is ADReSS and not DementiaBank.
    
    Args:
        config: The data source configuration
        
    Raises:
        ValueError: If DementiaBank is detected or source is missing
    """
    # Use getattr for compatibility with both old and new config structures
    source = getattr(config, 'source', None) or getattr(config, 'dataset_source', None)
    
    if source is None:
        raise ValueError("DATASET_SOURCE is not configured. Please set it in config.py.")
    
    if source != "ADReSS":
        raise ValueError(f"Invalid dataset source: {source}. Only ADReSS is supported per project scope.")
    
    logger.info(f"Scope validated: {source} is the only allowed dataset.")

def clean_transcript_text(text: str) -> str:
    """
    Clean transcript text by removing non-verbal annotations and normalizing.
    
    Args:
        text: Raw transcript text
        
    Returns:
        Cleaned text
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove non-verbal annotations (e.g., <laughter>, <pause>, <silence>)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Normalize to UTF-8 (handled by pandas read_csv, but ensure here)
    text = normalize_text(text)
    
    return text.strip()

def parse_cognitive_status(filename: str) -> str:
    """
    Parse cognitive status from filename.
    
    Args:
        filename: The filename of the transcript
        
    Returns:
        One of 'Control', 'MCI', 'AD'
    """
    filename_lower = filename.lower()
    
    if re.search(r'control|cnt', filename_lower):
        return 'Control'
    elif re.search(r'mci|mild', filename_lower):
        return 'MCI'
    elif re.search(r'\bad\b|dementia', filename_lower):
        return 'AD'
    
    return 'Unknown'

def extract_metadata_and_log_exclusions(
    df: pd.DataFrame, 
    exclusion_log_path: Path
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Extract metadata and log exclusions.
    Delegates to t015_metadata_extraction for actual implementation.
    """
    from t015_metadata_extraction import extract_metadata_and_log_exclusions as impl
    return impl(df, exclusion_log_path)

def count_raw_records_from_csv(csv_path: Path) -> Dict[str, int]:
    """
    Count raw records in the downloaded dataset.
    
    Args:
        csv_path: Path to the raw CSV file
        
    Returns:
        Dictionary with counts by group
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Raw CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    counts = {
        'total': len(df),
        'Control': 0,
        'MCI': 0,
        'AD': 0
    }
    
    if 'label' in df.columns:
        counts['Control'] = (df['label'] == 'Control').sum()
        counts['MCI'] = (df['label'] == 'MCI').sum()
        counts['AD'] = (df['label'] == 'AD').sum()
    
    return counts

def save_raw_record_count(counts: Dict[str, int], output_path: Path) -> None:
    """Save raw record count to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({'raw_count': counts['total']}, f, indent=2)

def validate_dataset_size(df: pd.DataFrame, min_records: int = 10) -> bool:
    """Validate dataset has sufficient records."""
    return len(df) >= min_records

def calculate_valid_label_proportion(
    raw_count: int, 
    filtered_count: int
) -> float:
    """Calculate proportion of valid labels."""
    if raw_count == 0:
        return 0.0
    return filtered_count / raw_count

def save_valid_label_proportion(
    proportion: float, 
    output_path: Path
) -> None:
    """Save valid label proportion to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({'valid_label_proportion': proportion}, f, indent=2)

def merge_metadata_files(
    raw_count_path: Path,
    filtered_count: int,
    group_counts: Dict[str, int],
    output_path: Path
) -> None:
    """Merge metadata files into a single summary."""
    raw_count = 0
    if raw_count_path.exists():
        with open(raw_count_path, 'r') as f:
            data = json.load(f)
            raw_count = data.get('raw_count', 0)
    
    valid_label_proportion = calculate_valid_label_proportion(raw_count, filtered_count)
    
    metadata = {
        'raw_count': raw_count,
        'filtered_count': filtered_count,
        'valid_label_proportion': valid_label_proportion,
        'group_counts': group_counts
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)

def main():
    """Main entry point for ingestion pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(get_path('data/interim', 'ingestion.log')),
            logging.StreamHandler()
        ]
    )
    
    logger.info("Starting ADReSS ingestion pipeline")
    
    # Load config and validate scope
    from config import DataSourceConfig
    config = DataSourceConfig()
    validate_scope(config)
    
    # Define paths
    raw_data_dir = get_path('data/raw')
    interim_dir = get_path('data/interim')
    results_dir = get_path('data/results')
    
    # Ensure directories exist
    ensure_dirs(raw_data_dir)
    ensure_dirs(interim_dir)
    ensure_dirs(results_dir)
    
    # Download ADReSS dataset
    # Primary URL (GitHub)
    primary_url = "https://github.com/cocacola-lab/ADReSS/raw/master/data/ADReSS_challenge.zip"
    # Mirror URL (Zenodo)
    mirror_url = "https://zenodo.org/record/3735249/files/ADReSS_challenge.zip"
    
    zip_path = raw_data_dir / "ADReSS_challenge.zip"
    extracted_path = raw_data_dir / "ADReSS_challenge"
    
    # Attempt primary download
    if not zip_path.exists():
        logger.info(f"Attempting download from primary URL: {primary_url}")
        if not download_file(primary_url, zip_path, "Downloading ADReSS (Primary)"):
            logger.warning("Primary download failed, trying mirror...")
            if not download_file(mirror_url, zip_path, "Downloading ADReSS (Mirror)"):
                raise ConnectionError("ADReSS download failed. No synthetic fallback.")
    
    # Extract if needed
    if not extracted_path.exists():
        logger.info(f"Extracting {zip_path}")
        shutil.unpack_archive(zip_path, extracted_path)
    
    # Find CSV files
    csv_files = list(extracted_path.rglob("*.csv"))
    if not csv_files:
        # Try to find transcripts and create a combined CSV
        transcript_files = list(extracted_path.rglob("*.txt"))
        if transcript_files:
            logger.info("Creating CSV from transcript files...")
            records = []
            for txt_file in transcript_files:
                with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                records.append({
                    'participant_id': txt_file.stem,
                    'filename': txt_file.name,
                    'text': text,
                    'label': parse_cognitive_status(txt_file.name)
                })
            df = pd.DataFrame(records)
            csv_path = raw_data_dir / "ADReSS_combined.csv"
            df.to_csv(csv_path, index=False)
            csv_files = [csv_path]
        else:
            raise FileNotFoundError("No CSV or TXT files found in ADReSS dataset")
    
    # Process the first CSV file found
    csv_path = csv_files[0]
    logger.info(f"Processing {csv_path}")
    
    # Count raw records
    raw_counts = count_raw_records_from_csv(csv_path)
    save_raw_record_count(raw_counts, results_dir / "raw_record_count.json")
    logger.info(f"Raw record counts: {raw_counts}")
    
    # Load and clean data
    df = pd.read_csv(csv_path)
    
    # Clean text
    if 'text' in df.columns:
        df['text'] = df['text'].apply(clean_transcript_text)
    
    # Extract metadata and log exclusions
    exclusion_log_path = interim_dir / "exclusions.log"
    df, exclusions = extract_metadata_and_log_exclusions(df, exclusion_log_path)
    
    # Filter records (T014 logic)
    if 'label' in df.columns:
        df = df[df['label'].notna() & (df['label'] != '')]
    
    if 'text' in df.columns:
        df = df[df['text'].str.len() >= 50]
    
    # Save cleaned dataset
    cleaned_path = interim_dir / "cleaned_adress.csv"
    df.to_csv(cleaned_path, index=False)
    logger.info(f"Saved {len(df)} cleaned records to {cleaned_path}")
    
    # Save metadata
    group_counts = df['label'].value_counts().to_dict() if 'label' in df.columns else {}
    merge_metadata_files(
        results_dir / "raw_record_count.json",
        len(df),
        group_counts,
        results_dir / "metadata.json"
    )
    
    logger.info("Ingestion pipeline completed successfully")

if __name__ == '__main__':
    main()