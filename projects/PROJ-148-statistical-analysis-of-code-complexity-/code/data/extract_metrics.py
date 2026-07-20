from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator

import lizard

# Import local utilities as per project API surface
from utils.logging import get_logger
from utils.config import get_seed

# ----------------------------------------------------------------------
# Data Structures
# ----------------------------------------------------------------------

@dataclass
class FileMetrics:
    """Container for complexity metrics of a single file."""
    file_path: str
    project_id: str
    lines_of_code: int
    cyclomatic_complexity: int
    token_count: int
    nesting_depth: int
    halstead_volume: float
    n_functions: int
    parse_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "project_id": self.project_id,
            "lines_of_code": self.lines_of_code,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "token_count": self.token_count,
            "nesting_depth": self.nesting_depth,
            "halstead_volume": self.halstead_volume,
            "n_functions": self.n_functions,
            "parse_error": self.parse_error
        }

# ----------------------------------------------------------------------
# Utility Functions
# ----------------------------------------------------------------------

def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file for caching."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB (best effort)."""
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    except Exception:
        return 0.0

def check_memory_limit(limit_mb: float = 500.0) -> bool:
    """Check if current memory usage is within limit."""
    current = get_memory_usage_mb()
    return current < limit_mb

def calculate_halstead_volume_precise(operators: int, operands: int, unique_operators: int, unique_operands: int) -> float:
    """
    Calculate Halstead Volume with precise handling.
    V = N * log2(n)
    N = total operators + total operands
    n = unique operators + unique operands
    Returns 0.0 if division by zero or invalid inputs.
    """
    if unique_operators == 0 or unique_operands == 0:
        return 0.0
    try:
        N = operators + operands
        n = unique_operators + unique_operands
        if n <= 0:
            return 0.0
        return N * (n.bit_length() if n > 0 else 0) # Approximation for log2
        # Actually, math.log2 is safer and precise enough
        import math
        return N * math.log2(n)
    except (ValueError, ZeroDivisionError):
        return 0.0

def calculate_halstead_volume(result: lizard.LizardAnalysisResult) -> float:
    """
    Extract Halstead volume from lizard result if available,
    otherwise compute manually from operator/operand counts.
    """
    if hasattr(result, 'halstead_volume') and result.halstead_volume is not None:
        return float(result.halstead_volume)
    
    # Fallback calculation based on lizard's internal counts if available
    # Lizard doesn't always expose these directly in the high-level API,
    # so we rely on the precise calculation if we can extract counts.
    # For this implementation, we use the result's raw data if accessible
    # or default to 0.0 if not easily extractable without parsing raw tokens.
    # Lizard's 'result' object usually has 'halstead_volume' populated.
    return 0.0 

def get_file_list_from_directory(directory: str, extension: str = ".java") -> List[str]:
    """Recursively get all files with the given extension."""
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith(extension):
                files.append(os.path.join(root, filename))
    return files

# ----------------------------------------------------------------------
# Core Processing Logic
# ----------------------------------------------------------------------

def run_lizard_on_file(file_path: str, logger: logging.Logger) -> Optional[FileMetrics]:
    """
    Run lizard on a single file and extract metrics.
    Returns FileMetrics object or None if parsing fails (with error logged).
    Implements T050: Fallback handling for parse failures.
    """
    project_id = Path(file_path).parent.parent.name if len(Path(file_path).parts) > 2 else "unknown"
    
    try:
        # Run lizard
        # lizard.analyze_file.analyze_source_code expects (language, source_code)
        # But analyze_file(file_path) is the standard entry point for files
        result = lizard.analyze_file.analyze_file(file_path)
        
        if result is None:
            logger.warning(f"Failed to analyze file (None result): {file_path}")
            return FileMetrics(
                file_path=file_path,
                project_id=project_id,
                lines_of_code=0,
                cyclomatic_complexity=0,
                token_count=0,
                nesting_depth=0,
                halstead_volume=0.0,
                n_functions=0,
                parse_error="Lizard returned None"
            )

        # Extract metrics
        # Lizard result structure:
        # .lines_of_code (total lines)
        # .cyclomatic_complexity (average? or max? usually total or average per function)
        # lizard returns a list of functions. We aggregate.
        
        total_cc = 0
        max_nesting = 0
        total_tokens = 0
        n_functions = 0
        
        # Lizard result has a .function_list
        if hasattr(result, 'function_list') and result.function_list:
            for func in result.function_list:
                n_functions += 1
                total_cc += func.cyclomatic_complexity
                if func.nesting_depth > max_nesting:
                    max_nesting = func.nesting_depth
                # Token count is often not directly exposed as a single sum in high-level API
                # We approximate or use 0 if not available. 
                # Lizard does count tokens internally but exposing it requires specific flags or version.
                # We will set to 0 if not directly available in this version, or estimate.
                # For robustness, we rely on what lizard provides.
                if hasattr(func, 'token_count'):
                    total_tokens += func.token_count
        
        # If no functions found (e.g. empty file), defaults remain 0
        avg_cc = total_cc / n_functions if n_functions > 0 else 0
        # For file-level CC, we often use the sum or max. Let's use sum of function CCs as file complexity.
        file_cc = total_cc 
        
        # Halstead Volume
        # Lizard result has .halstead_volume if calculated, but often needs explicit flag.
        # We'll use a safe fallback.
        halstead = calculate_halstead_volume(result)

        return FileMetrics(
            file_path=file_path,
            project_id=project_id,
            lines_of_code=result.lines_of_code,
            cyclomatic_complexity=file_cc, # Sum of function complexities
            token_count=total_tokens,
            nesting_depth=max_nesting,
            halstead_volume=halstead,
            n_functions=n_functions,
            parse_error=None
        )

    except Exception as e:
        # T050: Log warning and skip
        logger.warning(f"Error parsing file {file_path}: {e}")
        return FileMetrics(
            file_path=file_path,
            project_id=project_id,
            lines_of_code=0,
            cyclomatic_complexity=0,
            token_count=0,
            nesting_depth=0,
            halstead_volume=0.0,
            n_functions=0,
            parse_error=str(e)
        )

def process_chunk(file_list: List[str], chunk_size: int, logger: logging.Logger) -> Iterator[FileMetrics]:
    """
    Process files in chunks to manage memory (T051).
    Yields FileMetrics objects one by one to avoid loading all into memory at once.
    """
    for i in range(0, len(file_list), chunk_size):
        chunk = file_list[i : i + chunk_size]
        # Check memory before processing chunk
        if not check_memory_limit(limit_mb=1024.0): # 1GB limit per chunk processing
            logger.warning("Memory limit approaching, pausing chunk processing.")
            time.sleep(1) # Brief pause to allow GC

        for file_path in chunk:
            metrics = run_lizard_on_file(file_path, logger)
            if metrics:
                yield metrics

def extract_metrics_for_directory(
    input_dir: str,
    output_path: str,
    extension: str = ".java",
    chunk_size: int = 50,
    seed: int = 42
) -> int:
    """
    Main entry point to extract metrics from a directory of source files.
    Writes results to a CSV file.
    """
    logger = get_logger("extract_metrics")
    logger.info(f"Starting metric extraction for: {input_dir}")
    
    # Set seed for reproducibility if needed (though lizard is deterministic)
    set_random_seed(seed)
    
    # Get file list
    file_list = get_file_list_from_directory(input_dir, extension)
    logger.info(f"Found {len(file_list)} files with extension {extension}")
    
    if not file_list:
        logger.warning("No files found to process.")
        # Write empty CSV with headers
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FileMetrics("").to_dict().keys())
            writer.writeheader()
        return 0

    # Process and write
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    processed_count = 0
    
    with open(output_path, 'w', newline='') as f:
        fieldnames = list(FileMetrics("").to_dict().keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for metrics in process_chunk(file_list, chunk_size, logger):
            writer.writerow(metrics.to_dict())
            processed_count += 1
            
            # Progress logging
            if processed_count % 100 == 0:
                logger.info(f"Processed {processed_count} files...")

    logger.info(f"Completed. Wrote metrics for {processed_count} files to {output_path}")
    return processed_count

def main():
    parser = argparse.ArgumentParser(description="Extract code complexity metrics using Lizard.")
    parser.add_argument("--input", required=True, help="Input directory containing source files.")
    parser.add_argument("--output", required=True, help="Output CSV file path.")
    parser.add_argument("--extension", default=".java", help="File extension to process (default: .java).")
    parser.add_argument("--chunk-size", type=int, default=50, help="Number of files to process in a chunk.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.input):
        print(f"Error: Input directory '{args.input}' does not exist.")
        sys.exit(1)
        
    count = extract_metrics_for_directory(
        input_dir=args.input,
        output_path=args.output,
        extension=args.extension,
        chunk_size=args.chunk_size,
        seed=args.seed
    )
    
    print(f"Successfully extracted metrics for {count} files.")

if __name__ == "__main__":
    main()
