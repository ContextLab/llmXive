"""
Module: code/05_optimize_data_loading.py
Task: T031 - Performance optimization: Ensure data loading is chunked where possible.

This module implements chunked data loading and processing to minimize memory spikes
during the data pipeline execution. It provides utilities to load large datasets in
manageable chunks, process them in batches, and aggregate statistics without loading
the entire dataset into memory at once.

Key features:
- Chunked loading of Parquet files using PyArrow
- Batch processing of feature extraction
- Memory-efficient aggregation of statistics
- Integration with existing memory monitoring utilities
"""

import gc
import json
import logging
import os
from pathlib import Path
from typing import Generator, List, Tuple, Any, Dict, Optional

import pandas as pd
import numpy as np
import pyarrow.parquet as pq

from utils.logger import get_logger, configure_logging_for_pipeline
from utils.memory_monitor import (
    get_memory_usage_gb, 
    check_memory_limit, 
    force_gc,
    MemoryMonitor
)

# Configure logging
logger = get_logger("optimize_data_loading")
configure_logging_for_pipeline("code/05_optimize_data_loading.py")

# Constants
DEFAULT_CHUNK_SIZE = 10000  # Number of rows per chunk
MEMORY_LIMIT_GB = 6.5       # Maximum memory usage before triggering downsampling


class ChunkedDataLoader:
    """
    A class to load and process large datasets in chunks to minimize memory usage.
    
    This loader is designed to work with Parquet files and provides methods to:
    - Load data in configurable chunk sizes
    - Process each chunk independently
    - Aggregate results across chunks
    - Monitor memory usage and trigger garbage collection when needed
    """
    
    def __init__(
        self, 
        file_path: str, 
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        memory_limit_gb: float = MEMORY_LIMIT_GB
    ):
        """
        Initialize the ChunkedDataLoader.
        
        Args:
            file_path: Path to the Parquet file to load
            chunk_size: Number of rows to load per chunk
            memory_limit_gb: Memory limit in GB before triggering cleanup
        """
        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        self.memory_limit_gb = memory_limit_gb
        self.logger = logger
        
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        self.logger.info(f"Initialized ChunkedDataLoader for {self.file_path} "
                       f"with chunk_size={chunk_size}")
    
    def load_chunks(self) -> Generator[pd.DataFrame, None, None]:
        """
        Load the Parquet file in chunks.
        
        Yields:
            pd.DataFrame: A chunk of the dataset
        """
        try:
            # Use PyArrow's ParquetFile for efficient chunked reading
            parquet_file = pq.ParquetFile(self.file_path)
            
            for batch in parquet_file.iter_batches(batch_size=self.chunk_size):
                # Convert batch to DataFrame
                df_chunk = batch.to_pandas()
                
                # Check memory usage after loading chunk
                current_memory = get_memory_usage_gb()
                self.logger.debug(f"Loaded chunk: {len(df_chunk)} rows, "
                                f"current memory: {current_memory:.2f} GB")
                
                if current_memory > self.memory_limit_gb * 0.8:
                    self.logger.warning(f"Memory usage high ({current_memory:.2f} GB), "
                                      f"triggering garbage collection")
                    force_gc()
                
                yield df_chunk
                
        except Exception as e:
            self.logger.error(f"Error loading chunks from {self.file_path}: {e}")
            raise
    
    def process_chunks(
        self, 
        process_func, 
        *args, 
        **kwargs
    ) -> Generator[Any, None, None]:
        """
        Process each chunk through a user-defined function.
        
        Args:
            process_func: Function to apply to each chunk
            *args: Positional arguments to pass to process_func
            **kwargs: Keyword arguments to pass to process_func
        
        Yields:
            Any: Result of processing each chunk
        """
        for chunk in self.load_chunks():
            try:
                result = process_func(chunk, *args, **kwargs)
                yield result
                
                # Force garbage collection after processing if memory is high
                if get_memory_usage_gb() > self.memory_limit_gb * 0.7:
                    force_gc()
                    
            except Exception as e:
                self.logger.error(f"Error processing chunk: {e}")
                raise
    
    def aggregate_results(
        self, 
        results_generator: Generator[Any, None, None],
        aggregate_func
    ) -> Any:
        """
        Aggregate results from processed chunks.
        
        Args:
            results_generator: Generator yielding processed chunk results
            aggregate_func: Function to aggregate results
        
        Returns:
            Any: Aggregated result
        """
        results = []
        for result in results_generator:
            results.append(result)
            
            # Periodically check memory and clean up
            if len(results) % 10 == 0:
                if get_memory_usage_gb() > self.memory_limit_gb * 0.8:
                    self.logger.info(f"Aggregated {len(results)} chunks, "
                                   f"memory: {get_memory_usage_gb():.2f} GB, "
                                   f"triggering GC")
                    force_gc()
        
        return aggregate_func(results) if results else None


def load_data_chunked(
    file_path: str, 
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    memory_limit_gb: float = MEMORY_LIMIT_GB
) -> Generator[pd.DataFrame, None, None]:
    """
    Load a Parquet file in chunks.
    
    This is a convenience function that creates a ChunkedDataLoader and yields chunks.
    
    Args:
        file_path: Path to the Parquet file
        chunk_size: Number of rows per chunk
        memory_limit_gb: Memory limit in GB
    
    Yields:
        pd.DataFrame: Chunks of the dataset
    """
    loader = ChunkedDataLoader(file_path, chunk_size, memory_limit_gb)
    yield from loader.load_chunks()


def aggregate_chunked_statistics(
    chunk_results: List[Dict[str, Any]],
    target_descriptors: List[str] = ['dipole', 'HOMO', 'LUMO']
) -> Dict[str, Any]:
    """
    Aggregate statistics from chunked processing results.
    
    Args:
        chunk_results: List of dictionaries containing statistics from each chunk
        target_descriptors: List of descriptors to compute statistics for
    
    Returns:
        Dict containing aggregated statistics (mean, std, count) for each descriptor
    """
    if not chunk_results:
        return {}
    
    aggregated = {desc: {'sum': 0.0, 'sum_sq': 0.0, 'count': 0} 
                 for desc in target_descriptors}
    
    for chunk_stats in chunk_results:
        for desc in target_descriptors:
            if desc in chunk_stats:
                stats = chunk_stats[desc]
                aggregated[desc]['sum'] += stats.get('sum', 0.0)
                aggregated[desc]['sum_sq'] += stats.get('sum_sq', 0.0)
                aggregated[desc]['count'] += stats.get('count', 0)
    
    # Calculate final statistics
    final_stats = {}
    for desc in target_descriptors:
        count = aggregated[desc]['count']
        if count > 0:
            mean = aggregated[desc]['sum'] / count
            variance = (aggregated[desc]['sum_sq'] / count) - (mean ** 2)
            std = np.sqrt(max(0, variance))  # Handle potential numerical issues
            final_stats[desc] = {
                'mean': mean,
                'std': std,
                'count': count
            }
        else:
            final_stats[desc] = {'mean': 0.0, 'std': 0.0, 'count': 0}
    
    return final_stats


def process_features_in_batches(
    data_frame: pd.DataFrame,
    batch_size: int = 1000,
    feature_func: Optional[callable] = None
) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
    """
    Process a DataFrame in batches to extract features.
    
    Args:
        data_frame: Input DataFrame
        batch_size: Number of rows per batch
        feature_func: Optional function to extract features from each row
    
    Yields:
        Tuple of (features_array, labels_array) for each batch
    """
    n_rows = len(data_frame)
    
    for start_idx in range(0, n_rows, batch_size):
        end_idx = min(start_idx + batch_size, n_rows)
        batch = data_frame.iloc[start_idx:end_idx]
        
        # Check memory before processing batch
        if get_memory_usage_gb() > MEMORY_LIMIT_GB * 0.8:
            logger.warning(f"Memory high before batch {start_idx}, triggering GC")
            force_gc()
        
        if feature_func:
            # Apply feature extraction function to the batch
            features = feature_func(batch)
            labels = batch[['dipole', 'HOMO', 'LUMO']].values
            yield features, labels
        else:
            # Default: return selected columns as features and labels
            # This is a fallback for testing without a specific feature function
            feature_cols = [col for col in data_frame.columns 
                          if col not in ['dipole', 'HOMO', 'LUMO', 'smiles']]
            if feature_cols:
                features = batch[feature_cols].values
            else:
                features = np.zeros((len(batch), 1))  # Dummy features
            labels = batch[['dipole', 'HOMO', 'LUMO']].values
            yield features, labels
        
        # Clean up batch reference
        del batch
        gc.collect()


def optimize_data_loading_workflow(
    input_path: str,
    output_path: Optional[str] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    memory_limit_gb: float = MEMORY_LIMIT_GB
) -> Dict[str, Any]:
    """
    Execute a complete chunked data loading and processing workflow.
    
    This function:
    1. Loads data in chunks
    2. Processes each chunk (statistics, feature extraction, etc.)
    3. Aggregates results
    4. Saves aggregated results if output_path is provided
    
    Args:
        input_path: Path to input Parquet file
        output_path: Optional path to save aggregated results
        chunk_size: Number of rows per chunk
        memory_limit_gb: Memory limit in GB
    
    Returns:
        Dict containing aggregated statistics and metadata
    """
    logger.info(f"Starting optimized data loading workflow for {input_path}")
    
    # Initialize loader
    loader = ChunkedDataLoader(input_path, chunk_size, memory_limit_gb)
    
    # Process chunks and collect statistics
    def compute_chunk_stats(chunk: pd.DataFrame) -> Dict[str, Any]:
        """Compute statistics for a single chunk."""
        stats = {}
        target_descriptors = ['dipole', 'HOMO', 'LUMO']
        
        for desc in target_descriptors:
            if desc in chunk.columns:
                values = chunk[desc].dropna()
                if len(values) > 0:
                    stats[desc] = {
                        'sum': float(values.sum()),
                        'sum_sq': float((values ** 2).sum()),
                        'count': int(len(values))
                    }
            else:
                stats[desc] = {'sum': 0.0, 'sum_sq': 0.0, 'count': 0}
        
        return stats
    
    # Process chunks and aggregate
    results_generator = loader.process_chunks(compute_chunk_stats)
    aggregated_stats = loader.aggregate_results(
        results_generator, 
        lambda results: aggregate_chunked_statistics(results)
    )
    
    # Add metadata
    workflow_results = {
        'input_file': input_path,
        'chunk_size': chunk_size,
        'memory_limit_gb': memory_limit_gb,
        'aggregated_statistics': aggregated_stats,
        'final_memory_gb': get_memory_usage_gb()
    }
    
    # Save results if output path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(workflow_results, f, indent=2)
        logger.info(f"Saved workflow results to {output_path}")
    
    logger.info(f"Workflow completed. Final memory: {workflow_results['final_memory_gb']:.2f} GB")
    return workflow_results


def main():
    """
    Main entry point for the data loading optimization script.
    
    This function demonstrates the chunked data loading workflow by:
    1. Loading the cleaned molecules dataset
    2. Processing it in chunks
    3. Computing and saving aggregated statistics
    """
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(
        description="Optimize data loading with chunked processing"
    )
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/molecules_cleaned.parquet",
        help="Path to input Parquet file"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/loading_stats.json",
        help="Path to save aggregated statistics"
    )
    parser.add_argument(
        "--chunk-size", 
        type=int, 
        default=DEFAULT_CHUNK_SIZE,
        help=f"Number of rows per chunk (default: {DEFAULT_CHUNK_SIZE})"
    )
    parser.add_argument(
        "--memory-limit", 
        type=float, 
        default=MEMORY_LIMIT_GB,
        help=f"Memory limit in GB (default: {MEMORY_LIMIT_GB})"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    configure_logging_for_pipeline("code/05_optimize_data_loading.py")
    
    # Check if input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run T010 first to generate molecules_cleaned.parquet")
        return 1
    
    # Run the optimization workflow
    try:
        results = optimize_data_loading_workflow(
            input_path=str(input_path),
            output_path=args.output,
            chunk_size=args.chunk_size,
            memory_limit_gb=args.memory_limit
        )
        
        logger.info("Optimization workflow completed successfully")
        logger.info(f"Aggregated statistics: {json.dumps(results['aggregated_statistics'], indent=2)}")
        return 0
        
    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
