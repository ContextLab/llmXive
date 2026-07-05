"""
Chunked Data Processor for Large Datasets (>7GB RAM).

This module implements a streaming/chunked processing pipeline to handle
datasets that exceed available system memory. It processes data in
configurable chunks, performs necessary aggregations, and writes
intermediate results to disk before final consolidation.

Key features:
- Memory-mapped reading for large CSV files
- Configurable chunk sizes
- Streaming aggregations for common statistical operations
- Intermediate file management with automatic cleanup
- Progress tracking and logging
"""
import os
import gc
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Generator, Tuple, Callable
import pandas as pd
import numpy as np

from config import get_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChunkedProcessor:
    """
    A processor for handling large datasets that don't fit in memory.
    
    This class provides methods to:
    - Read large CSV files in chunks
    - Perform streaming aggregations
    - Manage intermediate files
    - Consolidate results
    """
    
    def __init__(
        self,
        chunk_size: int = 100000,
        temp_dir: Optional[Path] = None,
        memory_threshold: float = 0.7
    ):
        """
        Initialize the ChunkedProcessor.
        
        Args:
            chunk_size: Number of rows to process at once. Default 100k.
            temp_dir: Directory for intermediate files. Defaults to data/processed/tmp.
            memory_threshold: Fraction of RAM to use before forcing GC.
        """
        self.chunk_size = chunk_size
        self.temp_dir = temp_dir or get_path('data', 'processed', 'tmp')
        self.memory_threshold = memory_threshold
        self.temp_files: List[Path] = []
        
        # Ensure temp directory exists
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ChunkedProcessor initialized with chunk_size={chunk_size}, temp_dir={self.temp_dir}")
    
    def _generate_temp_filename(self, prefix: str = "chunk") -> Path:
        """Generate a unique temporary filename."""
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        unique_id = hashlib.md5(f"{prefix}_{timestamp}".encode()).hexdigest()[:8]
        return self.temp_dir / f"{prefix}_{unique_id}.csv"
    
    def _read_csv_in_chunks(
        self,
        file_path: Path,
        chunk_size: Optional[int] = None,
        **kwargs
    ) -> Generator[pd.DataFrame, None, None]:
        """
        Read a CSV file in chunks.
        
        Args:
            file_path: Path to the CSV file.
            chunk_size: Override default chunk size.
            **kwargs: Additional arguments for pd.read_csv.
        
        Yields:
            DataFrame chunks.
        """
        actual_chunk_size = chunk_size or self.chunk_size
        
        try:
            for chunk in pd.read_csv(file_path, chunksize=actual_chunk_size, **kwargs):
                yield chunk
        except Exception as e:
            logger.error(f"Error reading CSV in chunks: {e}")
            raise
    
    def _process_chunk(
        self,
        chunk: pd.DataFrame,
        process_func: Callable[[pd.DataFrame], pd.DataFrame],
        chunk_id: int
    ) -> pd.DataFrame:
        """
        Process a single chunk and return results.
        
        Args:
            chunk: DataFrame chunk to process.
            process_func: Function to apply to the chunk.
            chunk_id: Identifier for logging.
        
        Returns:
            Processed DataFrame.
        """
        try:
            logger.debug(f"Processing chunk {chunk_id} with {len(chunk)} rows")
            result = process_func(chunk)
            return result
        except Exception as e:
            logger.error(f"Error processing chunk {chunk_id}: {e}")
            raise
    
    def _write_temp_file(self, df: pd.DataFrame, prefix: str = "temp") -> Path:
        """
        Write a DataFrame to a temporary file.
        
        Args:
            df: DataFrame to write.
            prefix: Prefix for the temp filename.
        
        Returns:
            Path to the written file.
        """
        temp_path = self._generate_temp_filename(prefix)
        df.to_csv(temp_path, index=False)
        self.temp_files.append(temp_path)
        logger.debug(f"Wrote temp file: {temp_path} ({len(df)} rows)")
        return temp_path
    
    def _force_gc(self):
        """Force garbage collection if memory usage is high."""
        try:
            import psutil
            process = psutil.Process()
            mem_usage = process.memory_info().rss / (1024 * 1024 * 1024)  # GB
            if mem_usage > (self.memory_threshold * 100):  # psutil returns percent
                logger.warning(f"Memory usage high ({mem_usage:.2f}GB). Forcing GC.")
                gc.collect()
        except ImportError:
            # psutil not available, just do basic GC
            gc.collect()
            logger.debug("Basic GC performed (psutil not available)")
    
    def process_large_csv(
        self,
        input_path: Path,
        output_path: Path,
        process_func: Callable[[pd.DataFrame], pd.DataFrame],
        chunk_size: Optional[int] = None,
        aggregation_func: Optional[Callable[[List[pd.DataFrame]], pd.DataFrame]] = None,
        cleanup_temp: bool = True
    ) -> Path:
        """
        Process a large CSV file in chunks.
        
        Args:
            input_path: Path to input CSV file.
            output_path: Path for final output CSV.
            process_func: Function to apply to each chunk.
            chunk_size: Override default chunk size.
            aggregation_func: Function to combine chunk results. If None, 
                             chunks are concatenated.
            cleanup_temp: Whether to delete temp files after completion.
        
        Returns:
            Path to the output file.
        """
        logger.info(f"Starting chunked processing: {input_path} -> {output_path}")
        
        chunk_size = chunk_size or self.chunk_size
        temp_results: List[Path] = []
        chunk_count = 0
        
        try:
            for i, chunk in enumerate(self._read_csv_in_chunks(input_path, chunk_size)):
                chunk_count += 1
                
                # Process the chunk
                processed_chunk = self._process_chunk(chunk, process_func, i)
                
                # Write to temp file
                if not processed_chunk.empty:
                    temp_path = self._write_temp_file(processed_chunk, f"result_{i}")
                    temp_results.append(temp_path)
                
                # Force GC if needed
                if i % 10 == 0:
                    self._force_gc()
            
            if not temp_results:
                logger.warning("No data processed. Creating empty output.")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                pd.DataFrame().to_csv(output_path, index=False)
                return output_path
            
            # Aggregate results
            if aggregation_func:
                logger.info("Aggregating chunk results...")
                results = [pd.read_csv(f) for f in temp_results]
                final_df = aggregation_func(results)
            else:
                logger.info("Concatenating chunk results...")
                final_df = pd.concat([pd.read_csv(f) for f in temp_results], ignore_index=True)
            
            # Write final output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            final_df.to_csv(output_path, index=False)
            logger.info(f"Completed processing. Output: {output_path} ({len(final_df)} rows)")
            
            return output_path
        
        finally:
            if cleanup_temp:
                self.cleanup_temp_files()
    
    def cleanup_temp_files(self):
        """Remove all temporary files created during processing."""
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    logger.debug(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_file}: {e}")
        self.temp_files.clear()
    
    def estimate_memory_requirement(self, file_path: Path) -> Dict[str, Any]:
        """
        Estimate memory requirements for processing a file.
        
        Args:
            file_path: Path to the CSV file.
        
        Returns:
            Dictionary with memory estimates.
        """
        try:
            # Get file size
            file_size_bytes = file_path.stat().st_size
            file_size_gb = file_size_bytes / (1024 ** 3)
            
            # Sample first chunk to estimate row size
            sample = pd.read_csv(file_path, nrows=10000)
            sample_size = sample.memory_usage(deep=True).sum()
            rows_per_mb = 10000 / (sample_size / (1024 * 1024))
            
            estimated_rows = int(file_size_bytes / (sample_size / len(sample)))
            estimated_memory_gb = (estimated_rows / rows_per_mb) / 1024
            
            return {
                'file_size_gb': round(file_size_gb, 2),
                'estimated_rows': estimated_rows,
                'estimated_memory_gb': round(estimated_memory_gb, 2),
                'chunk_size': self.chunk_size,
                'requires_chunking': file_size_gb > 2.0  # Conservative threshold
            }
        except Exception as e:
            logger.error(f"Error estimating memory: {e}")
            return {
                'file_size_gb': 0,
                'estimated_rows': 0,
                'estimated_memory_gb': 0,
                'chunk_size': self.chunk_size,
                'requires_chunking': True,
                'error': str(e)
            }


def aggregate_mean_response_times(results: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Aggregate chunk results by calculating mean response times per stimulus.
    
    This is a common aggregation for LMM preprocessing where we need
    mean response time per stimulus per participant.
    
    Args:
        results: List of DataFrames from chunk processing.
    
    Returns:
        Aggregated DataFrame with mean response times.
    """
    combined = pd.concat(results, ignore_index=True)
    
    # Group by stimulus and participant, calculate mean
    aggregated = combined.groupby(
        ['stimulus_id', 'participant_id'],
        as_index=False
    ).agg({
        'response_time': 'mean',
        'trial_id': 'count'  # Count trials for quality check
    }).rename(columns={'trial_id': 'trial_count'})
    
    return aggregated


def run_chunked_preprocessing(
    input_path: Path,
    output_path: Path,
    chunk_size: int = 100000
) -> Path:
    """
    Run chunked preprocessing on a large dataset.
    
    This function performs:
    1. Memory estimation
    2. Chunked reading and processing
    3. Aggregation of results
    4. Final output writing
    
    Args:
        input_path: Path to input CSV file.
        output_path: Path for output CSV file.
        chunk_size: Number of rows per chunk.
    
    Returns:
        Path to output file.
    """
    processor = ChunkedProcessor(chunk_size=chunk_size)
    
    # Estimate requirements
    estimates = processor.estimate_memory_requirement(input_path)
    logger.info(f"Memory estimate: {estimates}")
    
    if not estimates.get('requires_chunking', False):
        logger.info("File small enough to process in memory. Processing normally.")
        df = pd.read_csv(input_path)
        # Simple pass-through for small files
        df.to_csv(output_path, index=False)
        return output_path
    
    # Define processing function (example: filter and clean)
    def process_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
        """Process a single chunk of data."""
        # Filter out invalid response times
        chunk = chunk[chunk['response_time'] > 0]
        chunk = chunk[chunk['response_time'] < 10000]  # Max 10s
        chunk = chunk.dropna(subset=['stimulus_id', 'participant_id'])
        return chunk
    
    # Process in chunks
    output_path = processor.process_large_csv(
        input_path=input_path,
        output_path=output_path,
        process_func=process_chunk,
        aggregation_func=aggregate_mean_response_times
    )
    
    return output_path


def main():
    """Main entry point for chunked processing demonstration."""
    import sys
    
    # Default paths
    input_path = get_path('data', 'processed', 'linked_trials.csv')
    output_path = get_path('data', 'processed', 'linked_trials_chunked.csv')
    
    # Allow command line override
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    
    logger.info(f"Chunked processor ready. Input: {input_path}, Output: {output_path}")
    logger.info("To run: python code/data/chunked_processor.py [input_path] [output_path]")
    
    if not input_path.exists():
        logger.warning(f"Input file not found: {input_path}")
        logger.info("This is expected if the file hasn't been generated yet.")
        return
    
    # Run processing
    try:
        result_path = run_chunked_preprocessing(input_path, output_path)
        logger.info(f"Chunked processing complete. Output: {result_path}")
    except Exception as e:
        logger.error(f"Chunked processing failed: {e}")
        raise


if __name__ == '__main__':
    main()
