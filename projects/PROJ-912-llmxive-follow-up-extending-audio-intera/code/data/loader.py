import os
import json
import hashlib
import logging
from typing import Dict, List, Set, Optional, Iterator, Any, Tuple
from pathlib import Path
import yaml
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datasets import load_dataset

from config import get_path_config, get_dataset_config
from utils.logger import get_logger, DataLoadError

# Configure logging
logger = get_logger(__name__)

# Constants
DATASET_NAME = "esc50"  # Using ESC-50 as the base dataset for audio cues
DATASET_SPLIT = "train"
STREAMING_BUFFER_SIZE = 1000  # Number of examples to buffer during streaming

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksum_to_state(checksum: str, filename: str, state_dir: Path) -> None:
    """Save checksum to state tracking file."""
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / f"{filename}.checksum"
    with open(state_file, "w") as f:
        f.write(checksum)
    logger.info(f"Saved checksum for {filename} to {state_file}")

def verify_checksum(file_path: Path, state_dir: Path, filename: str) -> bool:
    """Verify file checksum against stored value."""
    if not state_dir.exists():
        raise FileNotFoundError(f"State directory not found: {state_dir}")
    
    state_file = state_dir / f"{filename}.checksum"
    if not state_file.exists():
        logger.warning(f"No stored checksum found for {filename}")
        return False
    
    with open(state_file, "r") as f:
        stored_checksum = f.read().strip()
    
    current_checksum = compute_file_checksum(file_path)
    return current_checksum == stored_checksum

def load_class_config(config_path: Path) -> Dict[str, List[int]]:
    """Load class configuration from YAML file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Class config file not found: {config_path}")
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Validate structure
    if "subtle_classes" not in config or "control_classes" not in config:
        raise ValueError(f"Invalid class config format in {config_path}")
    
    return {
        "subtle_classes": config["subtle_classes"],
        "control_classes": config["control_classes"]
    }

class FilteredAudioDataset:
    """
    A streaming dataset wrapper that filters audio examples based on class IDs.
    """
    def __init__(
        self,
        dataset_name: str,
        split: str,
        subtle_class_ids: Set[int],
        control_class_ids: Set[int],
        label_mapping: Dict[int, int],
        buffer_size: int = STREAMING_BUFFER_SIZE
    ):
        self.dataset_name = dataset_name
        self.split = split
        self.subtle_class_ids = subtle_class_ids
        self.control_class_ids = control_class_ids
        self.label_mapping = label_mapping
        self.buffer_size = buffer_size
        
        # Load dataset in streaming mode
        logger.info(f"Loading dataset {dataset_name} in streaming mode...")
        self.dataset = load_dataset(
            dataset_name,
            split=split,
            streaming=True
        )
        
        # Validate that the dataset has the required features
        features = self.dataset.features
        if "audio" not in features:
            raise DataLoadError(f"Dataset {dataset_name} missing 'audio' feature")
        if "class" not in features:
            raise DataLoadError(f"Dataset {dataset_name} missing 'class' feature")
        
        logger.info(f"Dataset loaded successfully. Features: {list(features.keys())}")

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Iterate through dataset and yield filtered examples."""
        for example in self.dataset:
            class_id = example["class"]
            
            # Determine label: 1 for subtle, 0 for control
            if class_id in self.subtle_class_ids:
                label = 1
            elif class_id in self.control_class_ids:
                label = 0
            else:
                # Skip examples that don't match either category
                continue
            
            # Map class_id to a standardized label if needed
            standardized_class_id = self.label_mapping.get(class_id, class_id)
            
            # Extract audio path (if available) or use dataset index
            # For streaming datasets, we might not have a direct file path
            # We'll use a synthetic path based on dataset info
            audio_path = f"{self.dataset_name}/{self.split}/{class_id}_{id(example)}"
            
            yield {
                "audio_path": audio_path,
                "class_id": standardized_class_id,
                "label": label
            }

class FilteredDataLoader:
    """
    A data loader that streams and filters audio data based on class configurations.
    """
    def __init__(
        self,
        subtle_config_path: Path,
        control_config_path: Path,
        output_path: Path,
        state_dir: Optional[Path] = None
    ):
        self.subtle_config_path = subtle_config_path
        self.control_config_path = control_config_path
        self.output_path = output_path
        self.state_dir = state_dir or Path("state")
        
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load class configurations
        logger.info("Loading class configurations...")
        try:
            subtle_config = load_class_config(self.subtle_config_path)
            control_config = load_class_config(self.control_config_path)
        except Exception as e:
            raise DataLoadError(f"Failed to load class configurations: {e}")
        
        # Combine configurations
        self.subtle_class_ids = set(subtle_config["subtle_classes"])
        self.control_class_ids = set(control_config["control_classes"])
        
        logger.info(f"Loaded {len(self.subtle_class_ids)} subtle classes and {len(self.control_class_ids)} control classes")
        
        # Create label mapping (identity mapping for now)
        all_class_ids = self.subtle_class_ids.union(self.control_class_ids)
        self.label_mapping = {cid: cid for cid in all_class_ids}
        
        # Initialize dataset
        self.dataset = FilteredAudioDataset(
            dataset_name=DATASET_NAME,
            split=DATASET_SPLIT,
            subtle_class_ids=self.subtle_class_ids,
            control_class_ids=self.control_class_ids,
            label_mapping=self.label_mapping
        )

    def stream_and_save(self, max_examples: Optional[int] = None) -> Path:
        """
        Stream filtered data and save to Parquet file.
        
        Args:
            max_examples: Maximum number of examples to process (None for unlimited)
        
        Returns:
            Path to the saved Parquet file
        """
        logger.info(f"Starting data streaming to {self.output_path}")
        
        # Prepare data for Parquet
        data_rows = []
        example_count = 0
        
        try:
            for example in self.dataset:
                data_rows.append(example)
                example_count += 1
                
                if max_examples and example_count >= max_examples:
                    break
                
                # Log progress every 1000 examples
                if example_count % 1000 == 0:
                    logger.info(f"Processed {example_count} examples...")
        
        except Exception as e:
            raise DataLoadError(f"Error during data streaming: {e}")
        
        if not data_rows:
            raise DataLoadError("No data was collected. Check class configurations and dataset.")
        
        # Create PyArrow table and save to Parquet
        logger.info(f"Saving {len(data_rows)} examples to Parquet...")
        table = pa.Table.from_pylist(data_rows)
        pq.write_table(table, self.output_path)
        
        logger.info(f"Successfully saved data to {self.output_path}")
        
        # Compute and save checksum
        checksum = compute_file_checksum(self.output_path)
        logger.info(f"File checksum: {checksum}")
        
        if self.state_dir:
            save_checksum_to_state(checksum, "subtle_cue_subset", self.state_dir)
            logger.info("Checksum saved to state directory")
        
        return self.output_path

def main():
    """Main entry point for the filtered data loader."""
    path_config = get_path_config()
    dataset_config = get_dataset_config()
    
    # Define paths
    subtle_config_path = path_config.processed_dir / "class_config_subtle.yaml"
    control_config_path = path_config.processed_dir / "class_config_control.yaml"
    output_path = path_config.processed_dir / "subtle_cue_subset.parquet"
    state_dir = path_config.state_dir
    
    logger.info(f"Subtle config path: {subtle_config_path}")
    logger.info(f"Control config path: {control_config_path}")
    logger.info(f"Output path: {output_path}")
    
    # Check if config files exist
    if not subtle_config_path.exists():
        raise FileNotFoundError(f"Subtle class config not found: {subtle_config_path}")
    if not control_config_path.exists():
        raise FileNotFoundError(f"Control class config not found: {control_config_path}")
    
    # Initialize loader
    loader = FilteredDataLoader(
        subtle_config_path=subtle_config_path,
        control_config_path=control_config_path,
        output_path=output_path,
        state_dir=state_dir
    )
    
    # Stream and save data
    # For testing purposes, we limit to a small number of examples
    # In production, remove the max_examples parameter to process all data
    output_file = loader.stream_and_save(max_examples=1000)
    
    logger.info(f"Data loading complete. Output file: {output_file}")
    
    # Verify the output file
    if output_file.exists():
        logger.info(f"Verification: Output file exists at {output_file}")
        logger.info(f"File size: {output_file.stat().st_size} bytes")
    else:
        raise DataLoadError(f"Output file was not created: {output_file}")

if __name__ == "__main__":
    main()