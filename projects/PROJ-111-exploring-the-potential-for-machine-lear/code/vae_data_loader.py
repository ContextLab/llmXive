"""
VAE Data Loader Module for US2.

Integrates data loaders from US1 (preprocessing output) and implements
batch processing with strict memory monitoring to ensure fit within 7GB RAM.
"""
import os
import logging
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from typing import Optional, Tuple, List, Dict, Any
import psutil
import sys

from config import get_config
from logging_config import get_logger
from preprocessing import load_raw_data, check_memory_usage

logger = get_logger(__name__)

class SpinDataset(Dataset):
    """
    PyTorch Dataset for spin configurations.
    Loads preprocessed data from US1 pipeline.
    """
    def __init__(self, data_path: str, temperature_path: Optional[str] = None):
        """
        Args:
            data_path: Path to the processed numpy file containing spin data.
            temperature_path: Optional path to temperature labels.
        """
        super().__init__()
        self.data_path = data_path
        self.temperature_path = temperature_path
        
        logger.info(f"Loading dataset from {data_path}")
        
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Processed data file not found: {data_path}")
        
        # Load data using US1 preprocessing output format
        # Expected shape: [N, 3, L, L]
        self.data = np.load(data_path, allow_pickle=True)
        
        if self.temperature_path and os.path.exists(self.temperature_path):
            self.temperatures = np.load(self.temperature_path, allow_pickle=True)
        else:
            self.temperatures = None
        
        logger.info(f"Loaded {len(self.data)} samples with shape {self.data.shape}")
        
        # Validate data integrity
        if len(self.data.shape) != 4:
            raise ValueError(f"Expected 4D data [N, 3, L, L], got {self.data.shape}")
        
        if self.data.shape[1] != 3:
            raise ValueError(f"Expected 3 spin components, got {self.data.shape[1]}")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        sample = self.data[idx]
        
        # Convert to torch tensor
        if isinstance(sample, np.ndarray):
            sample = torch.from_numpy(sample).float()
        
        if self.temperatures is not None:
            temp = self.temperatures[idx]
            if isinstance(temp, np.ndarray):
                temp = torch.from_numpy(temp).float()
            return sample, temp
        
        return sample

def check_batch_memory_usage(batch_size: int, data_shape: Tuple[int, ...], 
                             dtype: torch.dtype = torch.float32) -> bool:
    """
    Estimates memory usage for a single batch and checks against 7GB limit.
    
    Args:
        batch_size: Number of samples in batch
        data_shape: Shape of a single sample (e.g., (3, 16, 16))
        dtype: Data type (default float32 = 4 bytes)
        
    Returns:
        True if batch fits in memory, False otherwise
        
    Raises:
        MemoryError: If batch exceeds 7GB limit
    """
    # Calculate bytes per sample
    bytes_per_element = torch.tensor([], dtype=dtype).element_size()
    elements_per_sample = np.prod(data_shape)
    bytes_per_sample = elements_per_sample * bytes_per_element
    
    # Total batch size in bytes
    batch_bytes = batch_size * bytes_per_sample
    batch_gb = batch_bytes / (1024 ** 3)
    
    # Safety margin: allow 80% of 7GB for batch to account for overhead
    max_batch_gb = 7.0 * 0.8
    
    logger.info(f"Batch size {batch_size}, sample shape {data_shape}, "
               f"estimated memory: {batch_gb:.3f} GB (limit: {max_batch_gb:.3f} GB)")
    
    if batch_gb > max_batch_gb:
        raise MemoryError(
            f"Batch size {batch_size} exceeds memory limit. "
            f"Estimated usage: {batch_gb:.3f} GB > {max_batch_gb:.3f} GB. "
            f"Reduce batch size or use smaller lattice size."
        )
    
    return True

def create_vae_dataloader(data_path: str, batch_size: int = 64, 
                          temperature_path: Optional[str] = None,
                          shuffle: bool = True,
                          num_workers: int = 0,
                          pin_memory: bool = True) -> DataLoader:
    """
    Creates a DataLoader for VAE training with memory safety checks.
    
    Args:
        data_path: Path to preprocessed data file
        batch_size: Number of samples per batch
        temperature_path: Optional path to temperature labels
        shuffle: Whether to shuffle data
        num_workers: Number of worker processes for data loading
        pin_memory: Whether to pin memory for faster CUDA transfer (if applicable)
        
    Returns:
        Configured DataLoader
        
    Raises:
        MemoryError: If batch size would exceed 7GB limit
    """
    config = get_config()
    
    # Get sample shape from first element
    dataset = SpinDataset(data_path, temperature_path)
    sample_shape = dataset.data.shape[1:]  # (3, L, L)
    
    # Check memory usage before creating dataloader
    check_batch_memory_usage(batch_size, sample_shape)
    
    logger.info(f"Creating DataLoader with batch_size={batch_size}, "
               f"dataset_size={len(dataset)}, num_workers={num_workers}")
    
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=pin_memory,
        drop_last=True,  # Ensure consistent batch sizes
        persistent_workers=False if num_workers == 0 else True
    )
    
    return dataloader

def main():
    """
    Main function to demonstrate data loader integration and memory checks.
    Runs a validation test to ensure batch processing fits within 7GB RAM.
    """
    config = get_config()
    
    # Setup logging
    log_dir = config.get("log_dir", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    logger.info("Starting VAE Data Loader Integration Test")
    
    # Test parameters
    test_lattice_sizes = [16, 24]
    test_batch_sizes = [32, 64, 128]
    
    for L in test_lattice_sizes:
        logger.info(f"\nTesting lattice size L={L}")
        
        # Construct expected data path based on US1 output structure
        data_path = f"data/processed/spins_L{L}_processed.npy"
        temp_path = f"data/processed/temps_L{L}_processed.npy"
        
        if not os.path.exists(data_path):
            logger.warning(f"Data file not found: {data_path}. Skipping L={L}")
            continue
        
        for batch_size in test_batch_sizes:
            try:
                logger.info(f"  Testing batch_size={batch_size}...")
                
                # Create dataloader (this will validate memory)
                dataloader = create_vae_dataloader(
                    data_path=data_path,
                    batch_size=batch_size,
                    temperature_path=temp_path,
                    shuffle=False,
                    num_workers=0
                )
                
                # Verify we can iterate
                sample_batch = next(iter(dataloader))
                if isinstance(sample_batch, tuple):
                    x, y = sample_batch
                    logger.info(f"    ✓ Batch shape: {x.shape}, Temp shape: {y.shape}")
                else:
                    logger.info(f"    ✓ Batch shape: {sample_batch.shape}")
                
                logger.info(f"    ✓ Memory check passed for L={L}, batch_size={batch_size}")
                
            except MemoryError as e:
                logger.error(f"    ✗ Memory error for L={L}, batch_size={batch_size}: {e}")
            except Exception as e:
                logger.error(f"    ✗ Error for L={L}, batch_size={batch_size}: {e}")
    
    logger.info("\nData loader integration test completed.")

if __name__ == "__main__":
    main()
