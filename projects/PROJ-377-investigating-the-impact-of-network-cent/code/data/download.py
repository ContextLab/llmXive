"""
Dataset Download Module (US1).

Implements T011: Dataset download script using openneuro-cli.
"""
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional

from utils.config import get_config, get_dataset_config
from utils.logging import setup_logger

logger = setup_logger(__name__)

def download_dataset(dataset_id: str = "ds000030", output_dir: Optional[str] = None) -> str:
    """
    Downloads a dataset from OpenNeuro using the openneuro-cli tool.
    
    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds000030').
        output_dir: Directory to download the dataset to. If None, uses config.
        
    Returns:
        Path to the downloaded dataset directory.
        
    Raises:
        RuntimeError: If the download command fails.
        FileNotFoundError: If openneuro-cli is not installed.
    """
    cfg = get_config()
    if output_dir is None:
        output_dir = cfg.data.raw_dir
        
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Starting download of {dataset_id} to {output_dir}")
    
    # Check if openneuro-cli is available
    try:
        subprocess.run(["openneuro", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("openneuro-cli is not installed or not in PATH. Please install it via: pip install openneuro-cli")
        # For the purpose of the integration test, we might want to simulate this
        # But in a real run, we must fail loudly.
        # However, the task says "Real data only". If we can't download, we fail.
        # But for the test to pass in a CI environment without network, we might need a mock.
        # The test file T010 mocks this function. So here we implement the REAL logic.
        raise RuntimeError("openneuro-cli not found. Please install it.")
    
    # Construct command
    # openneuro download --dataset ds000030 --output-dir <path>
    cmd = [
        "openneuro", "download",
        "--dataset", dataset_id,
        "--output-dir", output_dir
    ]
    
    try:
        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Download successful: {result.stdout}")
        
        # Verify download
        dataset_path = os.path.join(output_dir, dataset_id)
        if os.path.exists(dataset_path):
            logger.info(f"Dataset verified at {dataset_path}")
            return dataset_path
        else:
            # Sometimes the tool creates a subfolder named differently or the path is direct
            # Check if the directory exists directly in output_dir
            possible_paths = [
                os.path.join(output_dir, dataset_id),
                os.path.join(output_dir, dataset_id.split("-")[0] if "-" in dataset_id else dataset_id)
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    return p
            
            logger.error(f"Downloaded files not found in expected location: {output_dir}")
            raise FileNotFoundError(f"Dataset not found after download: {output_dir}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Download failed: {e.stderr}")
        raise RuntimeError(f"Download failed: {e.stderr}")

if __name__ == "__main__":
    config = get_config()
    # Example usage
    # path = download_dataset("ds000030")
    # print(f"Downloaded to: {path}")
    print("Download module loaded.")
