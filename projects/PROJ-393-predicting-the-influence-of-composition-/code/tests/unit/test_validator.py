"""
Unit tests for the composition validator (T025).
"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys

# Add src to path for imports if running from tests directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from preprocessing.validator import extract_elements_from_composition, validate_compositions


class TestExtractElements:
    """Tests for element extraction regex logic."""

    def test_simple_formula(self):
        """Test basic Heusler formula extraction."""
        result = extract_elements_from_composition("Co2MnGa")
        assert result == {"Co", "Mn", "Ga"}

    def test_formula_with_spaces(self):
        """Test formula with spaces."""
        result = extract_elements_from_composition("Co2 Mn Ga")
        assert result == {"Co", "Mn", "Ga"}

    def test_colon_separated(self):
        """Test colon separated format."""
        result = extract_elements_from_composition("Co:Mn:Ga")
        assert result == {"Co", "Mn", "Ga"}

    def test_decimal_composition(self):
        """Test composition with decimal fractions."""
        result = extract_elements_from_composition("Co2Mn0.5Ga0.5")
        assert result == {"Co", "Mn", "Ga"}

    def test_empty_string(self):
        """Test empty string."""
        result = extract_elements_from_composition("")
        assert result == set()

    def test_non_string(self):
        """Test non-string input."""
        result = extract_elements_from_composition(123)
        assert result == set()

    def test_mixed_case_elements(self):
        """Test elements with mixed case (should handle standard symbols)."""
        result = extract_elements_from_composition("FeNiCu")
        assert result == {"Fe", "Ni", "Cu"}


class TestValidateCompositions:
    """Tests for the main validation logic."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            "composition": ["Co2MnGa", "Fe3Al", "CoMnSi", "UnknownElementX"],
            "coercivity": [100, 200, 150, 300],
            "saturation": [1.2, 1.5, 1.3, 1.1]
        })

    @pytest.fixture
    def mock_properties(self):
        """Mock periodic table properties containing only known elements."""
        return {
            "Co": {"electronegativity": 1.88, "atomic_radii": 1.25, "valence_electrons": 9},
            "Mn": {"electronegativity": 1.55, "atomic_radii": 1.27, "valence_electrons": 7},
            "Ga": {"electronegativity": 1.81, "atomic_radii": 1.22, "valence_electrons": 3},
            "Fe": {"electronegativity": 1.83, "atomic_radii": 1.26, "valence_electrons": 8},
            "Al": {"electronegativity": 1.61, "atomic_radii": 1.43, "valence_electrons": 3},
            "Si": {"electronegativity": 1.90, "atomic_radii": 1.17, "valence_electrons": 4},
            # Note: "X" is intentionally missing
        }

    def test_all_known_elements(self, sample_df, mock_properties):
        """Test validation when all elements are known."""
        # Modify df to remove the unknown element row
        clean_df = sample_df.iloc[:3].reset_index(drop=True)
        df_out, warnings = validate_compositions(clean_df, allowed_elements=mock_properties)
        
        assert len(warnings) == 0
        assert df_out.equals(clean_df)

    def test_unknown_elements_found(self, sample_df, mock_properties):
        """Test validation when unknown elements are present."""
        # The last row has "UnknownElementX" which contains 'X' (unknown)
        df_out, warnings = validate_compositions(sample_df, allowed_elements=mock_properties)
        
        assert len(warnings) > 0
        assert any("UnknownElementX" in w["composition"] for w in warnings)
        assert any("X" in w["unknown_elements"] for w in warnings)

    def test_strict_mode_raises_error(self, sample_df, mock_properties):
        """Test that strict mode raises ValueError on unknown elements."""
        with pytest.raises(ValueError, match="Strict validation failed"):
            validate_compositions(sample_df, allowed_elements=mock_properties, strict=True)

    def test_missing_column_raises_error(self, sample_df, mock_properties):
        """Test that missing composition column raises ValueError."""
        with pytest.raises(ValueError, match="Column 'composition' not found"):
            validate_compositions(sample_df, composition_column="nonexistent_col", allowed_elements=mock_properties)

    def test_non_string_composition_handled(self, mock_properties):
        """Test handling of non-string composition values."""
        df = pd.DataFrame({
            "composition": [123, None, "Co2MnGa"],
            "value": [1, 2, 3]
        })
        df_out, warnings = validate_compositions(df, allowed_elements=mock_properties)
        
        # Should not crash, only warn on valid strings
        assert len(warnings) == 0
        assert df_out.equals(df)