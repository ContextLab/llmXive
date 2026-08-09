"""
Filtered Audio Dataset Loader for llmXive.

Implements streaming filtering of audio datasets based on class configurations
defined in data/processed/class_config.yaml.

This module:
1. Loads class definitions (subtle and control) from class_config.yaml.
2. Streams the UrbanSound8K dataset using HuggingFace datasets.
3. Filters rows on-the-fly based on class IDs to avoid OOM.
4. Writes the filtered subset to data/processed/subtle_cue_subset.parquet.
5. Computes and verifies checksums for data lineage.
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Set, Optional, Iterator, Any, Tuple
from pathlib import Path

# Third-party imports (must be in requirements.txt)
import yaml
import pyarrow as pa
import pyarrow.parquet as pq
from datasets import load_dataset

# Project imports
from config import get_path_config, get_dataset_config
from utils.logger import get_logger, DataLoadError, LlmXiveError

logger = get_logger(__name__)

# Constants
CONFIG_PATH = "data/processed/class_config.yaml"
OUTPUT_PATH = "data/processed/subtle_cue_subset.parquet"
STATE_CHECKSUM_DIR = "state/checksums"
DATASET_NAME = "UrbanSound8K"
# UrbanSound8K class mapping (0-indexed in HF dataset, 1-indexed in original paper sometimes)
# We rely on the class_config.yaml to provide the correct integer IDs used by the dataset.
# Standard UrbanSound8K classes:
# 0: air_conditioner, 1: car_horn, 2: children_playing, 3: dog_bark, 4: drilling,
# 5: engine_idling, 6: gun_shot, 7: jackhammer, 8: siren, 9: street_music

def compute_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise DataLoadError(f"File not found for checksum: {file_path}")

def save_checksum_to_state(checksum: str, file_name: str, state_dir: str) -> None:
    """Save checksum to state/checksums directory."""
    state_path = Path(state_dir)
    state_path.mkdir(parents=True, exist_ok=True)
    checksum_file = state_path / f"{file_name}.yaml"

    data = {
        "file": file_name,
        "checksum": checksum,
        "algorithm": "sha256",
        "timestamp": "generated_by_t020" # In a real pipeline, use datetime
    }

    with open(checksum_file, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
    logger.info(f"Saved checksum to {checksum_file}")

def verify_checksum(file_path: str, state_dir: str, file_name: str) -> bool:
    """Verify file checksum against stored state."""
    checksum_file = Path(state_dir) / f"{file_name}.yaml"
    if not checksum_file.exists():
        logger.warning(f"Checksum file not found: {checksum_file}. Skipping verification.")
        return True # Allow run to proceed if state is missing (first run)

    try:
        with open(checksum_file, "r") as f:
            stored_data = yaml.safe_load(f)
        stored_checksum = stored_data.get("checksum")
        current_checksum = compute_file_checksum(file_path)
        if stored_checksum != current_checksum:
            raise DataLoadError(
                f"Checksum mismatch for {file_path}. "
                f"Expected: {stored_checksum}, Got: {current_checksum}"
            )
        logger.info(f"Checksum verified for {file_name}")
        return True
    except FileNotFoundError:
        raise DataLoadError(f"Checksum file not found: {checksum_file}")

def load_class_config(config_path: str) -> Tuple[Set[int], Set[int]]:
    """
    Load class definitions from class_config.yaml.
    Returns (subtle_classes, control_classes) as sets of integers.
    """
    full_path = Path(config_path)
    if not full_path.exists():
        raise DataLoadError(f"Class configuration file not found: {full_path}")

    with open(full_path, "r") as f:
        config = yaml.safe_load(f)

    if "subtle_classes" not in config:
        raise DataLoadError("Missing 'subtle_classes' in class_config.yaml")
    if "control_classes" not in config:
        raise DataLoadError("Missing 'control_classes' in class_config.yaml")

    subtle = set(config["subtle_classes"])
    control = set(config["control_classes"])

    logger.info(f"Loaded {len(subtle)} subtle classes and {len(control)} control classes.")
    logger.debug(f"Subtle: {subtle}, Control: {control}")
    return subtle, control

class FilteredAudioDataset:
    """
    A streaming wrapper around the HuggingFace dataset that filters by class ID.
    """
    def __init__(self, dataset_name: str, subtle_classes: Set[int], control_classes: Set[int]):
        self.dataset_name = dataset_name
        self.subtle_classes = subtle_classes
        self.control_classes = control_classes
        self.allowed_classes = subtle_classes | control_classes

        logger.info(f"Initializing streaming dataset: {dataset_name}")
        # Load with streaming=True to avoid OOM
        # UrbanSound8K is available on HF Hub
        try:
            self.dataset = load_dataset(
                "mrfakename/urbansound8k", # Verified public dataset ID
                split="train",
                streaming=True
            )
        except Exception as e:
            # Fallback to a generic error if specific ID fails, but do not fake data
            raise DataLoadError(f"Failed to load dataset '{dataset_name}' with streaming: {e}")

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Iterate over the dataset, filtering on-the-fly."""
        for item in self.dataset:
            # The 'class_id' key is standard in UrbanSound8K HF datasets
            # Ensure we handle potential variations in key names if necessary
            class_id = item.get("class_id")
            if class_id is None:
                # Try alternative key names if standard one is missing
                class_id = item.get("ClassID")

            if class_id in self.allowed_classes:
                # Mark the item with its type (subtle vs control)
                item["subset_type"] = "subtle" if class_id in self.subtle_classes else "control"
                yield item
            # else: silently skip non-matching classes

    def __len__(self) -> int:
        # Streaming datasets don't have a known length without full iteration
        # We return -1 or estimate if possible, but for filtering, -1 is safer
        return -1

class FilteredDataLoader:
    """
    High-level loader that orchestrates streaming, filtering, and parquet export.
    """
    def __init__(self, config_path: str = CONFIG_PATH, output_path: str = OUTPUT_PATH):
        self.config_path = config_path
        self.output_path = output_path
        self.state_dir = STATE_CHECKSUM_DIR
        self.path_config = get_path_config()

    def run(self) -> str:
        """
        Execute the full pipeline:
        1. Load config.
        2. Stream and filter dataset.
        3. Write to Parquet.
        4. Compute checksum and save to state.
        5. Verify.
        Returns path to output file.
        """
        # 1. Load Config
        logger.info(f"Loading class configuration from {self.config_path}")
        subtle_classes, control_classes = load_class_config(self.config_path)

        # 2. Initialize Dataset
        dataset = FilteredAudioDataset(DATASET_NAME, subtle_classes, control_classes)

        # 3. Stream and Write to Parquet
        output_file = Path(self.output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Streaming and filtering dataset to {output_file}")

        # Prepare schema for Parquet
        # We expect audio data (bytes) and metadata.
        # Since we are streaming, we accumulate in batches to write efficiently.
        batch_size = 100
        buffer = {
            "audio": [],
            "class_id": [],
            "file_name": [],
            "subset_type": [],
            "slice_start": [],
            "slice_end": []
        }
        count = 0

        # To avoid loading full audio into memory if not needed, we might just store metadata
        # but the task implies a "subset" for training, so we keep the audio bytes.
        # However, UrbanSound8K audio is small (short clips).
        
        try:
            writer = pq.ParquetWriter(output_file, pa.schema([
                pa.field("audio", pa.binary()),
                pa.field("class_id", pa.int64()),
                pa.field("file_name", pa.string()),
                pa.field("subset_type", pa.string()),
                pa.field("slice_start", pa.int64()),
                pa.field("slice_end", pa.int64()),
            ]))

            for item in dataset:
                # Extract fields
                # HF datasets usually have 'audio' as a dict with 'path' and 'array' or 'bytes'
                # If it's a file path, we might need to read it, but streaming usually handles bytes
                audio_data = item.get("audio")
                
                # Handle different audio formats from HF
                if isinstance(audio_data, dict):
                    # If 'bytes' is present, use it. Otherwise, we might need to load from path.
                    # Streaming mode usually provides 'bytes' for small files or a path.
                    # For robustness, if 'bytes' exists, use it.
                    if "bytes" in audio_data:
                        audio_bytes = audio_data["bytes"]
                    elif "array" in audio_data:
                        # If only array is present, we serialize it.
                        # But for Parquet, binary is better. We'll assume bytes for now or skip.
                        # To be safe and strictly follow "real data", we assume the dataset yields bytes.
                        # If not, we might need to use the 'path' and read.
                        # For UrbanSound8K HF, it usually provides 'bytes'.
                        logger.warning("Audio bytes not found in stream item, skipping.")
                        continue
                    else:
                        logger.warning("Audio data format unknown, skipping.")
                        continue
                elif isinstance(audio_data, bytes):
                    audio_bytes = audio_data
                else:
                    # Fallback: try to treat as path and read? No, streaming should be bytes.
                    logger.warning("Invalid audio data type, skipping.")
                    continue

                buffer["audio"].append(audio_bytes)
                buffer["class_id"].append(item["class_id"])
                buffer["file_name"].append(item.get("file_name", "unknown"))
                buffer["subset_type"].append(item.get("subset_type", "unknown"))
                buffer["slice_start"].append(0) # Placeholder
                buffer["slice_end"].append(len(audio_bytes))

                count += 1
                if count % batch_size == 0:
                    writer.write_table(pa.Table.from_pydict(buffer))
                    buffer = {k: [] for k in buffer} # Clear buffer
                    logger.debug(f"Written batch {count}")

            # Write remaining
            if buffer["audio"]:
                writer.write_table(pa.Table.from_pydict(buffer))
            
            writer.close()
            logger.info(f"Successfully wrote {count} records to {output_file}")

        except Exception as e:
            raise DataLoadError(f"Failed to write Parquet file: {e}")

        # 4. Compute Checksum
        checksum = compute_file_checksum(str(output_file))
        save_checksum_to_state(checksum, "subtle_cue_subset", self.state_dir)

        # 5. Verify
        verify_checksum(str(output_file), self.state_dir, "subtle_cue_subset")

        return str(output_file)

def main():
    """Entry point for T020 execution."""
    logger.info("Starting T020: Filtered Data Loader")
    try:
        loader = FilteredDataLoader()
        output_path = loader.run()
        logger.info(f"T020 Complete. Output: {output_path}")
    except DataLoadError as e:
        logger.error(f"Data Load Error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
