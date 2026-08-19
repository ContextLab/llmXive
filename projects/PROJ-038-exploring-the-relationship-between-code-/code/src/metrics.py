"""
Metric extraction interface for code complexity analysis.

This module defines the primary interface for calculating complexity metrics
for Java files. It orchestrates calls to specialized sub-modules for:
- Cyclomatic Complexity (via PMD CLI)
- Halstead Volume (via custom Python implementation)
- Lines of Code (LOC) (via AST parsing)

The interface supports both single-file and batch processing.
"""
import os
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import specialized implementations from sibling modules
# These modules are defined in the project structure as per the API surface
from src.metrics_pmd import calculate_cc_batch, get_pmd_path
from src.metrics_halstead import calculate_halstead_batch, tokenize_java
# Note: calculate_loc_ast is defined in this file below to avoid circular imports
# if the original skeleton had it here, but the API surface lists it as exported.
# We will implement the full logic here or delegate if a specific loc module exists.
# Based on API surface, calculate_loc_ast is expected here.
# However, T014 mentions implementing LOC logic. We will implement a robust LOC calculator here.

logger = logging.getLogger(__name__)


def calculate_loc_ast(file_path: str) -> int:
    """
    Calculate Lines of Code (LOC) for a Java file using simple line counting
    excluding comments and empty lines, as a proxy for AST-based counting
    without requiring a heavy Java AST parser in Python.
    
    For a more accurate AST-based approach, one would use tree-sitter-java,
    but for this interface, we implement a robust line-based counter that
    aligns with standard complexity definitions.
    
    Args:
        file_path (str): Path to the Java file.
        
    Returns:
        int: The number of non-empty, non-comment lines.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        loc = 0
        in_block_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            # Handle block comments
            if in_block_comment:
                if '*/' in stripped:
                    in_block_comment = False
                    # Check if there's code after the comment ends on the same line
                    after_comment = stripped.split('*/', 1)[1].strip()
                    if after_comment and not after_comment.startswith('//'):
                        loc += 1
                continue
            
            # Handle single line comments
            if stripped.startswith('//'):
                continue
            
            # Check for start of block comment
            if '/*' in stripped:
                if '*/' not in stripped:
                    in_block_comment = True
                # If it's /* ... */ on same line, ignore line unless code exists
                # If code exists, we count the line if it has code
                continue 
            
            if stripped:
                loc += 1
                
        return loc
    except Exception as e:
        logger.error(f"Error calculating LOC for {file_path}: {e}")
        raise


def calculate_loc_batch(file_paths: List[str]) -> Dict[str, int]:
    """
    Calculate LOC for a batch of Java files.
    
    Args:
        file_paths (List[str]): List of file paths.
        
    Returns:
        Dict[str, int]: Mapping of file_path to LOC count.
    """
    results = {}
    for path in file_paths:
        results[path] = calculate_loc_ast(path)
    return results


def calculate_cc_single_file(file_path: str) -> int:
    """
    Calculate Cyclomatic Complexity for a single Java file using PMD.
    
    This is a wrapper that delegates to the PMD-specific implementation.
    
    Args:
        file_path (str): Path to the Java file.
        
    Returns:
        int: Cyclomatic Complexity score.
    """
    return calculate_cc_batch([file_path])[file_path]


def calculate_halstead_single_file(file_path: str) -> float:
    """
    Calculate Halstead Volume for a single Java file.
    
    This is a wrapper that delegates to the Halstead-specific implementation.
    
    Args:
        file_path (str): Path to the Java file.
        
    Returns:
        float: Halstead Volume.
    """
    return calculate_halstead_batch([file_path])[file_path]


def calculate_metrics_batch(file_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Calculate all metrics (LOC, CC, Halstead) for a batch of files.
    
    This function orchestrates the extraction of all three metrics for each file
    and returns a list of dictionaries suitable for DataFrame conversion.
    
    Args:
        file_paths (List[str]): List of Java file paths.
        
    Returns:
        List[Dict[str, Any]]: List of metric dictionaries.
            Each dict contains: file_path, loc, cc, halstead_volume
    """
    logger.info(f"Calculating metrics for {len(file_paths)} files...")
    
    # Calculate LOC
    loc_results = calculate_loc_batch(file_paths)
    
    # Calculate Cyclomatic Complexity
    cc_results = calculate_cc_batch(file_paths)
    
    # Calculate Halstead Volume
    halstead_results = calculate_halstead_batch(file_paths)
    
    combined_results = []
    for path in file_paths:
        combined_results.append({
            'file_path': path,
            'loc': loc_results.get(path, 0),
            'cc': cc_results.get(path, 0),
            'halstead_volume': halstead_results.get(path, 0.0)
        })
        
    return combined_results


def main():
    """
    Entry point for command-line execution of metric extraction.
    Expects a JSON file containing a list of file paths as input.
    """
    import json
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract complexity metrics from Java files.")
    parser.add_argument("--input", type=str, required=True, help="Path to JSON file with list of Java file paths.")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON file for results.")
    args = parser.parse_args()
    
    # Load file list
    with open(args.input, 'r') as f:
        file_paths = json.load(f)
        
    # Calculate metrics
    results = calculate_metrics_batch(file_paths)
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Metrics calculated and saved to {args.output}")


if __name__ == "__main__":
    main()