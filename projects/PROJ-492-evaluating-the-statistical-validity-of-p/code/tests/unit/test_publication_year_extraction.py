"""
Unit tests for T050b: Verify publication year extraction.

This test suite verifies that:
1. The publication year is extracted during the extraction phase (T020c).
2. The extracted year is present in the audit records passed to subgroup_analysis.
"""
import json
import os
import sys
from pathlib import Path
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from code.src.audit.extractor import extract_summary_from_html
from code.src.audit.subgroup_analysis import extract_year_from_record, load_audit_records_from_json
from code.src.audit.validator import validate_summary
from code.src.models.data_models import ABTestSummary, AuditRecord


def test_year_extraction_from_html():
    """
    Verify that publication year is extracted from HTML content.
    This simulates the extraction phase (T020c) where metadata is pulled.
    """
    # Create a mock HTML snippet containing a publication year
    mock_html = """
    <html>
    <head>
        <title>Test A/B Result</title>
        <meta name="pub-date" content="2023-05-15">
    </head>
    <body>
        <h1>A/B Test Summary</h1>
        <p>Published on: 2023-05-15</p>
        <div class="metrics">
            <span class="baseline-rate">0.05</span>
            <span class="variant-rate">0.07</span>
            <span class="p-value">0.03</span>
            <span class="sample-size">1000</span>
        </div>
    </body>
    </html>
    """
    
    # Extract summary
    summary = extract_summary_from_html(mock_html, "https://example.com/test")
    
    # Assert that a year was extracted (either from meta tag or parsed from date)
    assert summary is not None
    assert hasattr(summary, 'publication_year')
    # The extractor should parse "2023-05-15" to year 2023
    assert summary.publication_year == 2023, f"Expected year 2023, got {summary.publication_year}"


def test_year_present_in_audit_record():
    """
    Verify that the extracted year is preserved in the AuditRecord
    passed to subgroup analysis.
    """
    # Create a valid ABTestSummary with a known year
    summary_data = {
        "url": "https://example.com/test",
        "domain": "example.com",
        "baseline_rate": 0.05,
        "variant_rate": 0.07,
        "p_value": 0.03,
        "sample_size": 1000,
        "publication_year": 2023,
        "outcome_type": "binary"
    }
    
    summary = ABTestSummary(**summary_data)
    
    # Validate and create audit record (simulating T025)
    audit_record = validate_summary(summary)
    
    # Assert the year is present in the audit record
    assert audit_record is not None
    assert hasattr(audit_record, 'publication_year')
    assert audit_record.publication_year == 2023


def test_subgroup_analysis_can_extract_year():
    """
    Verify that subgroup_analysis.py can successfully extract the year
    from the audit records it receives.
    """
    # Create a temporary audit report with year data
    temp_dir = Path(__file__).parent / "temp_test_data"
    temp_dir.mkdir(exist_ok=True)
    temp_file = temp_dir / "test_audit_report.json"
    
    audit_records = [
        {
            "url": "https://example.com/1",
            "domain": "example.com",
            "is_inconsistent": False,
            "publication_year": 2022,
            "data_quality_warning": None
        },
        {
            "url": "https://example.com/2",
            "domain": "example.com",
            "is_inconsistent": True,
            "publication_year": 2023,
            "data_quality_warning": None
        },
        {
            "url": "https://example.com/3",
            "domain": "example.com",
            "is_inconsistent": False,
            "publication_year": 2024,
            "data_quality_warning": None
        }
    ]
    
    with open(temp_file, 'w') as f:
        json.dump(audit_records, f)
    
    try:
        # Load records as subgroup_analysis would
        records = load_audit_records_from_json(temp_file)
        
        # Verify we can extract years
        years = [extract_year_from_record(r) for r in records]
        
        assert len(years) == 3
        assert 2022 in years
        assert 2023 in years
        assert 2024 in years
        
    finally:
        # Cleanup
        if temp_file.exists():
            temp_file.unlink()
        if temp_dir.exists() and not any(temp_dir.iterdir()):
            temp_dir.rmdir()


def test_year_extraction_handles_missing_year():
    """
    Verify that the system handles cases where year might be missing
    (graceful degradation).
    """
    # Create a summary without year
    summary_data = {
        "url": "https://example.com/no-year",
        "domain": "example.com",
        "baseline_rate": 0.05,
        "variant_rate": 0.07,
        "p_value": 0.03,
        "sample_size": 1000,
        "publication_year": None,  # Explicitly None
        "outcome_type": "binary"
    }
    
    summary = ABTestSummary(**summary_data)
    audit_record = validate_summary(summary)
    
    # The extractor should handle missing year (either None or a default)
    assert audit_record is not None
    # Verify the field exists even if None
    assert hasattr(audit_record, 'publication_year')
    assert audit_record.publication_year is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
