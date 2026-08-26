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
    """Calculate Lines of Code (LOC) for a single Java file using AST parsing."""
    # This is a simplified implementation. In a real scenario, we would use
    # a proper Java AST parser like tree-sitter-java or JavaParser.
    # For now, we'll count non-empty, non-comment lines.
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
    """Calculate LOC for a batch of files."""
    results = {}
    for file_path in files:
        results[file_path] = calculate_loc_ast(file_path)
    return results

def calculate_cc_single_file(file_path: Path) -> int:
    """Calculate Cyclomatic Complexity for a single Java file."""
    # Delegate to PMD wrapper
    return calculate_cc_single_file(file_path)

def calculate_halstead_single_file(file_path: Path) -> float:
    """Calculate Halstead Volume for a single Java file."""
    # Delegate to Halstead wrapper
    return calculate_halstead_for_file(file_path)

def calculate_metrics_batch(files: List[Path], log_interval: int = 100) -> List[Dict[str, Any]]:
    """Calculate all metrics for a batch of files with memory monitoring."""
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
    """Main entry point for the metrics module."""
    logger.info("Starting metrics calculation with memory monitoring.")
    
    # Example usage (in a real scenario, this would be driven by ingest.py)
    # This is just a placeholder to demonstrate the interface
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
