import hashlib
import json
import logging
import os
import sys
import requests
from pathlib import Path
from typing import Optional

from utils.config import get_project_root, get_path, ensure_dir

logger = logging.getLogger(__name__)

def download_file(url: str, dest_path: Path) -> None:
    logger.info(f"Downloading {url} to {dest_path}")
    ensure_dir(dest_path)
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    logger.info(f"Downloaded to {dest_path}")

def download_videokr_sft() -> Path:
    url = "https://example.com/videokr_sft.csv" # Replace with real URL
    dest = get_path("data/raw/videokr_sft.csv")
    
    # In a real implementation, this would fetch from a verified source
    # For now, we assume the file exists or download fails loudly
    if not dest.exists():
        try:
            download_file(url, dest)
        except Exception as e:
            logger.error(f"Failed to download VideoKR-SFT: {e}")
            raise
    
    return dest

def download_knowledge_graph() -> Path:
    url = "https://example.com/knowledge_graph.json" # Replace with real URL
    dest = get_path("data/raw/knowledge_graph.json")
    
    if not dest.exists():
        try:
            download_file(url, dest)
        except Exception as e:
            logger.error(f"Failed to download Knowledge Graph: {e}")
            raise
    
    return dest

def verify_checksums() -> bool:
    from ingest.checksum import verify_all_raw_data
    return verify_all_raw_data()

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        logger.info("Downloading VideoKR-SFT...")
        videokr_path = download_videokr_sft()
        logger.info(f"VideoKR-SFT at {videokr_path}")
        
        logger.info("Downloading Knowledge Graph...")
        graph_path = download_knowledge_graph()
        logger.info(f"Knowledge Graph at {graph_path}")
        
        logger.info("Verifying checksums...")
        if verify_checksums():
            logger.info("Checksums verified.")
        else:
            logger.warning("Checksum verification failed.")
        
        logger.info("Data download complete.")
        
    except Exception as e:
        logger.error(f"Error in download_data main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
