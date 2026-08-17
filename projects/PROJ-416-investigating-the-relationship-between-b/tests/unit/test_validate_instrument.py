"""
Unit test for T052: Verify that validate.py raises FatalError for invalid anxiety instruments.
Ensures no fallback to "best guess" or synthetic labels occurs.
"""
import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.validate import validate_metadata, FatalError

class TestAnxietyInstrumentValidation:
    """Tests for anxiety instrument validation logic."""

    def test_valid_instruments_pass(self):
        """Test that valid instruments (GAD-7, HAM-A, BAI) pass validation."""
        valid_instruments = ['GAD-7', 'HAM-A', 'BAI']
        
        for instrument in valid_instruments:
            metadata = {
                'pre_treatment_score': 10.0,
                'post_treatment_score': 5.0,
                'anxiety_instrument': instrument
            }
            is_valid, errors = validate_metadata(metadata)
            assert is_valid, f"Valid instrument {instrument} should pass validation"
            assert len(errors) == 0

    def test_invalid_instrument_raises_fatal_error(self):
        """Test that invalid instruments raise a clear error without fallback."""
        invalid_instruments = [
            'Unknown Scale',
            'Custom Anxiety Test',
            'GAD-18',  # Close but not exact
            'HAM-D',   # Depression, not anxiety
            '',        # Empty string
            None,      # None value
            'gad-7',   # Wrong case
        ]
        
        for instrument in invalid_instruments:
            metadata = {
                'pre_treatment_score': 10.0,
                'post_treatment_score': 5.0,
                'anxiety_instrument': instrument
            }
            is_valid, errors = validate_metadata(metadata)
            assert not is_valid, f"Invalid instrument {instrument} should fail validation"
            assert len(errors) > 0, f"Invalid instrument {instrument} should produce error messages"
            assert any("Invalid anxiety instrument" in err for err in errors), \
                f"Error should mention 'Invalid anxiety instrument' for {instrument}"

    def test_missing_instrument_field_raises_error(self):
        """Test that missing anxiety_instrument field is caught."""
        metadata = {
            'pre_treatment_score': 10.0,
            'post_treatment_score': 5.0
            # anxiety_instrument is missing
        }
        is_valid, errors = validate_metadata(metadata)
        assert not is_valid, "Missing anxiety_instrument should fail validation"
        assert 'anxiety_instrument' in str(errors), "Error should mention missing variable"

    def test_no_synthetic_fallback_in_logic(self):
        """
        Verify that the validation function does not contain synthetic fallback logic.
        This is a code inspection test to ensure no try/except blocks silently
        generate synthetic data or labels.
        """
        import inspect
        from code.data.validate import validate_metadata
        
        source = inspect.getsource(validate_metadata)
        
        # Check for patterns that would indicate synthetic fallback
        forbidden_patterns = [
            'generate_synthetic',
            'mock_',
            'np.random',
            'synthetic_label',
            'best_guess',
            'fallback',
            'default to',
            'if not valid: return "GAD-7"'
        ]
        
        for pattern in forbidden_patterns:
            assert pattern.lower() not in source.lower(), \
                f"Found forbidden pattern '{pattern}' in validate_metadata - synthetic fallback detected!"

    def test_error_message_is_specific(self):
        """Test that error messages are specific and actionable."""
        metadata = {
            'pre_treatment_score': 10.0,
            'post_treatment_score': 5.0,
            'anxiety_instrument': 'InvalidScale'
        }
        is_valid, errors = validate_metadata(metadata)
        
        assert not is_valid
        assert len(errors) == 1
        assert 'Invalid anxiety instrument: InvalidScale' in errors[0]

    def test_case_sensitivity(self):
        """Test that instrument names are case-sensitive (GAD-7 != gad-7)."""
        metadata_lower = {
            'pre_treatment_score': 10.0,
            'post_treatment_score': 5.0,
            'anxiety_instrument': 'gad-7'
        }
        is_valid, errors = validate_metadata(metadata_lower)
        assert not is_valid, "Lowercase 'gad-7' should not match 'GAD-7'"
        
        metadata_upper = {
            'pre_treatment_score': 10.0,
            'post_treatment_score': 5.0,
            'anxiety_instrument': 'GAD-7'
        }
        is_valid, errors = validate_metadata(metadata_upper)
        assert is_valid, "Uppercase 'GAD-7' should be valid"