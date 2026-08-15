"""
Quickstart Validation Script for PROJ-487
==========================================
This script validates the full pipeline reproducibility by executing
all major stages in sequence and verifying output artifacts exist.

It serves as the final validation step (T034) ensuring:
1. Data fetch scripts produce valid CSVs
2. Preprocessing produces aligned, stationary data
3. Analysis produces Granger results and reports
4. All validation checks pass
"""
import os
import sys
import subprocess
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logging import get_logger

logger = get_logger("quickstart_validation")

def run_script(script_path: Path, args: List[str] = None, timeout: int = 3600) -> Tuple[bool, str]:
    """Execute a Python script and return success status and output."""
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output = result.stdout + "\n" + result.stderr
        
        if result.returncode != 0:
            logger.error(f"Script failed with exit code {result.returncode}")
            logger.error(f"Output:\n{output}")
            return False, output
        
        logger.info(f"Script completed successfully")
        return True, output
        
    except subprocess.TimeoutExpired:
        logger.error(f"Script timed out after {timeout} seconds")
        return False, f"Timeout after {timeout} seconds"
    except Exception as e:
        logger.error(f"Error running script: {str(e)}")
        return False, str(e)

def check_file_exists(file_path: Path, expected_min_rows: int = 0) -> Tuple[bool, str]:
    """Check if a file exists and has expected content."""
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    if file_path.suffix == '.csv':
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            if len(df) < expected_min_rows:
                return False, f"File {file_path} has {len(df)} rows, expected >= {expected_min_rows}"
            logger.info(f"File {file_path} validated: {len(df)} rows")
            return True, f"OK: {len(df)} rows"
        except Exception as e:
            return False, f"Error reading {file_path}: {str(e)}"
    
    elif file_path.suffix == '.json':
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return True, "OK: JSON file valid"
        except Exception as e:
            return False, f"Error reading {file_path}: {str(e)}"
    
    elif file_path.suffix == '.pdf':
        if file_path.stat().st_size == 0:
            return False, f"File {file_path} is empty"
        return True, f"OK: {file_path.stat().st_size} bytes"
    
    else:
        if file_path.stat().st_size == 0:
            return False, f"File {file_path} is empty"
        return True, f"OK: {file_path.stat().st_size} bytes"

def validate_artifacts() -> Dict[str, Tuple[bool, str]]:
    """Validate all required output artifacts."""
    artifacts = {
        "data/raw/gdelt_events.csv": (True, 1),
        "data/raw/google_trends.csv": (True, 1),
        "data/processed/aligned_timeseries.csv": (True, 20),
        "data/processed/stationarity_check.csv": (True, 1),
        "data/processed/granger_results.csv": (True, 1),
        "data/reports/analysis_report.pdf": (True, 0),
        "data/validation_status.json": (False, 0),  # Optional
    }
    
    results = {}
    for artifact_path, (required, min_rows) in artifacts.items():
        full_path = PROJECT_ROOT / artifact_path
        exists, msg = check_file_exists(full_path, min_rows)
        
        if not exists and required:
            logger.error(f"MISSING REQUIRED: {artifact_path} - {msg}")
        elif exists:
            logger.info(f"VALIDATED: {artifact_path} - {msg}")
        
        results[artifact_path] = (exists, msg)
    
    return results

def main():
    """Run the full validation pipeline."""
    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation for PROJ-487")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    validation_results = {}
    all_passed = True
    
    # Stage 1: Fetch Data (if raw data doesn't exist)
    logger.info("\n--- Stage 1: Data Fetch Validation ---")
    gdelt_path = PROJECT_ROOT / "data/raw/gdelt_events.csv"
    trends_path = PROJECT_ROOT / "data/raw/google_trends.csv"
    
    if not gdelt_path.exists() or not trends_path.exists():
        logger.info("Raw data missing, attempting fetch...")
        
        # Try fetch GDELT
        success, output = run_script(PROJECT_ROOT / "code/data/fetch_gdelt.py")
        if not success:
            logger.error("GDELT fetch failed - validation cannot proceed without data")
            all_passed = False
        else:
            logger.info("GDELT fetch completed")
        
        # Try fetch Google Trends
        success, output = run_script(PROJECT_ROOT / "code/data/fetch_google_trends.py")
        if not success:
            logger.error("Google Trends fetch failed - validation cannot proceed without data")
            all_passed = False
        else:
            logger.info("Google Trends fetch completed")
    else:
        logger.info("Raw data already exists, skipping fetch")
    
    # Stage 2: Preprocess Data
    logger.info("\n--- Stage 2: Preprocessing Validation ---")
    success, output = run_script(PROJECT_ROOT / "code/data/preprocess.py")
    if not success:
        logger.error("Preprocessing failed")
        all_passed = False
    else:
        logger.info("Preprocessing completed")
    
    # Stage 3: Analysis
    logger.info("\n--- Stage 3: Analysis Validation ---")
    success, output = run_script(PROJECT_ROOT / "code/data/analyze.py")
    if not success:
        logger.error("Analysis failed")
        all_passed = False
    else:
        logger.info("Analysis completed")
    
    # Stage 4: Validate all artifacts
    logger.info("\n--- Stage 4: Artifact Validation ---")
    artifact_results = validate_artifacts()
    
    for artifact, (exists, msg) in artifact_results.items():
        if not exists:
            all_passed = False
        validation_results[artifact] = {"exists": exists, "message": msg}
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total duration: {duration:.2f} seconds")
    logger.info(f"Overall status: {'PASSED' if all_passed else 'FAILED'}")
    
    logger.info("\nArtifact Status:")
    for artifact, result in validation_results.items():
        status = "✓" if result["exists"] else "✗"
        logger.info(f"  {status} {artifact}: {result['message']}")
    
    # Write validation report
    report_path = PROJECT_ROOT / "data/reports/quickstart_validation_report.json"
    report = {
        "timestamp": start_time.isoformat(),
        "duration_seconds": duration,
        "status": "passed" if all_passed else "failed",
        "artifacts": validation_results
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"\nValidation report saved to: {report_path}")
    
    if not all_passed:
        logger.error("\nVALIDATION FAILED: Check logs for details")
        sys.exit(1)
    else:
        logger.info("\nVALIDATION PASSED: Pipeline is reproducible")
        sys.exit(0)

if __name__ == "__main__":
    main()
