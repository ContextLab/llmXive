"""
Unit tests for citation validation functionality.
Tests the Reference-Validator Agent (Constitution Principle II).
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validate.citations import (
    CitationValidationResult,
    CitationValidationReport,
    verify_url_accessible,
    verify_checksum,
    verify_required_variables,
    validate_citation,
    validate_citations,
    generate_validation_report,
)


class TestCitationValidationResult(TestCase):
    """Tests for CitationValidationResult dataclass."""

    def test_result_creation(self):
        """Test creating a validation result."""
        result = CitationValidationResult(
            citation_id="test-001",
            url="https://example.com/data.csv",
            url_accessible=True,
            checksum_verified=True,
            expected_checksum="abc123",
            actual_checksum="abc123",
            variables_present=True,
            missing_variables=[],
            validation_passed=True,
            error_message=None,
            verified_at="2024-01-01T00:00:00",
        )

        self.assertEqual(result.citation_id, "test-001")
        self.assertTrue(result.validation_passed)
        self.assertIsNone(result.error_message)

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = CitationValidationResult(
            citation_id="test-001",
            url="https://example.com/data.csv",
            url_accessible=True,
            checksum_verified=True,
            expected_checksum="abc123",
            actual_checksum="abc123",
            variables_present=True,
            missing_variables=[],
            validation_passed=True,
            error_message=None,
            verified_at="2024-01-01T00:00:00",
        )

        result_dict = result.to_dict()
        self.assertIsInstance(result_dict, dict)
        self.assertIn("citation_id", result_dict)
        self.assertIn("validation_passed", result_dict)


class TestCitationValidationReport(TestCase):
    """Tests for CitationValidationReport dataclass."""

    def test_report_creation(self):
        """Test creating a validation report."""
        result = CitationValidationResult(
            citation_id="test-001",
            url="https://example.com/data.csv",
            url_accessible=True,
            checksum_verified=True,
            expected_checksum="abc123",
            actual_checksum="abc123",
            variables_present=True,
            missing_variables=[],
            validation_passed=True,
            error_message=None,
            verified_at="2024-01-01T00:00:00",
        )

        report = CitationValidationReport(
            total_citations=1,
            passed_citations=1,
            failed_citations=0,
            all_valid=True,
            verification_timestamp="2024-01-01T00:00:00",
            results=[result],
            summary={"test": "summary"},
        )

        self.assertTrue(report.all_valid)
        self.assertEqual(report.total_citations, 1)

    def test_report_to_dict(self):
        """Test converting report to dictionary."""
        result = CitationValidationResult(
            citation_id="test-001",
            url="https://example.com/data.csv",
            url_accessible=True,
            checksum_verified=True,
            expected_checksum="abc123",
            actual_checksum="abc123",
            variables_present=True,
            missing_variables=[],
            validation_passed=True,
            error_message=None,
            verified_at="2024-01-01T00:00:00",
        )

        report = CitationValidationReport(
            total_citations=1,
            passed_citations=1,
            failed_citations=0,
            all_valid=True,
            verification_timestamp="2024-01-01T00:00:00",
            results=[result],
            summary={"test": "summary"},
        )

        report_dict = report.to_dict()
        self.assertIsInstance(report_dict, dict)
        self.assertIn("all_valid", report_dict)
        self.assertIn("results", report_dict)


class TestVerifyUrlAccessible(TestCase):
    """Tests for URL accessibility verification."""

    def test_invalid_scheme(self):
        """Test that invalid URL schemes are rejected."""
        accessible, error = verify_url_accessible("ftp://example.com/data.csv")
        self.assertFalse(accessible)
        self.assertIn("Invalid URL scheme", error)

    def test_http_error_handling(self):
        """Test that HTTP errors are properly caught."""
        accessible, error = verify_url_accessible(
            "https://httpstat.us/404", timeout=5
        )
        # This may or may not be accessible depending on service availability
        # We just test that the function doesn't crash
        self.assertIsInstance(accessible, bool)
        self.assertIsInstance(error, (str, type(None)))


class TestVerifyChecksum(TestCase):
    """Tests for checksum verification."""

    def test_checksum_verification(self):
        """Test checksum verification with a real file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            temp_path = f.name

        try:
            # Calculate expected checksum
            import hashlib
            with open(temp_path, "rb") as f:
                expected = hashlib.sha256(f.read()).hexdigest()

            # Verify
            matches, actual = verify_checksum(temp_path, expected)
            self.assertTrue(matches)
            self.assertEqual(actual, expected)
        finally:
            os.unlink(temp_path)

    def test_checksum_mismatch(self):
        """Test that checksum mismatch is detected."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            temp_path = f.name

        try:
            matches, actual = verify_checksum(temp_path, "wrong_checksum")
            self.assertFalse(matches)
            self.assertNotEqual(actual, "wrong_checksum")
        finally:
            os.unlink(temp_path)


class TestVerifyRequiredVariables(TestCase):
    """Tests for required variable verification."""

    def test_all_variables_present(self):
        """Test verification when all variables are present."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            f.write("tool_usage,task_time,defect_rate,experience_years,task_complexity,project_type,team_size\n")
            f.write("1,10,0.1,3,medium,web,5\n")
            temp_path = f.name

        try:
            all_present, missing = verify_required_variables(
                temp_path,
                [
                    "tool_usage",
                    "task_time",
                    "defect_rate",
                    "experience_years",
                    "task_complexity",
                    "project_type",
                    "team_size",
                ],
            )
            self.assertTrue(all_present)
            self.assertEqual(missing, [])
        finally:
            os.unlink(temp_path)

    def test_missing_variables(self):
        """Test verification when some variables are missing."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            f.write("tool_usage,task_time\n")
            f.write("1,10\n")
            temp_path = f.name

        try:
            all_present, missing = verify_required_variables(
                temp_path,
                [
                    "tool_usage",
                    "task_time",
                    "defect_rate",
                    "experience_years",
                ],
            )
            self.assertFalse(all_present)
            self.assertIn("defect_rate", missing)
            self.assertIn("experience_years", missing)
        finally:
            os.unlink(temp_path)


class TestValidateCitation(TestCase):
    """Tests for individual citation validation."""

    def test_valid_citation_structure(self):
        """Test that a valid citation produces correct structure."""
        citation = {
            "id": "test-citation-001",
            "url": "https://example.com/data.csv",
            "expected_checksum": None,
            "description": "Test citation",
        }

        # Note: This will fail URL check since example.com doesn't serve CSV
        # We test that the function returns a proper result structure
        result = validate_citation(citation, download_dir=None)

        self.assertIsInstance(result, CitationValidationResult)
        self.assertEqual(result.citation_id, "test-citation-001")
        self.assertIn("url", result.__dict__)
        self.assertIn("validation_passed", result.__dict__)


class TestGenerateValidationReport(TestCase):
    """Tests for report generation."""

    def test_report_generation(self):
        """Test that reports are generated correctly."""
        result = CitationValidationResult(
            citation_id="test-001",
            url="https://example.com/data.csv",
            url_accessible=True,
            checksum_verified=True,
            expected_checksum="abc123",
            actual_checksum="abc123",
            variables_present=True,
            missing_variables=[],
            validation_passed=True,
            error_message=None,
            verified_at="2024-01-01T00:00:00",
        )

        report = CitationValidationReport(
            total_citations=1,
            passed_citations=1,
            failed_citations=0,
            all_valid=True,
            verification_timestamp="2024-01-01T00:00:00",
            results=[result],
            summary={"test": "summary"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_report.json")
            generated_path = generate_validation_report(report, output_path)

            self.assertEqual(generated_path, output_path)
            self.assertTrue(os.path.exists(output_path))

            with open(output_path, "r") as f:
                loaded = json.load(f)

            self.assertEqual(loaded["total_citations"], 1)
            self.assertTrue(loaded["all_valid"])
