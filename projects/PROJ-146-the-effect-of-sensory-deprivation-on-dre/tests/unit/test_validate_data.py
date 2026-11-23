import pytest
import pandas as pd
import numpy as np
from code.validate_data import validate_recall_binary, validate_bizarreness_range, run_validation

class TestValidateRecallBinary:
    def test_valid_binary_int(self):
        df = pd.DataFrame({'recall': [0, 1, 0, 1]})
        is_valid, errors = validate_recall_binary(df)
        assert is_valid is True
        assert len(errors) == 0

    def test_valid_binary_float(self):
        df = pd.DataFrame({'recall': [0.0, 1.0, 0.0, 1.0]})
        is_valid, errors = validate_recall_binary(df)
        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_values(self):
        df = pd.DataFrame({'recall': [0, 1, 2, 3]})
        is_valid, errors = validate_recall_binary(df)
        assert is_valid is False
        assert any("invalid values" in e.lower() for e in errors)

    def test_missing_column(self):
        df = pd.DataFrame({'other': [1, 2]})
        is_valid, errors = validate_recall_binary(df)
        assert is_valid is False
        assert any("missing" in e.lower() for e in errors)

    def test_null_values(self):
        df = pd.DataFrame({'recall': [0, 1, np.nan, 1]})
        is_valid, errors = validate_recall_binary(df)
        assert is_valid is False
        assert any("null" in e.lower() for e in errors)

    def test_non_numeric(self):
        df = pd.DataFrame({'recall': ['yes', 'no', 'yes']})
        is_valid, errors = validate_recall_binary(df)
        assert is_valid is False
        assert any("not numeric" in e.lower() for e in errors)

class TestValidateBizarrenessRange:
    def test_valid_range(self):
        df = pd.DataFrame({'bizarreness': [1, 4, 7, 3]})
        is_valid, errors = validate_bizarreness_range(df)
        assert is_valid is True
        assert len(errors) == 0

    def test_valid_float_integers(self):
        df = pd.DataFrame({'bizarreness': [1.0, 4.0, 7.0]})
        is_valid, errors = validate_bizarreness_range(df)
        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_low(self):
        df = pd.DataFrame({'bizarreness': [0, 1, 4]})
        is_valid, errors = validate_bizarreness_range(df)
        assert is_valid is False
        assert any("outside range" in e.lower() for e in errors)

    def test_invalid_high(self):
        df = pd.DataFrame({'bizarreness': [1, 7, 8]})
        is_valid, errors = validate_bizarreness_range(df)
        assert is_valid is False
        assert any("outside range" in e.lower() for e in errors)

    def test_non_integer_float(self):
        df = pd.DataFrame({'bizarreness': [1.5, 4.0, 7.0]})
        is_valid, errors = validate_bizarreness_range(df)
        assert is_valid is False
        assert any("non-integer" in e.lower() for e in errors)

    def test_missing_column(self):
        df = pd.DataFrame({'other': [1, 2]})
        is_valid, errors = validate_bizarreness_range(df)
        assert is_valid is False
        assert any("missing" in e.lower() for e in errors)

    def test_null_values(self):
        df = pd.DataFrame({'bizarreness': [1, np.nan, 4]})
        is_valid, errors = validate_bizarreness_range(df)
        assert is_valid is False
        assert any("null" in e.lower() for e in errors)

class TestRunValidation:
    def test_full_valid(self, caplog):
        df = pd.DataFrame({
            'recall': [0, 1, 0],
            'bizarreness': [1, 4, 7]
        })
        # Capture log output
        import logging
        caplog.set_level(logging.INFO)
        
        result = run_validation(df, source_name="test_source")
        
        assert result is True
        assert "Validation SUCCESS" in caplog.text

    def test_full_invalid(self, caplog):
        df = pd.DataFrame({
            'recall': [0, 2, 0], # Invalid recall
            'bizarreness': [1, 8, 7] # Invalid bizarreness
        })
        import logging
        caplog.set_level(logging.ERROR)
        
        result = run_validation(df, source_name="test_source")
        
        assert result is False
        assert "Validation FAILED" in caplog.text