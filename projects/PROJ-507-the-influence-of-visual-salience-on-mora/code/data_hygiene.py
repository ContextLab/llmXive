import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class DataHygieneError(Exception):
    """Custom exception for data hygiene violations."""
    pass

def verify_data_separation(file_path: str) -> Tuple[bool, str]:
    """
    Verify that the file path belongs to an allowed data directory.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Tuple of (is_valid, message).
    """
    path = Path(file_path)
    path_str = str(path).replace("\\", "/") # Normalize for cross-platform check
    
    # Define allowed real data directories
    allowed_real_prefixes = [
        "data/raw/",
        "data/processed/",
        "data/survey/"
    ]
    
    # Define synthetic data directory
    synthetic_prefix = "data/synth/"
    
    is_synthetic = path_str.startswith(synthetic_prefix)
    is_real = any(path_str.startswith(prefix) for prefix in allowed_real_prefixes)
    
    if is_synthetic:
        return False, f"File path '{file_path}' is in the synthetic data directory."
    elif is_real:
        return True, f"File path '{file_path}' is in an allowed real data directory."
    else:
        # If it's not in any known directory, we might allow it or warn, 
        # but for strict separation, we assume it's suspicious if not in 'data/'
        # However, the task specifically targets 'data/synth/'
        # We'll allow other paths but log a warning if they are not in 'data/'
        if not path_str.startswith("data/"):
            logger.warning(f"File path '{file_path}' is outside the standard 'data/' directory structure.")
        return True, f"File path '{file_path}' is not in the synthetic directory."

def enforce_data_separation(file_path: str, allow_synthetic: bool = False) -> None:
    """
    Enforce strict separation of synthetic and real data paths.
    
    Args:
        file_path: Path to the file to check.
        allow_synthetic: If True, allow paths in 'data/synth/'.
        
    Raises:
        DataHygieneError: If the path is synthetic and allow_synthetic is False.
    """
    is_valid, message = verify_data_separation(file_path)
    
    if not is_valid:
        # This means it's a synthetic path
        if not allow_synthetic:
            error_msg = (
                f"DataHygieneError: Attempting to analyze synthetic data from '{file_path}'. "
                "This is not allowed for empirical claims. "
                "Use the '--allow-synthetic' flag explicitly if you intend to run analysis on synthetic data for testing purposes."
            )
            logger.error(error_msg)
            raise DataHygieneError(error_msg)
        else:
            logger.warning(f"Allowing synthetic data analysis: {file_path}. This is for testing only.")
    else:
        logger.info(f"Data hygiene check passed: {message}")

def get_data_inventory(base_dir: str = "data") -> Dict[str, List[str]]:
    """
    Scan the data directory and categorize files into real and synthetic.
    
    Args:
        base_dir: Base directory to scan.
        
    Returns:
        Dictionary with keys 'real' and 'synthetic' containing lists of file paths.
    """
    inventory = {"real": [], "synthetic": []}
    base = Path(base_dir)
    
    if not base.exists():
        return inventory
        
    for file_path in base.rglob("*"):
        if file_path.is_file():
            path_str = str(file_path).replace("\\", "/")
            if path_str.startswith("data/synth/"):
                inventory["synthetic"].append(path_str)
            else:
                inventory["real"].append(path_str)
                
    return inventory

def main():
    """
    Main entry point for data hygiene verification script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify data separation in the project.")
    parser.add_argument(
        "--scan", 
        action="store_true", 
        help="Scan the entire 'data' directory and report inventory."
    )
    parser.add_argument(
        "--check", 
        type=str, 
        help="Check a specific file path."
    )
    
    args = parser.parse_args()
    
    if args.scan:
        inventory = get_data_inventory()
        print("Data Inventory:")
        print(f"  Real files ({len(inventory['real'])}):")
        for f in inventory['real'][:10]: # Show first 10
            print(f"    - {f}")
        if len(inventory['real']) > 10:
            print(f"    ... and {len(inventory['real']) - 10} more")
            
        print(f"  Synthetic files ({len(inventory['synthetic'])}):")
        for f in inventory['synthetic']:
            print(f"    - {f}")
            
    elif args.check:
        try:
            enforce_data_separation(args.check, allow_synthetic=False)
            print(f"OK: {args.check} is valid.")
        except DataHygieneError as e:
            print(f"ERROR: {e}")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()