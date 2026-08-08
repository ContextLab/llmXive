import os
import hashlib
import logging
import requests
import pandas as pd
from pathlib import Path
from datasets import load_dataset
import yaml

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state file path
STATE_FILE = Path("state/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m.yaml")

def calculate_sha256(filepath):
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url, output_path, timeout=300):
    """Download a file from a URL with progress logging."""
    logger.info(f"Downloading {url} to {output_path}")
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logger.info(f"Download complete: {output_path}")
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def verify_checksum(filepath, expected_hash):
    """Verify file checksum against expected hash."""
    actual_hash = calculate_sha256(filepath)
    return actual_hash == expected_hash

def load_huggingface_dataset(dataset_id, split="train", streaming=False):
    """
    Load a dataset from Hugging Face.
    If streaming=True, returns an iterable dataset to save memory.
    """
    try:
        logger.info(f"Loading HuggingFace dataset: {dataset_id} (split={split}, streaming={streaming})")
        ds = load_dataset(dataset_id, split=split, streaming=streaming)
        return ds
    except Exception as e:
        logger.error(f"Failed to load HuggingFace dataset {dataset_id}: {e}")
        raise

def download_oqmd_constitution(output_path=None):
    """Download OQMD dataset from Hugging Face."""
    if output_path is None:
        output_path = Path("data/raw/oqmd.parquet")
    else:
        output_path = Path(output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        ds = load_huggingface_dataset("oqmd/oqmd-dataset", split="train")
        # Convert to pandas and save as parquet
        # Note: If dataset is large, we might need to stream and chunk
        # For now, assuming it fits in memory or we take a sample if too large
        # The task requires real data, so we attempt full load first
        try:
            df = ds.to_pandas()
            df.to_parquet(output_path, index=False)
            logger.info(f"OQMD dataset saved to {output_path}")
            return str(output_path)
        except Exception as e:
            logger.warning(f"Full dataset too large to load into memory: {e}")
            logger.info("Attempting to stream and save first 100,000 rows as a representative sample...")
            count = 0
            max_rows = 100000
            dfs = []
            for item in ds:
                if count >= max_rows:
                    break
                dfs.append(pd.DataFrame([item]))
                count += 1
            if dfs:
                df_sample = pd.concat(dfs, ignore_index=True)
                df_sample.to_parquet(output_path, index=False)
                logger.info(f"Saved {count} rows to {output_path}")
                return str(output_path)
            else:
                raise RuntimeError("Failed to retrieve any data from OQMD dataset")
    except Exception as e:
        logger.error(f"Failed to download OQMD dataset: {e}")
        raise

def download_aflow_constitution(output_path=None):
    """Download AFLOW dataset from Hugging Face."""
    if output_path is None:
        output_path = Path("data/raw/aflow.parquet")
    else:
        output_path = Path(output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        ds = load_huggingface_dataset("aflow/aflow-dataset", split="train")
        try:
            df = ds.to_pandas()
            df.to_parquet(output_path, index=False)
            logger.info(f"AFLOW dataset saved to {output_path}")
            return str(output_path)
        except Exception as e:
            logger.warning(f"Full dataset too large to load into memory: {e}")
            logger.info("Attempting to stream and save first 100,000 rows as a representative sample...")
            count = 0
            max_rows = 100000
            dfs = []
            for item in ds:
                if count >= max_rows:
                    break
                dfs.append(pd.DataFrame([item]))
                count += 1
            if dfs:
                df_sample = pd.concat(dfs, ignore_index=True)
                df_sample.to_parquet(output_path, index=False)
                logger.info(f"Saved {count} rows to {output_path}")
                return str(output_path)
            else:
                raise RuntimeError("Failed to retrieve any data from AFLOW dataset")
    except Exception as e:
        logger.error(f"Failed to download AFLOW dataset: {e}")
        raise

def download_materials_project_constitution(output_path=None):
    """
    Download Materials Project dataset if API key is available.
    If no API key or fetch fails, log warning and skip (do not raise error).
    Output: data/raw/mp.parquet
    """
    if output_path is None:
        output_path = Path("data/raw/mp.parquet")
    else:
        output_path = Path(output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    mp_api_key = os.getenv("MP_API_KEY")
    if not mp_api_key:
        logger.warning("MP_API_KEY environment variable not found. Skipping Materials Project dataset download.")
        return None
    
    try:
        # Try Hugging Face first
        logger.info("Attempting to load Materials Project dataset from Hugging Face...")
        try:
            ds = load_huggingface_dataset("materials_project/mp-dataset", split="train")
            try:
                df = ds.to_pandas()
                df.to_parquet(output_path, index=False)
                logger.info(f"Materials Project dataset saved to {output_path}")
                return str(output_path)
            except Exception as e:
                logger.warning(f"Full dataset too large to load into memory: {e}")
                logger.info("Attempting to stream and save first 100,000 rows as a representative sample...")
                count = 0
                max_rows = 100000
                dfs = []
                for item in ds:
                    if count >= max_rows:
                        break
                    dfs.append(pd.DataFrame([item]))
                    count += 1
                if dfs:
                    df_sample = pd.concat(dfs, ignore_index=True)
                    df_sample.to_parquet(output_path, index=False)
                    logger.info(f"Saved {count} rows to {output_path}")
                    return str(output_path)
                else:
                    raise RuntimeError("Failed to retrieve any data from MP dataset")
        except Exception as hf_error:
            logger.warning(f"HuggingFace load failed: {hf_error}. Attempting raw API endpoint...")
            # Fallback to raw API if HF fails
            # Note: This is a simplified example; real implementation would need proper API handling
            url = "https://materialsproject.org/rest/v2/materials?api_key=" + mp_api_key
            # For demonstration, we assume the HF dataset exists as per task description
            # If HF fails and raw API is not implemented in detail, we log and return None
            logger.error("Raw API endpoint fallback not fully implemented for this task. Skipping MP dataset.")
            return None
    except Exception as e:
        logger.error(f"Failed to download Materials Project dataset: {e}")
        # Per task spec: log warning and skip, do not raise error
        logger.warning("Skipping Materials Project dataset due to persistent failure.")
        return None

def generate_checksum_file(file_path, checksum_file_path=None):
    """Generate a checksum file in sha256sum format."""
    if checksum_file_path is None:
        checksum_file_path = str(file_path) + ".sha256"
    
    file_hash = calculate_sha256(file_path)
    filename = os.path.basename(file_path)
    
    with open(checksum_file_path, 'w') as f:
        f.write(f"{file_hash}  {filename}\n")
    
    logger.info(f"Checksum file generated: {checksum_file_path}")
    return file_hash

def update_state_file(checksums):
    """
    Update the project state YAML file with artifact hashes.
    checksums: dict mapping artifact name to hash
    """
    if not STATE_FILE.exists():
        logger.warning(f"State file {STATE_FILE} does not exist. Creating new one.")
        state_data = {
            "project_id": "PROJ-756-assessing-dataset-imbalance-effects-on-m",
            "artifact_hashes": {}
        }
    else:
        with open(STATE_FILE, 'r') as f:
            state_data = yaml.safe_load(f)
        if state_data is None:
            state_data = {
                "project_id": "PROJ-756-assessing-dataset-imbalance-effects-on-m",
                "artifact_hashes": {}
            }
    
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
    
    for name, hash_val in checksums.items():
        state_data["artifact_hashes"][name] = hash_val
    
    with open(STATE_FILE, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)
    
    logger.info(f"State file updated: {STATE_FILE}")

def main():
    """Main entry point for downloading datasets."""
    logger.info("Starting dataset download process...")
    
    # Ensure data/raw directory exists
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    checksums = {}
    
    # Download OQMD
    try:
        oqmd_path = download_oqmd_constitution()
        if oqmd_path:
            oqmd_hash = generate_checksum_file(oqmd_path)
            checksums["oqmd.parquet"] = oqmd_hash
    except Exception as e:
        logger.error(f"OQMD download failed: {e}")
    
    # Download AFLOW
    try:
        aflow_path = download_aflow_constitution()
        if aflow_path:
            aflow_hash = generate_checksum_file(aflow_path)
            checksums["aflow.parquet"] = aflow_hash
    except Exception as e:
        logger.error(f"AFLOW download failed: {e}")
    
    # Download Materials Project (optional, skips if no key/fails)
    mp_path = download_materials_project_constitution()
    if mp_path:
        mp_hash = generate_checksum_file(mp_path)
        checksums["mp.parquet"] = mp_hash
    else:
        logger.info("Materials Project dataset not downloaded (skipped).")
    
    # Update state file with checksums
    if checksums:
        update_state_file(checksums)
    
    logger.info("Dataset download process completed.")
    return checksums

if __name__ == "__main__":
    main()