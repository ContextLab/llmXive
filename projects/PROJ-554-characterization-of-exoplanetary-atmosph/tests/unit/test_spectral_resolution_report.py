"""
Unit tests for the Spectral Resolution Reporting module (T045).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from spectral_resolution_report import load_metadata, compute_resolution_statistics, generate_report_md


class TestLoadMetadata:
    def test_load_metadata_success(self, tmp_path):
        """Test successful loading of metadata CSV."""
        csv_path = tmp_path / "metadata.csv"
        data = {
            'resolution': [100, 200, 300, 400],
            'instrument': ['HST', 'HST', 'Spitzer', 'JWST'],
            'planet_name': ['P1', 'P2', 'P3', 'P4']
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        result = load_metadata(str(csv_path))

        assert len(result) == 4
        assert 'resolution' in result.columns
        assert result['resolution'].dtype in ['int64', 'float64']

    def test_load_metadata_missing_file(self, tmp_path):
        """Test error when file does not exist."""
        with pytest.raises(FileNotFoundError):
            load_metadata(str(tmp_path / "nonexistent.csv"))

    def test_load_metadata_missing_columns(self, tmp_path):
        """Test error when required columns are missing."""
        csv_path = tmp_path / "metadata.csv"
        data = {
            'resolution': [100, 200],
            'planet_name': ['P1', 'P2']
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)

        with pytest.raises(ValueError) as excinfo:
            load_metadata(str(csv_path))

        assert "instrument" in str(excinfo.value)

    def test_load_metadata_handles_non_numeric(self, tmp_path):
        """Test that non-numeric resolution values are coerced to NaN and dropped."""
        csv_path = tmp_path / "metadata.csv"
        data = {
            'resolution': [100, 'N/A', 300],
            'instrument': ['HST', 'HST', 'Spitzer'],
            'planet_name': ['P1', 'P2', 'P3']
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)

        result = load_metadata(str(csv_path))

        assert len(result) == 2
        assert result['resolution'].tolist() == [100.0, 300.0]


class TestComputeResolutionStatistics:
    def test_compute_statistics_basic(self):
        """Test basic statistics computation."""
        data = {
            'resolution': [100, 200, 300, 400, 500],
            'instrument': ['A', 'A', 'B', 'B', 'B']
        }
        df = pd.DataFrame(data)

        stats = compute_resolution_statistics(df)

        assert stats['median_R'] == 300.0
        assert stats['min_R'] == 100.0
        assert stats['max_R'] == 500.0
        assert 'instrument_breakdown' in stats
        assert 'A' in stats['instrument_breakdown']
        assert 'B' in stats['instrument_breakdown']

    def test_compute_statistics_single_instrument(self):
        """Test with a single instrument."""
        data = {
            'resolution': [100, 200, 300],
            'instrument': ['HST', 'HST', 'HST']
        }
        df = pd.DataFrame(data)

        stats = compute_resolution_statistics(df)

        assert len(stats['instrument_breakdown']) == 1
        assert stats['instrument_breakdown']['HST']['count'] == 3


class TestGenerateReportMd:
    def test_generate_report_creates_file(self, tmp_path):
        """Test that the report file is created and contains expected content."""
        stats = {
            'median_R': 250.0,
            'min_R': 100.0,
            'max_R': 500.0,
            'instrument_breakdown': {
                'HST': {'count': 10, 'median': 200.0, 'min': 100.0, 'max': 300.0},
                'JWST': {'count': 5, 'median': 300.0, 'min': 250.0, 'max': 500.0}
            }
        }

        output_path = tmp_path / "report.md"
        generate_report_md(stats, str(output_path))

        assert output_path.exists()

        content = output_path.read_text()
        assert "Spectral Resolution Report" in content
        assert "250.00" in content
        assert "100.00" in content
        assert "500.00" in content
        assert "HST" in content
        assert "JWST" in content

    def test_generate_report_creates_directories(self, tmp_path):
        """Test that missing directories are created."""
        stats = {
            'median_R': 100.0,
            'min_R': 50.0,
            'max_R': 200.0,
            'instrument_breakdown': {}
        }

        deep_path = tmp_path / "results" / "plots" / "report.md"
        generate_report_md(stats, str(deep_path))

        assert deep_path.exists()