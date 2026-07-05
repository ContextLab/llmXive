import os
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any

from src.utils.logging import get_logger

logger = get_logger()

def load_environment_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    if config_path is None:
        config_path = os.getenv("LLMXIVE_CONFIG", "data/metadata/config.json")
    
    path = Path(config_path)
    if not path.exists():
        logger.warning(f"Config file not found at {config_path}, using defaults.")
        return {}
    
    with open(path) as f:
        return json.load(f)

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_obj = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    try:
        actual_checksum = compute_file_checksum(file_path)
        return actual_checksum == expected_checksum
    except Exception as e:
        logger.error(f"Checksum verification failed for {file_path}: {e}")
        return False

def register_checksum(file_path: Path, checksum: str, manifest_path: Path):
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_dict = {}
    
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest_dict = json.load(f)
    
    manifest_dict[str(file_path)] = checksum
    
    with open(manifest_path, "w") as f:
        json.dump(manifest_dict, f, indent=2)
    
    logger.info(f"Registered checksum for {file_path}")

def verify_all_downloads(manifest_path: Path) -> bool:
    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        return False
    
    with open(manifest_path) as f:
        manifest_dict = json.load(f)
    
    all_valid = True
    for file_str, expected_checksum in manifest_dict.items():
        file_path = Path(file_str)
        if not file_path.exists():
            logger.error(f"File missing: {file_path}")
            all_valid = False
        elif not verify_checksum(file_path, expected_checksum):
            logger.error(f"Checksum mismatch for {file_path}")
            all_valid = False
    
    if all_valid:
        logger.info("All downloads verified successfully.")
    else:
        logger.warning("Some downloads failed verification.")
    
    return all_valid
