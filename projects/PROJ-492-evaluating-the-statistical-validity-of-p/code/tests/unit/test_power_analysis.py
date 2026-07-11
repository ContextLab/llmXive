"""
Unit tests for power analysis utility.

Tests cover:
- Sample size calculations for binary and continuous outcomes
- Corpus size counting
- Compliance validation against claim c_21f3e400
- JSON output generation
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

import numpy as np
from scipy import stats

# Import the module under test
from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    write_power_analysis_result,
    run_power_analysis,
    MIN_CORPUS_SIZE_THRESHOLD
)


class TestCalculateSampleSizeBinary:
    """Tests for binary outcome sample size calculation."""

    def test_basic_calculation(self):
        """Test basic sample size calculation with standard parameters."""
        result = calculate_sample_size_binary(
            p1=0.10,
            p2=0.15,
            alpha=0.05,
            power=0.80
        )
        
        assert result['baseline_proportion'] == 0.10
        assert result['treatment_proportion'] == 0.15
        assert result['effect_size'] == 0.05
        assert result['alpha'] == 0.05
        assert result['power'] == 0.80
        assert result['sample_size_control'] > 0
        assert result['sample_size_treatment'] > 0
        assert result['total_sample_size'] > 0
        assert result['calculation_method'] == 'two_proportion_z_test'

    def test_effect_size_calculation(self):
        """Verify effect size is correctly calculated as absolute difference."""
        result = calculate_sample_size_binary(
            p1=0.20,
            p2=0.25,
            alpha=0.05,
            power=0.80
        )
        
        assert result['effect_size'] == 0.05

    def test_invalid_proportions_equal(self):
        """Test that equal proportions raise an error."""
        with pytest.raises(ValueError, match="must differ"):
            calculate_sample_size_binary(
                p1=0.10,
                p2=0.10,
                alpha=0.05,
                power=0.80
            )

    def test_invalid_proportions_out_of_range(self):
        """Test that proportions outside (0, 1) raise an error."""
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            calculate_sample_size_binary(
                p1=0.0,
                p2=0.15,
                alpha=0.05,
                power=0.80
            )

        with pytest.raises(ValueError, match="must be between 0 and 1"):
            calculate_sample_size_binary(
                p1=1.0,
                p2=0.15,
                alpha=0.05,
                power=0.80
            )

    def test_custom_ratio(self):
        """Test sample size calculation with custom treatment:control ratio."""
        result = calculate_sample_size_binary(
            p1=0.10,
            p2=0.15,
            alpha=0.05,
            power=0.80,
            ratio=2.0
        )
        
        assert result['sample_size_treatment'] == result['sample_size_control'] * 2

    def test_higher_power_requires_larger_sample(self):
        """Verify that higher power requires larger sample size."""
        result_80 = calculate_sample_size_binary(
            p1=0.10,
            p2=0.15,
            alpha=0.05,
            power=0.80
        )
        
        result_90 = calculate_sample_size_binary(
            p1=0.10,
            p2=0.15,
            alpha=0.05,
            power=0.90
        )
        
        assert result_90['total_sample_size'] > result_80['total_sample_size']


class TestCalculateSampleSizeContinuous:
    """Tests for continuous outcome sample size calculation."""

    def test_basic_calculation(self):
        """Test basic sample size calculation for continuous outcomes."""
        result = calculate_sample_size_continuous(
            mu1=100.0,
            mu2=105.0,
            sigma=15.0,
            alpha=0.05,
            power=0.80
        )
        
        assert result['control_mean'] == 100.0
        assert result['treatment_mean'] == 105.0
        assert result['standard_deviation'] == 15.0
        assert result['effect_size_cohen_d'] == pytest.approx(5.0 / 15.0, rel=0.01)
        assert result['sample_size_control'] > 0
        assert result['sample_size_treatment'] > 0
        assert result['calculation_method'] == 'welch_t_test_approximation'

    def test_invalid_sigma(self):
        """Test that non-positive sigma raises an error."""
        with pytest.raises(ValueError, match="must be positive"):
            calculate_sample_size_continuous(
                mu1=100.0,
                mu2=105.0,
                sigma=0.0,
                alpha=0.05,
                power=0.80
            )

        with pytest.raises(ValueError, match="must be positive"):
            calculate_sample_size_continuous(
                mu1=100.0,
                mu2=105.0,
                sigma=-5.0,
                alpha=0.05,
                power=0.80
            )

    def test_equal_means_raises_error(self):
        """Test that equal means raise an error."""
        with pytest.raises(ValueError, match="must differ"):
            calculate_sample_size_continuous(
                mu1=100.0,
                mu2=100.0,
                sigma=15.0,
                alpha=0.05,
                power=0.80
            )


class TestCountCorpusSize:
    """Tests for corpus size counting."""

    def test_count_valid_records(self):
        """Test counting valid records from a JSON file."""
        # Create temporary file with test data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"sample_size": 100, "other_field": "data1"},
                {"sample_size": 200, "other_field": "data2"},
                {"sample_size": 150, "other_field": "data3"}
            ], f)
            temp_path = Path(f.name)
        
        try:
            count, records = count_corpus_size(temp_path)
            assert count == 3
            assert len(records) == 3
        finally:
            os.unlink(temp_path)

    def test_filter_invalid_sample_sizes(self):
        """Test that records with invalid sample sizes are filtered out."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"sample_size": 100},
                {"sample_size": 0},  # Invalid
                {"sample_size": -5},  # Invalid
                {"other_field": "no_sample_size"},  # Missing
                {"sample_size": 200}
            ], f)
            temp_path = Path(f.name)
        
        try:
            count, records = count_corpus_size(temp_path)
            assert count == 2
            assert all(r['sample_size'] > 0 for r in records)
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            count_corpus_size(Path("/nonexistent/path/file.json"))

    def test_single_record_handling(self):
        """Test handling of single record (non-list) JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"sample_size": 150}, f)
            temp_path = Path(f.name)
        
        try:
            count, records = count_corpus_size(temp_path)
            assert count == 1
            assert len(records) == 1
        finally:
            os.unlink(temp_path)


class TestWritePowerAnalysisResult:
    """Tests for writing power analysis results."""

    def test_write_to_json(self):
        """Test writing results to a JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.json"
            results = {
                "test_field": "test_value",
                "number": 42,
                "nested": {"key": "value"}
            }
            
            write_power_analysis_result(results, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded == results

    def test_creates_parent_directories(self):
        """Test that parent directories are created if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "nested" / "output.json"
            results = {"test": "data"}
            
            write_power_analysis_result(results, output_path)
            
            assert output_path.exists()


class TestRunPowerAnalysis:
    """Tests for the main power analysis workflow."""

    def test_successful_analysis(self):
        """Test successful power analysis execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create mock audit report
            audit_path = tmpdir_path / "output"
            audit_path.mkdir()
            audit_report_path = audit_path / "audit_report.json"
            
            with open(audit_report_path, 'w') as f:
                json.dump([
                    {"sample_size": 3000, "domain": "tech"},
                    {"sample_size": 2500, "domain": "finance"},
                    {"sample_size": 4000, "domain": "health"}
                ], f)
            
            output_path = tmpdir_path / "output" / "power_analysis.json"
            
            results = run_power_analysis(
                audit_report_path=audit_report_path,
                output_path=output_path,
                baseline_proportion=0.10,
                detectable_effect=0.05,
                min_corpus_size_threshold=100  # Lower threshold for testing
            )
            
            # Verify output file exists
            assert output_path.exists()
            
            # Verify results structure
            assert 'parameters' in results
            assert 'corpus_analysis' in results
            assert 'sample_size_requirements' in results
            assert 'compliance' in results
            
            # Verify compliance status
            assert results['compliance']['status'] == 'PASS'
            assert results['corpus_analysis']['total_records'] == 3

    def test_compliance_failure(self):
        """Test power analysis when corpus doesn't meet requirements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create mock audit report with small corpus
            audit_path = tmpdir_path / "output"
            audit_path.mkdir()
            audit_report_path = audit_path / "audit_report.json"
            
            with open(audit_report_path, 'w') as f:
                json.dump([
                    {"sample_size": 100},
                    {"sample_size": 200}
                ], f)
            
            output_path = tmpdir_path / "output" / "power_analysis.json"
            
            results = run_power_analysis(
                audit_report_path=audit_report_path,
                output_path=output_path,
                min_corpus_size_threshold=1000  # High threshold to trigger failure
            )
            
            assert results['compliance']['status'] == 'FAIL'
            assert results['corpus_analysis']['meets_minimum_threshold'] is False

    def test_output_file_format(self):
        """Test that output JSON contains required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            audit_path = tmpdir_path / "output"
            audit_path.mkdir()
            audit_report_path = audit_path / "audit_report.json"
            
            with open(audit_report_path, 'w') as f:
                json.dump([{"sample_size": 5000}], f)
            
            output_path = tmpdir_path / "output" / "power_analysis.json"
            
            run_power_analysis(
                audit_report_path=audit_report_path,
                output_path=output_path,
                min_corpus_size_threshold=100
            )
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            # Check required numeric N field
            assert 'sample_size_requirements' in loaded
            assert 'binary_outcome' in loaded['sample_size_requirements']
            assert 'total_sample_size' in loaded['sample_size_requirements']['binary_outcome']
            
            # Check compliance section
            assert 'compliance' in loaded
            assert 'claim_c_21f3e400_satisfied' in loaded['compliance']
            assert 'minimum_corpus_size' in loaded['compliance']
            assert 'actual_corpus_size' in loaded['compliance']


class TestClaimC21F3E400Compliance:
    """Tests specifically for claim c_21f3e400 compliance."""

    def test_threshold_constant(self):
        """Verify the minimum corpus size threshold constant."""
        # The threshold should be the ceiling of 2510.17487
        assert MIN_CORPUS_SIZE_THRESHOLD == 2511

    def test_compliance_check_logic(self):
        """Test that compliance check correctly compares corpus size to threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            audit_path = tmpdir_path / "output"
            audit_path.mkdir()
            audit_report_path = audit_path / "audit_report.json"
            
            # Test with corpus exactly at threshold
            with open(audit_report_path, 'w') as f:
                json.dump([{"sample_size": 2511} for _ in range(2511)], f)
            
            output_path = tmpdir_path / "output" / "power_analysis.json"
            
            results = run_power_analysis(
                audit_report_path=audit_report_path,
                output_path=output_path,
                min_corpus_size_threshold=MIN_CORPUS_SIZE_THRESHOLD
            )
            
            assert results['compliance']['claim_c_21f3e400_satisfied'] is True
            assert results['compliance']['status'] == 'PASS'

    def test_compliance_below_threshold(self):
        """Test compliance when corpus is below threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            audit_path = tmpdir_path / "output"
            audit_path.mkdir()
            audit_report_path = audit_path / "audit_report.json"
            
            # Test with corpus below threshold
            with open(audit_report_path, 'w') as f:
                json.dump([{"sample_size": 100} for _ in range(100)], f)
            
            output_path = tmpdir_path / "output" / "power_analysis.json"
            
            results = run_power_analysis(
                audit_report_path=audit_report_path,
                output_path=output_path,
                min_corpus_size_threshold=MIN_CORPUS_SIZE_THRESHOLD
            )
            
            assert results['compliance']['claim_c_21f3e400_satisfied'] is False
            assert results['compliance']['status'] == 'FAIL'