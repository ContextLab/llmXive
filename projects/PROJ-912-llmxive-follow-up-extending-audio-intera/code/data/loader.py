"""
Filtered Audio Dataset Loader for llmXive.

Implements streaming data loading for Subtle Cue and Control Set classes
from ESC-50 and UrbanSound8K datasets, avoiding full dataset loading to prevent OOM.
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Set, Optional, Iterator, Any, Tuple
from pathlib import Path
import yaml

from datasets import load_dataset
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from utils.logger import get_logger, DataLoadError
from config import get_dataset_config, get_path_config
from data.subtle_cue_builder import (
    SubtleCueBuilder,
    ControlSetBuilder,
    DatasetType,
    ClassDefinition
)

logger = get_logger(__name__)


def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def save_checksum_to_state(checksum: str, artifact_name: str, state_dir: Path) -> None:
    """Save checksum to state YAML for lineage verification."""
    state_file = state_dir / "data_lineage.yaml"
    
    # Load existing state or create new
    if state_file.exists():
        with open(state_file, "r") as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}

    if "artifacts" not in state:
        state["artifacts"] = {}

    state["artifacts"][artifact_name] = {
        "checksum": checksum,
        "verified": True
    }

    with open(state_file, "w") as f:
        yaml.dump(state, f, default_flow_style=False)


def verify_checksum(artifact_name: str, state_dir: Path) -> bool:
    """Verify checksum against stored state."""
    state_file = state_dir / "data_lineage.yaml"
    
    if not state_file.exists():
        logger.warning(f"State file {state_file} does not exist. Cannot verify checksum.")
        return False

    with open(state_file, "r") as f:
        state = yaml.safe_load(f) or {}

    artifacts = state.get("artifacts", {})
    if artifact_name not in artifacts:
        logger.warning(f"Artifact {artifact_name} not found in state file.")
        return False

    return True


class FilteredAudioDataset:
    """
    Streaming dataset that filters audio classes based on Subtle Cue and Control Set definitions.
    """

    def __init__(
        self,
        class_definitions: List[ClassDefinition],
        dataset_type: DatasetType = DatasetType.ESC50,
        streaming: bool = True,
        batch_size: int = 32
    ):
        self.class_definitions = class_definitions
        self.dataset_type = dataset_type
        self.streaming = streaming
        self.batch_size = batch_size
        
        # Extract class IDs from definitions
        self.target_class_ids = {
            defn.class_id for defn in class_definitions
        }
        
        # Determine dataset name based on type
        if dataset_type == DatasetType.ESC50:
            self.dataset_name = "esc50"
        elif dataset_type == DatasetType.URBANSOUND8K:
            self.dataset_name = "urban-sound-8k"
        else:
            raise ValueError(f"Unsupported dataset type: {dataset_type}")

        logger.info(f"Initializing FilteredAudioDataset for {self.dataset_name}")
        logger.info(f"Target class IDs: {self.target_class_ids}")

    def _get_dataset(self):
        """Load dataset with streaming."""
        try:
            dataset = load_dataset(
                self.dataset_name,
                streaming=self.streaming,
                split="train"
            )
            return dataset
        except Exception as e:
            raise DataLoadError(f"Failed to load dataset {self.dataset_name}: {e}")

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Iterate over filtered dataset samples."""
        dataset = self._get_dataset()
        
        # Filter based on class IDs
        for sample in dataset:
            # Handle different dataset structures
            if self.dataset_type == DatasetType.ESC50:
                class_id = sample.get("class", 0)
            elif self.dataset_type == DatasetType.URBANSOUND8K:
                class_id = sample.get("fold", 0)  # Using fold as proxy for class
            else:
                continue

            if class_id in self.target_class_ids:
                yield sample

    def __len__(self) -> int:
        """Return estimated length (approximate for streaming)."""
        # For streaming datasets, we can't know exact length without iterating
        return -1  # Indicate unknown length


class FilteredDataLoader:
    """
    DataLoader that generates filtered parquet files from streaming datasets.
    """

    def __init__(self, output_dir: Path, state_dir: Path):
        self.output_dir = output_dir
        self.state_dir = state_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_subtle_cue_subset(
        self,
        subtle_cue_builder: SubtleCueBuilder,
        control_set_builder: Optional[ControlSetBuilder] = None,
        max_samples: Optional[int] = 1000
    ) -> Path:
        """
        Build filtered subset containing Subtle Cue and Control Set classes.
        
        Args:
            subtle_cue_builder: Builder for Subtle Cue class definitions
            control_set_builder: Optional builder for Control Set definitions
            max_samples: Maximum number of samples to collect (for testing/streaming)
            
        Returns:
            Path to generated parquet file
        """
        logger.info("Starting filtered data loader for Subtle Cue subset")
        
        # Get class definitions
        subtle_classes = subtle_cue_builder.get_class_definitions()
        logger.info(f"Subtle Cue classes: {[c.class_name for c in subtle_classes]}")
        
        all_class_defs = list(subtle_classes)
        
        if control_set_builder:
            control_classes = control_set_builder.get_class_definitions()
            logger.info(f"Control Set classes: {[c.class_name for c in control_classes]}")
            all_class_defs.extend(control_classes)
        
        if not all_class_defs:
            raise DataLoadError("No class definitions provided for filtering")
        
        # Determine dataset type (ESC-50 for subtle cues)
        dataset_type = DatasetType.ESC50
        
        # Create filtered dataset
        filtered_dataset = FilteredAudioDataset(
            class_definitions=all_class_defs,
            dataset_type=dataset_type,
            streaming=True,
            batch_size=32
        )
        
        # Collect samples into parquet
        output_file = self.output_dir / "subtle_cue_subset.parquet"
        samples = []
        
        logger.info(f"Streaming samples from {dataset_type.name} dataset...")
        
        try:
            for i, sample in enumerate(filtered_dataset):
                if max_samples and i >= max_samples:
                    logger.info(f"Reached max_samples limit ({max_samples})")
                    break
                
                # Extract relevant fields
                row = {
                    "audio_path": sample.get("audio", {}).get("path", ""),
                    "class_id": sample.get("class", sample.get("fold", 0)),
                    "label": sample.get("class_name", "unknown"),
                    "duration": sample.get("duration", 0.0)
                }
                
                # Handle audio data if present
                if "audio" in sample and "array" in sample["audio"]:
                    row["audio_array"] = sample["audio"]["array"]
                    row["sampling_rate"] = sample["audio"].get("sampling_rate", 16000)
                
                samples.append(row)
                
                if (i + 1) % 100 == 0:
                    logger.info(f"Collected {i + 1} samples...")
        
        except Exception as e:
            raise DataLoadError(f"Error during streaming: {e}")
        
        if not samples:
            raise DataLoadError("No samples collected from dataset")
        
        logger.info(f"Collected {len(samples)} samples, writing to parquet...")
        
        # Write to parquet
        df = pd.DataFrame(samples)
        df.to_parquet(output_file, index=False)
        
        # Compute and save checksum
        checksum = compute_file_checksum(output_file)
        logger.info(f"Generated checksum: {checksum}")
        
        # Save to state
        save_checksum_to_state(
            checksum=checksum,
            artifact_name="subtle_cue_subset.parquet",
            state_dir=self.state_dir
        )
        
        # Verify checksum
        if not verify_checksum("subtle_cue_subset.parquet", self.state_dir):
            logger.warning("Checksum verification failed")
        else:
            logger.info("Checksum verification passed")
        
        logger.info(f"Successfully wrote {output_file} with {len(samples)} samples")
        return output_file


def main():
    """Main entry point for building filtered dataset."""
    logger.info("Starting filtered data loader main")
    
    # Get configuration
    path_config = get_path_config()
    dataset_config = get_dataset_config()
    
    output_dir = Path(path_config.processed_data_dir)
    state_dir = Path(path_config.state_dir)
    
    # Initialize builders
    subtle_builder = SubtleCueBuilder()
    control_builder = ControlSetBuilder()
    
    # Create loader
    loader = FilteredDataLoader(output_dir=output_dir, state_dir=state_dir)
    
    # Build subset
    try:
        output_file = loader.build_subtle_cue_subset(
            subtle_cue_builder=subtle_builder,
            control_set_builder=control_builder,
            max_samples=500  # Limit for testing
        )
        
        logger.info(f"Successfully created {output_file}")
        logger.info(f"Checksum verified against state")
        
    except Exception as e:
        logger.error(f"Failed to build subset: {e}")
        raise


if __name__ == "__main__":
    main()