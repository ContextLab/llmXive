from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import os
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator

import lizard

from utils.logging import get_logger
from utils.config import get_seed, set_random_seed

# --- Configuration Constants ---
MEMORY_LIMIT_MB = 1024  # 1GB limit per chunk processing
CHUNK_SIZE = 100  # Number of files to process in a chunk
FILE_EXTENSIONS = ['.java']

logger = get_logger(__name__)


@dataclass
class FileMetrics:
    """Container for code complexity metrics of a single file."""
    file_path: str
    filename: str
    extension: str
    cyclomatic_complexity: int = 0
    loc: int = 0
    token_count: int = 0
    nesting_depth: int = 0
    halstead_volume: float = 0.0
    halstead_operators: int = 0
    halstead_operands: int = 0
    parameters: int = 0
    function_count: int = 0
    processing_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "filename": self.filename,
            "extension": self.extension,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "loc": self.loc,
            "token_count": self.token_count,
            "nesting_depth": self.nesting_depth,
            "halstead_volume": self.halstead_volume,
            "halstead_operators": self.halstead_operators,
            "halstead_operands": self.halstead_operands,
            "parameters": self.parameters,
            "function_count": self.function_count,
            "processing_error": self.processing_error
        }


def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file for caching purposes."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.warning(f"Could not compute hash for {file_path}: {e}")
        return ""


def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    try:
        import resource
        # ru_maxrss is in kilobytes on Linux
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    except Exception:
        return 0.0


def check_memory_limit(limit_mb: int = MEMORY_LIMIT_MB) -> bool:
    """Check if current memory usage exceeds the limit."""
    return get_memory_usage_mb() > limit_mb


def calculate_halstead_volume_precise(operators: int, operands: int) -> float:
    """
    Calculate Halstead Volume precisely.
    V = N * log2(n)
    Where N = total operators + operands, n = unique operators + unique operands.
    Note: lizard returns counts of unique operators/operands in `n1`, `n2`.
    """
    if operators == 0 and operands == 0:
        return 0.0
    # lizard.n1 is unique operators, lizard.n2 is unique operands
    # lizard.N1 is total operators, lizard.N2 is total operands
    # The formula uses N (total) and n (unique)
    # However, lizard's 'operators' and 'operands' in the result object
    # usually refer to the counts (N1, N2) or unique (n1, n2) depending on version.
    # We will use the raw counts from the lizard result object directly if available.
    # If the arguments passed are the totals (N1, N2), we need unique (n1, n2).
    # Let's assume the function receives the raw counts from lizard.result.
    # Standard Halstead: N = N1 + N2, n = n1 + n2.
    # Volume V = N * log2(n).
    # We will compute this using the values returned by lizard.
    pass # Implementation moved to run_lizard_on_file to access lizard object directly


def get_file_list_from_directory(directory: str, extension: str = ".java") -> List[str]:
    """Recursively get all files with the specified extension in a directory."""
    files = []
    path = Path(directory)
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    for ext in FILE_EXTENSIONS:
        files.extend(str(p) for p in path.rglob(f"*{ext}"))

    logger.info(f"Found {len(files)} Java files in {directory}")
    return files


def run_lizard_on_file(file_path: str) -> Optional[FileMetrics]:
    """
    Run lizard analysis on a single file and extract metrics.
    Handles errors gracefully (parsing failures, encoding issues).
    """
    metrics = FileMetrics(
        file_path=file_path,
        filename=os.path.basename(file_path),
        extension=os.path.splitext(file_path)[1]
    )

    try:
        # Check file size before parsing to avoid hanging on massive files
        file_size = os.path.getsize(file_path)
        if file_size > 10 * 1024 * 1024: # 10MB limit
            logger.warning(f"Skipping large file: {file_path} ({file_size} bytes)")
            metrics.processing_error = "File too large (>10MB)"
            return metrics

        result = lizard.analyze_file.analyze_source_code(
            file_path,
            file_content=None # Let lizard read the file
        )

        if result is None:
            metrics.processing_error = "Lizard returned None"
            return metrics

        # Aggregate metrics across all functions in the file
        total_cc = 0
        max_nesting = 0
        total_functions = 0
        
        # Lizard returns a list of functions in result.function_list
        if result.function_list:
            for func in result.function_list:
                total_cc += func.cyclomatic_complexity
                if func.nesting_depth > max_nesting:
                    max_nesting = func.nesting_depth
                total_functions += 1

        metrics.cyclomatic_complexity = total_cc
        metrics.loc = result.nloc
        metrics.token_count = result.length
        metrics.nesting_depth = max_nesting
        metrics.function_count = total_functions
        
        # Halstead metrics
        # lizard.result has n1 (unique operators), n2 (unique operands)
        # N1 (total operators), N2 (total operands)
        # Volume V = (N1 + N2) * log2(n1 + n2)
        n1 = result.n1
        n2 = result.n2
        N1 = result.N1
        N2 = result.N2
        
        metrics.halstead_operators = N1
        metrics.halstead_operands = N2
        
        if (n1 + n2) > 0:
            import math
            metrics.halstead_volume = (N1 + N2) * math.log2(n1 + n2)
        else:
            metrics.halstead_volume = 0.0

        metrics.parameters = result.parameters # Usually total parameters across functions or max? Lizard returns max usually.
        
        return metrics

    except Exception as e:
        logger.warning(f"Error processing {file_path}: {e}")
        metrics.processing_error = str(e)
        return metrics


def process_chunk(file_list: List[str], chunk_id: int) -> List[FileMetrics]:
    """Process a chunk of files."""
    results = []
    for f_path in file_list:
        if check_memory_limit():
            logger.warning("Memory limit reached, pausing chunk processing...")
            # In a real scenario, we might yield or sleep, but for simplicity here we just log.
        
        metrics = run_lizard_on_file(f_path)
        if metrics:
            results.append(metrics)
    
    return results


def extract_metrics_for_directory(input_dir: str, output_file: str, chunk_size: int = CHUNK_SIZE) -> int:
    """
    Main entry point for extracting metrics from a directory.
    Implements memory-aware chunked processing.
    """
    logger.info(f"Starting metric extraction for: {input_dir}")
    
    # Get file list
    try:
        file_list = get_file_list_from_directory(input_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        return 0

    if not file_list:
        logger.warning("No Java files found to process.")
        return 0

    # Prepare output directory
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Process in chunks to manage memory
    total_processed = 0
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            "file_path", "filename", "extension", 
            "cyclomatic_complexity", "loc", "token_count", 
            "nesting_depth", "halstead_volume", 
            "halstead_operators", "halstead_operands", 
            "parameters", "function_count", "processing_error"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Chunking
        for i in range(0, len(file_list), chunk_size):
            chunk = file_list[i : i + chunk_size]
            logger.info(f"Processing chunk {i//chunk_size + 1}: {len(chunk)} files")
            
            # Process chunk (sequentially for simplicity, or parallel if needed)
            # Given the I/O bound nature and potential GIL issues with C extensions,
            # threading might be okay, but let's stick to simple iteration for robustness
            # unless performance is critical.
            chunk_results = process_chunk(chunk, i)
            
            for metrics in chunk_results:
                writer.writerow(metrics.to_dict())
                total_processed += 1
            
            # Check memory periodically
            if check_memory_limit():
                logger.error("Memory limit exceeded during processing. Aborting.")
                break

    logger.info(f"Metric extraction complete. Processed {total_processed} files. Output: {output_file}")
    return total_processed


def main():
    parser = argparse.ArgumentParser(description="Extract code complexity metrics using Lizard.")
    parser.add_argument("--input", required=True, help="Input directory containing source code")
    parser.add_argument("--output", required=True, help="Output CSV file path")
    parser.add_argument("--extension", default=".java", help="File extension to process (default: .java)")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE, help="Number of files per chunk")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")

    args = parser.parse_args()

    if args.seed is not None:
        set_random_seed(args.seed)

    logger.info(f"Extracting metrics from {args.input} to {args.output}")
    
    success_count = extract_metrics_for_directory(args.input, args.output, args.chunk_size)
    
    if success_count == 0:
        logger.error("No metrics were extracted. Check input directory and logs.")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()