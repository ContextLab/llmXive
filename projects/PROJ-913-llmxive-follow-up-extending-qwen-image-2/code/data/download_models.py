"""
Download Qwen-Image-2.0 and Qwen-Image-2.0-RL models from Hugging Face.

Implements retry logic with exponential backoff and limited attempts.
Outputs:
    - data/models/Qwen-Image-2.0/
    - data/models/Qwen-Image-2.0-RL/
"""
import os
import time
import sys
from pathlib import Path
from typing import Optional
import logging

from huggingface_hub import snapshot_download, HfFileSystem, hf_hub_download
from config import PROJECT_ROOT
from utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

# Configuration
MAX_RETRIES = 5
INITIAL_BACKOFF = 2.0  # seconds
MAX_BACKOFF = 60.0     # seconds
MODELS = [
    "Qwen/Qwen-Image-2.0",
    "Qwen/Qwen-Image-2.0-RL"
]

def exponential_backoff(attempt: int, initial: float, max_backoff: float) -> float:
    """Calculate exponential backoff time with jitter."""
    backoff = min(initial * (2 ** attempt), max_backoff)
    # Add small jitter to avoid thundering herd
    jitter = backoff * 0.1 * (hash(time.time()) % 100) / 100.0
    return backoff + jitter

def download_with_retry(
    repo_id: str,
    local_dir: Path,
    allow_patterns: Optional[list] = None,
    ignore_patterns: Optional[list] = None
) -> bool:
    """
    Download a Hugging Face repository with retry logic.
    
    Args:
        repo_id: Hugging Face repository ID
        local_dir: Local directory to download to
        allow_patterns: Patterns to include (e.g., "*.safetensors", "*.json")
        ignore_patterns: Patterns to exclude
    
    Returns:
        True if download succeeded, False otherwise
    """
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Attempting download of {repo_id} (attempt {attempt + 1}/{MAX_RETRIES})")
            
            snapshot_download(
                repo_id=repo_id,
                local_dir=str(local_dir),
                allow_patterns=allow_patterns,
                ignore_patterns=ignore_patterns,
                resume_download=True,
                force=False
            )
            
            logger.info(f"Successfully downloaded {repo_id}")
            return True
            
        except Exception as e:
            logger.warning(f"Download failed for {repo_id}: {str(e)}")
            
            if attempt < MAX_RETRIES - 1:
                backoff_time = exponential_backoff(attempt, INITIAL_BACKOFF, MAX_BACKOFF)
                logger.info(f"Retrying in {backoff_time:.2f} seconds...")
                time.sleep(backoff_time)
            else:
                logger.error(f"Max retries exceeded for {repo_id}")
                return False

def verify_download(local_dir: Path) -> bool:
    """
    Verify that the downloaded model directory contains expected files.
    
    Args:
        local_dir: Path to the downloaded model directory
    
    Returns:
        True if verification passes, False otherwise
    """
    required_files = [
        "config.json",
        "model_index.json"
    ]
    
    missing_files = []
    for req_file in required_files:
        if not (local_dir / req_file).exists():
            missing_files.append(req_file)
    
    if missing_files:
        logger.error(f"Missing required files in {local_dir}: {missing_files}")
        return False
    
    # Check for at least one weight file
    weight_files = list(local_dir.glob("*.safetensors")) + list(local_dir.glob("*.bin"))
    if not weight_files:
        logger.error(f"No weight files found in {local_dir}")
        return False
    
    logger.info(f"Verification passed for {local_dir} ({len(weight_files)} weight files found)")
    return True

def main():
    """Main entry point for model download."""
    logger.info("Starting model download process")
    
    models_dir = PROJECT_ROOT / "data" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    failure_count = 0
    
    for model_id in MODELS:
        # Create local directory name from repo ID
        repo_name = model_id.split("/")[-1]
        local_dir = models_dir / repo_name
        
        logger.info(f"Processing {model_id} -> {local_dir}")
        
        if local_dir.exists() and any(local_dir.iterdir()):
            logger.info(f"Directory {local_dir} already exists and is not empty. Verifying...")
            if verify_download(local_dir):
                logger.info(f"Skipping download for {model_id} - already present and verified")
                success_count += 1
                continue
            else:
                logger.warning(f"Directory {local_dir} exists but verification failed. Re-downloading...")
        
        # Download with retry logic
        if download_with_retry(
            repo_id=model_id,
            local_dir=local_dir
        ):
            if verify_download(local_dir):
                success_count += 1
            else:
                logger.error(f"Download completed but verification failed for {model_id}")
                failure_count += 1
        else:
            failure_count += 1
    
    logger.info(f"Download process completed: {success_count} succeeded, {failure_count} failed")
    
    if failure_count > 0:
        logger.error("Some models failed to download. Check logs for details.")
        sys.exit(1)
    
    logger.info("All models downloaded successfully")
    sys.exit(0)

if __name__ == "__main__":
    main()