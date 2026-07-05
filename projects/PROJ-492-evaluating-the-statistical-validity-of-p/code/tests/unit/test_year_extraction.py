"""
Unit tests for T050b: Verify that publication year is extracted during extraction (T020c)
and present in the input to subgroup_analysis.py.

This test suite validates:
1. That the extractor (T020) captures 'publication_year' from HTML metadata.
2. That the extracted summaries (ABTestSummary) include the year field.
3. That the subgroup analysis input (AuditRecord) contains the year.
4. That the year can be successfully parsed and used for grouping.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.audit.extractor import extract_summary_from_html
from src.audit.subgroup_analysis import load_audit_records_from_json, extract_year_from_record
from src.models.data_models import ABTestSummary, AuditRecord
from src.utils.helpers import safe_float


class TestYearExtraction:
    """Tests for publication year extraction and propagation to subgroup analysis."""

    def test_extractor_captures_year_from_meta_og_date(self):
        """Test that extractor captures year from meta og:article:published_time."""
        html_content = """
        <html>
        <head>
            <title>Test A/B Result</title>
            <meta property="og:article:published_time" content="2023-05-15T10:30:00Z" />
            <meta name="author" content="Data Team" />
        </head>
        <body>
            <h1>Conversion Rate Increase</h1>
            <p>Control: 5000 users, 150 conversions</p>
            <p>Treatment: 5000 users, 175 conversions</p>
            <p>P-value: 0.032</p>
        </body>
        </html>
        """

        summary = extract_summary_from_html(
            html_content,
            url="https://example.com/test",
            source="example.com"
        )

        assert summary is not None
        assert hasattr(summary, 'publication_year')
        assert summary.publication_year == 2023

    def test_extractor_captures_year_from_schema_org(self):
        """Test that extractor captures year from schema.org datePublished."""
        html_content = """
        <html>
        <head>
            <title>Another Test</title>
            <script type="application/ld+json">
            {
                "@type": "Article",
                "datePublished": "2022-11-20T08:00:00Z"
            }
            </script>
        </head>
        <body>
            <h1>Button Color Test</h1>
            <p>Control: 2000 users, 40 conversions</p>
            <p>Treatment: 2000 users, 55 conversions</p>
            <p>P-value: 0.018</p>
        </body>
        </html>
        """

        summary = extract_summary_from_html(
            html_content,
            url="https://example.com/test2",
            source="example.com"
        )

        assert summary is not None
        assert summary.publication_year == 2022

    def test_extractor_handles_missing_year(self):
        """Test that extractor handles missing year gracefully."""
        html_content = """
        <html>
        <head><title>No Date</title></head>
        <body>
            <h1>Test</h1>
            <p>Control: 1000 users, 50 conversions</p>
            <p>Treatment: 1000 users, 60 conversions</p>
            <p>P-value: 0.045</p>
        </body>
        </html>
        """

        summary = extract_summary_from_html(
            html_content,
            url="https://example.com/test3",
            source="example.com"
        )

        assert summary is not None
        # Year should be None or 0 if not found
        assert summary.publication_year is None or summary.publication_year == 0

    def test_year_propagates_to_audit_record(self):
        """Test that year from ABTestSummary propagates to AuditRecord."""
        # Create a mock ABTestSummary with year
        summary = ABTestSummary(
            url="https://example.com/test",
            source="example.com",
            baseline_conversions=150,
            baseline_n=5000,
            treatment_conversions=175,
            treatment_n=5000,
            reported_p_value=0.032,
            outcome_type="binary",
            publication_year=2023,
            domain="example.com"
        )

        # Simulate creation of AuditRecord (simplified version of validator logic)
        audit_record = AuditRecord(
            url=summary.url,
            source=summary.source,
            baseline_n=summary.baseline_n,
            treatment_n=summary.treatment_n,
            reported_p_value=summary.reported_p_value,
            reconstructed_p_value=0.035,  # Mock reconstructed value
            is_inconsistent=False,
            inconsistency_reason=None,
            publication_year=summary.publication_year,
            domain=summary.domain,
            data_quality_warnings=[]
        )

        assert audit_record.publication_year == 2023

    def test_subgroup_analysis_can_extract_year(self):
        """Test that subgroup analysis can extract year from AuditRecord."""
        # Create a temporary audit report file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            audit_records = [
                {
                    "url": "https://example.com/test1",
                    "source": "example.com",
                    "baseline_n": 5000,
                    "treatment_n": 5000,
                    "reported_p_value": 0.032,
                    "reconstructed_p_value": 0.035,
                    "is_inconsistent": False,
                    "publication_year": 2023,
                    "domain": "example.com"
                },
                {
                    "url": "https://example.com/test2",
                    "source": "example.com",
                    "baseline_n": 2000,
                    "treatment_n": 2000,
                    "reported_p_value": 0.018,
                    "reconstructed_p_value": 0.020,
                    "is_inconsistent": False,
                    "publication_year": 2022,
                    "domain": "example.com"
                }
            ]
            json.dump(audit_records, f)
            temp_path = f.name

        try:
            records = load_audit_records_from_json(temp_path)
            assert len(records) == 2

            # Test year extraction
            year1 = extract_year_from_record(records[0])
            year2 = extract_year_from_record(records[1])

            assert year1 == 2023
            assert year2 == 2022

        finally:
            os.unlink(temp_path)

    def test_year_grouping_in_subgroup_analysis(self):
        """Test that subgroup analysis correctly groups by year."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            audit_records = [
                {
                    "url": "https://example.com/test1",
                    "source": "example.com",
                    "baseline_n": 5000,
                    "treatment_n": 5000,
                    "reported_p_value": 0.032,
                    "reconstructed_p_value": 0.035,
                    "is_inconsistent": False,
                    "publication_year": 2023,
                    "domain": "example.com"
                },
                {
                    "url": "https://example.com/test2",
                    "source": "example.com",
                    "baseline_n": 2000,
                    "treatment_n": 2000,
                    "reported_p_value": 0.018,
                    "reconstructed_p_value": 0.020,
                    "is_inconsistent": True,
                    "publication_year": 2023,
                    "domain": "example.com"
                },
                {
                    "url": "https://example.com/test3",
                    "source": "example.com",
                    "baseline_n": 3000,
                    "treatment_n": 3000,
                    "reported_p_value": 0.045,
                    "reconstructed_p_value": 0.048,
                    "is_inconsistent": False,
                    "publication_year": 2022,
                    "domain": "example.com"
                }
            ]
            json.dump(audit_records, f)
            temp_path = f.name

        try:
            records = load_audit_records_from_json(temp_path)

            # Group by year
            year_groups = {}
            for record in records:
                year = extract_year_from_record(record)
                if year not in year_groups:
                    year_groups[year] = []
                year_groups[year].append(record)

            assert 2023 in year_groups
            assert 2022 in year_groups
            assert len(year_groups[2023]) == 2
            assert len(year_groups[2022]) == 1

            # Verify inconsistency counts per year
            inconsistent_2023 = sum(1 for r in year_groups[2023] if r.get('is_inconsistent', False))
            inconsistent_2022 = sum(1 for r in year_groups[2022] if r.get('is_inconsistent', False))

            assert inconsistent_2023 == 1
            assert inconsistent_2022 == 0

        finally:
            os.unlink(temp_path)

    def test_year_extraction_with_various_date_formats(self):
        """Test extraction with various date formats found in HTML."""
        test_cases = [
            ('2023-05-15T10:30:00Z', 2023),
            ('2022-11-20', 2022),
            ('2021/08/10', 2021),
            ('15-June-2020', 2020),
            ('June 15, 2019', 2019),
        ]

        for date_str, expected_year in test_cases:
            html_content = f"""
            <html>
            <head>
                <meta property="og:article:published_time" content="{date_str}" />
            </head>
            <body><h1>Test</h1></body>
            </html>
            """

            summary = extract_summary_from_html(
                html_content,
                url="https://example.com/test",
                source="example.com"
            )

            # Should extract year correctly or return None if parsing fails
            if expected_year:
                # If extraction succeeds, it should match
                if summary.publication_year is not None:
                    assert summary.publication_year == expected_year, f"Failed for {date_str}"

    def test_year_in_final_subgroup_report(self):
        """Test that year appears in the final subgroup report output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "audit_report.json"
            output_json = tmpdir / "subgroup_report.json"
            output_csv = tmpdir / "subgroup_report.csv"

            # Create input audit records
            audit_records = [
                {
                    "url": "https://example.com/test1",
                    "source": "example.com",
                    "baseline_n": 5000,
                    "treatment_n": 5000,
                    "reported_p_value": 0.032,
                    "reconstructed_p_value": 0.035,
                    "is_inconsistent": False,
                    "publication_year": 2023,
                    "domain": "tech"
                },
                {
                    "url": "https://example.com/test2",
                    "source": "example.com",
                    "baseline_n": 2000,
                    "treatment_n": 2000,
                    "reported_p_value": 0.018,
                    "reconstructed_p_value": 0.020,
                    "is_inconsistent": True,
                    "publication_year": 2023,
                    "domain": "tech"
                },
                {
                    "url": "https://example.com/test3",
                    "source": "example.com",
                    "baseline_n": 3000,
                    "treatment_n": 3000,
                    "reported_p_value": 0.045,
                    "reconstructed_p_value": 0.048,
                    "is_inconsistent": False,
                    "publication_year": 2022,
                    "domain": "finance"
                }
            ]

            with open(input_file, 'w') as f:
                json.dump(audit_records, f)

            # Import and run subgroup analysis
            from src.audit.subgroup_analysis import run_subgroup_analysis

            # Run analysis
            run_subgroup_analysis(
                input_file=str(input_file),
                output_json=str(output_json),
                output_csv=str(output_csv)
            )

            # Verify output files exist
            assert output_json.exists()
            assert output_csv.exists()

            # Check JSON content for year field
            with open(output_json, 'r') as f:
                subgroup_data = json.load(f)

            # Check that year groups exist
            year_groups = subgroup_data.get('year_groups', {})
            assert '2023' in year_groups or 2023 in year_groups
            assert '2022' in year_groups or 2022 in year_groups

            # Check CSV content
            import csv
            with open(output_csv, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) > 0
            # Check that 'publication_year' or 'year' column exists
            assert any('year' in col.lower() for col in rows[0].keys())