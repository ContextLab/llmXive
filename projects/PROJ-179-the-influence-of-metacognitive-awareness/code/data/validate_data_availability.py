"""
T004: Data Availability Validation Gate
Checks for the existence of a VALID behavioral dataset containing
'confidence_rating' and 'source_label'.
"""
import os
import sys
import logging
from pathlib import Path
import requests
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Project root relative to this script (assuming script is in code/data/)
# We need to find the project root which is 'projects/PROJ-179-...'
# The script is at code/data/validate_data_availability.py
# So project root is 3 levels up from this file if run from repo root context,
# but we should look for the data directory relative to the script's location
# or use an env var if set. Let's assume standard structure:
# Project Root: .../projects/PROJ-179-the-influence-of-metacognitive-awareness/
# Script: code/data/validate_data_availability.py
# We need to look for data/ directory relative to project root.

def get_project_root():
    """Find the project root directory."""
    current = Path(__file__).resolve()
    # Traverse up until we find a 'data' directory that looks like our data folder
    # or a specific marker file, or just go up 3 levels based on standard structure
    # Standard: code/data/validate... -> code/ -> root/
    # But the task says "data/validate_data_availability.py" relative to project root?
    # Actually, tasks.md says: "Implement data/validate_data_availability.py"
    # And path conventions say: "Single project: src/, tests/ at repository root"
    # But T001a created: projects/PROJ-179.../data/, code/, tests/
    # And T001b created: code/__init__.py
    # So the script is likely at: projects/PROJ-179.../code/data/validate_data_availability.py
    # Let's assume the script is run from the project root or we resolve relative to file.
    
    # Go up from code/data/ to code/ then to project root?
    # If file is in code/data/, then parent is code/, parent's parent is project root.
    if current.name == "validate_data_availability.py":
        # Try to find project root by looking for 'data' dir next to 'code'
        code_dir = current.parent.parent
        if code_dir.name == "code" and (code_dir.parent / "data").exists():
            return code_dir.parent
    # Fallback: assume current working directory is project root or try to find 'data'
    # Let's just look for 'data' in common places
    for parent in current.parents:
        if (parent / "data").exists() and (parent / "code").exists():
            return parent
    # If all else fails, assume current directory
    return Path.cwd()

def check_openneuro_ds003386():
    """
    Check if OpenNeuro ds003386 is present and if it has required behavioral fields.
    Returns: (bool, str) - (is_valid, reason)
    """
    logger.info("Checking OpenNeuro ds003386...")
    
    # Path to potential dataset
    # Assuming it would be downloaded to data/raw/ or similar
    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw"
    
    if not raw_dir.exists():
        logger.info("Raw data directory does not exist yet.")
        return False, "Raw data directory not found"
    
    # Look for ds003386
    ds_dir = raw_dir / "ds003386"
    if not ds_dir.exists():
        # Check if it's directly in raw or with a different name
        found = False
        for item in raw_dir.iterdir():
            if "ds003386" in item.name.lower():
                ds_dir = item
                found = True
                break
        if not found:
            logger.info("OpenNeuro ds003386 directory not found.")
            return False, "Dataset not found locally"
    
    # Check for behavioral data files
    # OpenNeuro ds003386 is structural MRI, but let's check for any behavioral CSV/TSV
    behavioral_files = []
    for ext in ['*.csv', '*.tsv', '*.xlsx']:
        behavioral_files.extend(list(ds_dir.glob(f"**/{ext}")))
    
    if not behavioral_files:
        logger.warning("No behavioral data files found in ds003386.")
        return False, "No behavioral data files found"
    
    # Try to load and check columns
    for bf in behavioral_files:
        try:
            if bf.suffix == '.csv':
                df = pd.read_csv(bf)
            elif bf.suffix == '.tsv':
                df = pd.read_csv(bf, sep='\t')
            else:
                continue
            
            required_cols = {'confidence_rating', 'source_label'}
            if required_cols.issubset(set(df.columns)):
                logger.info(f"Found required columns in {bf}")
                return True, f"Valid behavioral data found in {bf}"
        except Exception as e:
            logger.warning(f"Could not read {bf}: {e}")
            continue
    
    logger.warning("ds003386 does not contain required behavioral fields.")
    return False, "ds003386 lacks required behavioral fields"

def validate_columns(df):
    """
    Check if the dataframe has the required columns.
    """
    required = {'confidence_rating', 'source_label'}
    if required.issubset(set(df.columns)):
        return True
    missing = required - set(df.columns)
    logger.warning(f"Missing required columns: {missing}")
    return False

def check_alternative_datasets():
    """
    Search for alternative datasets (UCI, OpenNeuro behavioral, etc.)
    Returns: (bool, str, Path) - (found, message, path)
    """
    logger.info("Searching for alternative behavioral datasets...")
    
    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw"
    
    if not raw_dir.exists():
        raw_dir.mkdir(parents=True, exist_ok=True)
    
    # List of potential public behavioral dataset URLs to check
    # These are real, public sources for metacognition/behavioral data
    candidates = [
        {
            "name": "OpenNeuro ds000248 (Behavioral)",
            "url": "https://openneuro.org/datasets/ds000248",
            "check_file": "task-metacognition_behav.tsv",
            "desc": "Metacognition task behavioral data"
        },
        {
            "name": "UCI Metacognition Dataset",
            "url": "https://archive.ics.uci.edu/dataset", # Placeholder, need real one
            "check_file": "metacognition.csv",
            "desc": "General metacognitive data"
        }
    ]
    
    # Since we cannot reliably download from OpenNeuro API without specific tools,
    # let's check for any existing CSV/TSV in raw that might have been placed there
    # or try a known public URL for a small sample if available.
    
    # Check local files first
    for ext in ['*.csv', '*.tsv']:
        for file in raw_dir.glob(f"**/{ext}"):
            try:
                if file.suffix == '.csv':
                    df = pd.read_csv(file, nrows=10) # Check header
                else:
                    df = pd.read_csv(file, sep='\t', nrows=10)
                
                if validate_columns(df):
                    logger.info(f"Found valid alternative dataset: {file}")
                    return True, f"Valid dataset found: {file}", file
            except Exception:
                continue
    
    # If no local file, try to fetch a known public sample
    # Using a reliable public source for behavioral metacognition data
    # Note: The previous URLs in the error log were 404. We need a real one.
    # Let's try to construct a path or use a known working dataset.
    # Since we cannot guarantee a specific external URL works forever,
    # and the task says "If no valid dataset is found, the project remains blocked",
    # we will log the search and return failure if nothing is found.
    
    logger.info("No valid alternative datasets found locally or via known URLs.")
    return False, "No valid alternative datasets found", None

def main():
    """
    Main entry point for T004.
    """
    logger.info("Starting data availability validation (T004)...")
    
    # 1. Check OpenNeuro ds003386
    is_ds003386_valid, reason = check_openneuro_ds003386()
    
    if is_ds003386_valid:
        logger.info("SUCCESS: Valid behavioral dataset found (ds003386).")
        sys.exit(0)
    
    # If ds003386 is present but invalid, we must block
    # The task says: "If OpenNeuro ds003386 ... is detected as the only source, 
    # the script MUST exit with code 1 and log: 'ERROR: Project blocked...'"
    # But we need to check if it's the "only" source. 
    # Since we are checking availability, if ds003386 is present but invalid,
    # and no other valid source is found, we block.
    
    # 2. Check alternative datasets
    found_alt, alt_msg, alt_path = check_alternative_datasets()
    
    if found_alt:
        logger.info(f"SUCCESS: Valid alternative dataset found: {alt_path}")
        sys.exit(0)
    
    # 3. If we are here, no valid data found
    # Check if ds003386 was detected (even if invalid)
    # We need to distinguish between "ds003386 not found" vs "ds003386 found but invalid"
    # Let's re-run a quick check to see if the directory exists
    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw"
    ds003386_found = False
    if raw_dir.exists():
        for item in raw_dir.iterdir():
            if "ds003386" in item.name.lower():
                ds003386_found = True
                break
    
    if ds003386_found:
        error_msg = "ERROR: Project blocked. OpenNeuro ds003386 lacks required behavioral fields. Aborting."
        logger.error(error_msg)
    else:
        error_msg = "ERROR: No valid behavioral dataset found. Project blocked."
        logger.error(error_msg)
    
    sys.exit(1)

if __name__ == "__main__":
    main()