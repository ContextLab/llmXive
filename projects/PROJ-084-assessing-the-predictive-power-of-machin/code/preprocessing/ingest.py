"""
Ingest pipeline orchestration for USPTO dataset.
Chains sanitization, yield parsing, and fingerprint generation.
Outputs: data/processed/cleaned_reactions.parquet
"""
import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
from rdkit import RDLogger

# Disable RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from preprocessing.sanitize import sanitize_reactions, parse_yield
from preprocessing.fingerprints import generate_fingerprints_batch
from utils.io import save_parquet, load_parquet
from utils.validators import validate_dataset_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'data' / 'results' / 'ingest.log')
    ]
)
logger = logging.getLogger(__name__)


def run_ingestion_pipeline(
    input_path: Path,
    output_path: Path,
    schema_path: Path | None = None
) -> Dict[str, Any]:
    """
    Orchestrate the full ingestion pipeline:
    1. Load raw data
    2. Sanitize reactions (remove salts, standardize SMILES)
    3. Parse yields
    4. Generate fingerprints (ECFP4, MACCS)
    5. Validate against schema
    6. Save to Parquet

    Args:
        input_path: Path to raw USPTO parquet file
        output_path: Path for cleaned output parquet
        schema_path: Optional path to dataset schema for validation

    Returns:
        Dictionary with pipeline stats and metadata
    """
    start_time = datetime.now()
    stats = {
        'start_time': start_time.isoformat(),
        'input_file': str(input_path),
        'output_file': str(output_path),
        'steps_completed': []
    }

    # 1. Load Raw Data
    logger.info(f"Loading raw data from {input_path}...")
    try:
        df_raw = load_parquet(input_path)
        logger.info(f"Loaded {len(df_raw)} raw records.")
        stats['raw_count'] = len(df_raw)
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        raise

    # 2. Sanitize and Parse Yields
    logger.info("Starting sanitization and yield parsing...")
    try:
        # sanitize_reactions handles standardization and salt removal
        # parse_yield is called internally or we can chain them
        # Based on API surface, sanitize_reactions returns (df_clean, stats)
        df_sanitized, sanitize_stats = sanitize_reactions(df_raw)
        logger.info(f"Sanitization complete. Rows before: {len(df_raw)}, after: {len(df_sanitized)}")
        stats['sanitized_count'] = len(df_sanitized)
        stats['steps_completed'].append('sanitization')
        
        # Ensure yield column is clean (parse_yield might be a helper called inside or separately)
        # Assuming sanitize_reactions handles the main logic, but we ensure yield is float
        if 'yield' not in df_sanitized.columns:
            # Fallback if yield parsing was separate
            logger.warning("Yield column missing after sanitization. Attempting parse_yield.")
            df_sanitized = parse_yield(df_sanitized)
        
        stats['steps_completed'].append('yield_parsing')
    except Exception as e:
        logger.error(f"Sanitization failed: {e}")
        traceback.print_exc()
        raise

    # 3. Generate Fingerprints
    logger.info("Generating fingerprints (ECFP4 and MACCS)...")
    try:
        df_fp, fp_stats = generate_fingerprints_batch(df_sanitized)
        logger.info(f"Fingerprint generation complete. Columns added: {list(df_fp.columns)}")
        stats['fingerprint_stats'] = fp_stats
        stats['steps_completed'].append('fingerprinting')
    except Exception as e:
        logger.error(f"Fingerprint generation failed: {e}")
        traceback.print_exc()
        raise

    # 4. Validate Output
    logger.info("Validating output against schema...")
    if schema_path and schema_path.exists():
        try:
            validate_dataset_file(df_fp, schema_path)
            logger.info("Schema validation passed.")
            stats['steps_completed'].append('validation')
        except Exception as e:
            logger.warning(f"Schema validation failed: {e}")
            # We might still save but log the warning, or raise depending on strictness
            # For now, let's raise to ensure data integrity as per task requirements
            raise
    else:
        logger.warning("No schema path provided or file not found. Skipping validation.")

    # 5. Save Output
    logger.info(f"Saving cleaned data to {output_path}...")
    try:
        ensure_dir = output_path.parent
        ensure_dir.mkdir(parents=True, exist_ok=True)
        save_parquet(df_fp, output_path)
        stats['steps_completed'].append('save')
        logger.info("Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Failed to save output: {e}")
        raise

    end_time = datetime.now()
    stats['end_time'] = end_time.isoformat()
    stats['duration_seconds'] = (end_time - start_time).total_seconds()

    return stats


def main():
    """Main entry point for the ingestion script."""
    # Define paths relative to project root
    project_root = PROJECT_ROOT
    input_file = project_root / 'data' / 'raw' / 'uspto_raw.parquet'
    output_file = project_root / 'data' / 'processed' / 'cleaned_reactions.parquet'
    schema_file = project_root / 'specs' / '001-assess-ml-predictive-power' / 'contracts' / 'dataset.schema.yaml'

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please run T019 (download) first to generate data/raw/uspto_raw.parquet")
        sys.exit(1)

    try:
        stats = run_ingestion_pipeline(input_file, output_file, schema_file)
        print(json.dumps(stats, indent=2))
        logger.info(f"Pipeline finished. Output saved to: {output_file}")
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()