import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path if needed
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.validator import (
    validate_required_columns,
    validate_data_quality,
    halt_if_invalid,
    create_validation_report,
    validate_and_halt,
    REQUIRED_COLUMNS
)

class TestValidator:
    
    def setup_method(self):
        """Setup valid test data."""
        self.valid_df = pd.DataFrame({
            "da_dN": [1e-5, 2e-5, 3e-5, 4e-5],
            "delta_K": [10, 15, 20, 25],
            "material": ["Al7075", "Al7075", "Ti64", "Ti64"],
            "heat_treatment": ["T6", "T6", "ST", "ST"]
        })
        
        self.missing_col_df = pd.DataFrame({
            "da_dN": [1e-5, 2e-5],
            "delta_K": [10, 15],
            "material": ["Al7075", "Al7075"]
            # Missing 'heat_treatment'
        })
        
        self.negative_df = pd.DataFrame({
            "da_dN": [1e-5, -2e-5, 3e-5],
            "delta_K": [10, 15, -20],
            "material": ["Al", "Al", "Al"],
            "heat_treatment": ["T6", "T6", "T6"]
        })

    def test_validate_required_columns_pass(self):
        """Test that valid data passes column validation."""
        missing = validate_required_columns(self.valid_df)
        assert len(missing) == 0

    def test_validate_required_columns_fail(self):
        """Test that missing columns are detected."""
        missing = validate_required_columns(self.missing_col_df)
        assert "heat_treatment" in missing
        assert len(missing) == 1

    def test_validate_data_quality_pass(self):
        """Test that valid data passes quality checks."""
        report = validate_data_quality(self.valid_df)
        assert report["valid"] is True
        assert report["has_infinite"] is False
        assert len(report["issues"]) == 1  # "No data quality issues detected"

    def test_validate_data_quality_negative_values(self):
        """Test detection of negative physical values."""
        report = validate_data_quality(self.negative_df)
        assert report["valid"] is False
        assert "da_dN" in report["negative_values"]
        assert "delta_K" in report["negative_values"]

    def test_halt_if_invalid_pass(self):
        """Test that halt_if_invalid returns True for valid data."""
        result = halt_if_invalid(self.valid_df, raise_on_missing=False)
        assert result is True

    def test_halt_if_invalid_fail(self):
        """Test that halt_if_invalid returns False for missing columns."""
        result = halt_if_invalid(self.missing_col_df, raise_on_missing=False)
        assert result is False

    def test_halt_if_invalid_raises(self):
        """Test that halt_if_invalid raises ValueError when configured."""
        with pytest.raises(ValueError):
            halt_if_invalid(self.missing_col_df, raise_on_missing=True)

    def test_create_validation_report(self):
        """Test comprehensive report generation."""
        report = create_validation_report(self.valid_df)
        assert report["summary"]["is_valid"] is True
        assert report["schema_validation"]["passed"] is True
        assert "data_quality" in report

    def test_validate_and_halt_pass(self):
        """Test that validate_and_halt succeeds for valid data."""
        # Should not raise
        validate_and_halt(self.valid_df, context="Test Dataset")

    def test_validate_and_halt_fail(self):
        """Test that validate_and_halt raises for invalid data."""
        with pytest.raises(ValueError):
            validate_and_halt(self.missing_col_df, context="Test Dataset")

    def test_validate_and_halt_negative_values(self):
        """Test that validate_and_halt raises for negative values."""
        with pytest.raises(ValueError):
            validate_and_halt(self.negative_df, context="Test Dataset")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])