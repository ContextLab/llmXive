"""
Orchestrate the USPTO data ingestion pipeline:
1. Load raw data from data/raw/uspto_raw.parquet
2. Sanitize reactions (remove salts, standardize SMILES, parse yields)
3. Generate fingerprints (ECFP4, MACCS)
4. Save cleaned dataset to data/processed/cleaned_reactions.parquet
"""

import logging
import sys
from pathlib import Path

import pandas as pd

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATA_RAW_DIR, DATA_PROCESSED_DIR
from preprocessing.sanitize import sanitize_reactions
from preprocessing.fingerprints import generate_fingerprints_batch
from utils.io import load_parquet, save_parquet, check_memory_limit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def run_ingestion_pipeline():
    """
    Execute the full ingestion pipeline:
    Raw -> Sanitize -> Fingerprint -> Cleaned Parquet
    """
    logger.info("Starting USPTO ingestion pipeline...")

    # 1. Load raw data
    input_path = DATA_RAW_DIR / "uspto_raw.parquet"
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Run preprocessing/download.py first to download raw data."
        )

    logger.info(f"Loading raw data from {input_path}...")
    df_raw = load_parquet(input_path)
    logger.info(f"Loaded {len(df_raw)} raw reactions.")

    # Check memory before processing
    check_memory_limit(df_raw)

    # 2. Sanitize reactions
    logger.info("Sanitizing reactions (removing salts, standardizing SMILES, parsing yields)...")
    df_clean = sanitize_reactions(df_raw)
    logger.info(f"Sanitization complete. {len(df_clean)} reactions remaining.")

    # 3. Generate fingerprints
    logger.info("Generating fingerprints (ECFP4, MACCS)...")
    df_fp = generate_fingerprints_batch(df_clean)
    logger.info(f"Fingerprint generation complete.")

    # 4. Save cleaned dataset
    output_path = DATA_PROCESSED_DIR / "cleaned_reactions.parquet"
    logger.info(f"Saving cleaned dataset to {output_path}...")
    save_parquet(df_fp, output_path)
    logger.info(f"Pipeline complete. Output saved to {output_path}")

    return df_fp

def main():
    """Entry point for the ingestion script."""
    try:
        df_final = run_ingestion_pipeline()
        logger.info("Ingestion pipeline succeeded.")
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()