"""
verify_accuracy_gate.py

Executes Reference-Validator logic on dataset URLs (PubChem/SDBS) BEFORE ingestion.
Verifies the presence of the `lambda_max_exp` column.
Raises FileNotFoundError if validation fails.

This task blocks Phase 3 (User Story 1).
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any

# Attempt to import pandas; if missing, we cannot validate the schema.
try:
    import pandas as pd
except ImportError:
    raise ImportError(
        "pandas is required for data validation. "
        "Install it via: pip install pandas"
    )

# Attempt to import rdkit for potential future validation, though not strictly needed for schema check.
try:
    from rdkit import Chem
except ImportError:
    # Non-fatal for this specific gate, but good to warn
    Chem = None

# Configure logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Required column name as per FR-001
REQUIRED_COLUMN = "lambda_max_exp"
REQUIRED_SMILES_COLUMN = "smi"  # Also expected for molecular data

def validate_schema(df: pd.DataFrame, source_name: str) -> bool:
    """
    Validates that the dataframe contains the required columns.
    
    Args:
        df: The dataframe to validate.
        source_name: Name of the data source for logging.
        
    Returns:
        True if schema is valid.
        
    Raises:
        FileNotFoundError: If required columns are missing.
    """
    if df.empty:
        logger.error(f"Data from {source_name} is empty.")
        raise FileNotFoundError(f"Validation failed: Data from {source_name} is empty.")

    cols = set(df.columns)
    missing = []
    
    if REQUIRED_COLUMN not in cols:
        missing.append(REQUIRED_COLUMN)
    if REQUIRED_SMILES_COLUMN not in cols:
        missing.append(REQUIRED_SMILES_COLUMN)

    if missing:
        msg = (
            f"Validation failed for {source_name}: "
            f"Missing required columns: {missing}. "
            f"Available columns: {list(df.columns)}"
        )
        logger.error(msg)
        raise FileNotFoundError(msg)

    logger.info(f"Validation passed for {source_name}: Found {REQUIRED_COLUMN} and {REQUIRED_SMILES_COLUMN}.")
    return True

def fetch_sample_from_pubchem(url: str) -> Optional[pd.DataFrame]:
    """
    Attempts to fetch a small sample from a PubChem-derived URL.
    Since direct PubChem API for UV-Vis tables is complex and often requires
    specific identifiers, this function assumes the URL points to a CSV/TSV
    export (e.g., from a curated dataset hosted on a repository).
    
    For the purpose of this gate, we try to read the head of the file.
    """
    logger.info(f"Attempting to fetch sample from PubChem URL: {url}")
    try:
        # Try reading just the first few rows to check schema without loading everything
        df = pd.read_csv(url, nrows=5)
        return df
    except Exception as e:
        logger.warning(f"Failed to fetch from PubChem URL {url}: {e}")
        return None

def fetch_sample_from_sdbs(url: str) -> Optional[pd.DataFrame]:
    """
    Attempts to fetch a sample from an SDBS URL.
    Similar to PubChem, assumes a CSV/TSV structure for the validation gate.
    """
    logger.info(f"Attempting to fetch sample from SDBS URL: {url}")
    try:
        df = pd.read_csv(url, nrows=5)
        return df
    except Exception as e:
        logger.warning(f"Failed to fetch from SDBS URL {url}: {e}")
        return None

def run_accuracy_gate(
    pubchem_url: Optional[str] = None,
    sdbs_url: Optional[str] = None,
    local_path: Optional[str] = None
) -> bool:
    """
    Executes the accuracy gate logic.
    
    Priority:
    1. If local_path is provided, validate it.
    2. Else, try pubchem_url.
    3. Else, try sdbs_url.
    
    Raises:
        FileNotFoundError: If no source is valid or required columns are missing.
    """
    sources_to_check = []
    
    if local_path:
        sources_to_check.append(("Local File", local_path))
    if pubchem_url:
        sources_to_check.append(("PubChem", pubchem_url))
    if sdbs_url:
        sources_to_check.append(("SDBS", sdbs_url))

    if not sources_to_check:
        raise FileNotFoundError(
            "No data source provided for verification. "
            "Provide --local-path, --pubchem-url, or --sdbs-url."
        )

    for source_name, source_loc in sources_to_check:
        logger.info(f"Checking source: {source_name} ({source_loc})")
        
        df = None
        try:
            if source_name == "Local File":
                if not os.path.exists(source_loc):
                    logger.warning(f"Local file not found: {source_loc}")
                    continue
                df = pd.read_csv(source_loc, nrows=5)
            elif source_name == "PubChem":
                df = fetch_sample_from_pubchem(source_loc)
            elif source_name == "SDBS":
                df = fetch_sample_from_sdbs(source_loc)
            
            if df is not None:
                validate_schema(df, source_name)
                logger.info(f"Accuracy Gate PASSED for {source_name}.")
                return True
                
        except FileNotFoundError:
            # Re-raise immediately if schema validation fails
            raise
        except Exception as e:
            logger.warning(f"Error processing {source_name}: {e}")
            continue

    raise FileNotFoundError(
        "Accuracy Gate FAILED: Could not validate any provided data source. "
        "Ensure the data source contains the 'lambda_max_exp' and 'smi' columns."
    )

def main():
    parser = argparse.ArgumentParser(
        description="Verify data sources for the presence of required columns before ingestion."
    )
    parser.add_argument(
        "--pubchem-url",
        type=str,
        default=None,
        help="URL to a CSV/TSV from PubChem containing UV-Vis data."
    )
    parser.add_argument(
        "--sdbs-url",
        type=str,
        default=None,
        help="URL to a CSV/TSV from SDBS containing UV-Vis data."
    )
    parser.add_argument(
        "--local-path",
        type=str,
        default=None,
        help="Path to a local CSV file to validate."
    )
    
    args = parser.parse_args()
    
    try:
        run_accuracy_gate(
            pubchem_url=args.pubchem_url,
            sdbs_url=args.sdbs_url,
            local_path=args.local_path
        )
        logger.info("Verification successful. Proceeding to ingestion.")
        sys.exit(0)
    except FileNotFoundError as e:
        logger.error(f"Verification FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()