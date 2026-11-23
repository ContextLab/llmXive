"""
Batch processing utilities for CPU efficiency.

This module provides utilities to process large datasets in batches to
reduce memory footprint and improve CPU cache utilization during
genomic feature extraction and model training.
"""
import os
import gc
import logging
from pathlib import Path
from typing import Iterator, List, Optional, Tuple, Any, Dict, Union
from typing import TypeVar, Generic

import numpy as np
import pandas as pd

from .logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class BatchProcessor(Generic[T]):
    """
    Generic batch processor for iterating over large datasets in chunks.
    
    This class helps manage memory usage by processing data in configurable
    batch sizes, with optional garbage collection between batches.
    """
    
    def __init__(
        self, 
        batch_size: int = 1000, 
        gc_interval: int = 5, 
        verbose: bool = True
    ):
        """
        Initialize the batch processor.
        
        Args:
            batch_size: Number of items per batch.
            gc_interval: Run garbage collection every N batches (0 to disable).
            verbose: Log batch processing progress.
        """
        self.batch_size = max(1, batch_size)
        self.gc_interval = max(0, gc_interval)
        self.verbose = verbose
        self._batch_count = 0
        self._total_processed = 0
        
        logger.debug(
            f"BatchProcessor initialized: batch_size={self.batch_size}, "
            f"gc_interval={self.gc_interval}"
        )

    def _maybe_gc(self) -> None:
        """Run garbage collection if interval is reached."""
        if self.gc_interval > 0 and self._batch_count % self.gc_interval == 0:
            if self.verbose:
                logger.debug(f"Running garbage collection (batch {self._batch_count})")
            gc.collect()

    def process_batches(
        self, 
        data: List[T], 
        process_fn: Any
    ) -> Iterator[Tuple[int, List[T], Any]]:
        """
        Process a list of items in batches.
        
        Args:
            data: List of items to process.
            process_fn: Function to apply to each batch.
            
        Yields:
            Tuples of (batch_index, batch_items, result_from_process_fn).
        """
        total = len(data)
        num_batches = (total + self.batch_size - 1) // self.batch_size
        
        if self.verbose:
            logger.info(f"Processing {total} items in {num_batches} batches")
        
        for start_idx in range(0, total, self.batch_size):
            end_idx = min(start_idx + self.batch_size, total)
            batch = data[start_idx:end_idx]
            
            result = process_fn(batch)
            
            self._batch_count += 1
            self._total_processed += len(batch)
            self._maybe_gc()
            
            if self.verbose and (start_idx + self.batch_size >= total or 
                                 (start_idx // self.batch_size) % 10 == 0):
                logger.debug(
                    f"Processed batch {start_idx//self.batch_size}: "
                    f"{len(batch)} items (total: {self._total_processed})"
                )
            
            yield start_idx // self.batch_size, batch, result

    def reset_stats(self) -> None:
        """Reset batch processing statistics."""
        self._batch_count = 0
        self._total_processed = 0


def chunk_dataframe(
    df: pd.DataFrame, 
    chunk_size: int = 1000
) -> Iterator[pd.DataFrame]:
    """
    Iterate over a DataFrame in chunks.
    
    Args:
        df: The DataFrame to chunk.
        chunk_size: Number of rows per chunk.
        
    Yields:
        DataFrame chunks.
    """
    total_rows = len(df)
    logger.debug(f"Chunking DataFrame with {total_rows} rows, chunk_size={chunk_size}")
    
    for start in range(0, total_rows, chunk_size):
        end = min(start + chunk_size, total_rows)
        yield df.iloc[start:end]


def batch_process_snp_data(
    snp_paths: List[Path], 
    output_dir: Path, 
    batch_size: int = 50
) -> Dict[str, Any]:
    """
    Process SNP data files in batches to reduce memory pressure.
    
    Args:
        snp_paths: List of paths to SNP data files.
        output_dir: Directory to write intermediate results.
        batch_size: Number of files to process per batch.
        
    Returns:
        Dictionary with processing statistics.
    """
    logger.info(f"Processing {len(snp_paths)} SNP files in batches of {batch_size}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    processor = BatchProcessor(batch_size=batch_size, gc_interval=3)
    results = []
    
    def process_batch(batch_files: List[Path]) -> List[Dict]:
        batch_results = []
        for f_path in batch_files:
            try:
                # Load and process individual SNP file
                df = pd.read_csv(f_path, sep='\t', index_col=0)
                batch_results.append({
                    'file': f_path.name,
                    'rows': len(df),
                    'status': 'success'
                })
            except Exception as e:
                logger.error(f"Failed to process {f_path}: {e}")
                batch_results.append({
                    'file': f_path.name,
                    'status': 'error',
                    'error': str(e)
                })
        return batch_results
    
    for batch_idx, batch_files, batch_results in processor.process_batches(
        snp_paths, process_batch
    ):
        results.extend(batch_results)
        
        # Save intermediate batch results
        intermediate_file = output_dir / f"batch_{batch_idx}_results.json"
        with open(intermediate_file, 'w') as f:
            import json
            json.dump(batch_results, f, indent=2)
    
    stats = {
        'total_files': len(snp_paths),
        'batches_processed': processor._batch_count,
        'successful': sum(1 for r in results if r.get('status') == 'success'),
        'failed': sum(1 for r in results if r.get('status') == 'error'),
        'intermediate_files': [
            str(f) for f in sorted(output_dir.glob("batch_*_results.json"))
        ]
    }
    
    logger.info(
        f"Batch SNP processing complete: {stats['successful']}/{stats['total_files']} "
        f"successful"
    )
    
    return stats


def batch_process_gene_presence(
    gene_paths: List[Path], 
    output_dir: Path, 
    batch_size: int = 50
) -> Dict[str, Any]:
    """
    Process gene presence/absence data in batches.
    
    Args:
        gene_paths: List of paths to gene presence data files.
        output_dir: Directory to write intermediate results.
        batch_size: Number of files per batch.
        
    Returns:
        Processing statistics.
    """
    logger.info(f"Processing {len(gene_paths)} gene files in batches of {batch_size}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    processor = BatchProcessor(batch_size=batch_size, gc_interval=3)
    results = []
    
    def process_batch(batch_files: List[Path]) -> List[Dict]:
        batch_results = []
        for f_path in batch_files:
            try:
                df = pd.read_csv(f_path, index_col=0)
                batch_results.append({
                    'file': f_path.name,
                    'genes': df.shape[1] if len(df.shape) > 1 else 0,
                    'samples': len(df),
                    'status': 'success'
                })
            except Exception as e:
                logger.error(f"Failed to process {f_path}: {e}")
                batch_results.append({
                    'file': f_path.name,
                    'status': 'error',
                    'error': str(e)
                })
        return batch_results
    
    for batch_idx, batch_files, batch_results in processor.process_batches(
        gene_paths, process_batch
    ):
        results.extend(batch_results)
        
        intermediate_file = output_dir / f"gene_batch_{batch_idx}_results.json"
        with open(intermediate_file, 'w') as f:
            import json
            json.dump(batch_results, f, indent=2)
    
    stats = {
        'total_files': len(gene_paths),
        'batches_processed': processor._batch_count,
        'successful': sum(1 for r in results if r.get('status') == 'success'),
        'failed': sum(1 for r in results if r.get('status') == 'error')
    }
    
    logger.info(f"Batch gene processing complete: {stats['successful']}/{stats['total_files']}")
    return stats


def optimize_memory_usage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize DataFrame memory usage by downcasting numeric types.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        DataFrame with optimized dtypes.
    """
    initial_memory = df.memory_usage(deep=True).sum()
    
    for col in df.columns:
        col_type = df[col].dtype
        
        if pd.api.types.is_integer_dtype(col_type):
            c_min = df[col].min()
            c_max = df[col].max()
            
            if c_min >= np.iinfo(np.int8).min and c_max <= np.iinfo(np.int8).max:
                df[col] = df[col].astype(np.int8)
            elif c_min >= np.iinfo(np.int16).min and c_max <= np.iinfo(np.int16).max:
                df[col] = df[col].astype(np.int16)
            elif c_min >= np.iinfo(np.int32).min and c_max <= np.iinfo(np.int32).max:
                df[col] = df[col].astype(np.int32)
                
        elif pd.api.types.is_float_dtype(col_type):
            c_min = df[col].min()
            c_max = df[col].max()
            
            if c_min >= np.finfo(np.float32).min and c_max <= np.finfo(np.float32).max:
                df[col] = df[col].astype(np.float32)
                
    final_memory = df.memory_usage(deep=True).sum()
    saved = initial_memory - final_memory
    percent_saved = (saved / initial_memory) * 100 if initial_memory > 0 else 0
    
    logger.debug(
        f"Memory optimization: {initial_memory/1e6:.2f}MB -> {final_memory/1e6:.2f}MB "
        f"({percent_saved:.1f}% saved)"
    )
    
    return df


def main():
    """CLI entry point for batch processing utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Batch processing utilities for genomic data"
    )
    parser.add_argument(
        "--snp-dir", type=Path, help="Directory containing SNP files"
    )
    parser.add_argument(
        "--gene-dir", type=Path, help="Directory containing gene presence files"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/processed/batches"),
        help="Output directory for batch results"
    )
    parser.add_argument(
        "--batch-size", type=int, default=50,
        help="Number of files per batch"
    )
    
    args = parser.parse_args()
    
    setup_logger = get_logger(__name__)
    setup_logger.info("Starting batch processing CLI")
    
    if args.snp_dir and args.snp_dir.exists():
        snp_files = list(args.snp_dir.glob("*.tsv")) + list(args.snp_dir.glob("*.csv"))
        if snp_files:
            stats = batch_process_snp_data(snp_files, args.output_dir / "snps", args.batch_size)
            print(f"SNP Processing Stats: {stats}")
    
    if args.gene_dir and args.gene_dir.exists():
        gene_files = list(args.gene_dir.glob("*.csv"))
        if gene_files:
            stats = batch_process_gene_presence(gene_files, args.output_dir / "genes", args.batch_size)
            print(f"Gene Processing Stats: {stats}")
    
    logger.info("Batch processing CLI completed")


if __name__ == "__main__":
    main()
