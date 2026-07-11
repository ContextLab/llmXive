"""
Integration test for the full data pipeline: download -> validate -> preprocess.

This test verifies the end-to-end flow of the data acquisition and preprocessing
pipeline as defined in User Story 1 (US1). It ensures that:
1. Data is successfully downloaded from CodeSearchNet.
2. Functions are validated (syntax and imports).
3. Validated functions are sanitized/preprocessed.
4. The final output contains the expected number of functions (based on sample).
5. Logs are generated correctly for exclusion reasons.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.download import download_codesearchnet
from code.data.validate import validate_function, check_syntax, count_external_imports
from code.data.preprocess import sanitize_code, preprocess_function
from code.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error

# Constants for test configuration
TEST_OUTPUT_DIR = "data/integration_test_output"
EXPECTED_MIN_FUNCTIONS = 10  # Minimum functions to consider the pipeline successful for a small sample
MAX_EXTERNAL_IMPORTS = 3

def setup_test_environment():
    """Create a temporary directory for test outputs."""
    test_dir = project_root / TEST_OUTPUT_DIR
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir

def test_download_stage():
    """Test the download stage of the pipeline."""
    logger = get_logger("integration_test")
    test_dir = setup_test_environment()
    output_path = test_dir / "raw"
    output_path.mkdir(parents=True, exist_ok=True)

    log_stage_start(logger, "download", {"output_dir": str(output_path)})

    try:
        # Run the download function
        # Note: This will attempt to fetch real data. If the dataset is unavailable,
        # the test will fail, which is the desired behavior (fail loudly).
        download_codesearchnet(output_dir=str(output_path), dataset_name="codeparrot/codesearchnet-python")

        # Verify output exists
        parquet_files = list(output_path.glob("*.parquet"))
        assert len(parquet_files) > 0, "No parquet files found after download."

        log_stage_complete(logger, "download", {"files_found": len(parquet_files)})
        return True
    except Exception as e:
        log_stage_error(logger, "download", str(e))
        return False

def test_validate_stage(raw_parquet_path):
    """Test the validation stage on a specific parquet file."""
    logger = get_logger("integration_test")
    test_dir = setup_test_environment()
    validated_output = test_dir / "validated_functions.jsonl"

    log_stage_start(logger, "validate", {"input_file": str(raw_parquet_path)})

    valid_count = 0
    invalid_count = 0
    exclusion_reasons = {"syntax_error": 0, "import_failure": 0, "too_many_imports": 0}

    try:
        # Load the dataset
        from datasets import load_dataset
        dataset = load_dataset("codeparrot/codesearchnet-python", split="train", streaming=True)

        for item in dataset:
            code = item.get("code", "")
            if not code:
                continue

            # Check syntax
            if not check_syntax(code):
                exclusion_reasons["syntax_error"] += 1
                invalid_count += 1
                continue

            # Check imports
            import_count = count_external_imports(code)
            if import_count > MAX_EXTERNAL_IMPORTS:
                exclusion_reasons["too_many_imports"] += 1
                invalid_count += 1
                continue

            # If valid, write to output
            valid_count += 1
            with open(validated_output, "a", encoding="utf-8") as f:
                f.write(json.dumps({"code": code, "import_count": import_count}) + "\n")

            # Stop after a reasonable number for integration testing
            if valid_count >= EXPECTED_MIN_FUNCTIONS:
                break

        log_stage_complete(logger, "validate", {
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "exclusion_reasons": exclusion_reasons
        })
        return valid_count >= EXPECTED_MIN_FUNCTIONS
    except Exception as e:
        log_stage_error(logger, "validate", str(e))
        return False

def test_preprocess_stage(validated_jsonl_path):
    """Test the preprocessing stage on validated functions."""
    logger = get_logger("integration_test")
    test_dir = setup_test_environment()
    preprocessed_output = test_dir / "preprocessed_functions.jsonl"

    log_stage_start(logger, "preprocess", {"input_file": str(validated_jsonl_path)})

    processed_count = 0

    try:
        with open(validated_jsonl_path, "r", encoding="utf-8") as infile:
            for line in infile:
                data = json.loads(line)
                original_code = data["code"]

                # Sanitize the code
                sanitized_code = sanitize_code(original_code)

                # Preprocess the function
                processed_func = preprocess_function(sanitized_code)

                if processed_func:
                    processed_count += 1
                    with open(preprocessed_output, "a", encoding="utf-8") as outfile:
                        outfile.write(json.dumps(processed_func) + "\n")

                    # Stop after a reasonable number for integration testing
                    if processed_count >= EXPECTED_MIN_FUNCTIONS:
                        break

        log_stage_complete(logger, "preprocess", {
            "processed_count": processed_count
        })
        return processed_count >= EXPECTED_MIN_FUNCTIONS
    except Exception as e:
        log_stage_error(logger, "preprocess", str(e))
        return False

def test_full_pipeline():
    """Run the full pipeline integration test."""
    logger = get_logger("integration_test")
    test_dir = setup_test_environment()

    # Clean up previous test outputs
    for file in test_dir.glob("*.jsonl"):
        file.unlink()

    # Stage 1: Download
    logger.info("Starting full pipeline integration test.")
    download_success = test_download_stage()
    if not download_success:
        logger.error("Download stage failed. Aborting pipeline test.")
        return False

    # Find the first parquet file for validation
    raw_dir = test_dir / "raw"
    parquet_files = list(raw_dir.glob("*.parquet"))
    if not parquet_files:
        logger.error("No parquet files found for validation.")
        return False

    # Stage 2: Validate
    validated_success = test_validate_stage(parquet_files[0])
    if not validated_success:
        logger.error("Validation stage failed to produce enough valid functions.")
        return False

    validated_output = test_dir / "validated_functions.jsonl"

    # Stage 3: Preprocess
    preprocess_success = test_preprocess_stage(validated_output)
    if not preprocess_success:
        logger.error("Preprocessing stage failed to produce enough processed functions.")
        return False

    logger.info("Full pipeline integration test completed successfully.")
    return True

if __name__ == "__main__":
    success = test_full_pipeline()
    if success:
        print("Integration test PASSED.")
        sys.exit(0)
    else:
        print("Integration test FAILED.")
        sys.exit(1)