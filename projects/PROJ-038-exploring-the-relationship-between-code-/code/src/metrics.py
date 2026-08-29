import os
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import psutil

from .config import get_memory_limit_bytes
from .metrics_pmd import calculate_cc_single_file
from .metrics_halstead import calculate_halstead_for_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_loc_ast(file_path: Path) -> int:
    """
    Calculate Lines of Code (LOC) for a single Java file.
    
    This implementation uses a heuristic approach (counting non-empty, 
    non-comment lines) as a proxy for AST parsing until a full Java 
    AST parser (like tree-sitter-java) is integrated in T014.
    
    Args:
        file_path: Path to the Java file.
        
    Returns:
        Integer count of lines of code. Returns 0 if file cannot be read.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        loc = 0
        in_multiline_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                continue
            
            # Handle multiline comments
            if '/*' in stripped:
                in_multiline_comment = True
            if '*/' in stripped:
                in_multiline_comment = False
                continue
            
            # Skip single-line comments
            if stripped.startswith('//'):
                continue
            
            # If we're in a multiline comment, skip
            if in_multiline_comment:
                continue
            
            loc += 1
        
        return loc
    except Exception as e:
        logger.warning(f"Could not calculate LOC for {file_path}: {e}")
        return 0

def calculate_loc_batch(files: List[Path]) -> Dict[Path, int]:
    """
    Calculate LOC for a batch of files.
    
    Args:
        files: List of file paths.
        
    Returns:
        Dictionary mapping file paths to LOC counts.
    """
    results = {}
    for file_path in files:
        results[file_path] = calculate_loc_ast(file_path)
    return results

def calculate_cc_single_file(file_path: Path) -> int:
    """
    Calculate Cyclomatic Complexity for a single Java file.
    
    This function delegates to the PMD CLI wrapper (metrics_pmd.py)
    which runs the PMD static analysis tool to compute complexity.
    
    Args:
        file_path: Path to the Java file.
        
    Returns:
        Integer Cyclomatic Complexity score.
        
    Raises:
        RuntimeError: If PMD CLI fails or is not available.
    """
    # Delegate to PMD wrapper
    return calculate_cc_single_file(file_path)

def calculate_halstead_single_file(file_path: Path) -> float:
    """
    Calculate Halstead Volume for a single Java file.
    
    This function delegates to the Halstead wrapper (metrics_halstead.py)
    which tokenizes the Java source and computes the volume metric.
    
    Args:
        file_path: Path to the Java file.
        
    Returns:
        Float Halstead Volume.
        
    Raises:
        RuntimeError: If parsing fails or metrics cannot be computed.
    """
    # Delegate to Halstead wrapper
    return calculate_halstead_for_file(file_path)

def calculate_metrics_batch(files: List[Path], log_interval: int = 100) -> List[Dict[str, Any]]:
    """
    Calculate all metrics (LOC, CC, Halstead) for a batch of files.
    
    Includes memory monitoring to ensure the process stays within 
    configured limits (see config.py).
    
    Args:
        files: List of file paths to process.
        log_interval: Number of files between memory usage logs.
        
    Returns:
        List of dictionaries containing metrics for each successfully processed file.
        
    Raises:
        MemoryError: If memory limit is exceeded during processing.
    """
    results = []
    limit_bytes = get_memory_limit_bytes()
    
    logger.info(f"Starting batch metric calculation for {len(files)} files.")
    
    for i, file_path in enumerate(files):
        try:
            # Calculate metrics
            loc = calculate_loc_ast(file_path)
            cc = calculate_cc_single_file(file_path)
            halstead = calculate_halstead_single_file(file_path)
            
            results.append({
                'file_path': str(file_path),
                'loc': loc,
                'cc': cc,
                'halstead': halstead
            })
            
            # Log memory usage every log_interval files
            if (i + 1) % log_interval == 0:
                current_ram = psutil.Process(os.getpid()).memory_info().rss
                logger.info(f"Processed {i + 1} files. Current RAM usage: {current_ram / (1024*1024):.2f} MB")
                
                if current_ram >= limit_bytes:
                    logger.error(f"Memory limit exceeded after processing {i + 1} files.")
                    raise MemoryError(f"Memory limit exceeded at file {i + 1}.")
            
        except Exception as e:
            logger.warning(f"Failed to calculate metrics for {file_path}: {e}")
            # Continue with next file
            continue
    
    logger.info(f"Completed batch metric calculation. Processed {len(results)} files successfully.")
    return results

def main():
    """
    Main entry point for the metrics module.
    
    This function serves as a CLI entry point for testing the metric 
    extraction interface. In production, it is driven by ingest.py.
    """
    logger.info("Starting metrics calculation with memory monitoring.")
    
    # Example usage (in a real scenario, this would be driven by ingest.py)
    # This demonstrates the interface without requiring actual Defects4J data
    sample_files = [
        Path('code/data/raw/defects4j/example1.java'),
        Path('code/data/raw/defects4j/example2.java')
    ]
    
    try:
        results = calculate_metrics_batch(sample_files)
        logger.info(f"Metrics calculation complete. {len(results)} files processed.")
    except MemoryError as e:
        logger.error(f"Memory error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during metrics calculation: {e}")
        raise

if __name__ == '__main__':
    main()