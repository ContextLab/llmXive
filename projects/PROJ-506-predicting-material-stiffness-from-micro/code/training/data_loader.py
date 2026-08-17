"""
Data loading and batching utilities for microstructure stiffness prediction.

Implements a streaming DataLoader that processes image metadata in chunks
to respect RAM limits while training on large datasets.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Generator, Optional, Any
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from skimage import io
from code.training.kfold_utils import load_dataset_metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MicrostructureDataset(Dataset):
    """
    A PyTorch Dataset that loads microstructure images and stiffness tensors
    on-demand from disk based on a metadata list.
    """
    def __init__(self, metadata_entries: List[Dict[str, Any]], target_key: str = "stiffness_tensor"):
        """
        Args:
            metadata_entries: List of dicts containing 'image_path' and target values.
            target_key: The key in the metadata dict to use as the target label.
        """
        self.metadata = metadata_entries
        self.target_key = target_key
        self.image_size = (128, 128)  # As per FR-001

    def __len__(self) -> int:
        return len(self.metadata)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        entry = self.metadata[idx]
        
        # Load image
        img_path = Path(entry["image_path"])
        if not img_path.exists():
            raise FileNotFoundError(f"Image not found: {img_path}")
        
        image = io.imread(img_path)
        
        # Normalize to [0, 1] if not already (assuming uint8 or float)
        if image.dtype == np.uint8:
            image = image.astype(np.float32) / 255.0
        elif image.max() > 1.0:
            # Handle other integer types
            image = image.astype(np.float32) / image.max()
        
        # Ensure shape is (C, H, W) for CNN
        if image.ndim == 2:
            image = image[np.newaxis, ...]
        elif image.ndim == 3 and image.shape[2] == 1:
            image = image[:, :, 0]
            image = image[np.newaxis, ...]
        
        # Resample if necessary (though generation should be 128x128)
        if image.shape[1:] != self.image_size:
            # Simple resize using numpy for speed, or use torchvision.transforms
            # For this implementation, we assume 128x128 as per spec
            logger.warning(f"Image {img_path} is not {self.image_size}, resizing.")
            from skimage.transform import resize
            image = resize(image, (image.shape[0], *self.image_size), anti_aliasing=True)
        
        # Convert to tensor
        image_tensor = torch.from_numpy(image).float()
        
        # Get target
        target = np.array(entry[self.target_key], dtype=np.float32)
        target_tensor = torch.from_numpy(target).float()
        
        return image_tensor, target_tensor

class MicrostructureDataLoader:
    """
    A wrapper around PyTorch DataLoader that handles streaming/batching
    of large datasets by loading metadata in chunks.
    
    This class ensures that we do not load the entire dataset into memory
    at once, respecting RAM limits (~7GB) by processing in batches.
    """
    def __init__(
        self, 
        metadata_path: Path, 
        batch_size: int = 32, 
        shuffle: bool = True, 
        num_workers: int = 0,
        pin_memory: bool = False
    ):
        """
        Args:
            metadata_path: Path to the JSON metadata file containing dataset info.
            batch_size: Number of samples per batch.
            shuffle: Whether to shuffle the data.
            num_workers: Number of subprocesses for data loading (0 = main thread).
            pin_memory: Whether to pin memory for faster GPU transfer (not used here as CPU-only).
        """
        self.metadata_path = Path(metadata_path)
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.num_workers = num_workers
        self.pin_memory = pin_memory
        
        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_path}")

    def __iter__(self) -> Generator[Tuple[torch.Tensor, torch.Tensor], None, None]:
        """
        Yields batches of (image, stiffness_tensor) tuples.
        
        This method loads the full metadata once (which is small), then yields
        batches from the Dataset. The Dataset itself loads images on-demand.
        """
        # Load metadata (lightweight compared to images)
        logger.info(f"Loading metadata from {self.metadata_path}")
        metadata_entries = load_dataset_metadata(self.metadata_path)
        
        if not metadata_entries:
            logger.warning("No metadata entries found.")
            return
        
        # Create the dataset
        dataset = MicrostructureDataset(metadata_entries)
        
        # Create DataLoader
        # Note: Since we are yielding batches, we use the standard DataLoader
        # which handles batching internally. The 'iter' on DataLoader yields batches.
        loader = DataLoader(
            dataset, 
            batch_size=self.batch_size, 
            shuffle=self.shuffle, 
            num_workers=self.num_workers,
            pin_memory=self.pin_memory,
            drop_last=False # Keep last batch even if smaller
        )
        
        for batch in loader:
            yield batch

    def get_dataset_size(self) -> int:
        """Returns the total number of samples in the dataset."""
        metadata_entries = load_dataset_metadata(self.metadata_path)
        return len(metadata_entries)

def main():
    """
    Simple test runner to verify the DataLoader works end-to-end.
    Expects a metadata file at data/processed/metadata.json (or similar).
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test MicrostructureDataLoader")
    parser.add_argument("--metadata", type=str, required=True, help="Path to metadata JSON")
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--check_batches", type=int, default=5, help="Number of batches to check")
    args = parser.parse_args()
    
    loader = MicrostructureDataLoader(
        metadata_path=Path(args.metadata),
        batch_size=args.batch_size
    )
    
    logger.info(f"Dataset size: {loader.get_dataset_size()}")
    
    count = 0
    for i, (images, targets) in enumerate(loader):
        logger.info(f"Batch {i}: images shape={images.shape}, targets shape={targets.shape}")
        count += 1
        if count >= args.check_batches:
            break
    
    logger.info("DataLoader test completed successfully.")

if __name__ == "__main__":
    main()