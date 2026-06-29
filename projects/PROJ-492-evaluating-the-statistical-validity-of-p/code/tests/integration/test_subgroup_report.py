"""
Integration test for T053: Subgroup Report Column Verification

This test runs the full pipeline on a mixed-domain synthetic corpus and verifies
that subgroup report columns are present and correct.

Dependencies:
  - T026: Synthetic dataset generator
  - T050: Subgroup analysis implementation
  - T052: Report generator extension for subgroup CSV
"""
import csv
import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

import pytest

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from src.audit.synthetic import (
    set_all_seeds,
    generate_synthetic_dataset,
    write_csv_output,
    write_json_output,
    verify_outcome_types,
)
from src.audit.subgroup_analysis import (
    set_rng_seed_for_subgroup_analysis,
    load_audit_records_from_json,
    group_records_by_subgroup,
    analyze_subgroups,
    write_subgroup_report,
    write_subgroup_csv,
    run_subgroup_analysis,
)
from src.audit.validator import (
    validate_all_summaries,
    write_audit_report,
)
from src.models.data_models import ABTestSummary, AuditRecord
from src.config import set_rng_seed

# Configure logging for test output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Required columns for subgroup report JSON
REQUIRED_JSON_COLUMNS = [
    'domain',
    'year',
    'count',
    'inconsistent_count',
    'prevalence',
    'fisher_pvalue',
    'bonferroni_adjusted_pvalue',
    'significant',
]

# Required columns for subgroup report CSV
REQUIRED_CSV_COLUMNS = [
    'domain',
    'year',
    'count',
    'inconsistent_count',
    'prevalence',
    'fisher_pvalue',
    'bonferroni_adjusted_pvalue',
    'significant',
]

def create_minimal_audit_records(output_dir: Path, num_records: int = 50) -> List[AuditRecord]:
    """
    Create minimal synthetic audit records with mixed domains and years.

    Args:
        output_dir: Directory to write intermediate files
        num_records: Number of audit records to create

    Returns:
        List of AuditRecord objects
    """
    set_rng_seed(42)
    set_rng_seed_for_subgroup_analysis(42)

    # Define mixed domains for the synthetic corpus
    domains = ['tech', 'e-commerce', 'finance', 'healthcare', 'saas']
    years = [2020, 2021, 2022, 2023, 2024]

    audit_records = []

    for i in range(num_records):
        domain = domains[i % len(domains)]
        year = years[i % len(years)]
        is_inconsistent = (i % 3 == 0)  # ~33% inconsistency rate

        record = AuditRecord(
          summary_url=f"https://{domain}.example.com/test/{i}",
          domain=domain,
          publication_year=year,
          is_inconsistent=is_inconsistent,
          reported_p_value=0.03 if is_inconsistent else 0.08,
          reconstructed_p_value=0.08 if is_inconsistent else 0.03,
          absolute_p_difference=0.05 if is_inconsistent else 0.05,
          effect_size_difference=0.06 if is_inconsistent else 0.04,
          sample_size_mismatch=False,
          data_quality_warning=None,
          validation_notes=f"Test {i}: {domain} domain, year {year}",
          audit_timestamp="2024-01-01T00:00:00Z",
        )
        audit_records.append(record)

    # Write audit records to JSON
    audit_json_path = output_dir / "audit_report.json"
    with open(audit_json_path, 'w') as f:
        json.dump([record.model_dump() for record in audit_records], f, indent=2)

    return audit_records

def test_subgroup_report_json_columns_exist():
    """
    Verify that the subgroup report JSON contains all required columns.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Create synthetic audit records
        logger.info("Creating synthetic audit records...")
        audit_records = create_minimal_audit_records(output_dir, num_records=100)

        # Run subgroup analysis
        logger.info("Running subgroup analysis...")
        run_subgroup_analysis(
            audit_json_path=output_dir / "audit_report.json",
            output_dir=output_dir,
        )

        # Load and verify subgroup report JSON
        subgroup_json_path = output_dir / "subgroup_report.json"
        assert subgroup_json_path.exists(), f"Subgroup report JSON not found at {subgroup_json_path}"

        with open(subgroup_json_path, 'r') as f:
            subgroup_data = json.load(f)

        # Check that the report is a list of records
        assert isinstance(subgroup_data, list), "Subgroup report should be a list of records"
        assert len(subgroup_data) > 0, "Subgroup report should contain at least one record"

        # Verify each record has required columns
        for record in subgroup_data:
            for col in REQUIRED_JSON_COLUMNS:
                assert col in record, f"Missing required column '{col}' in subgroup report record: {record}"

        logger.info(f"✓ Subgroup report JSON has all required columns: {REQUIRED_JSON_COLUMNS}")
        logger.info(f"  Total records: {len(subgroup_data)}")

def test_subgroup_report_csv_columns_exist():
    """
    Verify that the subgroup report CSV contains all required columns.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Create synthetic audit records
        logger.info("Creating synthetic audit records...")
        audit_records = create_minimal_audit_records(output_dir, num_records=100)

        # Run subgroup analysis
        logger.info("Running subgroup analysis...")
        run_subgroup_analysis(
            audit_json_path=output_dir / "audit_report.json",
            output_dir=output_dir,
        )

        # Load and verify subgroup report CSV
        subgroup_csv_path = output_dir / "subgroup_report.csv"
        assert subgroup_csv_path.exists(), f"Subgroup report CSV not found at {subgroup_csv_path}"

        with open(subgroup_csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

            assert fieldnames is not None, "CSV should have fieldnames"

            # Verify all required columns are present
            for col in REQUIRED_CSV_COLUMNS:
                assert col in fieldnames, f"Missing required column '{col}' in subgroup report CSV. Found: {fieldnames}"

        logger.info(f"✓ Subgroup report CSV has all required columns: {REQUIRED_CSV_COLUMNS}")

def test_subgroup_report_mixed_domains():
    """
    Verify that the subgroup report contains records for all expected domains.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Create synthetic audit records with specific domains
        logger.info("Creating synthetic audit records with mixed domains...")
        domains = ['tech', 'e-commerce', 'finance', 'healthcare', 'saas']
        num_records = 50

        set_rng_seed(42)
        set_rng_seed_for_subgroup_analysis(42)

        audit_records = []
        for i in range(num_records):
            domain = domains[i % len(domains)]
            year = 2023
            is_inconsistent = (i % 3 == 0)

            record = AuditRecord(
                summary_url=f"https://{domain}.example.com/test/{i}",
                domain=domain,
                publication_year=year,
                is_inconsistent=is_inconsistent,
                reported_p_value=0.03 if is_inconsistent else 0.08,
                reconstructed_p_value=0.08 if is_inconsistent else 0.03,
                absolute_p_difference=0.05 if is_inconsistent else 0.05,
                effect_size_difference=0.06 if is_inconsistent else 0.04,
                sample_size_mismatch=False,
                data_quality_warning=None,
                validation_notes=f"Test {i}: {domain} domain",
                audit_timestamp="2024-01-01T00:00:00Z",
            )
            audit_records.append(record)

        # Write audit records
        audit_json_path = output_dir / "audit_report.json"
        with open(audit_json_path, 'w') as f:
            json.dump([record.model_dump() for record in audit_records], f, indent=2)

        # Run subgroup analysis
        logger.info("Running subgroup analysis...")
        run_subgroup_analysis(
            audit_json_path=audit_json_path,
            output_dir=output_dir,
        )

        # Load subgroup report
        subgroup_json_path = output_dir / "subgroup_report.json"
        with open(subgroup_json_path, 'r') as f:
            subgroup_data = json.load(f)

        # Extract unique domains from the report
        report_domains = set(record['domain'] for record in subgroup_data)

        # Verify all expected domains are present
        for domain in domains:
            assert domain in report_domains, f"Domain '{domain}' not found in subgroup report. Found: {report_domains}"

        logger.info(f"✓ All expected domains present in subgroup report: {report_domains}")

def test_subgroup_report_prevalence_calculation():
    """
    Verify that prevalence is calculated correctly (inconsistent_count / count).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Create synthetic audit records
        logger.info("Creating synthetic audit records...")
        audit_records = create_minimal_audit_records(output_dir, num_records=60)

        # Run subgroup analysis
        logger.info("Running subgroup analysis...")
        run_subgroup_analysis(
            audit_json_path=output_dir / "audit_report.json",
            output_dir=output_dir,
        )

        # Load subgroup report
        subgroup_json_path = output_dir / "subgroup_report.json"
        with open(subgroup_json_path, 'r') as f:
            subgroup_data = json.load(f)

        # Verify prevalence calculation for each record
        for record in subgroup_data:
            count = record['count']
            inconsistent_count = record['inconsistent_count']
            prevalence = record['prevalence']

            if count > 0:
                expected_prevalence = inconsistent_count / count
                assert abs(prevalence - expected_prevalence) < 0.001, \
                    f"Prevalence mismatch: expected {expected_prevalence}, got {prevalence}"

        logger.info("✓ Prevalence calculations are correct")

def test_full_pipeline_subgroup_report():
    """
    Full integration test: run pipeline components and verify subgroup report.

    This test simulates the full pipeline flow from synthetic data generation
    through subgroup analysis to final report verification.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        data_dir = output_dir / "data" / "synthetic"
        data_dir.mkdir(parents=True)

        logger.info("=== Full Pipeline Subgroup Report Integration Test ===")

        # Step 1: Generate synthetic dataset
        logger.info("Step 1: Generating synthetic dataset...")
        set_all_seeds(42)

        synthetic_csv_path = data_dir / "synthetic_validation.csv"
        synthetic_json_path = data_dir / "synthetic_ground_truth.json"

        # Generate with mixed domains
        synthetic_data = generate_synthetic_dataset(
            num_records=100,
            binary_ratio=0.5,
            continuous_ratio=0.5,
            output_csv_path=synthetic_csv_path,
            output_json_path=synthetic_json_path,
        )

        assert synthetic_csv_path.exists(), "Synthetic CSV not created"
        assert synthetic_json_path.exists(), "Synthetic JSON not created"

        # Step 2: Create audit records from synthetic data
        logger.info("Step 2: Creating audit records...")
        set_rng_seed_for_subgroup_analysis(42)

        domains = ['tech', 'e-commerce', 'finance', 'healthcare', 'saas']
        audit_records = []

        for i, summary in enumerate(synthetic_data):
            domain = domains[i % len(domains)]
            year = 2020 + (i % 5)
            is_inconsistent = (i % 3 == 0)

            record = AuditRecord(
                summary_url=f"https://{domain}.example.com/test/{i}",
                domain=domain,
                publication_year=year,
                is_inconsistent=is_inconsistent,
                reported_p_value=summary.get('reported_p_value', 0.05),
                reconstructed_p_value=summary.get('reconstructed_p_value', 0.05),
                absolute_p_difference=abs(summary.get('reported_p_value', 0.05) - summary.get('reconstructed_p_value', 0.05)),
                effect_size_difference=summary.get('effect_size_difference', 0.05),
                sample_size_mismatch=False,
                data_quality_warning=None,
                validation_notes=f"Pipeline test record {i}",
                audit_timestamp="2024-01-01T00:00:00Z",
            )
            audit_records.append(record)

        # Write audit report
        audit_json_path = output_dir / "output" / "audit_report.json"
        audit_json_path.parent.mkdir(parents=True, exist_ok=True)

        with open(audit_json_path, 'w') as f:
            json.dump([record.model_dump() for record in audit_records], f, indent=2)

        # Step 3: Run subgroup analysis
        logger.info("Step 3: Running subgroup analysis...")
        run_subgroup_analysis(
            audit_json_path=audit_json_path,
            output_dir=output_dir / "output",
        )

        # Step 4: Verify subgroup report JSON
        logger.info("Step 4: Verifying subgroup report JSON...")
        subgroup_json_path = output_dir / "output" / "subgroup_report.json"
        assert subgroup_json_path.exists(), "Subgroup report JSON not created"

        with open(subgroup_json_path, 'r') as f:
            subgroup_data = json.load(f)

        for record in subgroup_data:
            for col in REQUIRED_JSON_COLUMNS:
                assert col in record, f"Missing column '{col}' in subgroup report JSON"

        # Step 5: Verify subgroup report CSV
        logger.info("Step 5: Verifying subgroup report CSV...")
        subgroup_csv_path = output_dir / "output" / "subgroup_report.csv"
        assert subgroup_csv_path.exists(), "Subgroup report CSV not created"

        with open(subgroup_csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

            for col in REQUIRED_CSV_COLUMNS:
                assert col in fieldnames, f"Missing column '{col}' in subgroup report CSV"

        # Step 6: Verify domain coverage
        logger.info("Step 6: Verifying domain coverage...")
        report_domains = set(record['domain'] for record in subgroup_data)
        for domain in domains:
            assert domain in report_domains, f"Domain '{domain}' not in report"

        logger.info("=== Full Pipeline Test PASSED ===")
        logger.info(f"  - Synthetic records: {len(synthetic_data)}")
        logger.info(f"  - Audit records: {len(audit_records)}")
        logger.info(f"  - Subgroup records: {len(subgroup_data)}")
        logger.info(f"  - Domains covered: {report_domains}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
