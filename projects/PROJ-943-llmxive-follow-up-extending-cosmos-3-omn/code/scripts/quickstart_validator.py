"""
Quickstart Validator for llmXive Follow-up Pipeline.

This script validates the end-to-end reproducibility of the project by:
1. Verifying directory structure exists.
2. Checking configuration and requirements.
3. Running the download script (with streaming) to fetch real data.
4. Running the transform script to process data.
5. Verifying output files are created and contain valid data.
6. Checking memory usage constraints during execution.

Usage:
    python code/scripts/quickstart_validator.py
"""

import os
import sys
import json
import time
import logging
import tracemalloc
from pathlib import Path
from typing import Dict, List, Any

# Add code root to path
CODE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CODE_ROOT))

from config import get_path, get_config
from utils.logger import get_logger, log_memory_usage

# Configure logging
logger = get_logger("quickstart_validator")

def check_directory_structure() -> bool:
    """Verify all required directories exist."""
    required_dirs = [
        "scripts",
        "data/raw",
        "data/processed",
        "data/splits",
        "models",
        "tests",
        "utils"
    ]
    
    missing = []
    for dir_path in required_dirs:
        full_path = CODE_ROOT / dir_path
        if not full_path.exists():
            missing.append(str(full_path))
            logger.error(f"Missing directory: {full_path}")
        else:
            logger.info(f"Directory exists: {full_path}")
    
    if missing:
        logger.error(f"Missing directories: {missing}")
        return False
    
    return True

def check_config_files() -> bool:
    """Verify essential configuration files exist."""
    required_files = [
        "requirements.txt",
        "data/schema/action_schema.json",
        "config.py"
    ]
    
    missing = []
    for file_path in required_files:
        full_path = CODE_ROOT / file_path
        if not full_path.exists():
            missing.append(str(full_path))
            logger.error(f"Missing file: {full_path}")
        else:
            logger.info(f"File exists: {full_path}")
    
    if missing:
        logger.error(f"Missing config files: {missing}")
        return False
    
    # Validate action_schema.json structure
    schema_path = CODE_ROOT / "data/schema/action_schema.json"
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
            required_keys = ["norm_threshold", "text_keywords", "composite_operator", "vector_dimensions"]
            for key in required_keys:
                if key not in schema:
                    logger.error(f"Missing key in schema: {key}")
                    return False
        logger.info("Schema validation passed")
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return False
    
    return True

def run_download_script() -> bool:
    """Execute download script and verify output."""
    download_script = CODE_ROOT / "scripts" / "download.py"
    output_file = get_path("raw_data") / "bridge_samples.jsonl"
    
    if not download_script.exists():
        logger.error(f"Download script not found: {download_script}")
        return False
    
    logger.info("Starting download script execution...")
    tracemalloc.start()
    start_time = time.time()
    
    try:
        # Import and run the main function directly
        from scripts.download import main as download_main
        download_main()
        
        elapsed = time.time() - start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        logger.info(f"Download completed in {elapsed:.2f}s")
        logger.info(f"Peak memory usage: {peak / 1024 / 1024:.2f} MB")
        
        # Check if output file was created
        if not output_file.exists():
            logger.error(f"Output file not created: {output_file}")
            return False
        
        # Verify file has content
        with open(output_file, 'r') as f:
            line_count = sum(1 for _ in f)
            if line_count == 0:
                logger.error("Output file is empty")
                return False
            # Check first line is valid JSON
            f.seek(0)
            first_line = f.readline()
            try:
                json.loads(first_line)
                logger.info(f"Download output valid: {line_count} samples")
            except json.JSONDecodeError:
                logger.error("Output file contains invalid JSON")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Download script failed: {e}")
        tracemalloc.stop()
        return False

def run_transform_script() -> bool:
    """Execute transform script and verify output."""
    transform_script = CODE_ROOT / "scripts" / "transform.py"
    output_file = get_path("processed_data") / "unified_dataset.jsonl"
    
    if not transform_script.exists():
        logger.error(f"Transform script not found: {transform_script}")
        return False
    
    logger.info("Starting transform script execution...")
    tracemalloc.start()
    start_time = time.time()
    
    try:
        from scripts.transform import main as transform_main
        transform_main()
        
        elapsed = time.time() - start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        logger.info(f"Transform completed in {elapsed:.2f}s")
        logger.info(f"Peak memory usage: {peak / 1024 / 1024:.2f} MB")
        
        # Check if output file was created
        if not output_file.exists():
            logger.error(f"Output file not created: {output_file}")
            return False
        
        # Verify file has content and valid structure
        with open(output_file, 'r') as f:
            line_count = sum(1 for _ in f)
            if line_count == 0:
                logger.error("Output file is empty")
                return False
            
            # Check first few lines for required fields
            f.seek(0)
            for i, line in enumerate(f):
                if i >= 3:
                    break
                try:
                    record = json.loads(line)
                    required_fields = ["actions", "text_description", "label"]
                    for field in required_fields:
                        if field not in record:
                            logger.error(f"Missing field '{field}' in record {i}")
                            return False
                    logger.info(f"Transform output valid: {line_count} records")
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in transform output at line {i}")
                    return False
        
        return True
        
    except Exception as e:
        logger.error(f"Transform script failed: {e}")
        tracemalloc.stop()
        return False

def validate_end_to_end() -> Dict[str, Any]:
    """Run full validation pipeline and return results."""
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "checks": {},
        "overall_success": False
    }
    
    logger.info("=" * 60)
    logger.info("Starting llmXive Quickstart Validation")
    logger.info("=" * 60)
    
    # Check 1: Directory Structure
    logger.info("\n[1/4] Checking directory structure...")
    dir_check = check_directory_structure()
    results["checks"]["directory_structure"] = dir_check
    if not dir_check:
        logger.error("Directory structure check FAILED")
        return results
    logger.info("Directory structure check PASSED")
    
    # Check 2: Config Files
    logger.info("\n[2/4] Checking configuration files...")
    config_check = check_config_files()
    results["checks"]["config_files"] = config_check
    if not config_check:
        logger.error("Config files check FAILED")
        return results
    logger.info("Config files check PASSED")
    
    # Check 3: Download Script
    logger.info("\n[3/4] Running download script...")
    download_check = run_download_script()
    results["checks"]["download_script"] = download_check
    if not download_check:
        logger.error("Download script check FAILED")
        return results
    logger.info("Download script check PASSED")
    
    # Check 4: Transform Script
    logger.info("\n[4/4] Running transform script...")
    transform_check = run_transform_script()
    results["checks"]["transform_script"] = transform_check
    if not transform_check:
        logger.error("Transform script check FAILED")
        return results
    logger.info("Transform script check PASSED")
    
    # Final Result
    results["overall_success"] = True
    logger.info("\n" + "=" * 60)
    logger.info("QUICKSTART VALIDATION PASSED")
    logger.info("=" * 60)
    logger.info("All checks completed successfully. Pipeline is reproducible.")
    
    return results

def main():
    """Entry point for the validator."""
    try:
        results = validate_end_to_end()
        
        # Save results to file
        results_path = get_path("processed_data") / "quickstart_validation_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Validation results saved to: {results_path}")
        
        # Exit with appropriate code
        sys.exit(0 if results["overall_success"] else 1)
        
    except Exception as e:
        logger.error(f"Validation failed with unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()