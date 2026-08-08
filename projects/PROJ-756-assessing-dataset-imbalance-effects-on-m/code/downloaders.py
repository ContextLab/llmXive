"""
Downloaders for OQMD, AFLOW, and Materials Project datasets.
Implements 'Fail Loudly' logic: raises DataFetchError on persistent failure.
No synthetic fallback is ever used.
"""
import os
import hashlib
import logging
import requests
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
from datasets import load_dataset
import yaml

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Custom exception for data fetching failures."""
    pass

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: str, timeout: int = 300) -> None:
    """Download a file from a URL with error handling."""
    logger.info(f"Downloading from {url} to {dest_path}")
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logger.info(f"Successfully downloaded {dest_path}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        raise DataFetchError(f"Failed to download {url}: {e}") from e

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """Verify file checksum against expected value."""
    actual_checksum = calculate_sha256(file_path)
    return actual_checksum == expected_checksum

def load_huggingface_dataset(dataset_id: str, split: str = "train") -> pd.DataFrame:
    """
    Load a dataset from Hugging Face.
    Raises DataFetchError if the dataset cannot be loaded.
    """
    logger.info(f"Loading dataset {dataset_id} from Hugging Face")
    try:
        dataset = load_dataset(dataset_id, split=split)
        df = dataset.to_pandas()
        logger.info(f"Successfully loaded {len(df)} rows from {dataset_id}")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id} from Hugging Face: {e}")
        raise DataFetchError(f"Failed to load dataset {dataset_id} from Hugging Face: {e}") from e

def download_oqmd_constitution(output_path: str, hf_id: str = "oqmd/oqmd-dataset", fallback_url: Optional[str] = None) -> None:
    """
    Download OQMD dataset.
    1. Try Hugging Face.
    2. If HF fails, try fallback URL (if provided).
    3. If both fail, raise DataFetchError.
    """
    logger.info(f"Attempting to download OQMD dataset to {output_path}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Try Hugging Face first
    try:
        df = load_huggingface_dataset(hf_id, split="train")
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved OQMD dataset to {output_path}")
        return
    except DataFetchError as e:
        logger.warning(f"HF download failed for OQMD: {e}")
    
    # Fallback to URL if provided
    if fallback_url:
        logger.info(f"Attempting fallback URL for OQMD: {fallback_url}")
        try:
            temp_path = output_path + ".tmp"
            download_file(fallback_url, temp_path)
            # Basic validation: try to read as parquet
            df = pd.read_parquet(temp_path)
            df.to_parquet(output_path, index=False)
            os.remove(temp_path)
            logger.info(f"Saved OQMD dataset from fallback URL to {output_path}")
            return
        except Exception as e:
            logger.error(f"Fallback URL download failed for OQMD: {e}")
    
    # If we reach here, both methods failed
    raise DataFetchError(f"Failed to download OQMD dataset from both HF and fallback URL")

def download_aflow_constitution(output_path: str, hf_id: str = "aflow/aflow-dataset", fallback_url: Optional[str] = None) -> None:
    """
    Download AFLOW dataset.
    1. Try Hugging Face.
    2. If HF fails, try fallback URL (if provided).
    3. If both fail, raise DataFetchError.
    """
    logger.info(f"Attempting to download AFLOW dataset to {output_path}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Try Hugging Face first
    try:
        df = load_huggingface_dataset(hf_id, split="train")
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved AFLOW dataset to {output_path}")
        return
    except DataFetchError as e:
        logger.warning(f"HF download failed for AFLOW: {e}")
    
    # Fallback to URL if provided
    if fallback_url:
        logger.info(f"Attempting fallback URL for AFLOW: {fallback_url}")
        try:
            temp_path = output_path + ".tmp"
            download_file(fallback_url, temp_path)
            # Basic validation: try to read as parquet
            df = pd.read_parquet(temp_path)
            df.to_parquet(output_path, index=False)
            os.remove(temp_path)
            logger.info(f"Saved AFLOW dataset from fallback URL to {output_path}")
            return
        except Exception as e:
            logger.error(f"Fallback URL download failed for AFLOW: {e}")
    
    # If we reach here, both methods failed
    raise DataFetchError(f"Failed to download AFLOW dataset from both HF and fallback URL")

def download_materials_project(output_path: str, hf_id: str = "materials_project/mp-dataset", fallback_url: Optional[str] = None) -> None:
    """
    Download Materials Project dataset.
    If no API key is available or fetch fails, log a warning and skip (do not raise error).
    """
    logger.info(f"Attempting to download Materials Project dataset to {output_path}")
    
    # Check for API key
    mp_api_key = os.getenv("MATERIALS_PROJECT_API_KEY")
    if not mp_api_key:
        logger.warning("Materials Project API key not found. Skipping MP download.")
        return
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Try Hugging Face first
    try:
        df = load_huggingface_dataset(hf_id, split="train")
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved Materials Project dataset to {output_path}")
        return
    except Exception as e:
        logger.warning(f"HF download failed for MP: {e}")
    
    # Fallback to URL if provided
    if fallback_url:
        logger.info(f"Attempting fallback URL for MP: {fallback_url}")
        try:
            temp_path = output_path + ".tmp"
            download_file(fallback_url, temp_path)
            df = pd.read_parquet(temp_path)
            df.to_parquet(output_path, index=False)
            os.remove(temp_path)
            logger.info(f"Saved Materials Project dataset from fallback URL to {output_path}")
            return
        except Exception as e:
            logger.error(f"Fallback URL download failed for MP: {e}")
    
    logger.warning("Failed to download Materials Project dataset from both HF and fallback URL. Skipping.")

def generate_checksum_file(file_path: str, checksum_file_path: str) -> None:
    """Generate a checksum file in sha256sum format."""
    checksum = calculate_sha256(file_path)
    filename = os.path.basename(file_path)
    with open(checksum_file_path, 'w') as f:
        f.write(f"{checksum}  {filename}\n")
    logger.info(f"Generated checksum file: {checksum_file_path}")

def update_state_file(state_path: str, artifact_name: str, checksum: str) -> None:
    """Update the project state YAML file with artifact checksums."""
    import yaml
    
    state_dir = os.path.dirname(state_path)
    if state_dir:
        os.makedirs(state_dir, exist_ok=True)
    
    state = {}
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}
    
    state['artifact_hashes'][artifact_name] = checksum
    
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    logger.info(f"Updated state file with checksum for {artifact_name}")

def main():
    """Main function to download all datasets."""
    # Define paths
    raw_data_dir = Path("data/raw")
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    oqmd_path = raw_data_dir / "oqmd.parquet"
    aflow_path = raw_data_dir / "aflow.parquet"
    mp_path = raw_data_dir / "mp.parquet"
    
    state_path = Path("state/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m.yaml")
    
    # Download OQMD
    try:
        download_oqmd_constitution(str(oqmd_path))
        oqmd_checksum = calculate_sha256(str(oqmd_path))
        generate_checksum_file(str(oqmd_path), str(raw_data_dir / "oqmd.parquet.sha256"))
        update_state_file(str(state_path), "oqmd.parquet", oqmd_checksum)
    except DataFetchError as e:
        logger.error(f"OQMD download failed: {e}")
        raise  # Re-raise to indicate failure
    
    # Download AFLOW
    try:
        download_aflow_constitution(str(aflow_path))
        aflow_checksum = calculate_sha256(str(aflow_path))
        generate_checksum_file(str(aflow_path), str(raw_data_dir / "aflow.parquet.sha256"))
        update_state_file(str(state_path), "aflow.parquet", aflow_checksum)
    except DataFetchError as e:
        logger.error(f"AFLOW download failed: {e}")
        raise  # Re-raise to indicate failure
    
    # Download Materials Project (optional, skip on failure)
    try:
        download_materials_project(str(mp_path))
        if mp_path.exists():
            mp_checksum = calculate_sha256(str(mp_path))
            generate_checksum_file(str(mp_path), str(raw_data_dir / "mp.parquet.sha256"))
            update_state_file(str(state_path), "mp.parquet", mp_checksum)
    except Exception as e:
        logger.error(f"MP download failed: {e}")
        # Do not raise, as MP is optional
    
    logger.info("All dataset downloads completed.")

if __name__ == "__main__":
    main()