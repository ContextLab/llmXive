"""
Filtered Data Loader for Audio Interaction Model.

Implements streaming data loading for 'Subtle Cue' and 'Control Set' classes
from ESC-50 and UrbanSound8K datasets to avoid OOM on CPU runners.
"""
import os
import json
from typing import Dict, List, Set, Optional, Iterator, Any
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Dataset
from datasets import load_dataset
from transformers import Wav2Vec2Processor

from config import get_dataset_config, PathConfig
from data.subtle_cue_builder import SubtleCueBuilder, ControlSetBuilder, get_binary_discrimination_mapping
from utils.logger import get_logger, DataLoadError

logger = get_logger(__name__)


class FilteredAudioDataset(Dataset):
    """
    A streaming wrapper around HuggingFace datasets that filters for specific classes.
    It yields processed audio tensors and labels.
    """
    def __init__(
        self,
        dataset_name: str,
        split: str,
        target_classes: Set[str],
        processor: Wav2Vec2Processor,
        sampling_rate: int = 16000,
        streaming: bool = True,
        max_samples: Optional[int] = None
    ):
        """
        Args:
            dataset_name: HuggingFace dataset name (e.g., 'esc-50', 'urban_sound_8k')
            split: Dataset split (e.g., 'train', 'test')
            target_classes: Set of class names to filter for.
            processor: Wav2Vec2Processor for audio normalization.
            sampling_rate: Target sampling rate.
            streaming: If True, streams data; if False, loads into memory (not recommended for large sets).
            max_samples: Optional limit on number of samples to process.
        """
        self.dataset_name = dataset_name
        self.split = split
        self.target_classes = target_classes
        self.processor = processor
        self.sampling_rate = sampling_rate
        self.streaming = streaming
        self.max_samples = max_samples

        logger.info(f"Initializing streaming dataset: {dataset_name} [{split}]")
        logger.info(f"Target classes: {target_classes}")

        try:
            # Load dataset with streaming enabled to prevent OOM
            self.dataset = load_dataset(
                dataset_name,
                split=split,
                streaming=streaming
            )
        except Exception as e:
            raise DataLoadError(f"Failed to load dataset '{dataset_name}': {e}")

        # Filter logic
        self.filtered_iterator = self._filter_iterator()
        self.length = self._estimate_length()

    def _filter_iterator(self) -> Iterator[Dict[str, Any]]:
        """Iterate over dataset and yield only items with target class names."""
        count = 0
        for item in self.dataset:
            if self.max_samples is not None and count >= self.max_samples:
                break

            # Handle different dataset structures for class identification
            # ESC-50 uses 'category', UrbanSound8K uses 'class' or 'fold' logic
            class_name = None
            if 'category' in item:
                class_name = item['category']
            elif 'class' in item:
                class_name = item['class']
            elif 'label' in item:
                class_name = item['label']

            if class_name in self.target_classes:
                count += 1
                yield item

    def _estimate_length(self) -> int:
        """
        Estimates the length of the filtered dataset.
        For streaming, this is an estimate based on a sample or a hard limit if streaming.
        """
        if self.streaming:
            # For streaming, we can't know the exact length without iterating.
            # We return a large number or rely on the max_samples limit if set.
            # If max_samples is set, length is max_samples.
            if self.max_samples:
                return self.max_samples
            # Otherwise, return a safe upper bound or -1 to indicate unknown
            return 10000 # Placeholder for streaming length if not bounded
        else:
            # If not streaming, we can calculate exact length (expensive)
            # For this implementation, we assume streaming is always True for large data
            return len(list(self._filter_iterator()))

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        """
        Retrieves an item by index.
        Note: With streaming=True, random access is not supported by the underlying dataset.
        This implementation assumes sequential iteration is preferred, or we convert to list
        if max_samples is small. However, for true streaming, __getitem__ is problematic.
        
        To support DataLoader with streaming, we usually rely on the iterator protocol
        or a custom sampler. Here, we implement a workaround:
        If max_samples is set and small, we materialize the filtered list once.
        If not, we raise an error or use an iterator-based approach.
        
        For robustness in this specific task (avoiding OOM), we will materialize
        ONLY if max_samples is small (e.g., < 5000), otherwise we rely on the
        iterator pattern in the training loop or use a custom generator-based DataLoader.
        
        Since torch.utils.data.DataLoader requires __getitem__, we will materialize
        a small subset if max_samples is defined, otherwise we assume the user
        will iterate the dataset directly or use a generator.
        
        To strictly follow the "streaming" requirement without OOM, we will
        raise an error if __getitem__ is called on a non-materialized stream,
        forcing the user to use an iterator-based approach or set max_samples.
        """
        if self.streaming and self.max_samples is None:
            raise NotImplementedError(
                "Random access (__getitem__) is not supported for streaming datasets without a max_samples limit. "
                "Please set max_samples or iterate the dataset directly."
            )

        # If we are here, we either have max_samples or streaming is False.
        # We need to reconstruct the item. Since we can't seek in a stream,
        # we assume the dataset has been materialized or max_samples is small enough
        # that we can re-iterate (inefficient but safe for small N).
        # A better approach for streaming is to use `iter(self)` in the training loop.
        
        # For this task, we will implement a cache if max_samples is set.
        # If not set and streaming, this method is a failure point by design to enforce constraints.
        
        # Re-implementation for safety:
        # We will iterate until we hit the index.
        current_idx = 0
        for item in self._filter_iterator():
            if current_idx == idx:
                # Process audio
                audio = item['audio'] if isinstance(item['audio'], dict) else item['audio']
                # Handle audio dict structure from HF datasets (array, sampling_rate)
                if isinstance(audio, dict):
                    array = audio['array']
                    sr = audio['sampling_rate']
                else:
                    # Fallback for older formats
                    array = audio
                    sr = self.sampling_rate

                # Resample if necessary
                if sr != self.sampling_rate:
                    # Simple resampling logic or rely on processor
                    # Wav2Vec2Processor handles resampling if we pass the array and sr
                    pass

                inputs = self.processor(
                    array,
                    sampling_rate=sr,
                    return_tensors="pt",
                    padding=True,
                    truncation=True
                )

                # Determine label index
                # We need a mapping from class_name to int label for the model
                # This mapping should be external or derived from the builder
                # For now, we return the class name and let the collator handle it,
                # or we assume a global mapping exists.
                
                # Retrieve class name again
                class_name = item.get('category') or item.get('class') or item.get('label')
                
                return {
                    "input_values": inputs['input_values'].squeeze(0),
                    "attention_mask": inputs['attention_mask'].squeeze(0) if 'attention_mask' in inputs else None,
                    "label_name": class_name,
                    "original_item": item
                }
            current_idx += 1
        
        raise IndexError(f"Index {idx} out of range for dataset of length {self.length}")

    def __iter__(self):
        """Support direct iteration for streaming efficiency."""
        return self._filter_iterator()


class FilteredDataLoader:
    """
    High-level interface to load filtered audio data for Subtle Cue and Control Set.
    """
    def __init__(self, config: Optional[PathConfig] = None):
        self.config = config or PathConfig()
        self.logger = get_logger(__name__)
        
        # Load processor (shared)
        from models.teacher_loader import get_teacher_model
        # We need the processor from the teacher model setup
        # Since T011 implemented teacher_loader, we import the helper
        try:
            # Re-load processor based on config
            model_id = get_teacher_model_id()
            self.processor = Wav2Vec2Processor.from_pretrained(model_id)
        except Exception as e:
            self.logger.warning(f"Could not load processor from {model_id}: {e}. Using default.")
            self.processor = None

    def get_subtle_cue_loader(
        self,
        split: str = "train",
        batch_size: int = 16,
        max_samples: Optional[int] = 1000
    ) -> DataLoader:
        """
        Loads the 'Subtle Cue' dataset stream.
        """
        # Get class definitions from SubtleCueBuilder
        builder = SubtleCueBuilder()
        # We need to map class names to dataset specific identifiers
        # The builder returns a list of ClassDefinition objects
        subtle_classes = builder.get_subtle_classes()
        target_names = {c.name for c in subtle_classes}

        self.logger.info(f"Loading Subtle Cue dataset. Classes: {target_names}")

        # Create dataset
        # Note: ESC-50 is the primary source for these classes in this context
        dataset = FilteredAudioDataset(
            dataset_name="esc-50",
            split=split,
            target_classes=target_names,
            processor=self.processor,
            streaming=True,
            max_samples=max_samples
        )

        # Custom collate function to handle variable lengths and labels
        def collate_fn(batch):
            # batch is a list of dicts from __getitem__
            input_values = torch.cat([item['input_values'] for item in batch], dim=0)
            attention_mask = torch.cat([item['attention_mask'] for item in batch], dim=0) if batch[0]['attention_mask'] is not None else None
            labels = [item['label_name'] for item in batch]
            return {
                "input_values": input_values,
                "attention_mask": attention_mask,
                "labels": labels
            }

        # Since streaming datasets don't support standard DataLoader well with __getitem__,
        # we return an iterator-based wrapper or a DataLoader with a custom sampler.
        # For simplicity and strict streaming adherence, we return the dataset iterator
        # wrapped in a way that mimics a loader if max_samples is set.
        
        if max_samples:
            return DataLoader(
                dataset,
                batch_size=batch_size,
                collate_fn=collate_fn,
                num_workers=0,
                shuffle=False
            )
        else:
            # If no max_samples, we cannot use standard DataLoader with __getitem__
            # We return a generator that yields batches
            self.logger.warning("max_samples not set for streaming. Returning generator.")
            return self._stream_generator(dataset, batch_size, collate_fn)

    def get_control_set_loader(
        self,
        split: str = "train",
        batch_size: int = 16,
        max_samples: Optional[int] = 1000
    ) -> DataLoader:
        """
        Loads the 'Control Set' dataset stream.
        """
        builder = ControlSetBuilder()
        control_classes = builder.get_control_classes()
        target_names = {c.name for c in control_classes}

        self.logger.info(f"Loading Control Set dataset. Classes: {target_names}")

        # Control set might come from UrbanSound8K or specific ESC-50 classes
        # Based on T021b, we use UrbanSound8K for low-frequency classes if available
        # Or fallback to ESC-50 if the specific classes exist there.
        # The builder should define the source.
        
        dataset_name = "urban_sound_8k" # Default assumption from T021b
        # Check if builder specifies a different source
        if hasattr(builder, 'source_dataset'):
            dataset_name = builder.source_dataset

        dataset = FilteredAudioDataset(
            dataset_name=dataset_name,
            split=split,
            target_classes=target_names,
            processor=self.processor,
            streaming=True,
            max_samples=max_samples
        )

        def collate_fn(batch):
            input_values = torch.cat([item['input_values'] for item in batch], dim=0)
            attention_mask = torch.cat([item['attention_mask'] for item in batch], dim=0) if batch[0]['attention_mask'] is not None else None
            labels = [item['label_name'] for item in batch]
            return {
                "input_values": input_values,
                "attention_mask": attention_mask,
                "labels": labels
            }

        if max_samples:
            return DataLoader(
                dataset,
                batch_size=batch_size,
                collate_fn=collate_fn,
                num_workers=0,
                shuffle=False
            )
        else:
            return self._stream_generator(dataset, batch_size, collate_fn)

    def _stream_generator(self, dataset, batch_size, collate_fn):
        """
        Generator that yields batches from a streaming dataset.
        """
        batch = []
        for item in dataset:
            batch.append(item)
            if len(batch) == batch_size:
                yield collate_fn(batch)
                batch = []
        if batch:
            yield collate_fn(batch)


def main():
    """
    Entry point for testing the data loader.
    Streams a small number of samples to verify functionality without OOM.
    """
    loader = FilteredDataLoader()
    
    # Test Subtle Cue
    print("Testing Subtle Cue Loader...")
    subtle_loader = loader.get_subtle_cue_loader(batch_size=2, max_samples=10)
    
    if isinstance(subtle_loader, DataLoader):
        for i, batch in enumerate(subtle_loader):
            print(f"Batch {i}: input_values shape {batch['input_values'].shape}, labels {batch['labels']}")
            if i >= 2: break
    else:
        # It's a generator
        for i, batch in enumerate(subtle_loader):
            print(f"Batch {i}: input_values shape {batch['input_values'].shape}, labels {batch['labels']}")
            if i >= 2: break

    # Test Control Set
    print("\nTesting Control Set Loader...")
    control_loader = loader.get_control_set_loader(batch_size=2, max_samples=10)
    
    if isinstance(control_loader, DataLoader):
        for i, batch in enumerate(control_loader):
            print(f"Batch {i}: input_values shape {batch['input_values'].shape}, labels {batch['labels']}")
            if i >= 2: break
    else:
        for i, batch in enumerate(control_loader):
            print(f"Batch {i}: input_values shape {batch['input_values'].shape}, labels {batch['labels']}")
            if i >= 2: break

    print("\nData loader test completed successfully.")


if __name__ == "__main__":
    main()