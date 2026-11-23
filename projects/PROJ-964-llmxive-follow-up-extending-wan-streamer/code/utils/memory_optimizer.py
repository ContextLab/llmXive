"""
Memory optimization utilities for llmXive pipeline.
Implements memory-efficient data loading and processing patterns.
"""
import os
import gc
import torch
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Generator, Optional, Dict, Any, List, Union
import logging

logger = logging.getLogger(__name__)


def get_memory_usage_mb() -> float:
    """
    Get current process memory usage in MB.
    Uses psutil if available, falls back to /proc on Linux.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        if os.name == 'posix' and os.path.exists('/proc/self/status'):
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        return int(line.split()[1]) / 1024.0
        return 0.0


def force_gc() -> None:
    """Force garbage collection and clear GPU cache if available."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.debug("Garbage collection completed")


def chunked_dataframe_reader(
    file_path: Union[str, Path],
    chunk_size: int = 100000,
    dtype: Optional[Dict[str, str]] = None
) -> Generator[pd.DataFrame, None, None]:
    """
    Read a large Parquet/CSV file in memory-efficient chunks.
    
    Args:
        file_path: Path to the input file
        chunk_size: Number of rows per chunk
        dtype: Optional dtype specification for memory optimization
        
    Yields:
        DataFrame chunks
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Determine file type and read in chunks
    suffix = file_path.suffix.lower()
    
    if suffix == '.parquet':
        # For parquet, we need to read all at once but can optimize dtypes
        # Then yield in chunks
        df = pd.read_parquet(file_path)
        total_rows = len(df)
        for start in range(0, total_rows, chunk_size):
            end = min(start + chunk_size, total_rows)
            chunk = df.iloc[start:end]
            yield chunk
            del chunk
            force_gc()
    elif suffix == '.csv':
        # CSV supports native chunking
        for chunk in pd.read_csv(file_path, chunksize=chunk_size, dtype=dtype):
            yield chunk
            force_gc()
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def optimize_dataframe_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize DataFrame memory usage by downcasting numeric types
    and converting object columns to category where appropriate.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Optimized DataFrame with reduced memory footprint
    """
    memory_before = df.memory_usage(deep=True).sum() / (1024 * 1024)
    optimized_df = df.copy()
    
    # Downcast numeric columns
    numeric_cols = optimized_df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        col_min = optimized_df[col].min()
        col_max = optimized_df[col].max()
        
        if col_min >= 0:
            if col_max <= 255:
                optimized_df[col] = optimized_df[col].astype(np.uint8)
            elif col_max <= 65535:
                optimized_df[col] = optimized_df[col].astype(np.uint16)
            elif col_max <= 4294967295:
                optimized_df[col] = optimized_df[col].astype(np.uint32)
            else:
                optimized_df[col] = optimized_df[col].astype(np.uint64)
        else:
            if col_min >= -128 and col_max <= 127:
                optimized_df[col] = optimized_df[col].astype(np.int8)
            elif col_min >= -32768 and col_max <= 32767:
                optimized_df[col] = optimized_df[col].astype(np.int16)
            elif col_min >= -2147483648 and col_max <= 2147483647:
                optimized_df[col] = optimized_df[col].astype(np.int32)
            else:
                optimized_df[col] = optimized_df[col].astype(np.int64)
    
    # Convert object columns to category if cardinality is low
    object_cols = optimized_df.select_dtypes(include=['object']).columns
    for col in object_cols:
        unique_count = optimized_df[col].nunique()
        total_count = len(optimized_df)
        if unique_count < total_count * 0.5 and unique_count > 1:
            optimized_df[col] = optimized_df[col].astype('category')
    
    memory_after = optimized_df.memory_usage(deep=True).sum() / (1024 * 1024)
    reduction = (1 - memory_after / memory_before) * 100 if memory_before > 0 else 0
    
    logger.info(f"Memory optimization: {memory_before:.2f} MB -> {memory_after:.2f} MB ({reduction:.1f}% reduction)")
    return optimized_df


def stream_process_large_dataset(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    process_func,
    chunk_size: int = 100000
) -> None:
    """
    Process a large dataset in chunks to avoid memory overflow.
    
    Args:
        input_path: Path to input file
        output_path: Path to output file
        process_func: Function to apply to each chunk (receives DataFrame, returns DataFrame)
        chunk_size: Number of rows per chunk
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    first_chunk = True
    for chunk in chunked_dataframe_reader(input_path, chunk_size):
        processed_chunk = process_func(chunk)
        
        if first_chunk:
            processed_chunk.to_parquet(output_path, index=False)
            first_chunk = False
        else:
            # Append to existing file
            existing = pd.read_parquet(output_path)
            combined = pd.concat([existing, processed_chunk], ignore_index=True)
            combined.to_parquet(output_path, index=False)
            del existing, combined
            force_gc()
        
        del processed_chunk, chunk
        force_gc()
    
    logger.info(f"Stream processing completed. Output written to {output_path}")


def validate_memory_constraints(max_memory_mb: float) -> bool:
    """
    Check if current memory usage is within constraints.
    
    Args:
        max_memory_mb: Maximum allowed memory in MB
        
    Returns:
        True if within constraints, False otherwise
    """
    current = get_memory_usage_mb()
    if current > max_memory_mb:
        logger.warning(f"Memory usage {current:.2f} MB exceeds limit {max_memory_mb:.2f} MB")
        return False
    logger.debug(f"Memory usage {current:.2f} MB within limit {max_memory_mb:.2f} MB")
    return True


def cleanup_tensor_memory(tensor_list: List[torch.Tensor]) -> None:
    """
    Clean up a list of tensors by setting to None and forcing GC.
    
    Args:
        tensor_list: List of tensors to clean up
    """
    for i in range(len(tensor_list)):
        tensor_list[i] = None
    force_gc()


def reduce_model_checkpoint_size(
    checkpoint_path: Union[str, Path],
    output_path: Union[str, Path],
    remove_optimizer: bool = True,
    remove_lr_scheduler: bool = True
) -> None:
    """
    Create a reduced-size model checkpoint by removing unnecessary components.
    
    Args:
        checkpoint_path: Path to original checkpoint
        output_path: Path for reduced checkpoint
        remove_optimizer: Whether to remove optimizer state
        remove_lr_scheduler: Whether to remove scheduler state
    """
    checkpoint_path = Path(checkpoint_path)
    output_path = Path(output_path)
    
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    
    checkpoint = torch.load(checkpoint_path, map_location='cpu')
    
    if remove_optimizer and 'optimizer' in checkpoint:
        del checkpoint['optimizer']
        logger.info("Removed optimizer state from checkpoint")
    
    if remove_lr_scheduler and 'scheduler' in checkpoint:
        del checkpoint['scheduler']
        logger.info("Removed scheduler state from checkpoint")
    
    # Save reduced checkpoint
    torch.save(checkpoint, output_path)
    
    original_size = checkpoint_path.stat().st_size / (1024 * 1024)
    reduced_size = output_path.stat().st_size / (1024 * 1024)
    reduction = (1 - reduced_size / original_size) * 100 if original_size > 0 else 0
    
    logger.info(f"Checkpoint reduced: {original_size:.2f} MB -> {reduced_size:.2f} MB ({reduction:.1f}% reduction)")


def main():
    """CLI entry point for memory optimization utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory optimization utilities")
    parser.add_argument('--action', choices=['check', 'optimize', 'reduce-checkpoint'],
                      required=True, help='Action to perform')
    parser.add_argument('--input', type=str, help='Input file path')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--max-memory', type=float, default=7000,
                      help='Maximum memory in MB (default: 7000)')
    
    args = parser.parse_args()
    
    if args.action == 'check':
        current = get_memory_usage_mb()
        if validate_memory_constraints(args.max_memory):
            print(f"Memory OK: {current:.2f} MB / {args.max_memory:.2f} MB")
        else:
            print(f"Memory EXCEEDED: {current:.2f} MB / {args.max_memory:.2f} MB")
            exit(1)
    
    elif args.action == 'optimize':
        if not args.input or not args.output:
            parser.error("--input and --output required for optimize action")
        
        def identity_process(df):
            return optimize_dataframe_dtypes(df)
        
        stream_process_large_dataset(args.input, args.output, identity_process)
    
    elif args.action == 'reduce-checkpoint':
        if not args.input or not args.output:
            parser.error("--input and --output required for reduce-checkpoint action")
        reduce_model_checkpoint_size(args.input, args.output)


if __name__ == '__main__':
    main()
