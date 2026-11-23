import os
import json
import hashlib
import logging
import yaml
from typing import Dict, List, Set, Optional, Iterator, Any, Tuple
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq

from config import get_path_config, get_dataset_config
from utils.logger import get_logger, LlmXiveError

logger = get_logger(__name__)

class DataIntegrityError(LlmXiveError):
    """Raised when data integrity verification fails."""
    pass

def compute_file_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    if not path.exists():
        raise DataIntegrityError(f"File not found for checksum: {file_path}")
    
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksum_to_state(file_path: str, checksum: str) -> None:
    """Save checksum to state manifest."""
    state_dir = get_path_config().state_dir
    state_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = state_dir / "data_manifest.json"
    
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    
    filename = os.path.basename(file_path)
    manifest[filename] = {
        "checksum": checksum,
        "path": str(file_path),
        "updated_at": str(pd.Timestamp.now())
    }
    
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Checksum saved to manifest for {filename}")

def verify_checksum(file_path: str) -> bool:
    """Verify file checksum against state manifest."""
    path = Path(file_path)
    if not path.exists():
        raise DataIntegrityError(f"File missing for verification: {file_path}")
    
    filename = os.path.basename(file_path)
    state_dir = get_path_config().state_dir
    manifest_path = state_dir / "data_manifest.json"
    
    if not manifest_path.exists():
        raise DataIntegrityError(f"State manifest not found: {manifest_path}")
    
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    
    if filename not in manifest:
        raise DataIntegrityError(f"No checksum recorded for {filename} in manifest")
    
    recorded_checksum = manifest[filename]["checksum"]
    current_checksum = compute_file_checksum(file_path)
    
    if current_checksum != recorded_checksum:
        raise DataIntegrityError(
            f"Checksum mismatch for {filename}. "
            f"Expected: {recorded_checksum}, Got: {current_checksum}"
        )
    
    return True

def load_class_config(config_path: str) -> List[int]:
    """Load class configuration from YAML file."""
    path = Path(config_path)
    if not path.exists():
        raise LlmXiveError(f"Class config file not found: {config_path}")
    
    with open(path, "r") as f:
        config = yaml.safe_load(f)
    
    return config.get("subtle_classes", []) if "subtle_classes" in config else config.get("control_classes", [])

class FilteredAudioDataset:
    """Dataset wrapper for streaming filtered audio data."""
    def __init__(self, subset_path: str):
        self.subset_path = subset_path
        self.path = Path(subset_path)
        if not self.path.exists():
            raise DataIntegrityError(f"Subset file not found: {subset_path}")
        self.dataset = pq.read_table(self.subset_path).to_pandas()

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        for _, row in self.dataset.iterrows():
            yield row.to_dict()

    def __len__(self) -> int:
        return len(self.dataset)

class FilteredDataLoader:
    """Data loader with integrity verification."""
    def __init__(self, subset_path: str):
        self.subset_path = subset_path
        self._verify_integrity()
        self.dataset = FilteredAudioDataset(subset_path)

    def _verify_integrity(self) -> None:
        """Verify dataset integrity before loading."""
        processed_dir = get_path_config().processed_dir
        processed_dir.mkdir(parents=True, exist_ok=True)
        log_path = processed_dir / "integrity_log.txt"
        
        success = False
        error_msg = None
        
        try:
            if verify_checksum(self.subset_path):
                success = True
                logger.info(f"Integrity verification PASSED for {self.subset_path}")
            else:
                error_msg = "Checksum verification returned False"
        except DataIntegrityError as e:
            error_msg = str(e)
        except Exception as e:
            error_msg = f"Unexpected error during verification: {str(e)}"
        
        with open(log_path, "a") as f:
            timestamp = pd.Timestamp.now().isoformat()
            status = "PASSED" if success else "FAILED"
            f.write(f"[{timestamp}] {status}: {self.subset_path} - {error_msg or 'OK'}\n")
        
        if not success:
            raise DataIntegrityError(f"Data integrity check failed: {error_msg}")

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        return iter(self.dataset)

    def __len__(self) -> int:
        return len(self.dataset)

def main():
    """Main entry point for integrity verification."""
    config = get_dataset_config()
    subset_path = get_path_config().processed_dir / "subtle_cue_subset.parquet"
    
    if not subset_path.exists():
        logger.warning(f"Subset file not found: {subset_path}. Skipping verification.")
        return
    
    loader = FilteredDataLoader(str(subset_path))
    logger.info(f"Data loader initialized with {len(loader)} samples.")
    
    # Consume a small sample to ensure streamability
    count = 0
    for item in loader:
        count += 1
        if count >= 5:
            break
    logger.info(f"Verified streaming of {count} samples.")

if __name__ == "__main__":
    main()