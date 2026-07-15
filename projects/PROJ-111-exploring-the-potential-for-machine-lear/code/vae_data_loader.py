"""
Data loader for VAE training integrating US1 preprocessing outputs.
Ensures batch processing fits within 7GB RAM constraint.
"""
import os
import logging
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from typing import Optional, Tuple, List, Dict, Any

# Import from existing US1 modules
from preprocessing import load_raw_data, normalize_spins, reshape_to_batch, stratified_split, save_processed_data
from config import get_config

logger = logging.getLogger(__name__)

# Memory constraint constants (7GB limit as per task requirement)
MAX_MEMORY_GB = 7.0
MAX_MEMORY_BYTES = MAX_MEMORY_GB * 1024**3

class SpinDataset(Dataset):
    """
    PyTorch Dataset for spin configurations.
    Loads data in batches to manage memory usage.
    """
    def __init__(self, processed_data_path: str, batch_size: int = 32):
        """
        Initialize dataset with processed spin data.
        
        Args:
            processed_data_path: Path to the processed data file (.npy)
            batch_size: Size of batches for memory management
        """
        self.batch_size = batch_size
        self.data_path = processed_data_path
        
        if not os.path.exists(processed_data_path):
            raise FileNotFoundError(f"Processed data not found at: {processed_data_path}")
        
        # Load metadata first to estimate memory requirements
        self._load_metadata()
        self._validate_memory_requirements()
        
        # Load data in memory-mapped mode for large datasets
        self.data = np.load(processed_data_path, mmap_mode='r')
        logger.info(f"Loaded dataset: {self.data.shape}, dtype: {self.data.dtype}")

    def _load_metadata(self) -> None:
        """Load dataset metadata if available."""
        metadata_path = self.data_path.replace('.npy', '_meta.json')
        if os.path.exists(metadata_path):
            import json
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}

    def _validate_memory_requirements(self) -> None:
        """Validate that the dataset fits within memory constraints."""
        # Estimate memory usage: data size + overhead
        estimated_size_bytes = self.data.nbytes * 1.5  # 50% overhead for processing
        estimated_size_gb = estimated_size_bytes / (1024**3)
        
        if estimated_size_gb > MAX_MEMORY_GB:
            raise MemoryError(
                f"Dataset size ({estimated_size_gb:.2f} GB) exceeds memory limit "
                f"({MAX_MEMORY_GB} GB). Consider using smaller batches or streaming."
            )
        
        logger.info(f"Memory check passed: {estimated_size_gb:.2f} GB < {MAX_MEMORY_GB} GB")

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> torch.Tensor:
        """
        Get a single sample or batch.
        
        Args:
            idx: Index or slice of indices
        
        Returns:
            torch.Tensor: Spin configuration(s) as tensor
        """
        if isinstance(idx, slice):
            # Batch access
            batch = self.data[idx]
        else:
            # Single sample access
            batch = self.data[idx:idx+1]
        
        # Convert to torch tensor
        tensor = torch.tensor(batch, dtype=torch.float32)
        
        # Normalize to [0, 1] range if not already (assuming data is normalized)
        # This ensures consistent input distribution for VAE
        if tensor.max() > 1.0 or tensor.min() < -1.0:
            tensor = (tensor - tensor.min()) / (tensor.max() - tensor.min())
        
        return tensor

def create_vae_dataloader(
    data_dir: str,
    split: str = 'train',
    batch_size: int = 32,
    shuffle: bool = True,
    num_workers: int = 0
) -> DataLoader:
    """
    Create a DataLoader for VAE training with memory management.
    
    Args:
        data_dir: Directory containing processed data files
        split: Data split ('train', 'val', 'test')
        batch_size: Batch size for training
        shuffle: Whether to shuffle data
        num_workers: Number of worker processes for data loading
    
    Returns:
        DataLoader: PyTorch DataLoader configured for VAE training
    """
    # Determine data file path based on split
    data_files = {
        'train': 'processed_train.npy',
        'val': 'processed_val.npy',
        'test': 'processed_test.npy'
    }
    
    if split not in data_files:
        raise ValueError(f"Invalid split: {split}. Must be one of {list(data_files.keys())}")
    
    data_path = os.path.join(data_dir, data_files[split])
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Processed data for split '{split}' not found at: {data_path}. "
            f"Run preprocessing first."
        )
    
    # Create dataset
    dataset = SpinDataset(data_path, batch_size=batch_size)
    
    # Create DataLoader with memory-efficient settings
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=False,  # Disable for CPU-only training to avoid CUDA overhead
        drop_last=True,    # Drop incomplete batches
        prefetch_factor=2 if num_workers > 0 else None
    )
    
    logger.info(
        f"Created DataLoader for '{split}' split: "
        f"{len(dataset)} samples, batch_size={batch_size}, "
        f"batches={len(dataloader)}"
    )
    
    return dataloader

def check_batch_memory_usage(
    data_path: str,
    batch_size: int,
    sample_size: int = 100
) -> Dict[str, Any]:
    """
    Estimate memory usage for a given batch size.
    
    Args:
        data_path: Path to processed data file
        batch_size: Proposed batch size
        sample_size: Number of samples to estimate from
    
    Returns:
        Dictionary with memory usage statistics
    """
    try:
        data = np.load(data_path, mmap_mode='r')
        sample_batch = data[:sample_size]
        
        # Calculate memory per sample
        bytes_per_sample = sample_batch.nbytes / sample_size
        bytes_per_batch = bytes_per_sample * batch_size
        gb_per_batch = bytes_per_batch / (1024**3)
        
        # Calculate total dataset size
        total_samples = len(data)
        total_batches = total_samples // batch_size
        total_gb = (bytes_per_sample * total_samples) / (1024**3)
        
        return {
            'bytes_per_sample': bytes_per_sample,
            'bytes_per_batch': bytes_per_batch,
            'gb_per_batch': gb_per_batch,
            'total_samples': total_samples,
            'total_batches': total_batches,
            'total_gb': total_gb,
            'fits_in_memory': gb_per_batch < MAX_MEMORY_GB
        }
    except Exception as e:
        logger.error(f"Error checking memory usage: {e}")
        return {'error': str(e)}

def main():
    """
    Main function to test data loader integration and memory constraints.
    """
    config = get_config()
    data_dir = config.get('paths', {}).get('processed_data', 'data/processed')
    
    logger.info("Testing VAE data loader integration...")
    
    # Test different batch sizes
    test_batch_sizes = [16, 32, 64]
    
    for batch_size in test_batch_sizes:
        logger.info(f"\nTesting batch size: {batch_size}")
        
        # Check memory usage
        mem_info = check_batch_memory_usage(
            os.path.join(data_dir, 'processed_train.npy'),
            batch_size
        )
        
        if 'error' in mem_info:
            logger.warning(f"Memory check failed for batch_size={batch_size}: {mem_info['error']}")
            continue
        
        logger.info(f"  Memory per batch: {mem_info['gb_per_batch']:.3f} GB")
        logger.info(f"  Total dataset: {mem_info['total_gb']:.1f} GB")
        logger.info(f"  Fits in memory: {mem_info['fits_in_memory']}")
        
        if mem_info['fits_in_memory']:
            # Try creating dataloader
            try:
                loader = create_vae_dataloader(data_dir, 'train', batch_size=batch_size)
                logger.info(f"  Successfully created DataLoader with {len(loader)} batches")
                
                # Test a forward pass
                for i, batch in enumerate(loader):
                    if i >= 1:  # Test one batch
                        break
                    logger.info(f"  Batch shape: {batch.shape}, dtype: {batch.dtype}")
                
                logger.info(f"  ✓ Batch size {batch_size} is valid")
            except Exception as e:
                logger.error(f"  ✗ Failed to create DataLoader: {e}")
        else:
            logger.warning(f"  ✗ Batch size {batch_size} exceeds memory limit")

if __name__ == '__main__':
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
