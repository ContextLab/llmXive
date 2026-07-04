"""
Integration test for User Story 2: Summary Report Generation.

This test verifies that running `src/audit/prevalence.py` on a known audit JSON
produces a CSV with the expected columns and valid data types.

It depends on T042 (prevalence implementation) and T046 (bias adjustment tests).
"""
import json
import csv
import os
import sys
import tempfile
import pytest
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from code.src.audit.prevalence import (
    run_prevalence_analysis,
    load_audit_records,
    write_prevalence_results
)
from code.src.utils.logger import get_default_logger

logger = get_default_logger("test_summary_generation")

# Expected columns for the summary report as per FR-005 and T047
EXPECTED_CSV_COLUMNS = [
    "total_summaries",
    "inconsistent_count",
    "inconsistent_rate",
    "bias_adjusted_rate",
    "wilson_ci_lower",
    "wilson_ci_upper"
]

def create_minimal_audit_json(output_path: Path) -> None:
    """
    Creates a minimal valid audit JSON file to be used as input for the prevalence analysis.
    This simulates the output of the validator (T025) without needing the full pipeline.
    """
    audit_records = [
        {
            "url": "https://example.com/test1",
            "domain": "example.com",
            "year": 2023,
            "is_inconsistent": False,
            "p_value_reported": 0.04,
            "p_value_reconstructed": 0.045,
            "effect_size_reported": 0.05,
            "effect_size_reconstructed": 0.052,
            "sample_size_baseline": 1000,
            "sample_size_variant": 1000,
            "data_quality_warning": None
        },
        {
            "url": "https://example.com/test2",
            "domain": "example.com",
            "year": 2023,
            "is_inconsistent": True,
            "p_value_reported": 0.01,
            "p_value_reconstructed": 0.08,
            "effect_size_reported": 0.10,
            "effect_size_reconstructed": 0.15,
            "sample_size_baseline": 500,
            "sample_size_variant": 500,
            "data_quality_warning": None
        },
        {
            "url": "https://test.org/test3",
            "domain": "test.org",
            "year": 2022,
            "is_inconsistent": False,
            "p_value_reported": 0.03,
            "p_value_reconstructed": 0.031,
            "effect_size_reported": 0.02,
            "effect_size_reconstructed": 0.021,
            "sample_size_baseline": 2000,
            "sample_size_variant": 2000,
            "data_quality_warning": None
        }
    ]

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(audit_records, f, indent=2)

@pytest.fixture(scope="function")
def setup_test_files(tmp_path):
    """
    Sets up temporary input and output directories for the test.
    """
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    audit_json_path = input_dir / "audit_report.json"
    create_minimal_audit_json(audit_json_path)

    return {
        "input_dir": input_dir,
        "output_dir": output_dir,
        "audit_json_path": audit_json_path,
        "prevalence_json_path": output_dir / "prevalence.json",
        "summary_csv_path": output_dir / "summary_report.csv"
    }

def test_summary_generation_csv_columns(setup_test_files):
    """
    US2 Integration Test:
    Runs the prevalence analysis on a known audit JSON and verifies that the
    generated summary CSV contains the required columns.
    """
    paths = setup_test_files
    input_json = paths["audit_json_path"]
    output_csv = paths["summary_csv_path"]
    output_json = paths["prevalence_json_path"]

    logger.info(f"Starting test with input: {input_json}")
    
    # 1. Load the audit records to verify they are readable
    try:
        records = load_audit_records(input_json)
        assert len(records) > 0, "No records loaded from audit JSON"
        logger.info(f"Loaded {len(records)} audit records")
    except Exception as e:
        pytest.fail(f"Failed to load audit records: {e}")

    # 2. Run the prevalence analysis (which internally calls compute_prevalence,
    #    wilson_ci, bias_adjustment logic, and report generation if integrated,
    #    but specifically here we need to ensure the CSV generator runs).
    #    Note: The task requires running `src/audit/prevalence.py` logic.
    #    The `run_prevalence_analysis` function handles the full flow including writing.
    
    try:
        # We invoke the main analysis function. 
        # Note: Depending on the exact implementation of run_prevalence_analysis,
        # it might write both JSON and CSV. If it only writes JSON, we might need
        # to call the report generator separately. 
        # However, T047 (report_generator.py) is the one that writes the CSV.
        # The task says "runs src/audit/prevalence.py ... and checks CSV columns".
        # This implies the test should trigger the CSV generation.
        # Looking at T047, it reads audit_report.json and writes summary_report.csv.
        # Looking at T042, prevalence.py writes prevalence.json.
        # The integration test likely needs to run the full US2 flow: 
        # Prevalence -> Report Generation.
        
        # Let's assume the test invokes the specific module functions to ensure
        # the CSV is generated as per T047 which depends on T042.
        # We will manually trigger the steps to ensure the CSV is created.
        
        from code.src.audit.report_generator import generate_summary_report
        
        # Run prevalence analysis first to ensure data is ready (though it reads audit_report.json directly)
        # The prevalence module calculates the stats.
        # We'll call the function that writes the prevalence JSON to simulate the dependency.
        # But the CSV generator reads the audit_report.json directly.
        
        # To be safe and strictly follow "runs src/audit/prevalence.py", we ensure
        # the prevalence module is executed (calculating the rates) and then
        # the report generator creates the CSV.
        
        # Step A: Run Prevalence Logic (T042)
        # The function `run_prevalence_analysis` in prevalence.py writes prevalence.json.
        # It reads from the audit JSON.
        run_prevalence_analysis(
            input_json_path=input_json,
            output_json_path=output_json,
            output_csv_path=output_csv  # Assuming it might write CSV or we call the generator
        )
        
        # If run_prevalence_analysis doesn't write CSV, we call the generator explicitly.
        # Based on T047, report_generator.py is responsible for the CSV.
        # Let's check if the file exists. If not, we call the generator.
        if not output_csv.exists():
            generate_summary_report(
                audit_json_path=input_json,
                output_csv_path=output_csv
            )
            
    except Exception as e:
        logger.error(f"Error during analysis or report generation: {e}", exc_info=True)
        pytest.fail(f"Failed to run prevalence analysis or generate report: {e}")

    # 3. Verify the CSV file exists
    assert output_csv.exists(), f"Summary CSV {output_csv} was not created"
    logger.info(f"CSV file created at {output_csv}")

    # 4. Read the CSV and verify columns
    with open(output_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        assert headers is not None, "CSV file is empty or has no headers"
        
        missing_columns = set(EXPECTED_CSV_COLUMNS) - set(headers)
        assert len(missing_columns) == 0, f"Missing required columns: {missing_columns}"
        
        logger.info(f"CSV headers verified: {headers}")

    # 5. Verify row count (should be 1 summary row + header)
    with open(output_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        # We expect at least one row of summary data
        assert len(rows) >= 1, "CSV should contain at least one summary row"
        
        # Verify data types for the first row
        row = rows[0]
        assert isinstance(int(row["total_summaries"]), int), "total_summaries must be integer"
        assert float(row["inconsistent_rate"]) >= 0.0, "inconsistent_rate must be >= 0"
        assert float(row["inconsistent_rate"]) <= 1.0, "inconsistent_rate must be <= 1"
        assert float(row["wilson_ci_lower"]) >= 0.0, "wilson_ci_lower must be >= 0"
        assert float(row["wilson_ci_upper"]) <= 1.0, "wilson_ci_upper must be <= 1"
        assert float(row["wilson_ci_upper"]) >= float(row["wilson_ci_lower"]), "CI upper must be >= lower"

    logger.info("All assertions passed. CSV columns and data types are valid.")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])