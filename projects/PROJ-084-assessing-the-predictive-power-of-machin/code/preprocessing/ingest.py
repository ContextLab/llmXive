"""
Ingest pipeline: Orchestrate sanitization, yield parsing, and fingerprint generation.
Validates output against dataset.schema.yaml and saves to data/processed/cleaned_reactions.parquet.
"""

import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np

# Project imports (matching API surface)
from utils.io import load_parquet, save_parquet, get_file_size_mb
from utils.validators import load_schema, validate_dataset, DatasetSchema, DatasetRecord
from preprocessing.sanitize import sanitize_reactions, parse_yield
from preprocessing.fingerprints import generate_fingerprints_batch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/ingest_pipeline.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-assess-ml-predictive-power" / "contracts" / "dataset.schema.yaml"
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "uspto_raw.parquet"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_reactions.parquet"
QUALITY_REPORT_PATH = PROJECT_ROOT / "data" / "results" / "data_quality_report.json"

def run_ingestion_pipeline(
    input_path: Path = INPUT_PATH,
    output_path: Path = OUTPUT_PATH,
    schema_path: Path = SCHEMA_PATH,
    batch_size: int = 5000
) -> Dict[str, Any]:
    """
    Execute the full ingestion pipeline:
    1. Load raw data
    2. Sanitize structures (remove salts, standardize)
    3. Parse yields
    4. Generate fingerprints
    5. Validate against schema
    6. Save results

    Returns:
        Dict containing pipeline statistics and paths.
    """
    start_time = datetime.now()
    stats = {
        "start_time": start_time.isoformat(),
        "input_path": str(input_path),
        "output_path": str(output_path),
        "schema_path": str(schema_path),
        "steps": []
    }

    logger.info(f"Starting ingestion pipeline at {start_time}")
    logger.info(f"Input file: {input_path}")

    # Step 1: Load raw data
    logger.info("Step 1: Loading raw data...")
    try:
        df_raw = load_parquet(input_path)
        stats["steps"].append({"step": "load_raw", "status": "success", "rows": len(df_raw)})
        logger.info(f"Loaded {len(df_raw)} rows from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        raise

    # Step 2: Sanitize structures and parse yields
    logger.info("Step 2: Sanitizing structures and parsing yields...")
    try:
        df_sanitized, exclusion_stats = sanitize_reactions(df_raw)
        stats["steps"].append({
            "step": "sanitize",
            "status": "success",
            "initial_rows": len(df_raw),
            "sanitized_rows": len(df_sanitized),
            "excluded_rows": exclusion_stats.get("excluded_count", 0),
            "exclusion_reasons": exclusion_stats.get("reasons", {})
        })
        logger.info(f"Sanitization complete. Rows: {len(df_raw)} -> {len(df_sanitized)}")
        logger.info(f"Exclusion reasons: {exclusion_stats.get('reasons', {})}")
    except Exception as e:
        logger.error(f"Failed during sanitization: {e}")
        raise

    # Step 3: Generate fingerprints
    logger.info("Step 3: Generating fingerprints...")
    try:
        df_with_fp = generate_fingerprints_batch(
            df_sanitized,
            batch_size=batch_size,
            logger=logger
        )
        stats["steps"].append({"step": "fingerprint", "status": "success", "rows": len(df_with_fp)})
        logger.info(f"Fingerprint generation complete. Rows: {len(df_with_fp)}")
    except Exception as e:
        logger.error(f"Failed during fingerprint generation: {e}")
        raise

    # Step 4: Validate against schema
    logger.info("Step 4: Validating output against schema...")
    try:
        schema = load_schema(schema_path)
        validation_result = validate_dataset(df_with_fp, schema)
        
        if not validation_result.get("valid", False):
            errors = validation_result.get("errors", [])
            logger.error(f"Schema validation failed: {errors}")
            raise ValueError(f"Output data failed schema validation: {errors}")
        
        stats["steps"].append({
            "step": "validation",
            "status": "success",
            "schema": str(schema_path),
            "valid": True
        })
        logger.info("Schema validation passed.")
    except Exception as e:
        logger.error(f"Schema validation error: {e}")
        raise

    # Step 5: Save output
    logger.info("Step 5: Saving processed data...")
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_parquet(df_with_fp, output_path)
        file_size_mb = get_file_size_mb(output_path)
        stats["steps"].append({
            "step": "save",
            "status": "success",
            "output_path": str(output_path),
            "file_size_mb": file_size_mb
        })
        logger.info(f"Saved {len(df_with_fp)} rows to {output_path} ({file_size_mb:.2f} MB)")
    except Exception as e:
        logger.error(f"Failed to save output: {e}")
        raise

    # Step 6: Generate quality report
    logger.info("Step 6: Generating data quality report...")
    try:
        total_rows = len(df_raw)
        excluded_rows = len(df_raw) - len(df_with_fp)
        exclusion_fraction = excluded_rows / total_rows if total_rows > 0 else 0.0

        quality_report = {
            "timestamp": datetime.now().isoformat(),
            "total_input_rows": total_rows,
            "total_output_rows": len(df_with_fp),
            "excluded_rows": excluded_rows,
            "exclusion_fraction": exclusion_fraction,
            "exclusion_reasons": exclusion_stats.get("reasons", {}),
            "pipeline_stats": stats
        }

        QUALITY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(QUALITY_REPORT_PATH, 'w') as f:
            json.dump(quality_report, f, indent=2)
        
        stats["quality_report_path"] = str(QUALITY_REPORT_PATH)
        logger.info(f"Quality report saved to {QUALITY_REPORT_PATH}")
    except Exception as e:
        logger.error(f"Failed to generate quality report: {e}")
        # Don't fail the pipeline if report generation fails, but log it
        stats["quality_report_error"] = str(e)

    end_time = datetime.now()
    stats["end_time"] = end_time.isoformat()
    stats["duration_seconds"] = (end_time - start_time).total_seconds()

    logger.info(f"Ingestion pipeline completed successfully in {stats['duration_seconds']:.2f} seconds")
    return stats

def main():
    """Main entry point for the ingestion pipeline."""
    try:
        logger.info("Starting main ingestion pipeline execution...")
        stats = run_ingestion_pipeline()
        print(json.dumps(stats, indent=2, default=str))
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
