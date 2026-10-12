"""
Data loader module for PROJ-712.

Implements DataChunk logic using numpy.memmap to handle large EEG datasets
within limited RAM constraints. This module focuses on the streaming and
chunking of raw binary EEG data to ensure that memory usage remains below
the 7 GB limit.

This module strictly adheres to the "Real Data Only" principle: it will
fail loudly if the real data source is not available, never falling back
to synthetic data.
"""
import os
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple, Iterator
from dataclasses import dataclass
import logging

from utils import set_global_seed, setup_logging

# Configure logging
_base_logger = setup_logging()
logger = logging.getLogger(__name__)

@dataclass
class DataChunk:
    """
    Represents a memory-mapped chunk of EEG data to avoid loading the entire
    dataset into RAM.

    Attributes:
        path: Path to the raw data file.
        shape: Tuple (n_channels, n_samples).
        dtype: Data type of the array.
        offset: Byte offset in the file where this chunk starts.
        memmap: The numpy.memmap object.
    """
    path: Path
    shape: Tuple[int, int]
    dtype: np.dtype
    offset: int
    memmap: Optional[np.memmap] = None

    def __post_init__(self):
        self._initialize_memmap()

    def _initialize_memmap(self):
        """Initialise the memory-mapped array."""
        if not self.path.exists():
            raise FileNotFoundError(f"Data file not found: {self.path}")

        # Ensure the offset and shape are within file boundaries
        item_size = np.dtype(self.dtype).itemsize
        expected_size = self.shape[0] * self.shape[1] * item_size
        if self.offset + expected_size > os.path.getsize(self.path):
            raise ValueError(
                f"Chunk boundaries exceed file size. File: {os.path.getsize(self.path)}, "
                f"Required: {self.offset + expected_size}"
            )

        self.memmap = np.memmap(
            self.path,
            dtype=self.dtype,
            mode='r',
            shape=self.shape,
            offset=self.offset
        )

    def get_data(self) -> np.ndarray:
        """Return the underlying memmap (read-only)."""
        if self.memmap is None:
            raise RuntimeError("Memmap not initialised")
        return self.memmap

    def close(self):
        """Explicitly delete the memmap reference to release resources."""
        if self.memmap is not None:
            del self.memmap
            self.memmap = None

class EEGDataLoader:
    """
    Loader for EEG data supporting memory-mapped access and streaming.
    Designed to handle raw binary files (e.g., float32 dumps) to respect
    RAM constraints.
    """

    def __init__(self, data_path: Path, seed: int = 42):
        """
        Initialise the loader.

        Args:
            data_path: Directory containing raw EEG files.
            seed: Random seed for reproducibility.
        """
        self.data_path = Path(data_path)
        set_global_seed(seed)
        self.logger = logging.getLogger(self.__class__.__name__)

        if not self.data_path.exists():
            raise FileNotFoundError(f"Data path does not exist: {self.data_path}")

    def get_participant_ids(self) -> List[str]:
        """
        Infer participant identifiers from filenames.
        Assumes filenames start with 'sub-' or uses the file stem.
        """
        ids = set()
        for file in self.data_path.iterdir():
            if file.is_file():
                stem = file.stem
                ids.add(stem if stem.startswith("sub-") else stem)
        return sorted(list(ids))

    def load_chunk(
            self,
            filename: str,
            shape: Tuple[int, int],
            offset: int = 0,
            dtype: np.dtype = np.float32) -> DataChunk:
        """
        Load a specific segment of a file as a memory-mapped DataChunk.
        """
        full_path = self.data_path / filename
        return DataChunk(
            path=full_path,
            shape=shape,
            dtype=dtype,
            offset=offset
        )

    def iterate_chunks(self,
                       filename: str,
                       chunk_size_samples: int = 100_000,
                       n_channels: int = 64,
                       dtype: np.dtype = np.float32) -> Iterator[DataChunk]:
        """
        Stream a large binary EEG file in time-wise chunks.
        Assumes data is stored as [n_channels, n_samples].

        Args:
            filename: Name of the binary file.
            chunk_size_samples: Number of samples per yielded chunk.
            n_channels: Number of EEG channels.
            dtype: Data type of the stored values.

        Yields:
            DataChunk objects covering successive time windows.
        """
        full_path = self.data_path / filename
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")

        file_size = os.path.getsize(full_path)
        item_size = np.dtype(dtype).itemsize
        total_samples = file_size // (n_channels * item_size)

        if total_samples == 0:
            raise ValueError("File is empty or does not match the expected channel count.")

        for start in range(0, total_samples, chunk_size_samples):
            end = min(start + chunk_size_samples, total_samples)
            current_chunk_samples = end - start
            offset = start * n_channels * item_size
            
            yield DataChunk(
                path=full_path,
                shape=(n_channels, current_chunk_samples),
                dtype=dtype,
                offset=offset
            )

def main():
    """
    Simple command-line demonstration of the loader.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Test EEGDataLoader")
    parser.add_argument("--data-dir", type=str, required=True)
    parser.add_argument("--file", type=str, required=True)
    parser.add_argument("--shape", type=str, required=True, help="channels,samples")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    shape = tuple(map(int, args.shape.split(',')))
    
    loader = EEGDataLoader(data_dir)
    chunk = loader.load_chunk(args.file, shape)
    print(f"SUCCESS: Loaded chunk with shape {chunk.get_data().shape}")

if __name__ == "__main__":
    main()
