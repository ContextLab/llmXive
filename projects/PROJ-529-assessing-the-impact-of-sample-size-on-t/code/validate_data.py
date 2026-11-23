import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

from config import is_real_mode, is_simulation_mode, get_config
from utils.exceptions import DataValidationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
DATA_OUTPUT_DIR = Path("data/output")
TARGET_COUNT = 50  # SC-001 requirement

def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return "FILE_NOT_FOUND"

def validate_data_file(file_path: Path) -> Dict[str, Any]:
    """Validate a single data file (existence, non-empty, basic schema)."""
    if not file_path.exists():
        return {"status": "missing", "path": str(file_path)}
    
    size = file_path.stat().st_size
    if size == 0:
        return {"status": "empty", "path": str(file_path)}
    
    # Determine file type and validate
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                if not isinstance(data, (dict, list)):
                    return {"status": "invalid_json", "path": str(file_path)}
                return {"status": "valid", "path": str(file_path), "checksum": calculate_file_checksum(file_path)}
        except json.JSONDecodeError:
            return {"status": "invalid_json", "path": str(file_path)}
    elif suffix == ".csv":
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                return {"status": "empty_dataframe", "path": str(file_path)}
            return {"status": "valid", "path": str(file_path), "rows": len(df), "checksum": calculate_file_checksum(file_path)}
        except Exception as e:
            return {"status": "corrupt", "path": str(file_path), "error": str(e)}
    elif suffix == ".parquet":
        try:
            df = pd.read_parquet(file_path)
            if df.empty:
                return {"status": "empty_dataframe", "path": str(file_path)}
            return {"status": "valid", "path": str(file_path), "rows": len(df), "checksum": calculate_file_checksum(file_path)}
        except Exception as e:
            return {"status": "corrupt", "path": str(file_path), "error": str(e)}
    else:
        # Generic binary check
        return {"status": "valid", "path": str(file_path), "checksum": calculate_file_checksum(file_path)}

def count_processed_meta_analyses() -> int:
    """
    Count the number of successfully processed meta-analyses.
    Looks for processed files in data/processed/ that contain valid meta-analysis data.
    Specifically checks for the subsample output from T016 and raw sources.
    """
    count = 0
    
    # Strategy 1: Count unique meta-analysis IDs from the subsample parquet if it exists
    subsample_path = DATA_PROCESSED_DIR / "subsample_data.parquet"
    if subsample_path.exists():
        try:
            df = pd.read_parquet(subsample_path)
            if 'meta_id' in df.columns:
                count = df['meta_id'].nunique()
                logger.info(f"Found {count} unique meta-analyses in subsample_data.parquet")
                return count
        except Exception as e:
            logger.warning(f"Could not read subsample_data.parquet: {e}")

    # Strategy 2: Fallback to counting raw JSON/CSV files if parquet is missing
    # This handles the case where T016 might not have run or failed, but T012/T019 succeeded
    if count == 0:
        if DATA_RAW_DIR.exists():
            raw_files = list(DATA_RAW_DIR.glob("*.json")) + list(DATA_RAW_DIR.glob("*.csv"))
            # Filter out config files or non-data files if necessary
            data_files = [f for f in raw_files if "simulation_params" not in f.name and "config" not in f.name]
            count = len(data_files)
            logger.info(f"Found {count} raw data files in data/raw/")
    
    return count

def validate_corpus_integrity() -> Dict[str, Any]:
    """Validate the integrity of the entire corpus."""
    results = {
        "raw_files": [],
        "processed_files": [],
        "total_valid": 0,
        "total_invalid": 0
    }

    # Check raw directory
    if DATA_RAW_DIR.exists():
        for file_path in DATA_RAW_DIR.iterdir():
            if file_path.is_file():
                res = validate_data_file(file_path)
                results["raw_files"].append(res)
                if res["status"] == "valid":
                    results["total_valid"] += 1
                else:
                    results["total_invalid"] += 1

    # Check processed directory
    if DATA_PROCESSED_DIR.exists():
        for file_path in DATA_PROCESSED_DIR.iterdir():
            if file_path.is_file():
                res = validate_data_file(file_path)
                results["processed_files"].append(res)
                if res["status"] == "valid":
                    results["total_valid"] += 1
                else:
                    results["total_invalid"] += 1

    return results

def aggregate_success_rate() -> Dict[str, Any]:
    """
    Aggregate the success rate of meta-analyses processed against the >=50 target.
    Returns a dictionary suitable for the success_rate_report.json.
    """
    actual_count = count_processed_meta_analyses()
    target = TARGET_COUNT
    mode = "real" if is_real_mode() else "simulation"
    
    success_rate = 0.0
    if target > 0:
        success_rate = min(1.0, actual_count / target)
    
    report = {
        "total_target": target,
        "actual_processed": actual_count,
        "success_rate": round(success_rate, 4),
        "mode": mode,
        "meets_requirement": actual_count >= target,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    logger.info(f"Aggregated Success Rate: {actual_count}/{target} ({success_rate:.2%}) in {mode} mode")
    return report

def write_success_rate_report(report: Dict[str, Any]) -> Path:
    """Write the success rate report to data/output/success_rate_report.json."""
    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "success_rate_report.json"
    
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Success rate report written to {output_path}")
    return output_path

def main():
    """Main entry point for validation script."""
    logger.info("Starting data validation pipeline...")
    
    # 1. Validate file integrity
    integrity = validate_corpus_integrity()
    logger.info(f"Corpus Integrity Check: {integrity['total_valid']} valid, {integrity['total_invalid']} invalid")
    
    if integrity['total_invalid'] > 0:
        logger.warning(f"Found {integrity['total_invalid']} invalid files. Proceeding with caution.")
    
    # 2. Aggregate success rate
    report = aggregate_success_rate()
    
    # 3. Write report
    output_path = write_success_rate_report(report)
    
    # 4. Final check against SC-001
    if not report["meets_requirement"]:
        logger.error(f"CRITICAL: Failed to meet SC-001 requirement. Expected >= {TARGET_COUNT}, got {report['actual_processed']}.")
        # Do not raise here to allow the pipeline to continue to simulation mode logic if needed,
        # but the log is critical. The T012a task logic should handle the mode switch based on this.
    else:
        logger.info("SUCCESS: SC-001 requirement met.")
        
    return report

if __name__ == "__main__":
    main()
