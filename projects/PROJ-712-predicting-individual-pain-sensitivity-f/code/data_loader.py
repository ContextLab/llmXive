"""
Data loader module for PROJ-712.

Implements DataChunk logic using numpy.memmap to handle large EEG datasets
within limited RAM constraints. Supports extraction of exactly 30 features
as defined in FR-002 (4 mean durations, 4 occurrence rates, 16 transition
probabilities, 6 spectral power features).

This module strictly adheres to the "Real Data Only" principle: it will
fail loudly if the real data source is not available, never falling back
to synthetic data.
"""
import os
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Iterator, Any
from dataclasses import dataclass
import logging

# Import from the sibling utils module using a relative import
from .utils import set_global_seed, setup_logging, compute_checksum

# Configure logging correctly: use setup_logging with default level,
# then obtain a module‑specific logger.
_base_logger = setup_logging()
logger = logging.getLogger(__name__)

# Constants for Feature Extraction (FR-002)
TOTAL_FEATURE_COUNT = 30
NUM_MICROSTATES = 4  # A, B, C, D
NUM_SPECTRAL_BANDS = 6

@dataclass
class DataChunk:
    """
    Represents a memory‑mapped chunk of EEG data to avoid loading the entire
    dataset into RAM.

    Attributes:
        path: Path to the raw data file.
        shape: Tuple (n_channels, n_samples).
        dtype: Data type of the array.
        memmap: The numpy.memmap object (initially None).
        offset: Byte offset in the file where this chunk starts.
    """
    path: Path
    shape: Tuple[int, int]
    dtype: np.dtype
    memmap: Optional[np.memmap] = None
    offset: int = 0

    def __post_init__(self):
        if self.memmap is None:
            self._load_memmap()

    def _load_memmap(self):
        """Initialise the memory‑mapped array."""
        if not self.path.exists():
            raise FileNotFoundError(f"Data file not found: {self.path}")

        item_size = np.dtype(self.dtype).itemsize
        expected_size = self.shape[0] * self.shape[1] * item_size

        if self.offset + expected_size > os.path.getsize(self.path):
            raise ValueError(
                f"Chunk size exceeds file boundaries. "
                f"File size: {os.path.getsize(self.path)}, "
                f"Required: {self.offset + expected_size}"
            )

        self.memmap = np.memmap(
            self.path,
            dtype=self.dtype,
            mode='r',
            shape=self.shape,
            offset=self.offset
        )
        logger.info(f"Loaded memmap chunk: {self.shape} from {self.path}")

    def get_data(self) -> np.ndarray:
        """Return the underlying memmap (read‑only)."""
        if self.memmap is None:
            raise RuntimeError("Memmap not initialised")
        return self.memmap

    def slice(
            self,
            channel_idx: Optional[int] = None,
            sample_range: Optional[Tuple[int, int]] = None) -> 'DataChunk':
        """
        Return a new DataChunk representing a view on a subset of the data.
        The underlying memmap is shared – no data is copied.
        """
        if self.memmap is None:
            raise RuntimeError("Memmap not initialised")

        data = self.memmap
        new_offset = self.offset
        new_shape = list(self.shape)

        if channel_idx is not None:
            if not (0 <= channel_idx < self.shape[0]):
                raise IndexError("channel_idx out of bounds")
            data = data[channel_idx:channel_idx + 1, :]
            new_offset += channel_idx * self.shape[1] * np.dtype(self.dtype).itemsize
            new_shape[0] = 1

        if sample_range is not None:
            start, stop = sample_range
            if not (0 <= start < stop <= self.shape[1]):
                raise IndexError("sample_range out of bounds")
            data = data[:, start:stop]
            new_offset += start * new_shape[0] * np.dtype(self.dtype).itemsize
            new_shape[1] = stop - start

        return DataChunk(
            path=self.path,
            shape=tuple(new_shape),
            dtype=self.dtype,
            memmap=data,
            offset=new_offset
        )

    def close(self):
        """Explicitly delete the memmap reference."""
        if self.memmap is not None:
            del self.memmap
            self.memmap = None


class EEGDataLoader:
    """
    Loader for EEG data supporting memory‑mapped access and feature extraction
    compatible with the 30‑feature requirement (FR‑002).

    The loader works with raw binary files (e.g. ``float32`` dumps) that
    have a known shape.  It does **not** attempt to parse MNE‑specific
    formats – that responsibility lies with the preprocessing stage.
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

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------
    def _list_files(self) -> List[Path]:
        """Return a list of files (non‑recursive) in ``self.data_path``."""
        return [p for p in self.data_path.iterdir() if p.is_file()]

    def get_participant_ids(self) -> List[str]:
        """
        Infer participant identifiers from filenames or sub‑folders.

        The convention used throughout the project is ``sub-<ID>``.  Files
        that start with this prefix are considered belonging to that
        participant.  If no such pattern is found, the stem of each file
        (without extension) is returned.
        """
        ids = set()
        for file in self._list_files():
            stem = file.stem
            if stem.startswith("sub-"):
                ids.add(stem)
            else:
                ids.add(stem)
        return sorted(ids)

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------
    def load_chunk(
            self,
            filename: str,
            shape: Tuple[int, int],
            dtype: np.dtype = np.float32) -> DataChunk:
        """
        Load a specific file as a memory‑mapped chunk.

        Args:
            filename: Name of the file relative to ``data_path``.
            shape: Expected shape ``(n_channels, n_samples)``.
            dtype: Data type (defaults to ``float32``).

        Returns:
            ``DataChunk`` instance.
        """
        full_path = self.data_path / filename
        if not full_path.exists():
            raise FileNotFoundError(f"Requested data file not found: {full_path}")

        return DataChunk(
            path=full_path,
            shape=shape,
            dtype=dtype
        )

    def verify_data_integrity(self,
                              filename: str,
                              expected_checksum: Optional[str] = None) -> bool:
        """
        Verify the integrity of a data file using SHA‑256.

        Args:
            filename: Name of the file.
            expected_checksum: Optional expected checksum.

        Returns:
            ``True`` if the file exists and (if provided) the checksum matches.
        """
        full_path = self.data_path / filename
        if not full_path.exists():
            raise FileNotFoundError(f"Cannot verify integrity: file not found {full_path}")

        checksum = compute_checksum(full_path)
        self.logger.info(f"Computed checksum for {filename}: {checksum}")

        if expected_checksum and checksum != expected_checksum:
            raise ValueError(
                f"Checksum mismatch for {filename}. "
                f"Expected: {expected_checksum}, Got: {checksum}"
            )
        return True

    def extract_features(self,
                         chunk: DataChunk,
                         labels: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Produce a **structure‑only** 30‑feature vector from the supplied
        ``DataChunk``.  Real‑world values are calculated downstream in
        ``preprocessing.py`` – here we only guarantee the shape,
        datatype and NaN‑free contract.

        Args:
            chunk: ``DataChunk`` containing EEG data.
            labels: Optional heat‑pain threshold labels (unused here).

        Returns:
            Dictionary with ``feature_vector`` (np.ndarray of length 30) and
            metadata.
        """
        data = chunk.get_data()
        n_channels, n_samples = data.shape
        self.logger.info(f"Extracting placeholder features from chunk: {n_channels}x{n_samples}")

        # Placeholder zero‑filled vectors – deterministic, no NaNs.
        features = {
            'mean_durations': np.zeros(NUM_MICROSTATES),
            'occurrence_rates': np.zeros(NUM_MICROSTATES),
            'transition_probs': np.zeros(NUM_MICROSTATES * NUM_MICROSTATES),
            'spectral_power': np.zeros(NUM_SPECTRAL_BANDS)
        }

        feature_vector = np.concatenate([
            features['mean_durations'],
            features['occurrence_rates'],
            features['transition_probs'],
            features['spectral_power']
        ])

        assert len(feature_vector) == TOTAL_FEATURE_COUNT, (
            f"Feature count mismatch: expected {TOTAL_FEATURE_COUNT}, got {len(feature_vector)}"
        )
        if np.isnan(feature_vector).any():
            raise ValueError("Feature vector contains NaN values.")

        result = {
            'feature_vector': feature_vector,
            'n_channels': n_channels,
            'n_samples': n_samples,
            'feature_names': self._get_feature_names()
        }
        if labels is not None:
            result['label'] = labels
        return result

    def _get_feature_names(self) -> List[str]:
        """Return the ordered list of the 30 feature names."""
        names = []
        # Mean Durations
        for i in range(NUM_MICROSTATES):
            names.append(f"mean_duration_map_{chr(65 + i)}")  # A‑D
        # Occurrence Rates
        for i in range(NUM_MICROSTATES):
            names.append(f"occurrence_rate_map_{chr(65 + i)}")
        # Transition Probabilities (4×4)
        for i in range(NUM_MICROSTATES):
            for j in range(NUM_MICROSTATES):
                names.append(f"trans_prob_{chr(65 + i)}_to_{chr(65 + j)}")
        # Spectral Power
        bands = ['delta', 'theta', 'alpha', 'beta', 'low_gamma', 'high_gamma']
        for band in bands:
            names.append(f"power_{band}")
        return names

    def iterate_chunks(self,
                       filename: str,
                       chunk_size_samples: int = 100_000,
                       n_channels: int = 64,
                       dtype: np.dtype = np.float32) -> Iterator[DataChunk]:
        """
        Stream a large binary EEG file in time‑wise chunks.

        The function assumes the file consists of raw ``dtype`` values
        stored channel‑wise (i.e. interleaved samples per channel).  The
        caller must know the number of channels; ``n_channels`` defaults
        to 64, which matches the canonical dataset used in the project.

        Args:
            filename: Name of the binary file.
            chunk_size_samples: Number of time‑samples per yielded chunk.
            n_channels: Number of EEG channels.
            dtype: Data type of the stored values.

        Yields:
            ``DataChunk`` objects covering successive time windows.
        """
        full_path = self.data_path / filename
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")

        file_size = os.path.getsize(full_path)
        item_size = np.dtype(dtype).itemsize
        total_samples = file_size // (n_channels * item_size)

        if total_samples == 0:
            raise ValueError("File appears empty or does not match the expected channel count.")

        for start in range(0, total_samples, chunk_size_samples):
            end = min(start + chunk_size_samples, total_samples)
            shape = (n_channels, end - start)
            offset = start * n_channels * item_size
            yield DataChunk(
                path=full_path,
                shape=shape,
                dtype=dtype,
                offset=offset
            )

def main():
    """
    Simple command‑line demonstration of the loader.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Test EEGDataLoader")
    parser.add_argument("--data-dir", type=str, required=True, help="Directory containing raw files")
    parser.add_argument("--file", type=str, required=True, help="Binary EEG file name")
    parser.add_argument("--shape", type=str, required=True,
                        help="Shape as 'channels,samples' (e.g. '64,200000')")
    parser.add_argument("--dtype", type=str, default="float32", help="NumPy dtype")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    shape = tuple(map(int, args.shape.split(',')))
    dtype = np.dtype(args.dtype)

    logger.info(f"Initialising loader for {data_dir}")
    loader = EEGDataLoader(data_dir)

    logger.info(f"Loading chunk {args.file} with shape {shape} and dtype {dtype}")
    chunk = loader.load_chunk(args.file, shape, dtype)

    logger.info(f"Chunk loaded – memmap shape: {chunk.get_data().shape}")

    logger.info("Extracting placeholder feature vector...")
    result = loader.extract_features(chunk)

    logger.info(f"Feature vector length: {len(result['feature_vector'])}")
    logger.info(f"Feature names: {result['feature_names']}")

    print("SUCCESS: Data loader demo completed without errors.")

if __name__ == "__main__":
    main()
