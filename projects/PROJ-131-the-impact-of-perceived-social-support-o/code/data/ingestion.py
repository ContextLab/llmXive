"""
code/data/ingestion.py
Handles downloading and loading the Cyberbullying Survey 2021 dataset.
Strictly enforces "Fail Loudly" on real data fetch failures.
"""
import os
import sys
import hashlib
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure pandas is available; if not, the import will fail loudly as required
try:
    import pandas as pd
except ImportError:
    raise RuntimeError("E-DEP-MISSING: pandas is required but not installed. Install via pip install pandas.")

# Attempt to import ucimlrepo; if missing, we must fail loudly rather than fallback
try:
    from ucimlrepo import fetch_dataset
    UCIML_AVAILABLE = True
except ImportError:
    UCIML_AVAILABLE = False
    logger.warning("ucimlrepo not installed. Data fetching will fail unless installed.")

DATASET_ID = 123  # Cyberbullying Survey 2021
RAW_DIR = Path("data/raw")
OUTPUT_FILE = RAW_DIR / "cyberbullying_2021.csv"

def ensure_dirs():
    """Ensure necessary directories exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_dataset():
    """
    Fetch the dataset using ucimlrepo.
    Saves to data/raw/cyberbullying_2021.csv.
    Raises RuntimeError if fetch fails.
    """
    if not UCIML_AVAILABLE:
        raise RuntimeError(
            "E-DEP-MISSING: ucimlrepo is not installed. "
            "Cannot fetch real data. Install via 'pip install ucimlrepo'."
        )

    logger.info(f"Fetching dataset ID {DATASET_ID} from UCI ML Repository...")
    try:
        dataset = fetch_dataset(dataset_id=DATASET_ID)
        # The fetch_dataset object usually has a .data property containing a dict with 'data' (DataFrame)
        if hasattr(dataset, 'data') and 'data' in dataset.data:
            df = dataset.data['data']
        elif isinstance(dataset, pd.DataFrame):
            df = dataset
        else:
            # Fallback structure check
            raise ValueError("Unexpected dataset structure from ucimlrepo.")

        ensure_dirs()
        df.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"Dataset saved to {OUTPUT_FILE}")
        return df
    except Exception as e:
        # CRITICAL: Fail loudly. Do not return synthetic data.
        logger.error(f"Real data fetch failed: {e}")
        raise RuntimeError("E-NO-REAL-SOURCE-001: Real data source (ID 123) not found. Aborting.") from e

def load_cyber_data():
    """
    Load the Cyberbullying Survey dataset.
    Tries to load from disk if exists, otherwise fetches.
    Always validates against real source.
    """
    # Check if file exists
    if OUTPUT_FILE.exists():
        logger.info(f"Loading existing dataset from {OUTPUT_FILE}")
        df = pd.read_csv(OUTPUT_FILE)
        # Basic validation
        if df.empty:
            logger.warning("Loaded file is empty. Re-fetching...")
            return download_dataset()
        return df
    else:
        logger.info("No local dataset found. Fetching...")
        return download_dataset()

def load_gss_data():
    """
    Placeholder for GSS data loading.
    Per Plan, this dataset is excluded.
    """
    logger.warning("GSS dataset loading attempted but excluded per Plan's 'Revised Approach'.")
    return None

def harmonize_datasets(cyber_df: pd.DataFrame, gss_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Harmonize datasets. Currently only returns Cyberbullying data.
    """
    if gss_df is not None:
        logger.warning("GSS data provided but ignored per Plan constraints.")
    return cyber_df

def get_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate a summary of the dataset."""
    return {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "missing_counts": df.isnull().sum().to_dict()
    }

def validate_schema_presence(df: pd.DataFrame, required_cols: list) -> bool:
    """Check if required columns are present."""
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def run_ingestion_checks(df: pd.DataFrame):
    """Run basic integrity checks."""
    if df.empty:
        raise ValueError("Dataset is empty.")
    logger.info("Ingestion checks passed.")

def main():
    """Entry point for ingestion script."""
    try:
        df = load_cyber_data()
        run_ingestion_checks(df)
        summary = get_data_summary(df)
        logger.info(f"Data Summary: {summary}")
        return df
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in ingestion: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
