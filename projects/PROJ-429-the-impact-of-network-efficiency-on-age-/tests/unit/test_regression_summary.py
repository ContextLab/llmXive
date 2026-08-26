"""
Unit tests for T032: regression_summary.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from stats.regression_summary import generate_summary, load_power_analysis, load_regression_results


class TestLoadRegressionResults:
    def test_load_existing_file(self):
        """Test loading an existing regression results file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'test': 'data'}, f)
            temp_path = Path(f.name)
        
        try:
            result = load_regression_results(temp_path)
            assert result == {'test': 'data'}
        finally:
            temp_path.unlink()

    def test_load_missing_file(self):
        """Test loading a missing regression results file."""
        result = load_regression_results(Path('/nonexistent/path.json'))
        assert result == {}

    def test_load_invalid_json(self):
        """Test loading an invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('invalid json')
            temp_path = Path(f.name)
        
        try:
            result = load_regression_results(temp_path)
            assert result == {}
        finally:
            temp_path.unlink()


class TestLoadPowerAnalysis:
    def test_load_existing_file(self):
        """Test loading an existing power analysis file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'power_for_r03': 0.85, 'is_sufficient': True}, f)
            temp_path = Path(f.name)
        
        try:
            result = load_power_analysis(temp_path)
            assert result['power_for_r03'] == 0.85
            assert result['is_sufficient'] is True
        finally:
            temp_path.unlink()

    def test_load_missing_file(self):
        """Test loading a missing power analysis file."""
        result = load_power_analysis(Path('/nonexistent/path.json'))
        assert result == {}

    def test_load_invalid_json(self):
        """Test loading an invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('invalid json')
            temp_path = Path(f.name)
        
        try:
            result = load_power_analysis(temp_path)
            assert result == {}
        finally:
            temp_path.unlink()


class TestGenerateSummary:
    def test_sufficient_power_no_warnings(self):
        """Test summary generation with sufficient power (no warnings)."""
        regression_results = {'coef': 0.5}
        power_analysis = {'is_sufficient': True, 'power_for_r03': 0.85}
        
        summary = generate_summary(regression_results, power_analysis)
        
        assert 'warnings' in summary
        assert len(summary['warnings']) == 0
        assert summary['power_analysis_status'] is True
        assert summary['regression_results_available'] is True

    def test_insufficient_power_warning(self):
        """Test summary generation with insufficient power (warning added)."""
        regression_results = {'coef': 0.5}
        power_analysis = {'is_sufficient': False, 'power_for_r03': 0.45}
        
        summary = generate_summary(regression_results, power_analysis)
        
        assert 'warnings' in summary
        assert 'Low Power for Cognitive Analysis' in summary['warnings']
        assert summary['power_analysis_status'] is False
        assert summary['regression_results_available'] is True

    def test_missing_power_analysis(self):
        """Test summary generation with missing power analysis."""
        regression_results = {'coef': 0.5}
        power_analysis = {}
        
        summary = generate_summary(regression_results, power_analysis)
        
        assert 'warnings' in summary
        assert len(summary['warnings']) == 0
        assert summary['power_analysis_status'] == 'unknown'
        assert summary['regression_results_available'] is True

    def test_missing_regression_results(self):
        """Test summary generation with missing regression results."""
        regression_results = {}
        power_analysis = {'is_sufficient': True}
        
        summary = generate_summary(regression_results, power_analysis)
        
        assert 'warnings' in summary
        assert 'No regression results available' in summary['warnings']
        assert summary['regression_results_available'] is False

    def test_both_missing(self):
        """Test summary generation with both missing."""
        regression_results = {}
        power_analysis = {}
        
        summary = generate_summary(regression_results, power_analysis)
        
        assert 'warnings' in summary
        assert 'No regression results available' in summary['warnings']
        assert summary['regression_results_available'] is False
        assert summary['power_analysis_status'] == 'unknown'