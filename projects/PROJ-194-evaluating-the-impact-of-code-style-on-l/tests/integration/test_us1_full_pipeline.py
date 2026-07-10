"""
Integration test for User Story 1: Full Pipeline.

This test runs the full transformation pipeline on 10 sample functions
and asserts that 80 output files (10 functions * 8 variants) exist
with valid Python syntax.

Dependencies:
- code/transform/generator.py (to generate variants)
- code/transform/validator.py (to validate syntax)
- data/raw/sample_functions.json (must exist)
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from transform.generator import generate_all_variants
from transform.validator import validate_python_syntax, ValidationError

SAMPLE_FUNCTIONS_PATH = "data/raw/sample_functions.json"
OUTPUT_DIR = "data/derived/variants"

def load_sample_functions():
    """Load the 10 sample functions from the dataset."""
    path = project_root / SAMPLE_FUNCTIONS_PATH
    if not path.exists():
        raise FileNotFoundError(f"Sample functions file not found at {path}. "
                                "Please ensure data/raw/sample_functions.json exists.")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def test_full_pipeline_variants_generation():
    """
    Integration Test: T012
    
    1. Loads 10 sample functions.
    2. Runs the full 8-way factorial generation.
    3. Asserts exactly 80 variant files are created.
    4. Asserts every generated file has valid Python syntax.
    """
    # Ensure output directory exists
    output_path = project_root / OUTPUT_DIR
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load samples
    samples = load_sample_functions()
    assert len(samples) == 10, f"Expected 10 sample functions, got {len(samples)}"

    # Run generation
    # We assume generate_all_variants returns a list of metadata dicts
    # and writes files to the specified output directory.
    # If the function signature differs, it will raise an error here,
    # which is acceptable for a test failure indicating implementation mismatch.
    try:
        results = generate_all_variants(
            samples=samples,
            output_dir=str(output_path)
        )
    except Exception as e:
        # If generation fails, the test fails immediately.
        raise AssertionError(f"Pipeline generation failed: {str(e)}")

    # Count generated files
    generated_files = list(output_path.glob("*.py"))
    expected_count = 10 * 8  # 10 functions * 8 variants
    
    assert len(generated_files) == expected_count, \
        f"Expected {expected_count} variant files, but found {len(generated_files)}"

    # Validate syntax for every generated file
    validation_errors = []
    for file_path in generated_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            validate_python_syntax(code)
        except ValidationError as ve:
            validation_errors.append(f"{file_path.name}: {ve.message}")
        except SyntaxError as se:
            validation_errors.append(f"{file_path.name}: SyntaxError - {se}")

    if validation_errors:
        error_msg = "Syntax validation failed for the following files:\n" + "\n".join(validation_errors)
        raise AssertionError(error_msg)

    # If we reach here, all checks passed
    print(f"SUCCESS: Generated and validated {len(generated_files)} variants.")
    assert True

if __name__ == "__main__":
    test_full_pipeline_variants_generation()
    print("Integration test T012 passed.")
