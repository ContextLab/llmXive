"""
Chunked Hyperspectral Data Loader.

Implements a streaming loader for large hyperspectral cubes to prevent OOM errors.
Processes data in configurable chunks, yielding batches of spectral data and labels.
Includes memory monitoring to ensure usage stays within constraints (< 7GB).
"""
import os
import gc
import json
import logging
from pathlib import Path
from typing import Iterator, Tuple, Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
import numpy as np

from code.utils.logger import get_logger
from code.utils.timer import get_current_memory_usage_mb, Timer
from code.utils.config import get_config

# Import existing schemas for type hints if needed, though we use dicts/ndarrays for speed
# from code.models.schemas import ProcessedRecord, BiomassLabel

@dataclass
class ChunkedDataBatch:
    """Container for a single batch of loaded data."""
    spectral_data: np.ndarray  # Shape: (batch_size, num_bands)
    biomass_labels: np.ndarray # Shape: (batch_size,)
    site_ids: np.ndarray       # Shape: (batch_size,)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def shape(self) -> Tuple[int, int]:
        """Returns (batch_size, num_bands)."""
        return self.spectral_data.shape

class ChunkedHyperspectralLoader:
    """
    A memory-efficient loader for hyperspectral data cubes.

    This loader processes data in chunks to avoid loading the entire dataset
    into RAM. It is designed to handle the full HyBiomass/NEON dataset
    while keeping memory usage under 7GB.

    Attributes:
        data_path (Path): Path to the processed data directory.
        chunk_size (int): Number of samples to load per iteration.
        max_memory_gb (float): Maximum allowed memory usage in GB.
        logger: Project logger instance.
    """

    def __init__(
        self,
        data_path: Union[str, Path],
        chunk_size: int = 10000,
        max_memory_gb: float = 7.0,
        logger: Optional[logging.Logger] = None
    ):
        self.data_path = Path(data_path)
        self.chunk_size = chunk_size
        self.max_memory_gb = max_memory_gb
        self.max_memory_bytes = int(max_memory_gb * 1024 ** 3)
        self.logger = logger or get_logger(__name__)

        # Validate data path
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data path does not exist: {self.data_path}")

        # Locate data files (assuming processed CSV or Parquet from T011/T012)
        # We look for the primary processed dataset file
        self.data_files = sorted(self.data_path.glob("*.csv")) + sorted(self.data_path.glob("*.parquet"))
        if not self.data_files:
            raise FileNotFoundError(f"No CSV or Parquet files found in {self.data_path}")
        
        self.logger.info(f"Found {len(self.data_files)} data files for loading.")

    def _check_memory_usage(self) -> bool:
        """
        Checks current memory usage. Returns True if usage is safe, False otherwise.
        """
        current_mb = get_current_memory_usage_mb()
        current_gb = current_mb / 1024.0
        if current_gb > self.max_memory_gb:
            self.logger.warning(f"Memory usage {current_gb:.2f}GB exceeds limit {self.max_memory_gb}GB. Triggering GC.")
            gc.collect()
            return False
        return True

    def _load_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Loads metadata about the data file (shape, columns)."""
        # Simple heuristic: read first few lines to determine structure
        # In a production scenario, this might read a separate .json manifest
        if file_path.suffix == '.csv':
            import pandas as pd
            # Read header only to get columns
            df_head = pd.read_csv(file_path, nrows=0)
            return {
                "format": "csv",
                "columns": list(df_head.columns),
                "shape_hint": "unknown" # Actual count requires full scan or metadata file
            }
        elif file_path.suffix == '.parquet':
            import pandas as pd
            df_head = pd.read_parquet(file_path, columns=[])
            return {
                "format": "parquet",
                "columns": list(df_head.columns),
                "shape_hint": "unknown"
            }
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

    def _stream_csv(self, file_path: Path) -> Iterator[Dict[str, Any]]:
        """
        Generator that yields rows from a CSV file in chunks.
        Uses pandas chunksize for efficient memory usage.
        """
        import pandas as pd
        
        # Determine column mapping based on expected schema from T011/T012
        # Expected columns: 'spectral_bands' (array string or json), 'biomass', 'site_id'
        # Or separate columns: 'band_1', 'band_2', ..., 'biomass', 'site_id'
        
        # Strategy: Read in chunks, parse spectral data, yield batches
        try:
            for chunk in pd.read_csv(file_path, chunksize=self.chunk_size):
                # Identify spectral columns (usually prefixed with 'band_' or 'spec_')
                # Or a single column containing JSON array
                spectral_cols = [c for c in chunk.columns if c.startswith('band_') or c.startswith('spec_')]
                has_json_bands = 'spectral_bands' in chunk.columns or 'bands' in chunk.columns

                if not spectral_cols and not has_json_bands:
                    self.logger.warning(f"No spectral columns found in {file_path}. Skipping chunk.")
                    continue

                if has_json_bands:
                    # Parse JSON array in 'spectral_bands' column
                    # Assuming format: "[1.2, 3.4, ...]"
                    def parse_bands(bands_str):
                        if isinstance(bands_str, str):
                            return np.fromstring(bands_str.strip('[]'), sep=',')
                        return np.array(bands_str)
                    
                    try:
                        # Vectorized parsing might be slow, loop is safer for mixed types
                        spectral_matrix = np.vstack([parse_bands(x) for x in chunk['spectral_bands']])
                    except Exception as e:
                        self.logger.error(f"Failed to parse spectral bands in {file_path}: {e}")
                        continue
                else:
                    # Extract columns directly
                    spectral_matrix = chunk[spectral_cols].to_numpy()

                # Extract labels and IDs
                # Look for 'biomass', 'dry_mass', or similar
                label_col = next((c for c in chunk.columns if 'biomass' in c.lower() or 'mass' in c.lower()), None)
                id_col = next((c for c in chunk.columns if 'site' in c.lower() or 'id' in c.lower()), None)

                if label_col is None:
                    raise ValueError(f"Label column not found in {file_path}")
                
                labels = chunk[label_col].to_numpy()
                site_ids = chunk[id_col].to_numpy() if id_col else np.full(len(chunk), "unknown")

                yield {
                    "spectral": spectral_matrix,
                    "labels": labels,
                    "site_ids": site_ids,
                    "source_file": file_path.name
                }

        except Exception as e:
            self.logger.error(f"Error reading CSV {file_path}: {e}")
            raise

    def _stream_parquet(self, file_path: Path) -> Iterator[Dict[str, Any]]:
        """
        Generator that yields data from a Parquet file in chunks.
        """
        import pandas as pd
        import pyarrow.parquet as pq

        try:
            parquet_file = pq.ParquetFile(file_path)
            for batch in parquet_file.iter_batches(batch_size=self.chunk_size):
                df = batch.to_pandas()
                
                spectral_cols = [c for c in df.columns if c.startswith('band_') or c.startswith('spec_')]
                has_json_bands = 'spectral_bands' in df.columns

                if has_json_bands:
                    # Parquet usually stores arrays as lists, so this might be direct
                    # If stored as stringified JSON, parse it
                    if df['spectral_bands'].dtype == object:
                        # Check if it's a list or string
                        first_val = df['spectral_bands'].iloc[0]
                        if isinstance(first_val, str):
                            import ast
                            df['spectral_bands'] = df['spectral_bands'].apply(ast.literal_eval)
                        spectral_matrix = np.array(df['spectral_bands'].tolist())
                    else:
                        # It's already an array/list column
                        spectral_matrix = np.array(df['spectral_bands'].tolist())
                else:
                    spectral_matrix = df[spectral_cols].to_numpy()

                label_col = next((c for c in df.columns if 'biomass' in c.lower() or 'mass' in c.lower()), None)
                id_col = next((c for c in df.columns if 'site' in c.lower() or 'id' in c.lower()), None)

                if label_col is None:
                    raise ValueError(f"Label column not found in {file_path}")

                labels = df[label_col].to_numpy()
                site_ids = df[id_col].to_numpy() if id_col else np.full(len(df), "unknown")

                yield {
                    "spectral": spectral_matrix,
                    "labels": labels,
                    "site_ids": site_ids,
                    "source_file": file_path.name
                }

        except Exception as e:
            self.logger.error(f"Error reading Parquet {file_path}: {e}")
            raise

    def load_batches(self) -> Iterator[ChunkedDataBatch]:
        """
        Iterator yielding ChunkedDataBatch objects.
        Handles the full dataset streaming without OOM.
        """
        total_samples = 0
        total_batches = 0

        for file_path in self.data_files:
            self.logger.info(f"Processing file: {file_path.name}")
            
            # Select streamer based on extension
            if file_path.suffix == '.csv':
                streamer = self._stream_csv
            elif file_path.suffix == '.parquet':
                streamer = self._stream_parquet
            else:
                self.logger.warning(f"Skipping unsupported file: {file_path}")
                continue

            try:
                for chunk_data in streamer(file_path):
                    # Check memory before creating batch
                    if not self._check_memory_usage():
                        # Force GC and wait
                        gc.collect()
                        time.sleep(0.1)
                        if not self._check_memory_usage():
                            self.logger.error("Memory limit exceeded even after GC. Stopping load.")
                            break

                    batch = ChunkedDataBatch(
                        spectral_data=chunk_data["spectral"],
                        biomass_labels=chunk_data["labels"],
                        site_ids=chunk_data["site_ids"],
                        metadata={"source": chunk_data["source_file"]}
                    )
                    
                    yield batch
                    total_samples += batch.shape[0]
                    total_batches += 1
                    
                    # Log progress periodically
                    if total_batches % 10 == 0:
                        self.logger.info(f"Loaded {total_samples} samples across {total_batches} batches.")
                        
            except Exception as e:
                self.logger.error(f"Failed to stream file {file_path}: {e}")
                raise

        self.logger.info(f"Finished loading. Total batches: {total_batches}, Total samples: {total_samples}")

    def get_dataset_stats(self) -> Dict[str, Any]:
        """
        Calculates basic statistics about the dataset without loading all data into memory.
        Streams through the data to compute mean, std, min, max for bands and labels.
        """
        self.logger.info("Computing dataset statistics (this may take a while)...")
        
        stats = {
            "num_samples": 0,
            "num_bands": 0,
            "band_stats": {}, # Will be populated after first batch
            "label_stats": {}
        }

        first_batch = True
        
        for batch in self.load_batches():
            if first_batch:
                stats["num_bands"] = batch.shape[1]
                # Initialize accumulators
                stats["band_stats"] = {
                    "sum": np.zeros(batch.shape[1]),
                    "sum_sq": np.zeros(batch.shape[1]),
                    "min": np.full(batch.shape[1], np.inf),
                    "max": np.full(batch.shape[1], -np.inf)
                }
                stats["label_stats"] = {
                    "sum": 0.0,
                    "sum_sq": 0.0,
                    "min": np.inf,
                    "max": -np.inf
                }
                first_batch = False

            # Update band stats
            stats["band_stats"]["sum"] += np.sum(batch.spectral_data, axis=0)
            stats["band_stats"]["sum_sq"] += np.sum(batch.spectral_data ** 2, axis=0)
            stats["band_stats"]["min"] = np.minimum(stats["band_stats"]["min"], np.min(batch.spectral_data, axis=0))
            stats["band_stats"]["max"] = np.maximum(stats["band_stats"]["max"], np.max(batch.spectral_data, axis=0))

            # Update label stats
            stats["label_stats"]["sum"] += np.sum(batch.biomass_labels)
            stats["label_stats"]["sum_sq"] += np.sum(batch.biomass_labels ** 2)
            stats["label_stats"]["min"] = min(stats["label_stats"]["min"], np.min(batch.biomass_labels))
            stats["label_stats"]["max"] = max(stats["label_stats"]["max"], np.max(batch.biomass_labels))

            stats["num_samples"] += batch.shape[0]

        if stats["num_samples"] == 0:
            return {"error": "No data found"}

        # Calculate means and stds
        n = stats["num_samples"]
        stats["band_stats"]["mean"] = stats["band_stats"]["sum"] / n
        stats["band_stats"]["std"] = np.sqrt((stats["band_stats"]["sum_sq"] / n) - (stats["band_stats"]["mean"] ** 2))
        
        stats["label_stats"]["mean"] = stats["label_stats"]["sum"] / n
        stats["label_stats"]["std"] = np.sqrt((stats["label_stats"]["sum_sq"] / n) - (stats["label_stats"]["mean"] ** 2))

        # Cleanup accumulators
        del stats["band_stats"]["sum"], stats["band_stats"]["sum_sq"]
        del stats["label_stats"]["sum"], stats["label_stats"]["sum_sq"]

        self.logger.info(f"Dataset stats computed for {n} samples.")
        return stats

def main():
    """
    Main entry point for testing the loader and generating dataset statistics.
    Usage: python code/data/loader.py --data_path data/processed --chunk_size 5000
    """
    import argparse
    from code.utils.timer import Timer

    parser = argparse.ArgumentParser(description="Chunked Hyperspectral Loader")
    parser.add_argument("--data_path", type=str, required=True, help="Path to processed data directory")
    parser.add_argument("--chunk_size", type=int, default=10000, help="Number of samples per chunk")
    parser.add_argument("--max_memory_gb", type=float, default=7.0, help="Max memory limit in GB")
    parser.add_argument("--stats", action="store_true", help="Compute and print dataset statistics")
    
    args = parser.parse_args()

    logger = get_logger(__name__)
    logger.info(f"Initializing loader with data_path={args.data_path}, chunk_size={args.chunk_size}")

    try:
        loader = ChunkedHyperspectralLoader(
            data_path=args.data_path,
            chunk_size=args.chunk_size,
            max_memory_gb=args.max_memory_gb,
            logger=logger
        )

        if args.stats:
            with Timer("Dataset Statistics"):
                stats = loader.get_dataset_stats()
                print(json.dumps(stats, indent=2, default=str))
        else:
            # Demo: Load first 5 batches and verify structure
            count = 0
            with Timer("Load Demo"):
                for batch in loader.load_batches():
                    logger.info(f"Batch {count}: shape={batch.shape}, label_range=[{batch.biomass_labels.min():.2f}, {batch.biomass_labels.max():.2f}]")
                    count += 1
                    if count >= 5:
                        break
            logger.info(f"Verified loading of {count} batches successfully.")

    except Exception as e:
        logger.error(f"Loader execution failed: {e}")
        raise

if __name__ == "__main__":
    main()
