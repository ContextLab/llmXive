"""
Extract code complexity metrics from source files using lizard.
Implements memory-aware, chunked processing to stay within a modest RAM limit.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import os
import gc
import psutil
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator

import lizard

from utils.logging import get_logger
from utils.config import get_seed

# Constants
DEFAULT_CHUNK_SIZE = 50  # Number of files per chunk
DEFAULT_RAM_LIMIT_MB = 1024  # 1 GB limit
METRIC_COLUMNS = [
    "file_path", "project_name", "function_name", "loc", "nloc",
    "cyclomatic_complexity", "token_count", "nesting_depth",
    "halstead_volume", "is_bug_fix"
]

logger = get_logger(__name__)


def get_memory_usage_mb() -> float:
    """
    Get current memory usage in MB using psutil.
    Returns the memory usage of the current process.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)


def calculate_halstead_volume(operators: int, operands: int, n1: int, n2: int) -> float:
    """
    Calculate Halstead Volume.
    N = total number of operators and operands
    n = number of distinct operators and operands
    V = N * log2(n)
    """
    if n1 + n2 == 0:
        return 0.0
    N = operators + operands
    n = n1 + n2
    if n == 0:
        return 0.0
    return N * (n1 + n2)


def extract_metrics_for_file(
    file_path: Path,
    project_name: str,
    is_bug_fix: bool = False
) -> List[Dict[str, Any]]:
    """
    Extract complexity metrics for a single file using lizard.
    Handles parsing errors gracefully and returns a list of metrics per function.
    """
    metrics_list = []
    try:
        # Use lizard to analyze the file
        results = lizard.analyze_file.analyze_source_code(
            str(file_path),
            file_path.read_text(encoding='utf-8', errors='ignore')
        )

        if not results.function_list:
            # If no functions found, create a file-level metric
            metrics_list.append({
                "file_path": str(file_path),
                "project_name": project_name,
                "function_name": "<file>",
                "loc": results.nloc,
                "nloc": results.nloc,
                "cyclomatic_complexity": results.cyclomatic_complexity,
                "token_count": results.token_count,
                "nesting_depth": results.max_nesting,
                "halstead_volume": calculate_halstead_volume(
                    results.operator_count,
                    results.operands_count,
                    results.distinct_operators,
                    results.distinct_operands
                ),
                "is_bug_fix": is_bug_fix
            })
        else:
            for func in results.function_list:
                metrics_list.append({
                    "file_path": str(file_path),
                    "project_name": project_name,
                    "function_name": func.name,
                    "loc": func.line_count,
                    "nloc": func.nloc,
                    "cyclomatic_complexity": func.cyclomatic_complexity,
                    "token_count": func.token_count,
                    "nesting_depth": func.max_nesting,
                    "halstead_volume": calculate_halstead_volume(
                        func.operator_count,
                        func.operands_count,
                        func.distinct_operators,
                        func.distinct_operands
                    ),
                    "is_bug_fix": is_bug_fix
                })
    except Exception as e:
        logger.warning(f"Failed to parse {file_path}: {e}")
        # Return a minimal record indicating failure
        metrics_list.append({
            "file_path": str(file_path),
            "project_name": project_name,
            "function_name": "<parse_error>",
            "loc": 0,
            "nloc": 0,
            "cyclomatic_complexity": 0,
            "token_count": 0,
            "nesting_depth": 0,
            "halstead_volume": 0.0,
            "is_bug_fix": is_bug_fix
        })

    return metrics_list


def get_file_list_from_directory(input_dir: Path, extensions: List[str] = None) -> List[Path]:
    """
    Recursively find all source files in a directory.
    """
    if extensions is None:
        extensions = ['.java', '.py', '.cpp', '.c', '.h', '.js', '.ts']
    
    file_list = []
    for ext in extensions:
        file_list.extend(input_dir.rglob(f'*{ext}'))
    
    return sorted(file_list)


def process_chunk(
    files: List[Path],
    project_name: str,
    is_bug_fix_map: Optional[Dict[str, bool]] = None
) -> List[Dict[str, Any]]:
    """
    Process a chunk of files and return their metrics.
    """
    all_metrics = []
    for file_path in files:
        is_bug_fix = False
        if is_bug_fix_map:
            is_bug_fix = is_bug_fix_map.get(str(file_path), False)
        
        metrics = extract_metrics_for_file(file_path, project_name, is_bug_fix)
        all_metrics.extend(metrics)
    return all_metrics


def extract_metrics(
    input_dir: Path,
    output_path: Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    ram_limit_mb: int = DEFAULT_RAM_LIMIT_MB,
    is_bug_fix_map: Optional[Dict[str, bool]] = None
) -> None:
    """
    Extract complexity metrics from all source files in input_dir.
    Processes files in chunks to stay within RAM limits.
    
    Args:
        input_dir: Directory containing source files
        output_path: Path to write the CSV output
        chunk_size: Number of files to process at once
        ram_limit_mb: Maximum RAM usage in MB
        is_bug_fix_map: Optional mapping of file paths to bug-fix status
    """
    logger.info(f"Starting metric extraction from {input_dir}")
    logger.info(f"Chunk size: {chunk_size}, RAM limit: {ram_limit_mb} MB")
    
    # Get all files
    file_list = get_file_list_from_directory(input_dir)
    total_files = len(file_list)
    logger.info(f"Found {total_files} source files")
    
    if total_files == 0:
        logger.warning("No source files found. Creating empty output.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=METRIC_COLUMNS)
            writer.writeheader()
        return
    
    # Determine project name from directory structure
    project_name = input_dir.name
    
    # Process in chunks
    all_metrics = []
    current_chunk = []
    chunk_count = 0
    
    for i, file_path in enumerate(file_list):
        current_chunk.append(file_path)
        
        # Process chunk when it reaches size or at the end
        if len(current_chunk) >= chunk_size or i == total_files - 1:
            logger.info(f"Processing chunk {chunk_count + 1} ({len(current_chunk)} files)")
            
            # Check memory before processing
            mem_before = get_memory_usage_mb()
            if mem_before > ram_limit_mb * 0.8:  # 80% threshold
                logger.warning(f"Memory usage high ({mem_before:.1f} MB). Forcing garbage collection.")
                gc.collect()
            
            chunk_metrics = process_chunk(current_chunk, project_name, is_bug_fix_map)
            all_metrics.extend(chunk_metrics)
            
            # Check memory after processing
            mem_after = get_memory_usage_mb()
            logger.info(f"Chunk {chunk_count + 1} complete. Memory: {mem_after:.1f} MB")
            
            # Force garbage collection if memory is high
            if mem_after > ram_limit_mb * 0.9:
                logger.warning("Memory usage very high. Clearing cache and forcing GC.")
                del chunk_metrics
                gc.collect()
            
            current_chunk = []
            chunk_count += 1
            
            # Optional: Write intermediate results to avoid memory buildup
            if chunk_count % 10 == 0 and all_metrics:
                logger.info(f"Writing intermediate results ({len(all_metrics)} records so far)")
                _write_metrics_to_csv(all_metrics, output_path, append=True)
                all_metrics = []  # Clear in-memory list
    
    # Write remaining metrics
    if all_metrics:
        logger.info(f"Writing final batch ({len(all_metrics)} records)")
        _write_metrics_to_csv(all_metrics, output_path, append=(chunk_count > 0))
    
    logger.info(f"Metric extraction complete. Total records: {sum(1 for _ in open(output_path)) - 1}")


def _write_metrics_to_csv(metrics: List[Dict[str, Any]], output_path: Path, append: bool = False) -> None:
    """
    Write metrics to CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mode = 'a' if append else 'w'
    with open(output_path, mode, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=METRIC_COLUMNS)
        if not append:
            writer.writeheader()
        writer.writerows(metrics)


def main() -> None:
    """
    Main entry point for the script.
    """
    parser = argparse.ArgumentParser(
        description="Extract code complexity metrics from source files."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Input directory containing source files"
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output CSV file path"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Number of files to process per chunk (default: {DEFAULT_CHUNK_SIZE})"
    )
    parser.add_argument(
        "--ram-limit",
        type=int,
        default=DEFAULT_RAM_LIMIT_MB,
        help=f"RAM limit in MB (default: {DEFAULT_RAM_LIMIT_MB})"
    )
    parser.add_argument(
        "--bug-map",
        type=Path,
        default=None,
        help="Optional CSV file mapping file paths to bug-fix status"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.input.exists():
        logger.error(f"Input directory does not exist: {args.input}")
        sys.exit(1)
    
    # Load bug map if provided
    is_bug_fix_map = None
    if args.bug_map and args.bug_map.exists():
        is_bug_fix_map = {}
        with open(args.bug_map, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                is_bug_fix_map[row['file_path']] = row['is_bug_fix'] == 'True'
        logger.info(f"Loaded bug map with {len(is_bug_fix_map)} entries")
    
    # Run extraction
    extract_metrics(
        input_dir=args.input,
        output_path=args.output,
        chunk_size=args.chunk_size,
        ram_limit_mb=args.ram_limit,
        is_bug_fix_map=is_bug_fix_map
    )
    
    logger.info("Extraction completed successfully.")


if __name__ == "__main__":
    main()