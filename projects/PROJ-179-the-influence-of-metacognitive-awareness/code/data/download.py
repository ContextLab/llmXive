import os
import sys
import json
import logging
import hashlib
import requests
from pathlib import Path

# Import shared config utilities
from code.config.env_config import load_config, setup_logging

def log_info(msg):
    logging.info(msg)

def log_error(msg):
    logging.error(msg)

def calculate_sha256(filename):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filename, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_config_wrapper():
    """Load configuration safely."""
    try:
        return load_config()
    except Exception:
        return {}

def download_dataset():
    """
    Download a valid behavioral dataset.
    Tries multiple known public sources.
    """
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Known public datasets for metacognition research
    # Using a reliable, direct CSV source from a public repository
    urls = [
        "https://raw.githubusercontent.com/psychoinformatics-de/psychoinformatics-data/main/behavioral_metacognition_sample.csv",
        "https://raw.githubusercontent.com/psychopy/datasets/main/behavioral_metacognition_sample.csv",
        # Fallback to a generic public dataset if specific ones fail
        "https://raw.githubusercontent.com/llmXive/datasets/main/sample_behavioral_data.csv"
    ]
    
    expected_columns = ['participant_id', 'trial_id', 'stimulus_modality', 
                       'source_label', 'participant_response', 'confidence_rating']
    
    for url in urls:
        try:
            log_info(f"Attempting to download dataset from: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save to file
            filename = url.split("/")[-1]
            if not filename.endswith('.csv'):
                filename = "behavioral_data.csv"
            
            filepath = output_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Quick validation: check if file has content
            df = pd.read_csv(filepath)
            if all(col in df.columns for col in expected_columns):
                log_info(f"Successfully downloaded and validated: {filepath}")
                return filepath
            else:
                log_error(f"Downloaded file missing required columns. Trying next URL...")
                filepath.unlink() # Remove invalid file
                
        except Exception as e:
            log_error(f"Failed to download from {url}: {e}")
            continue
    
    log_error("ERROR: Could not download a valid behavioral dataset from any source.")
    log_error("Project blocked. No real data source available.")
    return None

def validate_checksum(filepath, expected_checksum=None):
    """Validate file checksum if provided."""
    if not expected_checksum:
        return True
    
    actual = calculate_sha256(filepath)
    return actual == expected_checksum

def main():
    """Main entry point for T005 download task."""
    config = load_config_wrapper()
    setup_logging(config)
    
    try:
        log_info("Starting data download (T005)...")
        
        filepath = download_dataset()
        
        if filepath:
            log_info("Download completed successfully.")
            return 0
        else:
            return 1
            
    except Exception as e:
        log_error(f"Download failed: {e}")
        return 1

if __name__ == "__main__":
    # Import pandas here to avoid circular import issues if any
    import pandas as pd
    sys.exit(main())
