"""
Memory-aware data loading for microstructure images.
Implements OOM-safe batch loading with dynamic batch size adjustment.
"""
import os
import gc
import json
import logging
import time
import traceback
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Iterator

import torch
import torch.utils.data as data
from torchvision import transforms
from PIL import Image
import numpy as np

from utils.config import get_data_dir, get_processed_dir, get_results_dir, get_seed, set_seed
from data.models import MicrostructureImage

# Configuration constants for memory management
MAX_MEMORY_GB = 7.0  # Threshold to trigger OOM protection
MIN_BATCH_SIZE = 1
MAX_RETRIES = 5
INITIAL_BATCH_SIZE = 32
BATCH_SIZE_REDUCTION_FACTOR = 2

logger = logging.getLogger(__name__)


def _get_available_memory_gb() -> float:
    """Estimate available GPU/CPU memory in GB."""
    if torch.cuda.is_available():
        try:
            total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            allocated = torch.cuda.memory_allocated(0) / (1024**3)
            reserved = torch.cuda.memory_reserved(0) / (1024**3)
            available = total - allocated
            logger.debug(f"GPU Memory: Total={total:.2f}GB, Allocated={allocated:.2f}GB, Available={available:.2f}GB")
            return available
        except Exception as e:
            logger.warning(f"Could not query GPU memory: {e}")
            return MAX_MEMORY_GB
    else:
        # CPU fallback: estimate based on typical system constraints
        # In practice, this is a heuristic; real systems should monitor RSS
        return MAX_MEMORY_GB


def _clear_memory() -> None:
    """Force garbage collection and clear GPU caches."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()


def get_optimal_batch_size(target_memory_fraction: float = 0.6) -> int:
    """
    Estimate a safe batch size based on available memory.
    Returns an integer batch size that should fit within target_memory_fraction of available memory.
    """
    available_gb = _get_available_memory_gb()
    target_gb = available_gb * target_memory_fraction

    # Heuristic: Assume ~200MB per batch of 32 images at 224x224 with augmentations
    # This is a rough estimate; real usage depends on model size and augmentations
    estimated_mb_per_batch_of_32 = 200
    estimated_mb_per_item = estimated_mb_per_batch_of_32 / 32

    target_mb = target_gb * 1024
    estimated_batch_size = int(target_mb / estimated_mb_per_item)

    # Clamp to valid range
    batch_size = max(MIN_BATCH_SIZE, min(estimated_batch_size, 128))

    logger.info(f"Estimated optimal batch size: {batch_size} (Available: {available_gb:.2f}GB, Target: {target_gb:.2f}GB)")
    return batch_size


class MicrostructureDataset(data.Dataset):
    """
    Dataset for loading microstructure images and their yield strength labels.
    Reads from processed manifest and loads images on-the-fly.
    """
    def __init__(self, manifest_path: str, transform: Optional[transforms.Compose] = None):
        """
        Args:
            manifest_path: Path to CSV manifest file with columns: filename, yield_strength
            transform: Optional torchvision transform to apply to images
        """
        self.manifest_path = Path(manifest_path)
        self.transform = transform
        self.data_dir = get_processed_dir()
        self.samples: List[Dict[str, Any]] = []

        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {self.manifest_path}")

        # Load manifest
        with open(self.manifest_path, 'r', newline='', encoding='utf-8') as f:
            import csv
            reader = csv.DictReader(f)
            for row in reader:
                if 'filename' in row and 'yield_strength' in row:
                    self.samples.append({
                        'image_path': self.data_dir / row['filename'],
                        'yield_strength': float(row['yield_strength'])
                    })

        logger.info(f"Loaded {len(self.samples)} samples from manifest: {self.manifest_path}")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, float]:
        sample = self.samples[idx]
        image_path = sample['image_path']
        yield_strength = sample['yield_strength']

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Load image
        image = Image.open(image_path).convert('RGB')

        if self.transform:
            image = self.transform(image)

        return image, yield_strength


class OOMSafeDataLoader:
    """
    Wrapper around torch.utils.data.DataLoader that implements OOM-safe loading.
    Automatically reduces batch size on OutOfMemory errors and retries.
    """
    def __init__(
        self,
        dataset: data.Dataset,
        batch_size: Optional[int] = None,
        shuffle: bool = True,
        num_workers: int = 0,
        pin_memory: bool = False,
        persistent_workers: bool = False,
        max_retries: int = MAX_RETRIES
    ):
        """
        Args:
            dataset: PyTorch Dataset
            batch_size: Initial batch size. If None, estimates optimal size.
            shuffle: Whether to shuffle data
            num_workers: Number of worker processes for data loading
            pin_memory: Whether to pin memory for faster GPU transfer
            persistent_workers: Whether to keep workers alive
            max_retries: Maximum number of retries with reduced batch size
        """
        self.dataset = dataset
        self.shuffle = shuffle
        self.num_workers = num_workers
        self.pin_memory = pin_memory
        self.persistent_workers = persistent_workers
        self.max_retries = max_retries

        if batch_size is None:
            self.batch_size = get_optimal_batch_size()
        else:
            self.batch_size = batch_size

        self._loader: Optional[data.DataLoader] = None
        self._current_batch_size = self.batch_size
        self._retry_count = 0
        self._last_error: Optional[Exception] = None

        logger.info(f"OOMSafeDataLoader initialized with batch_size={self._current_batch_size}")

    def _create_loader(self) -> data.DataLoader:
        """Create a new DataLoader instance with current settings."""
        return data.DataLoader(
            self.dataset,
            batch_size=self._current_batch_size,
            shuffle=self.shuffle,
            num_workers=self.num_workers,
            pin_memory=self.pin_memory,
            persistent_workers=self.persistent_workers and self.num_workers > 0,
            drop_last=False
        )

    def _reduce_batch_size(self) -> bool:
        """Reduce batch size by factor. Returns False if already at minimum."""
        if self._current_batch_size <= MIN_BATCH_SIZE:
            return False

        self._current_batch_size = max(MIN_BATCH_SIZE, self._current_batch_size // BATCH_SIZE_REDUCTION_FACTOR)
        self._retry_count += 1
        logger.warning(f"OOM detected. Reducing batch size to {self._current_batch_size} (Retry {self._retry_count}/{self.max_retries})")
        return True

    def __iter__(self) -> Iterator[Tuple[torch.Tensor, torch.Tensor]]:
        """
        Iterate over batches with OOM protection.
        Yields (images, labels) tuples.
        """
        if self._loader is None:
            self._loader = self._create_loader()

        try:
            for batch in self._loader:
                yield batch
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                self._last_error = e
                _clear_memory()

                if self._reduce_batch_size():
                    logger.info(f"Retrying with batch_size={self._current_batch_size}")
                    self._loader = self._create_loader()
                    # Retry the iteration
                    return iter(self)
                else:
                    logger.error(f"Cannot reduce batch size further. Min batch size reached.")
                    raise
            else:
                raise

    def __len__(self) -> int:
        """Return the number of batches."""
        return (len(self.dataset) + self._current_batch_size - 1) // self._current_batch_size

    def get_current_batch_size(self) -> int:
        """Get the current batch size being used."""
        return self._current_batch_size

    def get_stats(self) -> Dict[str, Any]:
        """Return statistics about the loader's performance."""
        return {
            "initial_batch_size": self.batch_size,
            "current_batch_size": self._current_batch_size,
            "retries": self._retry_count,
            "dataset_size": len(self.dataset),
            "num_batches": len(self)
        }


def main():
    """
    CLI entry point to test the OOM-safe loader.
    Usage: python -m code.data.loader --manifest <path> --batch-size <size> --stress-test
    """
    import argparse

    parser = argparse.ArgumentParser(description="Test OOM-safe data loader")
    parser.add_argument("--manifest", type=str, required=True, help="Path to manifest CSV")
    parser.add_argument("--batch-size", type=int, default=None, help="Initial batch size (auto if None)")
    parser.add_argument("--stress-test", action="store_true", help="Run stress test to verify memory management")
    parser.add_argument("--num-workers", type=int, default=0, help="Number of data loading workers")
    args = parser.parse_args()

    setup_logging()
    logger.info("Starting OOM-safe loader test")

    # Setup transform
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    try:
        dataset = MicrostructureDataset(args.manifest, transform=transform)
        loader = OOMSafeDataLoader(
            dataset,
            batch_size=args.batch_size,
            num_workers=args.num_workers,
            pin_memory=True
        )

        logger.info(f"Dataset size: {len(dataset)}")
        logger.info(f"Initial batch size: {loader.get_current_batch_size()}")

        total_samples = 0
        start_time = time.time()

        for i, (images, labels) in enumerate(loader):
            total_samples += images.size(0)
            if args.stress_test and i >= 10:
                break

        elapsed = time.time() - start_time
        logger.info(f"Processed {total_samples} samples in {elapsed:.2f}s")
        logger.info(f"Final batch size: {loader.get_current_batch_size()}")
        logger.info(f"Stats: {json.dumps(loader.get_stats(), indent=2)}")

        # Verify memory cleanup
        _clear_memory()
        logger.info("Memory cleanup completed")

    except Exception as e:
        logger.error(f"Error during loader test: {e}")
        traceback.print_exc()
        return 1

    return 0


def setup_logging():
    """Configure logging for the loader module."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(get_results_dir() / "loader.log", mode='a')
        ]
    )


if __name__ == "__main__":
    setup_logging()
    exit(main())