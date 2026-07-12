"""
Unit tests for the inconsistency validator (T025).

Tests:
- Absolute p-difference > 0.05 threshold
- Relative effect-size > 5% threshold
- Sample-size mismatch detection and data_quality_warning
- Exclusion from aggregate prevalence estimates (FR-004b)
"""
import json
import tempfile
from pathlib import Path
from datetime import datetime

import pytest
import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.audit.validator import (
    validate_single_summary,
    validate_all_summaries,
    run_validator,
    calculate_relative_difference,
    ABSOLUTE_P_THRESHOLD,
    RELATIVE_EFFECT_SIZE_THRESHOLD
)


class TestCalculateRelativeDifference:
    """Tests for the relative difference calculation helper."""
    
    def test_identical_values(self):
        assert calculate_relative_difference(0.5, 0.5) == 0.0
        assert calculate_relative_difference(100.0, 100.0) == 0.0
    
    def test_different_values(self):
        # 10% difference
        assert abs(calculate_relative_difference(10.0, 11.0) - 0.1) < 0.001
        # 50% difference
        assert abs(calculate_relative_difference(10.0, 15.0) - 0.5) < 0.001
    
    def test_zero_handling(self):
        # Both zero
        assert calculate_relative_difference(0.0, 0.0) == 0.0
        # One zero
        assert calculate_relative_difference(0.0, 1.0) == 1.0
        assert calculate_relative_difference(1.0, 0.0) == 1.0


class TestValidateSingleSummary:
    """Tests for single summary validation."""
    
    def test_consistent_p_value(self):
        """Test that small p-value differences are considered consistent."""
        summary = ABTestSummary(
            url="https://example.com/test1",
            domain="example.com",
            test_type="binary",
            reported_p_value=0.04,
            effect_size=0.15,
            n_control=1000,
            n_treatment=1000,
            baseline_conversion_rate=0.10
        )
        
        reconstructed = {
            'reconstructed_p_value': 0.042,  # 0.002 difference
            'reconstructed_effect_size': 0.15,
            'reconstructed_n_control': 1000,
            'reconstructed_n_treatment': 1000
        }
        
        record, is_consistent = validate_single_summary(summary, reconstructed)
        
        assert is_consistent is True
        assert record.status == "consistent"
        assert record.data_quality_warning is False
    
    def test_inconsistent_p_value_threshold(self):
        """Test that p-value difference > 0.05 is flagged as inconsistent."""
        summary = ABTestSummary(
            url="https://example.com/test2",
            domain="example.com",
            test_type="binary",
            reported_p_value=0.05,
            effect_size=0.15,
            n_control=1000,
            n_treatment=1000,
            baseline_conversion_rate=0.10
        )
        
        reconstructed = {
            'reconstructed_p_value': 0.12,  # 0.07 difference > 0.05
            'reconstructed_effect_size': 0.15,
            'reconstructed_n_control': 1000,
            'reconstructed_n_treatment': 1000
        }
        
        record, is_consistent = validate_single_summary(summary, reconstructed)
        
        assert is_consistent is False
        assert record.status == "inconsistent"
        assert any("Absolute p-value difference" in err for err in record.errors)
    
    def test_inconsistent_effect_size_threshold(self):
        """Test that effect size difference > 5% is flagged as inconsistent."""
        summary = ABTestSummary(
            url="https://example.com/test3",
            domain="example.com",
            test_type="continuous",
            reported_p_value=0.03,
            effect_size=0.20,
            n_control=500,
            n_treatment=500,
            baseline_conversion_rate=None
        )
        
        reconstructed = {
            'reconstructed_p_value': 0.03,
            'reconstructed_effect_size': 0.25,  # 25% relative difference > 5%
            'reconstructed_n_control': 500,
            'reconstructed_n_treatment': 500
        }
        
        record, is_consistent = validate_single_summary(summary, reconstructed)
        
        assert is_consistent is False
        assert record.status == "inconsistent"
        assert any("Relative effect size difference" in err for err in record.errors)
    
    def test_sample_size_mismatch_warning(self):
        """Test that sample size mismatches generate data_quality_warning."""
        summary = ABTestSummary(
            url="https://example.com/test4",
            domain="example.com",
            test_type="binary",
            reported_p_value=0.04,
            effect_size=0.15,
            n_control=1000,
            n_treatment=1000,
            baseline_conversion_rate=0.10
        )
        
        reconstructed = {
            'reconstructed_p_value': 0.04,
            'reconstructed_effect_size': 0.15,
            'reconstructed_n_control': 1200,  # Mismatch
            'reconstructed_n_treatment': 1200  # Mismatch
        }
        
        record, is_consistent = validate_single_summary(summary, reconstructed)
        
        assert record.data_quality_warning is True
        assert record.sample_size_mismatch is True
        assert any("Sample size mismatch" in w for w in record.warnings)
    
    def test_missing_values_handling(self):
        """Test that missing values don't cause crashes."""
        summary = ABTestSummary(
            url="https://example.com/test5",
            domain="example.com",
            test_type="binary",
            reported_p_value=None,  # Missing
            effect_size=0.15,
            n_control=1000,
            n_treatment=1000,
            baseline_conversion_rate=0.10
        )
        
        reconstructed = {
            'reconstructed_p_value': None,  # Missing
            'reconstructed_effect_size': 0.15,
            'reconstructed_n_control': 1000,
            'reconstructed_n_treatment': 1000
        }
        
        record, is_consistent = validate_single_summary(summary, reconstructed)
        
        # Should be consistent if no values to compare
        assert is_consistent is True
        assert record.status == "consistent"


class TestValidateAllSummaries:
    """Tests for batch validation."""
    
    def test_batch_validation(self):
        """Test validation of multiple summaries."""
        summaries = [
            ABTestSummary(
                url=f"https://example.com/test{i}",
                domain="example.com",
                test_type="binary",
                reported_p_value=0.04,
                effect_size=0.15,
                n_control=1000,
                n_treatment=1000,
                baseline_conversion_rate=0.10
            )
            for i in range(3)
        ]
        
        reconstructed = [
            {
                'reconstructed_p_value': 0.04,
                'reconstructed_effect_size': 0.15,
                'reconstructed_n_control': 1000,
                'reconstructed_n_treatment': 1000
            }
            for _ in range(3)
        ]
        
        records = validate_all_summaries(summaries, reconstructed)
        
        assert len(records) == 3
        assert all(r.is_consistent for r in records)
    
    def test_mismatched_counts_raises_error(self):
        """Test that mismatched counts raise an error."""
        summaries = [
            ABTestSummary(
                url="https://example.com/test1",
                domain="example.com",
                test_type="binary",
                reported_p_value=0.04,
                effect_size=0.15,
                n_control=1000,
                n_treatment=1000,
                baseline_conversion_rate=0.10
            )
        ]
        
        reconstructed = [
            {
                'reconstructed_p_value': 0.04,
                'reconstructed_effect_size': 0.15,
                'reconstructed_n_control': 1000,
                'reconstructed_n_treatment': 1000
            },
            {
                'reconstructed_p_value': 0.05,
                'reconstructed_effect_size': 0.16,
                'reconstructed_n_control': 1000,
                'reconstructed_n_treatment': 1000
            }
        ]
        
        with pytest.raises(ValueError, match="Number of summaries must match"):
            validate_all_summaries(summaries, reconstructed)


class TestRunValidator:
    """Tests for the main validator entry point."""
    
    def test_full_validation_flow(self):
        """Test the complete validation flow with file I/O."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create test summaries
            summaries = [
                ABTestSummary(
                    url="https://example.com/test1",
                    domain="example.com",
                    test_type="binary",
                    reported_p_value=0.04,
                    effect_size=0.15,
                    n_control=1000,
                    n_treatment=1000,
                    baseline_conversion_rate=0.10
                ),
                ABTestSummary(
                    url="https://example.com/test2",
                    domain="example.com",
                    test_type="binary",
                    reported_p_value=0.05,
                    effect_size=0.15,
                    n_control=1000,
                    n_treatment=1000,
                    baseline_conversion_rate=0.10
                )
            ]
            
            summaries_path = tmpdir_path / "summaries.json"
            with open(summaries_path, 'w') as f:
                json.dump([s.model_dump() for s in summaries], f)
            
            # Create reconstructed results
            reconstructed = [
                {
                    'reconstructed_p_value': 0.04,
                    'reconstructed_effect_size': 0.15,
                    'reconstructed_n_control': 1000,
                    'reconstructed_n_treatment': 1000
                },
                {
                    'reconstructed_p_value': 0.12,  # Inconsistent
                    'reconstructed_effect_size': 0.15,
                    'reconstructed_n_control': 1000,
                    'reconstructed_n_treatment': 1000
                }
            ]
            
            reconstructed_path = tmpdir_path / "reconstructed.json"
            with open(reconstructed_path, 'w') as f:
                json.dump(reconstructed, f)
            
            output_path = tmpdir_path / "audit_report.json"
            
            # Run validator
            records = run_validator(summaries_path, reconstructed_path, output_path)
            
            # Verify output file exists
            assert output_path.exists()
            
            # Verify results
            assert len(records) == 2
            assert records[0].is_consistent is True
            assert records[1].is_consistent is False
            
            # Verify JSON content
            with open(output_path, 'r') as f:
                output_data = json.load(f)
            
            assert len(output_data) == 2
            assert output_data[0]['status'] == 'consistent'
            assert output_data[1]['status'] == 'inconsistent'
    
    def test_sample_size_mismatch_exclusion(self):
        """Test that sample size mismatches are flagged for exclusion from prevalence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            summaries = [
                ABTestSummary(
                    url="https://example.com/test1",
                    domain="example.com",
                    test_type="binary",
                    reported_p_value=0.04,
                    effect_size=0.15,
                    n_control=1000,
                    n_treatment=1000,
                    baseline_conversion_rate=0.10
                )
            ]
            
            summaries_path = tmpdir_path / "summaries.json"
            with open(summaries_path, 'w') as f:
                json.dump([s.model_dump() for s in summaries], f)
            
            # Reconstructed with mismatched sample sizes
            reconstructed = [
                {
                    'reconstructed_p_value': 0.04,
                    'reconstructed_effect_size': 0.15,
                    'reconstructed_n_control': 1500,  # Mismatch
                    'reconstructed_n_treatment': 1500  # Mismatch
                }
            ]
            
            reconstructed_path = tmpdir_path / "reconstructed.json"
            with open(reconstructed_path, 'w') as f:
                json.dump(reconstructed, f)
            
            output_path = tmpdir_path / "audit_report.json"
            
            records = run_validator(summaries_path, reconstructed_path, output_path)
            
            # Verify sample_size_mismatch flag is set
            assert records[0].sample_size_mismatch is True
            assert records[0].data_quality_warning is True
            assert any("Sample size mismatch" in w for w in records[0].warnings)


class TestThresholds:
    """Tests for threshold constants."""
    
    def test_absolute_p_threshold(self):
        """Verify the absolute p-value threshold is 0.05."""
        assert ABSOLUTE_P_THRESHOLD == 0.05
    
    def test_relative_effect_size_threshold(self):
        """Verify the relative effect size threshold is 5%."""
        assert RELATIVE_EFFECT_SIZE_THRESHOLD == 0.05
