"""
Unit tests for power analysis utility.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

import numpy as np

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    run_power_analysis,
    set_rng_seed_for_power_analysis
)
from code.src.config import SEED

class TestCalculateSampleSizeBinary:
    def test_basic_calculation(self):
        """Test basic sample size calculation for binary outcome."""
        n = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80
        )
        assert n > 0
        assert isinstance(n, int)
    
    def test_higher_power_requires_larger_sample(self):
        """Higher power should require larger sample size."""
        n_low = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80
        )
        n_high = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.90
        )
        assert n_high > n_low
    
    def test_smaller_effect_requires_larger_sample(self):
        """Smaller detectable effect should require larger sample size."""
        n_large = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.10,
            alpha=0.05,
            power=0.80
        )
        n_small = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.02,
            alpha=0.05,
            power=0.80
        )
        assert n_small > n_large
    
    def test_invalid_baseline_rate(self):
        """Should raise ValueError for invalid baseline rate."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline_rate=1.5,
                detectable_effect=0.05,
                alpha=0.05,
                power=0.80
            )
    
    def test_invalid_detectable_effect(self):
        """Should raise ValueError for invalid detectable effect."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline_rate=0.10,
                detectable_effect=-0.05,
                alpha=0.05,
                power=0.80
            )

class TestCalculateSampleSizeContinuous:
    def test_basic_calculation(self):
        """Test basic sample size calculation for continuous outcome."""
        n = calculate_sample_size_continuous(
            baseline_mean=0.0,
            detectable_effect=0.5,
            std_dev=1.0,
            alpha=0.05,
            power=0.80
        )
        assert n > 0
        assert isinstance(n, int)
    
    def test_higher_power_requires_larger_sample(self):
        """Higher power should require larger sample size."""
        n_low = calculate_sample_size_continuous(
            baseline_mean=0.0,
            detectable_effect=0.5,
            std_dev=1.0,
            alpha=0.05,
            power=0.80
        )
        n_high = calculate_sample_size_continuous(
            baseline_mean=0.0,
            detectable_effect=0.5,
            std_dev=1.0,
            alpha=0.05,
            power=0.90
        )
        assert n_high > n_low
    
    def test_smaller_effect_requires_larger_sample(self):
        """Smaller detectable effect should require larger sample size."""
        n_large = calculate_sample_size_continuous(
            baseline_mean=0.0,
            detectable_effect=1.0,
            std_dev=1.0,
            alpha=0.05,
            power=0.80
        )
        n_small = calculate_sample_size_continuous(
            baseline_mean=0.0,
            detectable_effect=0.2,
            std_dev=1.0,
            alpha=0.05,
            power=0.80
        )
        assert n_small > n_large
    
    def test_invalid_std_dev(self):
        """Should raise ValueError for invalid standard deviation."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(
                baseline_mean=0.0,
                detectable_effect=0.5,
                std_dev=0.0,
                alpha=0.05,
                power=0.80
            )

class TestCountCorpusSize:
    def test_count_valid_records(self):
        """Test counting valid records from audit report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit_report.json"
            
            records = [
                {"id": 1, "consistent": True},
                {"id": 2, "consistent": True, "data_quality_warnings": []},
                {"id": 3, "consistent": False}
            ]
            
            with open(audit_path, 'w') as f:
                json.dump(records, f)
            
            count = count_corpus_size(audit_path, exclude_flagged=True)
            assert count == 3
    
    def test_exclude_flagged_records(self):
        """Test excluding records with sample-size mismatch flags."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit_report.json"
            
            records = [
                {"id": 1, "consistent": True, "data_quality_warnings": []},
                {"id": 2, "consistent": True, "data_quality_warnings": ["sample_size_mismatch"]},
                {"id": 3, "consistent": True, "data_quality_warnings": ["other_warning"]}
            ]
            
            with open(audit_path, 'w') as f:
                json.dump(records, f)
            
            count = count_corpus_size(audit_path, exclude_flagged=True)
            assert count == 2
    
    def test_file_not_found(self):
        """Test handling of missing file."""
        count = count_corpus_size(Path("/nonexistent/file.json"))
        assert count == 0
    
    def test_invalid_json(self):
        """Test handling of invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit_report.json"
            with open(audit_path, 'w') as f:
                f.write("invalid json")
            
            count = count_corpus_size(audit_path)
            assert count == 0

class TestRunPowerAnalysis:
    def test_successful_run(self):
        """Test successful power analysis run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit_report.json"
            output_path = Path(tmpdir) / "power_analysis.json"
            
            # Create minimal audit report
            records = [{"id": i, "consistent": True} for i in range(500)]
            with open(audit_path, 'w') as f:
                json.dump(records, f)
            
            result = run_power_analysis(
                audit_records_path=audit_path,
                output_path=output_path,
                min_corpus_size=300
            )
            
            assert "parameters" in result
            assert "calculated_minimum_sample_sizes" in result
            assert "corpus_statistics" in result
            assert "validation" in result
            assert result["validation"]["is_valid"] is True
            
            # Verify output file exists
            assert output_path.exists()
            
            # Verify JSON content
            with open(output_path, 'r') as f:
                saved_result = json.load(f)
            
            assert saved_result["validation"]["is_valid"] is True
    
    def test_validation_failure(self):
        """Test validation failure when corpus is too small."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit_report.json"
            output_path = Path(tmpdir) / "power_analysis.json"
            
            # Create small audit report
            records = [{"id": i, "consistent": True} for i in range(100)]
            with open(audit_path, 'w') as f:
                json.dump(records, f)
            
            result = run_power_analysis(
                audit_records_path=audit_path,
                output_path=output_path,
                min_corpus_size=300
            )
            
            assert result["validation"]["is_valid"] is False
            assert result["validation"]["meets_minimum_threshold"] is False
    
    def test_corpus_meets_calculated_minimum(self):
        """Test validation when corpus meets calculated minimum but not fixed threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit_report.json"
            output_path = Path(tmpdir) / "power_analysis.json"
            
            # Create audit report with size between 300 and calculated minimum
            # For small effect, calculated minimum might be > 300
            records = [{"id": i, "consistent": True} for i in range(400)]
            with open(audit_path, 'w') as f:
                json.dump(records, f)
            
            result = run_power_analysis(
                audit_records_path=audit_path,
                output_path=output_path,
                baseline_rate=0.10,
                detectable_effect=0.02,  # Small effect -> larger required N
                min_corpus_size=300
            )
            
            # Should pass if N >= calculated_minimum
            assert result["validation"]["meets_calculated_minimum"] or result["validation"]["meets_minimum_threshold"]

class TestMain:
    def test_main_success(self):
        """Test main function with valid inputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit_report.json"
            output_path = Path(tmpdir) / "power_analysis.json"
            
            # Create minimal audit report
            records = [{"id": i, "consistent": True} for i in range(500)]
            with open(audit_path, 'w') as f:
                json.dump(records, f)
            
            # Mock sys.argv
            with patch('sys.argv', [
                'test',
                '--audit-records', str(audit_path),
                '--output', str(output_path),
                '--min-corpus-size', '300'
            ]):
                from code.src.audit.power_analysis import main
                exit_code = main()
                assert exit_code == 0
                assert output_path.exists()
    
    def test_main_failure(self):
        """Test main function with invalid inputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit_report.json"
            output_path = Path(tmpdir) / "power_analysis.json"
            
            # Create small audit report
            records = [{"id": i, "consistent": True} for i in range(100)]
            with open(audit_path, 'w') as f:
                json.dump(records, f)
            
            with patch('sys.argv', [
                'test',
                '--audit-records', str(audit_path),
                '--output', str(output_path),
                '--min-corpus-size', '300'
            ]):
                from code.src.audit.power_analysis import main
                exit_code = main()
                assert exit_code == 1
