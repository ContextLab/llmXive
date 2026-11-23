import os
import hashlib
import json
import time
import requests
from pathlib import Path
import pandas as pd
import numpy as np
from .logging_config import get_logger

logger = get_logger(__name__)

def calculate_file_checksum(filepath: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksum(checksum: str, filepath: str):
    """Save checksum to a .sha256 file."""
    checksum_path = f"{filepath}.sha256"
    with open(checksum_path, "w") as f:
        f.write(checksum)

def verify_existing_verification(verification_file: str) -> bool:
    """Check if dataset verification file exists and is valid."""
    if not os.path.exists(verification_file):
        return False
    try:
        with open(verification_file, 'r') as f:
            data = json.load(f)
            return data.get('status') == 'PASS'
    except Exception:
        return False

def fetch_emp_agricultural_samples(output_file: str, min_samples: int = 100):
    """
    Fetch EMP agricultural samples.
    Since real EMP download via Qiita is complex and may require authentication,
    we simulate the fetch from a verified local source or fail loudly if not available.
    
    NOTE: In a real scenario, this would use the Qiita API or download from a verified mirror.
    For this implementation, we assume T012 verified the source and we have a local copy or a real URL.
    If the real URL fails, we raise an error.
    """
    # Simulated real URL for demonstration (replace with actual verified URL from T012)
    # In production, this would be: https://qiita.ucsd.edu/static/download/emp_agricultural_subset.csv
    real_url = "https://raw.githubusercontent.com/llmXive/datasets/main/emp_agricultural_samples.csv"
    
    try:
        logger.info(f"Fetching EMP agricultural samples from {real_url}...")
        response = requests.get(real_url, timeout=30)
        response.raise_for_status()
        
        # Parse CSV from text
        df = pd.read_csv(pd.io.common.StringIO(response.text))
        
        if len(df) < min_samples:
            logger.warning(f"Only {len(df)} samples found, expected at least {min_samples}")
        
        # Ensure output directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        
        logger.info(f"Saved {len(df)} EMP samples to {output_file}")
        calculate_file_checksum(output_file)
        
    except Exception as e:
        logger.error(f"Failed to fetch EMP samples: {str(e)}")
        raise RuntimeError(f"EMP data acquisition failed: {str(e)}")

def fetch_mg_rast_soil_samples(output_file: str, min_samples: int = 100):
    """
    Fetch MG-RAST soil samples.
    Similar to EMP, this would use the MG-RAST API.
    """
    real_url = "https://raw.githubusercontent.com/llmXive/datasets/main/mg-rast_soil_samples.csv"
    
    try:
        logger.info(f"Fetching MG-RAST soil samples from {real_url}...")
        response = requests.get(real_url, timeout=30)
        response.raise_for_status()
        
        df = pd.read_csv(pd.io.common.StringIO(response.text))
        
        if len(df) < min_samples:
            logger.warning(f"Only {len(df)} samples found, expected at least {min_samples}")
        
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        
        logger.info(f"Saved {len(df)} MG-RAST samples to {output_file}")
        calculate_file_checksum(output_file)
        
    except Exception as e:
        logger.error(f"Failed to fetch MG-RAST samples: {str(e)}")
        raise RuntimeError(f"MG-RAST data acquisition failed: {str(e)}")

def fetch_disease_incidence_records(output_file: str, min_records: int = 50):
    """
    Fetch disease incidence records.
    This function downloads the disease incidence data required for matching.
    """
    # Real URL placeholder (replace with actual verified source)
    real_url = "https://raw.githubusercontent.com/llmXive/datasets/main/disease_incidence_records.csv"
    
    try:
        logger.info(f"Fetching disease incidence records from {real_url}...")
        response = requests.get(real_url, timeout=30)
        response.raise_for_status()
        
        df = pd.read_csv(pd.io.common.StringIO(response.text))
        
        if len(df) < min_records:
            logger.warning(f"Only {len(df)} records found, expected at least {min_records}")
        
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        
        logger.info(f"Saved {len(df)} disease records to {output_file}")
        calculate_file_checksum(output_file)
        
    except Exception as e:
        logger.error(f"Failed to fetch disease incidence records: {str(e)}")
        raise RuntimeError(f"Disease data acquisition failed: {str(e)}")

def augment_with_required_metadata(df: pd.DataFrame, metadata_source: str) -> pd.DataFrame:
    """Augment dataframe with required metadata from a source."""
    # Placeholder for metadata augmentation logic
    return df

def generate_synthetic_samples(count: int = 100):
    """
    GENERATE SYNTHETIC SAMPLES - ONLY FOR TESTING WHEN REAL DATA IS UNAVAILABLE.
    This should NOT be used in production data acquisition.
    """
    logger.warning("Generating synthetic samples for testing only!")
    data = {
        'sample_id': [f'SYN-{i:03d}' for i in range(count)],
        'gps_latitude': np.random.uniform(25, 48, count),
        'gps_longitude': np.random.uniform(-125, -70, count),
        'collection_date': pd.date_range(start='2023-01-01', periods=count, freq='D'),
        'plant_species': np.random.choice(['Corn', 'Wheat', 'Soybean', 'Cotton'], count),
        'soil_type': np.random.choice(['Loamy', 'Sandy', 'Clay', 'Silt'], count)
    }
    return pd.DataFrame(data)

def run_data_acquisition():
    """Run the full data acquisition pipeline."""
    project_root = Path(__file__).parent.parent.parent
    emp_output = project_root / "data" / "raw" / "emp_agricultural_samples.csv"
    mg_output = project_root / "data" / "raw" / "mg-rast_soil_samples.csv"
    disease_output = project_root / "data" / "raw" / "disease_incidence_records.csv"
    
    verification_file = project_root / "data" / "processed" / "dataset_verification.json"
    
    if not verify_existing_verification(str(verification_file)):
        raise RuntimeError("Dataset verification (T012) has not passed. Cannot proceed with download.")
    
    fetch_emp_agricultural_samples(str(emp_output))
    fetch_mg_rast_soil_samples(str(mg_output))
    fetch_disease_incidence_records(str(disease_output))
    
    logger.info("Data acquisition completed successfully.")

if __name__ == "__main__":
    run_data_acquisition()
