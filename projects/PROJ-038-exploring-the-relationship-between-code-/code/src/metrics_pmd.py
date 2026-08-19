import os
import subprocess
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import logging
logger = logging.getLogger(__name__)

def get_pmd_path() -> str:
    """
    Retrieve the PMD binary path from environment variable or default.
    Raises FileNotFoundError if PMD is not found.
    """
    pmd_path = os.environ.get('PMD_PATH', 'pmd')
    if not shutil.which(pmd_path):
        # Try common locations if not in PATH
        import shutil
        candidates = [
            '/usr/local/bin/pmd',
            '/opt/pmd/bin/pmd',
            os.path.expanduser('~/.local/bin/pmd')
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                pmd_path = candidate
                break
        else:
            raise FileNotFoundError(
                f"PMD binary not found. Please set PMD_PATH environment variable "
                f"or ensure 'pmd' is in your PATH."
            )
    return pmd_path

def calculate_cc_single_file(file_path: str) -> Optional[int]:
    """
    Calculate Cyclomatic Complexity for a single Java file using PMD CLI.
    This is a wrapper around the logic in wrapper_pmd.py.
    
    Args:
        file_path: Path to the Java file
        
    Returns:
        Cyclomatic Complexity value (int) or None if parsing fails
    """
    try:
        from wrapper_pmd import calculate_cc_single_file as pmd_cc_calc
        return pmd_cc_calc(file_path, get_pmd_path())
    except ImportError:
        logger.error("wrapper_pmd module not found. Please ensure it's in the path.")
        return None

def calculate_cc_batch(file_list: List[str]) -> List[Dict[str, Any]]:
    """
    Calculate Cyclomatic Complexity for multiple files.
    
    Args:
        file_list: List of Java file paths
        
    Returns:
        List of dictionaries with file_path and cc values
    """
    try:
        from wrapper_pmd import calculate_cc_batch as pmd_cc_batch
        return pmd_cc_batch(file_list, get_pmd_path())
    except ImportError:
        logger.error("wrapper_pmd module not found. Please ensure it's in the path.")
        return [{'file_path': f, 'cc': None, 'status': 'error'} for f in file_list]

def calculate_cc_for_directory(dir_path: str, output_path: str) -> None:
    """
    Calculate Cyclomatic Complexity for all Java files in a directory.
    
    Args:
        dir_path: Directory to scan for Java files
        output_path: Path to save results JSON
    """
    try:
        from wrapper_pmd import calculate_cc_for_directory as pmd_cc_dir
        pmd_cc_dir(dir_path, get_pmd_path(), output_path)
    except ImportError:
        logger.error("wrapper_pmd module not found. Please ensure it's in the path.")
        raise

def main():
    """Main entry point for PMD metrics module."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Calculate Cyclomatic Complexity using PMD'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input: JSON file with file list OR directory path'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output JSON file path for results'
    )
    parser.add_argument(
        '--pmd-path',
        default=None,
        help='Path to PMD binary'
    )
    
    args = parser.parse_args()
    
    # Reuse wrapper_pmd main logic
    from wrapper_pmd import main as wrapper_main
    
    # Override pmd-path if provided
    if args.pmd_path:
        os.environ['PMD_PATH'] = args.pmd_path
        
    # Parse args for wrapper
    import sys
    sys.argv = [
        'wrapper_pmd.py',
        '--input', args.input,
        '--output', args.output
    ]
    if args.pmd_path:
        sys.argv.extend(['--pmd-path', args.pmd_path])
        
    wrapper_main()

if __name__ == '__main__':
    main()