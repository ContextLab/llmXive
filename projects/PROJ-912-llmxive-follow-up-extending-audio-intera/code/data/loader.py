"""
Audio data loading with filtering, streaming, and integrity verification.
"""
import os
import json
import hashlib
import logging
import yaml
from typing import Dict, List, Set, Optional, Iterator, Any, Tuple
from pathlib import Path
import pandas as pd
from datasets import load_dataset
from config import get_path_config, get_dataset_config
from utils.logger import get_logger, LlmXiveError

logger = get_logger(__name__)

class DataIntegrityError(LlmXiveError):
    """Raised when data integrity verification fails."""
    pass

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        
    Returns:
        Hex digest of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file for checksum: {file_path}") from e

def save_checksum_to_state(file_path: Path, checksum: str, state_file: Optional[Path] = None) -> None:
    """
    Save a file checksum to the state manifest.
    
    Args:
        file_path: Path to the file.
        checksum: The computed checksum.
        state_file: Path to the state manifest file. Defaults to state/checksums.json.
    """
    path_config = get_path_config()
    if state_file is None:
        state_file = path_config.state_dir / "checksums.json"
    
    # Ensure state directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing checksums or create new dict
    if state_file.exists():
        try:
            with open(state_file, "r") as f:
                checksums = json.load(f)
        except (json.JSONDecodeError, IOError):
            checksums = {}
    else:
        checksums = {}
    
    # Update with new checksum
    checksums[file_path.name] = {
        "path": str(file_path),
        "checksum": checksum,
        "algorithm": "sha256"
    }
    
    # Atomic write
    temp_file = state_file.with_suffix(".tmp")
    with open(temp_file, "w") as f:
        json.dump(checksums, f, indent=2)
    temp_file.replace(state_file)
    logger.info(f"Saved checksum for {file_path.name} to {state_file}")

def verify_checksum(file_path: Path, state_file: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Verify a file's checksum against the state manifest.
    
    Args:
        file_path: Path to the file to verify.
        state_file: Path to the state manifest file. Defaults to state/checksums.json.
        
    Returns:
        Tuple of (is_valid, message).
        
    Raises:
        DataIntegrityError: If the file is missing or checksum mismatch.
    """
    path_config = get_path_config()
    if state_file is None:
        state_file = path_config.state_dir / "checksums.json"
    
    if not file_path.exists():
        msg = f"Data integrity check failed: File not found - {file_path}"
        raise DataIntegrityError(msg)
    
    if not state_file.exists():
        msg = f"Data integrity check failed: State manifest not found - {state_file}. Cannot verify checksum."
        raise DataIntegrityError(msg)
    
    try:
        with open(state_file, "r") as f:
            checksums = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        msg = f"Data integrity check failed: Could not read state manifest - {e}"
        raise DataIntegrityError(msg)
    
    file_name = file_path.name
    if file_name not in checksums:
        msg = f"Data integrity check failed: No checksum record found for {file_name} in {state_file}"
        raise DataIntegrityError(msg)
    
    expected_checksum = checksums[file_name]["checksum"]
    actual_checksum = compute_file_checksum(file_path)
    
    if actual_checksum != expected_checksum:
        msg = (
            f"Data integrity check FAILED for {file_path}.\n"
            f"  Expected checksum: {expected_checksum}\n"
            f"  Actual checksum:   {actual_checksum}\n"
            f"  File may be corrupted or modified."
        )
        raise DataIntegrityError(msg)
    
    return True, f"Data integrity verified for {file_name}"

def load_class_config(config_path: Path) -> List[str]:
    """
    Load a list of class names/IDs from a YAML config file.
    
    Args:
        config_path: Path to the YAML config file.
        
    Returns:
        List of class identifiers (strings or ints).
        
    Raises:
        FileNotFoundError: If config file not found.
        ValueError: If config format is invalid.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Class config file not found: {config_path}")
    
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in class config {config_path}: {e}")
    
    if "subtle_classes" in config:
        return config["subtle_classes"]
    elif "control_classes" in config:
        return config["control_classes"]
    elif "classes" in config:
        return config["classes"]
    else:
        raise ValueError(f"Invalid class config format in {config_path}: missing 'subtle_classes', 'control_classes', or 'classes' key")

class FilteredAudioDataset:
    """
    A dataset wrapper that filters audio samples based on class configuration.
    Uses streaming to avoid loading full dataset into memory.
    """
    def __init__(
        self,
        dataset_name: str = "esc50",
        subtle_classes: Optional[List] = None,
        control_classes: Optional[List] = None,
        split: str = "train",
        streaming: bool = True
    ):
        self.dataset_name = dataset_name
        self.subtle_classes = set(subtle_classes) if subtle_classes else set()
        self.control_classes = set(control_classes) if control_classes else set()
        self.split = split
        self.streaming = streaming
        
        # Determine target classes
        self.target_classes = self.subtle_classes | self.control_classes
        
        if not self.target_classes:
            raise ValueError("At least one of subtle_classes or control_classes must be provided.")
        
        logger.info(f"FilteredAudioDataset initialized. Target classes: {len(self.target_classes)}")
        logger.info(f"  Subtle classes: {len(self.subtle_classes)}")
        logger.info(f"  Control classes: {len(self.control_classes)}")

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """
        Iterate over the dataset, filtering by class.
        """
        try:
            ds = load_dataset(
                self.dataset_name,
                split=self.split,
                streaming=self.streaming,
                trust_remote_code=True
            )
        except Exception as e:
            raise LlmXiveError(f"Failed to load dataset {self.dataset_name}: {e}") from e
        
        count = 0
        filtered_count = 0
        for item in ds:
            count += 1
            # ESC-50 uses 'label' as int, AudioSet might use 'class_label' or similar.
            # We assume 'label' for now based on T020 schema.
            item_class = item.get("label")
            
            if item_class is None:
                # Try alternative keys
                item_class = item.get("class_label")
            
            if item_class in self.target_classes:
                filtered_count += 1
                yield item
            
            # Optional: progress logging
            if count % 1000 == 0:
                logger.debug(f"Processed {count} items, yielded {filtered_count}")

class FilteredDataLoader:
    """
    Data loader that streams filtered audio data and handles checksum verification.
    """
    def __init__(
        self,
        parquet_path: Optional[Path] = None,
        subtle_config_path: Optional[Path] = None,
        control_config_path: Optional[Path] = None,
        verify_integrity: bool = True
    ):
        self.parquet_path = parquet_path
        self.subtle_config_path = subtle_config_path
        self.control_config_path = control_config_path
        self.verify_integrity = verify_integrity
        
        self.path_config = get_path_config()
        self.logger = get_logger(__name__)

    def load_subtle_classes(self) -> List:
        if not self.subtle_config_path:
            self.subtle_config_path = self.path_config.processed_dir / "class_config_subtle.yaml"
        return load_class_config(self.subtle_config_path)

    def load_control_classes(self) -> List:
        if not self.control_config_path:
            self.control_config_path = self.path_config.processed_dir / "class_config_control.yaml"
        return load_class_config(self.control_config_path)

    def verify_data_integrity(self, file_path: Path) -> None:
        """
        Verify the integrity of a data file against the state manifest.
        
        Args:
            file_path: Path to the data file to verify.
        
        Raises:
            DataIntegrityError: If verification fails.
        """
        if not self.verify_integrity:
            self.logger.info("Data integrity verification skipped.")
            return
        
        try:
            is_valid, message = verify_checksum(file_path)
            self.logger.info(f"Integrity check passed: {message}")
            self._log_integrity_result(file_path, True, message)
        except DataIntegrityError as e:
            self.logger.error(f"Integrity check failed: {e}")
            self._log_integrity_result(file_path, False, str(e))
            raise

    def _log_integrity_result(self, file_path: Path, success: bool, message: str) -> None:
        """
        Log the result of an integrity check to a file.
        
        Args:
            file_path: The file that was checked.
            success: Whether the check passed.
            message: The result message.
        """
        log_path = self.path_config.processed_dir / "integrity_log.txt"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        status = "PASS" if success else "FAIL"
        
        log_entry = f"[{timestamp}] [{status}] {file_path.name}: {message}\n"
        
        with open(log_path, "a") as f:
            f.write(log_entry)

    def get_filtered_dataset(self) -> FilteredAudioDataset:
        """
        Get a filtered dataset instance.
        
        Returns:
            FilteredAudioDataset instance.
        """
        subtle_classes = self.load_subtle_classes()
        control_classes = self.load_control_classes()
        
        return FilteredAudioDataset(
            subtle_classes=subtle_classes,
            control_classes=control_classes,
            streaming=True
        )

    def load_parquet_with_verification(self) -> pd.DataFrame:
        """
        Load the parquet file after verifying its integrity.
        
        Returns:
            DataFrame containing the audio subset.
        
        Raises:
            DataIntegrityError: If integrity check fails.
        """
        if not self.parquet_path:
            self.parquet_path = self.path_config.processed_dir / "subtle_cue_subset.parquet"
        
        # Verify integrity before loading
        self.verify_data_integrity(self.parquet_path)
        
        self.logger.info(f"Loading verified parquet file: {self.parquet_path}")
        df = pd.read_parquet(self.parquet_path)
        self.logger.info(f"Loaded {len(df)} rows from parquet.")
        return df

def main():
    """
    Main entry point for data loading and integrity verification.
    Demonstrates the workflow: load configs -> verify integrity -> load data.
    """
    path_config = get_path_config()
    
    # Define paths
    subtle_config = path_config.processed_dir / "class_config_subtle.yaml"
    control_config = path_config.processed_dir / "class_config_control.yaml"
    parquet_file = path_config.processed_dir / "subtle_cue_subset.parquet"
    
    # Check if files exist (fail loudly if not)
    if not subtle_config.exists():
        raise FileNotFoundError(f"Missing subtle class config: {subtle_config}")
    if not control_config.exists():
        raise FileNotFoundError(f"Missing control class config: {control_config}")
    if not parquet_file.exists():
        raise FileNotFoundError(f"Missing parquet subset: {parquet_file}")
    
    # Initialize loader
    loader = FilteredDataLoader(
        parquet_path=parquet_file,
        subtle_config_path=subtle_config,
        control_config_path=control_config,
        verify_integrity=True
    )
    
    try:
        # Verify integrity
        loader.verify_data_integrity(parquet_file)
        
        # Load data
        df = loader.load_parquet_with_verification()
        
        # Basic stats
        print(f"Dataset loaded successfully.")
        print(f"  Total samples: {len(df)}")
        if 'label' in df.columns:
            print(f"  Unique labels: {df['label'].nunique()}")
        
    except DataIntegrityError as e:
        print(f"CRITICAL: Data integrity verification failed. Aborting.")
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()