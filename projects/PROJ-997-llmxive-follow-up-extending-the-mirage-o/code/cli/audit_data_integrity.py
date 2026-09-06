import json
import logging
import sys
import hashlib
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pandas as pd

# Add project root to path to resolve imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.services.logger import get_logger

# Configure logging
logger = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file safely."""
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_parquet_file(file_path: Path) -> pd.DataFrame:
    """Load a Parquet file safely."""
    if not file_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {file_path}")
    return pd.read_parquet(file_path)

def count_rows_in_parquet(file_path: Path) -> int:
    """Count rows in a Parquet file efficiently."""
    df = pd.read_parquet(file_path)
    return len(df)

def count_prompts_in_sync_inputs(file_path: Path) -> int:
    """Count prompts in synchronized_inputs.json."""
    data = load_json_file(file_path)
    if isinstance(data, list):
        return len(data)
    elif isinstance(data, dict) and 'prompts' in data:
        return len(data['prompts'])
    else:
        # Fallback: assume top-level keys are prompts or count items
        return len(data) if isinstance(data, (list, dict)) else 0

def audit_data_integrity(
    training_sample_path: Path,
    synchronized_inputs_path: Optional[Path] = None,
    output_manifest_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Audit data integrity by:
    1. Generating a checksum manifest for training_sample.parquet
    2. Verifying no rows were dropped silently by comparing input prompt count
       against final output row count.

    Args:
        training_sample_path: Path to training_sample.parquet
        synchronized_inputs_path: Optional path to synchronized_inputs.json
        output_manifest_path: Optional path to write the manifest JSON

    Returns:
        Dictionary containing audit results
    """
    logger.info(f"Starting data integrity audit for {training_sample_path}")

    results = {
        "training_sample_path": str(training_sample_path),
        "checksum": None,
        "row_count": 0,
        "input_source": None,
        "input_count": None,
        "rows_dropped": None,
        "integrity_status": "UNKNOWN",
        "message": ""
    }

    # Step 1: Compute checksum
    try:
        checksum = compute_sha256(training_sample_path)
        results["checksum"] = checksum
        logger.info(f"Computed checksum: {checksum}")
    except Exception as e:
        error_msg = f"Failed to compute checksum: {str(e)}"
        logger.error(error_msg)
        results["message"] = error_msg
        results["integrity_status"] = "FAILED"
        return results

    # Step 2: Count rows in training_sample.parquet
    try:
        row_count = count_rows_in_parquet(training_sample_path)
        results["row_count"] = row_count
        logger.info(f"Training sample row count: {row_count}")
    except Exception as e:
        error_msg = f"Failed to count rows in training_sample.parquet: {str(e)}"
        logger.error(error_msg)
        results["message"] = error_msg
        results["integrity_status"] = "FAILED"
        return results

    # Step 3: Compare with input prompt count if available
    if synchronized_inputs_path and synchronized_inputs_path.exists():
        try:
            input_count = count_prompts_in_sync_inputs(synchronized_inputs_path)
            results["input_source"] = str(synchronized_inputs_path)
            results["input_count"] = input_count

            # Check for row drops
            if input_count != row_count:
                dropped = input_count - row_count
                results["rows_dropped"] = dropped
                if dropped > 0:
                    warning_msg = (
                        f"WARNING: {dropped} rows were dropped during streaming. "
                        f"Input prompts: {input_count}, Output rows: {row_count}"
                    )
                    logger.warning(warning_msg)
                    results["message"] = warning_msg
                    results["integrity_status"] = "WARNING"
                else:
                    error_msg = (
                        f"ERROR: Output rows ({row_count}) exceed input prompts ({input_count}). "
                        "This indicates a data duplication issue."
                    )
                    logger.error(error_msg)
                    results["message"] = error_msg
                    results["integrity_status"] = "FAILED"
            else:
                success_msg = "All input prompts were successfully processed. No rows dropped."
                logger.info(success_msg)
                results["message"] = success_msg
                results["integrity_status"] = "PASSED"

        except Exception as e:
            error_msg = f"Failed to read synchronized_inputs.json: {str(e)}"
            logger.error(error_msg)
            results["message"] = error_msg
            results["integrity_status"] = "FAILED"
    else:
        logger.warning("synchronized_inputs.json not found. Skipping row count comparison.")
        results["message"] = "Input source not provided. Only checksum and row count verified."
        results["integrity_status"] = "PARTIAL"

    # Step 4: Write manifest if path provided
    if output_manifest_path:
        try:
            output_manifest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_manifest_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Audit manifest written to {output_manifest_path}")
        except Exception as e:
            logger.error(f"Failed to write manifest: {str(e)}")

    return results

def main():
    """Main entry point for the audit script."""
    parser = argparse.ArgumentParser(
        description="Audit data integrity for training_sample.parquet"
    )
    parser.add_argument(
        "--training-sample",
        type=str,
        default="projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/data/processed/training_sample.parquet",
        help="Path to training_sample.parquet"
    )
    parser.add_argument(
        "--synchronized-inputs",
        type=str,
        default="projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/data/processed/synchronized_inputs.json",
        help="Path to synchronized_inputs.json (optional)"
    )
    parser.add_argument(
        "--output-manifest",
        type=str,
        default="projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/data/processed/data_integrity_manifest.json",
        help="Path to write the audit manifest JSON"
    )

    args = parser.parse_args()

    training_sample_path = Path(args.training_sample)
    synchronized_inputs_path = Path(args.synchronized_inputs) if args.synchronized_inputs else None
    output_manifest_path = Path(args.output_manifest)

    if not training_sample_path.exists():
        logger.error(f"Training sample file not found: {training_sample_path}")
        sys.exit(1)

    results = audit_data_integrity(
        training_sample_path=training_sample_path,
        synchronized_inputs_path=synchronized_inputs_path,
        output_manifest_path=output_manifest_path
    )

    # Print summary to stdout
    print(json.dumps(results, indent=2))

    # Exit with error code if integrity check failed
    if results["integrity_status"] == "FAILED":
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
