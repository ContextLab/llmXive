"""
Tests for the report generator module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from report_generator import generate_aggregate_report, _generate_markdown_report


@pytest.fixture
def mock_coverage_records():
    """Mock coverage records for testing."""
    return [
        {
            "dataset_id": "wine",
            "sample_size": 10,
            "interval_type": "t_interval",
            "interval_lower": 0.5,
            "interval_upper": 0.8,
            "contains_mean": True
        },
        {
            "dataset_id": "wine",
            "sample_size": 10,
            "interval_type": "t_interval",
            "interval_lower": 0.4,
            "interval_upper": 0.7,
            "contains_mean": False
        },
        {
            "dataset_id": "wine",
            "sample_size": 20,
            "interval_type": "bootstrap",
            "interval_lower": 0.55,
            "interval_upper": 0.85,
            "contains_mean": True
        }
    ]


@pytest.fixture
def mock_population_means():
    """Mock population means for testing."""
    return {
        "wine": {
            "alcohol": 0.65,
            "malic_acid": 0.20
        }
    }


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_generate_markdown_report_structure(mock_coverage_records, mock_population_means, temp_output_dir):
    """Test that the markdown report is generated with correct structure."""
    # Mock the aggregation functions
    with patch('report_generator.load_coverage_records', return_value=mock_coverage_records), \
         patch('report_generator.load_population_means', return_value=mock_population_means), \
         patch('report_generator.get_output_dir', return_value=temp_output_dir), \
         patch('report_generator.get_random_seed', return_value=42):

        report_path = generate_aggregate_report(temp_output_dir)

        # Verify file exists
        assert Path(report_path).exists()

        # Read and verify content
        content = Path(report_path).read_text()

        # Check for key sections
        assert "# Aggregate Report" in content
        assert "Executive Summary" in content
        assert "Scope and Generalization" in content
        assert "Detailed Results" in content
        assert "Methodology" in content
        assert "Conclusion" in content

        # Check for real data contrast
        assert "UCI" in content
        assert "synthetic" in content.lower()
        assert "associational" in content.lower()


def test_bonferroni_correction_applied(mock_coverage_records, mock_population_means, temp_output_dir):
    """Test that Bonferroni correction is mentioned in the report."""
    with patch('report_generator.load_coverage_records', return_value=mock_coverage_records), \
         patch('report_generator.load_population_means', return_value=mock_population_means), \
         patch('report_generator.get_output_dir', return_value=temp_output_dir), \
         patch('report_generator.get_random_seed', return_value=42):

        report_path = generate_aggregate_report(temp_output_dir)
        content = Path(report_path).read_text()

        assert "Bonferroni" in content
        assert "corrected" in content.lower() or "correction" in content.lower()


def test_empty_coverage_records_raises_error():
    """Test that an error is raised when no coverage records exist."""
    with patch('report_generator.load_coverage_records', return_value=[]), \
         patch('report_generator.get_output_dir', return_value=Path("/tmp")):

        with pytest.raises(ValueError, match="No coverage records found"):
            generate_aggregate_report()


def test_report_contains_dataset_table(mock_coverage_records, mock_population_means, temp_output_dir):
    """Test that the report contains a table with dataset results."""
    with patch('report_generator.load_coverage_records', return_value=mock_coverage_records), \
         patch('report_generator.load_population_means', return_value=mock_population_means), \
         patch('report_generator.get_output_dir', return_value=temp_output_dir), \
         patch('report_generator.get_random_seed', return_value=42):

        report_path = generate_aggregate_report(temp_output_dir)
        content = Path(report_path).read_text()

        # Check for markdown table
        assert "| Dataset |" in content
        assert "wine" in content.lower()
        assert "Coverage Rate" in content
        assert "Deviation" in content


def test_json_report_saved_alongside_md(mock_coverage_records, mock_population_means, temp_output_dir):
    """Test that both JSON and MD reports are saved."""
    with patch('report_generator.load_coverage_records', return_value=mock_coverage_records), \
         patch('report_generator.load_population_means', return_value=mock_population_means), \
         patch('report_generator.get_output_dir', return_value=temp_output_dir), \
         patch('report_generator.get_random_seed', return_value=42):

        report_path = generate_aggregate_report(temp_output_dir)

        md_path = Path(report_path)
        json_path = md_path.parent / "aggregate_report.json"

        assert md_path.exists()
        assert json_path.exists()

        # Verify JSON is valid
        with open(json_path) as f:
            data = json.load(f)
            assert 'results' in data
            assert 'seed' in data
            assert 'timestamp' in data
