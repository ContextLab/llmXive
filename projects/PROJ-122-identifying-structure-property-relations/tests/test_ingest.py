import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import tempfile

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from utils.ingest_utils import validate_weight_fractions

class TestWeightFractionValidation:
    """Unit tests for weight-fraction validation logic (T016)"""

    def test_valid_weight_fractions_exact_sum(self):
        """Test that weight fractions summing to exactly 1.0 are valid"""
        fractions = [0.5, 0.3, 0.2]
        is_valid, reason = validate_weight_fractions(fractions)
        assert is_valid is True
        assert reason is None

    def test_valid_weight_fractions_within_tolerance(self):
        """Test that weight fractions summing within tolerance (±0.02) are valid"""
        fractions = [0.49, 0.31, 0.20]  # Sum = 1.00
        is_valid, reason = validate_weight_fractions(fractions)
        assert is_valid is True
        assert reason is None

        fractions = [0.48, 0.32, 0.20]  # Sum = 1.00
        is_valid, reason = validate_weight_fractions(fractions)
        assert is_valid is True

    def test_invalid_weight_fractions_exceeds_upper_tolerance(self):
        """Test that weight fractions summing > 1.02 are invalid"""
        fractions = [0.51, 0.31, 0.21]  # Sum = 1.03
        is_valid, reason = validate_weight_fractions(fractions)
        assert is_valid is False
        assert "exceeds" in reason.lower() or "tolerance" in reason.lower()

    def test_invalid_weight_fractions_below_lower_tolerance(self):
        """Test that weight fractions summing < 0.98 are invalid"""
        fractions = [0.47, 0.30, 0.19]  # Sum = 0.96
        is_valid, reason = validate_weight_fractions(fractions)
        assert is_valid is False
        assert "below" in reason.lower() or "tolerance" in reason.lower()

    def test_invalid_weight_fractions_negative_value(self):
        """Test that negative weight fractions are invalid"""
        fractions = [0.5, -0.1, 0.6]
        is_valid, reason = validate_weight_fractions(fractions)
        assert is_valid is False
        assert "negative" in reason.lower()

    def test_invalid_weight_fractions_value_greater_than_one(self):
        """Test that weight fractions > 1.0 are invalid"""
        fractions = [0.5, 1.2, 0.3]
        is_valid, reason = validate_weight_fractions(fractions)
        assert is_valid is False
        assert "greater than 1" in reason.lower() or "invalid" in reason.lower()

    def test_empty_weight_fractions(self):
        """Test that empty weight fraction list is valid (no validation needed)"""
        fractions = []
        is_valid, reason = validate_weight_fractions(fractions)
        assert is_valid is True
        assert reason is None

    def test_single_component_weight_fraction(self):
        """Test single component weight fraction of 1.0"""
        fractions = [1.0]
        is_valid, reason = validate_weight_fractions(fractions)
        assert is_valid is True

    def test_single_component_weight_fraction_slightly_less(self):
        """Test single component weight fraction slightly less than 1.0"""
        fractions = [0.99]
        is_valid, reason = validate_weight_fractions(fractions)
        assert is_valid is True  # Within tolerance

    def test_invalid_weight_fraction_sum_zero(self):
        """Test that all zeros are invalid"""
        fractions = [0.0, 0.0, 0.0]
        is_valid, reason = validate_weight_fractions(fractions)
        assert is_valid is False
        assert "below" in reason.lower() or "tolerance" in reason.lower()

class TestRunHarmonizationWeightValidation:
    """Integration tests for weight-fraction validation in run_harmonization"""

    @pytest.fixture
    def temp_input_file(self):
        """Create a temporary input file with test data"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            data = [
                {"id": 1, "Tg_C": 25, "Modulus_Pa": 1e9, "w_polymer_a": 0.6, "w_polymer_b": 0.4},  # Valid
                {"id": 2, "Tg_C": 30, "Modulus_Pa": 2e9, "w_polymer_a": 0.5, "w_polymer_b": 0.6},  # Invalid (sum > 1.02)
                {"id": 3, "Tg_C": 35, "Modulus_Pa": 1.5e9, "w_polymer_a": 0.7, "w_polymer_b": 0.2},  # Valid
                {"id": 4, "Tg_C": 40, "Modulus_Pa": 3e9, "w_polymer_a": 0.3, "w_polymer_b": 0.3},  # Invalid (sum < 0.98)
                {"id": 5, "Tg_C": 45, "Modulus_Pa": 2.5e9, "w_polymer_a": 0.8, "w_polymer_b": 0.2},  # Valid (exactly 1.0)
            ]
            json.dump(data, f)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_weight_fraction_validation_excludes_invalid_records(self, temp_input_file, temp_output_dir):
        """Test that invalid weight fraction records are excluded from output"""
        from code_01_ingest import run_harmonization  # Import the actual module
        
        output_path = os.path.join(temp_output_dir, "output.json")
        valid_records, stats = run_harmonization(temp_input_file, output_path)
        
        # We expect 3 valid records (ids 1, 3, 5)
        assert len(valid_records) == 3
        assert stats['valid_count'] == 3
        assert stats['invalid_count'] == 2
        
        # Verify specific valid records are present
        valid_ids = [r['id'] for r in valid_records]
        assert 1 in valid_ids
        assert 3 in valid_ids
        assert 5 in valid_ids
        
        # Verify invalid records are excluded
        assert 2 not in valid_ids
        assert 4 not in valid_ids

    def test_weight_fraction_validation_report_generated(self, temp_input_file, temp_output_dir):
        """Test that validation report is generated with correct statistics"""
        from code_01_ingest import run_harmonization
        
        output_path = os.path.join(temp_output_dir, "output.json")
        valid_records, stats = run_harmonization(temp_input_file, output_path)
        
        report_path = os.path.join(temp_output_dir, "weight_fraction_validation_report.json")
        assert os.path.exists(report_path)
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert report['total_records'] == 5
        assert report['valid_count'] == 3
        assert report['invalid_count'] == 2
        assert len(report['invalid_reasons']) > 0

    def test_weight_fraction_validation_handles_missing_weights(self, temp_output_dir):
        """Test that records without weight fractions are treated as valid"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            data = [
                {"id": 1, "Tg_C": 25, "Modulus_Pa": 1e9},  # No weight fractions
                {"id": 2, "Tg_C": 30, "Modulus_Pa": 2e9, "w_polymer_a": 0.6, "w_polymer_b": 0.4},  # Valid
            ]
            json.dump(data, f)
            temp_path = f.name
        
        try:
            from code_01_ingest import run_harmonization
            
            output_path = os.path.join(temp_output_dir, "output.json")
            valid_records, stats = run_harmonization(temp_path, output_path)
            
            # Both records should be valid (one has no weights, one is valid)
            assert len(valid_records) == 2
            assert stats['valid_count'] == 2
            assert stats['invalid_count'] == 0
        finally:
            os.unlink(temp_path)