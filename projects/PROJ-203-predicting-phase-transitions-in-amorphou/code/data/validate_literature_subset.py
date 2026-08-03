"""
Validate the existence and integrity of literature_subset.csv.

T009: Check for the existence and integrity of the hard-coded data/raw/literature_subset.csv.

FAIL LOUDLY: If the file is missing or corrupted, raise FileNotFoundError with message
"FATAL: literature_subset.csv missing or corrupted" and exit with code 1.
Do NOT attempt to fetch from external sources (Zenodo/NIST).
"""

import sys
import os
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_config

def main():
    """Validate literature_subset.csv exists and is readable."""
    config = get_config()
    file_path = Path(config.data.raw_dir) / "literature_subset.csv"
    
    # Check if file exists
    if not file_path.exists():
        print("FATAL: literature_subset.csv missing or corrupted")
        sys.exit(1)
    
    # Try to read the file to verify integrity
    try:
        df = pd.read_csv(file_path)
        
        # Basic integrity checks
        if df.empty:
            print("FATAL: literature_subset.csv missing or corrupted")
            sys.exit(1)
        
        # Check for required columns
        required_columns = ['composition_id', 'Tg_exp', 'Tx_exp']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print("FATAL: literature_subset.csv missing or corrupted")
            sys.exit(1)
        
        print(f"Validated literature_subset.csv: {len(df)} compositions loaded successfully")
        
    except Exception as e:
        print("FATAL: literature_subset.csv missing or corrupted")
        print(f"Error details: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
