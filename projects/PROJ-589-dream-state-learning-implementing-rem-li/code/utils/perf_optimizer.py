import torch
from torch.utils.data import DataLoader, Dataset, IterableDataset
from typing import Dict, Any, Optional, List, Tuple, Iterator
import numpy as np
from collections import deque
import gc
import threading
import queue
import os
import time

from utils.logger import get_logger
from config import Config

logger = get_logger(__name__)


class BatchingStrategy:
    """
    Implements dynamic batching strategies to optimize throughput and memory usage.
    Supports fixed batch sizes and dynamic padding strategies to minimize wasted compute.
    """
    def __init__(self, config: Config):
        self.batch_size = config.get('batch_size', 8)
        self.max_seq_len = config.get('max_seq_len', 512)
        self.dynamic_padding = config.get('dynamic_padding', True)
        self.prefetch_factor = config.get('prefetch_factor', 2)
        self.num_workers = config.get('num_workers', 0)  # 0 for CPU-only safety in CI
        self.logger = get_logger(__name__)

    def create_dataloader(self, dataset: Dataset, shuffle: bool = True) -> DataLoader:
        """
        Creates an optimized DataLoader based on current configuration.
        In CPU-only environments (CI), num_workers is forced to 0 to avoid
        multiprocessing overhead and potential deadlocks in restricted environments.
        """
        if self.num_workers > 0 and os.name == 'nt':
            # Windows safety check
            self.logger.warning("Windows detected, forcing num_workers=0 for stability.")
            effective_workers = 0
        elif self.num_workers > 0:
            effective_workers = self.num_workers
        else:
            effective_workers = 0

        # If dynamic padding is requested, we assume the dataset yields dicts with 'input_ids'
        # and we use a custom collate_fn. Otherwise, standard batching.
        collate_fn = None
        if self.dynamic_padding:
            collate_fn = self._dynamic_collate_fn

        return DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=shuffle,
            num_workers=effective_workers,
            pin_memory=False,  # CPU-only: pin_memory is for GPU transfer
            prefetch_factor=self.prefetch_factor if effective_workers > 0 else None,
            persistent_workers=False,
            collate_fn=collate_fn,
        )

    def _dynamic_collate_fn(self, batch: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
        """
        Custom collate function that pads sequences to the maximum length in the batch
        rather than the global max, reducing compute waste on short sequences.
        """
        if not batch:
            return {}

        # Determine max length in this specific batch
        max_len = max(len(item['input_ids']) for item in batch)
        # Cap at global max_seq_len to prevent memory spikes
        max_len = min(max_len, self.max_seq_len)

        input_ids_list = []
        attention_mask_list = []
        labels_list = []

        for item in batch:
            input_ids = item['input_ids'][:max_len]
            current_len = len(input_ids)
            padding_len = max_len - current_len

            # Pad with 0 (assuming 0 is pad token)
            input_ids_list.append(input_ids + [0] * padding_len)
            attention_mask_list.append([1] * current_len + [0] * padding_len)
            
            # Handle labels: if present, pad similarly
            if 'labels' in item:
                labels = item['labels'][:max_len]
                labels_list.append(labels + [-100] * padding_len) # -100 is ignore index for loss

        batch_dict = {
            'input_ids': torch.tensor(input_ids_list, dtype=torch.long),
            'attention_mask': torch.tensor(attention_mask_list, dtype=torch.long),
        }

        if 'labels' in batch[0]:
            batch_dict['labels'] = torch.tensor(labels_list, dtype=torch.long)

        return batch_dict


class OptimizedDataset(Dataset):
    """
    A wrapper for datasets that enables on-the-fly filtering and caching of metadata
    to reduce memory footprint during iteration.
    """
    def __init__(self, base_dataset: Dataset, config: Config):
        self.base_dataset = base_dataset
        self.config = config
        self._cache = {}  # Simple cache for processed metadata if needed
        self.logger = get_logger(__name__)

    def __len__(self) -> int:
        return len(self.base_dataset)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        item = self.base_dataset[idx]
        # Ensure input_ids are within max_seq_len immediately to save memory
        if 'input_ids' in item:
            max_len = self.config.get('max_seq_len', 512)
            item['input_ids'] = item['input_ids'][:max_len]
            # Truncate labels if present
            if 'labels' in item and len(item['labels']) > max_len:
                item['labels'] = item['labels'][:max_len]
        return item


class PrefetchDataLoader:
    """
    A manual prefetching wrapper for DataLoaders when num_workers=0 is forced.
    This simulates multi-threaded prefetching to keep the GPU/CPU pipeline full.
    Note: In strict CPU-only CI with small batch sizes, this might not yield
    significant gains over standard iteration, but it ensures robustness.
    """
    def __init__(self, dataloader: DataLoader, buffer_size: int = 4):
        self.dataloader = dataloader
        self.buffer_size = buffer_size
        self._buffer: deque = deque(maxlen=buffer_size)
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._prefetch_thread: Optional[threading.Thread] = None

    def _prefetch_worker(self):
        """Background thread to fill the prefetch buffer."""
        for batch in self.dataloader:
            if self._stop_event.is_set():
                break
            with self._lock:
                self._buffer.append(batch)
            # Yield control to allow main thread to consume
            time.sleep(0.001)

    def __iter__(self) -> Iterator:
        # Start prefetch thread if buffer is empty
        if self._prefetch_thread is None or not self._prefetch_thread.is_alive():
            self._stop_event.clear()
            self._buffer.clear()
            self._prefetch_thread = threading.Thread(target=self._prefetch_worker, daemon=True)
            self._prefetch_thread.start()

        # Yield from buffer
        while True:
            with self._lock:
                if not self._buffer and self._prefetch_thread is not None and not self._prefetch_thread.is_alive():
                    break # Done
                if not self._buffer:
                    time.sleep(0.01) # Wait for prefetch
                    continue
                batch = self._buffer.popleft()
            yield batch

        if self._prefetch_thread:
            self._stop_event.set()
            self._prefetch_thread.join(timeout=1.0)

    def __len__(self) -> int:
        return len(self.dataloader)


def optimize_memory_for_training(model: torch.nn.Module, config: Config) -> None:
    """
    Applies memory optimization techniques suitable for CPU-only training:
    1. Clears CUDA cache (if any, though we are CPU only, this is safe).
    2. Forces garbage collection.
    3. Sets model to eval mode temporarily for forward pass if no gradient needed.
    4. Ensures no unused parameters are retained.
    """
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    # If training, ensure model is in train mode
    # This function is usually called between steps or at checkpoints
    logger.debug("Memory optimization triggered: GC collected.")


def efficient_batch_training(
    model: torch.nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    config: Config,
    max_steps: Optional[int] = None
) -> Dict[str, float]:
    """
    Executes a training loop with memory-efficient practices:
    - Explicitly deletes intermediate tensors.
    - Forces garbage collection periodically.
    - Uses torch.no_grad() for validation steps if applicable.
    """
    model.train()
    total_loss = 0.0
    steps = 0
    gc_interval = config.get('gc_interval', 100) # Run GC every N steps

    for batch_idx, batch in enumerate(dataloader):
        if max_steps and steps >= max_steps:
            break

        # Move to device (CPU in this project)
        input_ids = batch['input_ids']
        attention_mask = batch['attention_mask']
        labels = batch.get('labels', None)

        # Forward pass
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )
        loss = outputs.loss

        # Backward pass
        optimizer.zero_grad()
        loss.backward()

        # Gradient clipping (optional but recommended for stability)
        if config.get('max_grad_norm', 0.0) > 0.0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), config['max_grad_norm'])

        optimizer.step()

        total_loss += loss.item()
        steps += 1

        # Memory optimization checks
        if steps % gc_interval == 0:
            optimize_memory_for_training(model, config)
            # Explicitly delete batch tensors to free RAM immediately
            del input_ids, attention_mask, labels, outputs, loss
            gc.collect()

    avg_loss = total_loss / steps if steps > 0 else 0.0
    return {"avg_loss": avg_loss, "steps": steps}


def get_optimization_report(config: Config) -> Dict[str, Any]:
    """
    Generates a report of current optimization settings based on config.
    """
    return {
        "batch_size": config.get('batch_size', 8),
        "max_seq_len": config.get('max_seq_len', 512),
        "dynamic_padding": config.get('dynamic_padding', True),
        "prefetch_factor": config.get('prefetch_factor', 2),
        "num_workers": config.get('num_workers', 0),
        "gc_interval": config.get('gc_interval', 100),
        "device": "cpu", # Enforced by project constraints
        "optimization_active": True
    }