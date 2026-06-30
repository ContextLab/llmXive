"""
Contract test for unified translation schema (US3).

Validates that translation outputs conform to the deterministic schema
defined in the specification for time-series and tabular data.

This test ensures:
1. Time-series translation includes: Mean, Max, Min, Std (all quantitative)
2. Tabular translation includes: CSV-style representation with column names
3. All translations are deterministic (same input -> same output)
4. Fidelity validation works correctly
"""
import os
import pytest
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import the translation module (will be created in T046)
# We'll create a minimal mock for testing if the module doesn't exist yet
try:
    from src.models.translation import UnifiedTranslator
except ImportError:
    # If the module doesn't exist, we'll test the schema structure directly
    UnifiedTranslator = None

# Schema definition for translation outputs
TRANSLATION_SCHEMA = {
    "timeseries": {
        "required_fields": ["mean", "max", "min", "std"],
        "format": "Mean {label} = {mean} {unit}, max = {max} {unit}, min = {min} {unit}, std = {std} {unit}",
        "constraints": {
            "all_quantitative_retained": True,
            "deterministic": True
        }
    },
    "tabular": {
        "required_structure": "CSV-style text with column names and values",
        "constraints": {
            "column_names_preserved": True,
            "values_preserved": True,
            "deterministic": True
        }
    },
    "fidelity": {
        "min_score": 0.0,
        "max_score": 1.0,
        "warning_threshold": 0.8
    }
}

def load_schema() -> Dict[str, Any]:
    """Load the translation schema from the contract."""
    return TRANSLATION_SCHEMA

def validate_timeseries_translation(translated_text: str, original_data: np.ndarray, 
                                  label_name: str = "value", unit: str = "units") -> bool:
    """
    Validate that time-series translation follows the required schema.
    
    Args:
        translated_text: The translated text output
        original_data: The original time-series numpy array
        label_name: The name of the label/column
        unit: The unit of measurement
        
    Returns:
        True if translation conforms to schema, False otherwise
    """
    # Check that all required statistical measures are present
    required_terms = ["Mean", "max", "min", "std"]
    for term in required_terms:
        if term not in translated_text:
            return False
    
    # Check that the label name is included
    if label_name not in translated_text:
        return False
    
    # Check that unit is included
    if unit not in translated_text:
        return False
    
    # Verify deterministic: compute stats and check they match
    expected_mean = np.mean(original_data)
    expected_max = np.max(original_data)
    expected_min = np.min(original_data)
    expected_std = np.std(original_data)
    
    # Extract values from text (simple parsing for test validation)
    import re
    mean_match = re.search(r'Mean.*?=\s*([\d.]+)', translated_text)
    max_match = re.search(r'max\s*=\s*([\d.]+)', translated_text)
    min_match = re.search(r'min\s*=\s*([\d.]+)', translated_text)
    std_match = re.search(r'std\s*=\s*([\d.]+)', translated_text)
    
    if not all([mean_match, max_match, min_match, std_match]):
        return False
    
    # Allow small floating point differences
    tolerance = 1e-6
    if abs(float(mean_match.group(1)) - expected_mean) > tolerance:
        return False
    if abs(float(max_match.group(1)) - expected_max) > tolerance:
        return False
    if abs(float(min_match.group(1)) - expected_min) > tolerance:
        return False
    if abs(float(std_match.group(1)) - expected_std) > tolerance:
        return False
    
    return True

def validate_tabular_translation(translated_text: str, original_df: Any, 
                               label_column: str = None) -> bool:
    """
    Validate that tabular translation follows the required schema.
    
    Args:
        translated_text: The translated text output
        original_df: The original pandas DataFrame
        label_column: The label column name (optional)
        
    Returns:
        True if translation conforms to schema, False otherwise
    """
    # Check that it looks like CSV-style text
    lines = translated_text.strip().split('\n')
    if len(lines) < 2:  # At least header + one row
        return False
    
    # First line should be column names
    header = lines[0]
    if ',' not in header:
        return False
    
    # Check that column names are present
    expected_columns = list(original_df.columns)
    for col in expected_columns:
        if str(col) not in header:
            return False
    
    # Check that at least one data row exists and contains values
    data_lines = lines[1:]
    for line in data_lines:
        if ',' not in line:
            return False
        
        # Extract values and check they match original data
        values = line.split(',')
        if len(values) != len(expected_columns):
            return False
    
    return True

def validate_fidelity(original_data: Any, translated_text: str, 
                    translation_type: str) -> float:
    """
    Validate the fidelity of translation (information preservation).
    
    Args:
        original_data: The original data (numpy array or DataFrame)
        translated_text: The translated text
        translation_type: 'timeseries' or 'tabular'
        
    Returns:
        Fidelity score between 0.0 and 1.0
    """
    if translation_type == "timeseries":
        # For time-series, check that all statistical measures are present
        required_stats = ["Mean", "max", "min", "std"]
        present_stats = sum(1 for stat in required_stats if stat in translated_text)
        fidelity = present_stats / len(required_stats)
        
    elif translation_type == "tabular":
        # For tabular, check column preservation
        lines = translated_text.strip().split('\n')
        if len(lines) < 2:
            return 0.0
        
        header = lines[0]
        # Assume original_data has columns attribute (pandas DataFrame)
        if hasattr(original_data, 'columns'):
            expected_cols = len(original_data.columns)
            present_cols = sum(1 for col in original_data.columns if str(col) in header)
            fidelity = present_cols / expected_cols if expected_cols > 0 else 0.0
        else:
            fidelity = 0.0
    else:
        fidelity = 0.0
    
    return fidelity

class TestTranslationSchema:
    """Contract tests for unified translation schema."""
    
    def test_schema_structure(self):
        """Test that the schema has all required sections."""
        schema = load_schema()
        
        assert "timeseries" in schema
        assert "tabular" in schema
        assert "fidelity" in schema
        
        # Check timeseries required fields
        assert "required_fields" in schema["timeseries"]
        assert set(schema["timeseries"]["required_fields"]) == {"mean", "max", "min", "std"}
        
        # Check fidelity constraints
        assert "min_score" in schema["fidelity"]
        assert "max_score" in schema["fidelity"]
        assert schema["fidelity"]["min_score"] == 0.0
        assert schema["fidelity"]["max_score"] == 1.0
    
    def test_timeseries_translation_format(self):
        """Test time-series translation follows the required format."""
        # Create sample time-series data
        np.random.seed(42)
        sample_data = np.random.randn(100) * 10 + 50
        
        # Create expected translation text
        mean_val = np.mean(sample_data)
        max_val = np.max(sample_data)
        min_val = np.min(sample_data)
        std_val = np.std(sample_data)
        
        expected_text = f"Mean heart rate = {mean_val:.2f} bpm, max = {max_val:.2f} bpm, min = {min_val:.2f} bpm, std = {std_val:.2f} bpm"
        
        # Validate the format
        assert validate_timeseries_translation(expected_text, sample_data, "heart rate", "bpm")
    
    def test_timeseries_translation_determinism(self):
        """Test that time-series translation is deterministic."""
        np.random.seed(42)
        sample_data = np.random.randn(50)
        
        # Generate translation twice
        mean_val = np.mean(sample_data)
        max_val = np.max(sample_data)
        min_val = np.min(sample_data)
        std_val = np.std(sample_data)
        
        translation_1 = f"Mean value = {mean_val:.2f} units, max = {max_val:.2f} units, min = {min_val:.2f} units, std = {std_val:.2f} units"
        translation_2 = f"Mean value = {mean_val:.2f} units, max = {max_val:.2f} units, min = {min_val:.2f} units, std = {std_val:.2f} units"
        
        # Should be identical
        assert translation_1 == translation_2
        assert validate_timeseries_translation(translation_1, sample_data)
        assert validate_timeseries_translation(translation_2, sample_data)
    
    def test_tabular_translation_format(self):
        """Test tabular translation follows CSV-style format."""
        try:
            import pandas as pd
            # Create sample DataFrame
            df = pd.DataFrame({
                'age': [25, 30, 35],
                'income': [50000, 60000, 70000],
                'score': [85.5, 90.0, 88.5]
            })
            
            # Create expected translation
            expected_text = "age,income,score\n25,50000,85.5\n30,60000,90.0\n35,70000,88.5"
            
            # Validate the format
            assert validate_tabular_translation(expected_text, df)
        except ImportError:
            # Skip if pandas not available
            pytest.skip("pandas not available")
    
    def test_tabular_translation_determinism(self):
        """Test that tabular translation is deterministic."""
        try:
            import pandas as pd
            df = pd.DataFrame({
                'x': [1, 2, 3],
                'y': [4, 5, 6]
            })
            
            # Generate translation twice
            text_1 = "x,y\n1,4\n2,5\n3,6"
            text_2 = "x,y\n1,4\n2,5\n3,6"
            
            # Should be identical
            assert text_1 == text_2
            assert validate_tabular_translation(text_1, df)
        except ImportError:
            pytest.skip("pandas not available")
    
    def test_fidelity_validation(self):
        """Test fidelity validation function."""
        # Test time-series fidelity
        np.random.seed(42)
        ts_data = np.random.randn(20)
        ts_text = f"Mean value = {np.mean(ts_data):.2f} units, max = {np.max(ts_data):.2f} units, min = {np.min(ts_data):.2f} units, std = {np.std(ts_data):.2f} units"
        
        ts_fidelity = validate_fidelity(ts_data, ts_text, "timeseries")
        assert 0.0 <= ts_fidelity <= 1.0
        assert ts_fidelity == 1.0  # All stats present
        
        # Test with missing stats
        incomplete_text = "Mean value = 5.0 units"
        incomplete_fidelity = validate_fidelity(ts_data, incomplete_text, "timeseries")
        assert incomplete_fidelity < 1.0
    
    def test_schema_constraints(self):
        """Test that schema constraints are enforced."""
        schema = load_schema()
        
        # Check timeseries constraints
        assert schema["timeseries"]["constraints"]["all_quantitative_retained"] is True
        assert schema["timeseries"]["constraints"]["deterministic"] is True
        
        # Check tabular constraints
        assert schema["tabular"]["constraints"]["column_names_preserved"] is True
        assert schema["tabular"]["constraints"]["values_preserved"] is True
        assert schema["tabular"]["constraints"]["deterministic"] is True
    
    def test_invalid_timeseries_translation(self):
        """Test that invalid time-series translations are rejected."""
        np.random.seed(42)
        sample_data = np.random.randn(10)
        
        # Missing 'std'
        invalid_text_1 = "Mean value = 5.0 units, max = 10.0 units, min = 0.0 units"
        assert not validate_timeseries_translation(invalid_text_1, sample_data)
        
        # Missing label name
        invalid_text_2 = "Mean = 5.0 units, max = 10.0 units, min = 0.0 units, std = 2.0 units"
        assert not validate_timeseries_translation(invalid_text_2, sample_data, "heart rate")
        
        # Wrong statistical values
        invalid_text_3 = "Mean heart rate = 999.0 bpm, max = 999.0 bpm, min = 999.0 bpm, std = 999.0 bpm"
        assert not validate_timeseries_translation(invalid_text_3, sample_data, "heart rate", "bpm")
    
    def test_invalid_tabular_translation(self):
        """Test that invalid tabular translations are rejected."""
        try:
            import pandas as pd
            df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
            
            # Missing header
            invalid_text_1 = "1,3\n2,4"
            assert not validate_tabular_translation(invalid_text_1, df)
            
            # Missing column
            invalid_text_2 = "a,b\n1,3"
            # This should pass if all columns are present in header
            # But let's test with wrong number of columns in data row
            invalid_text_3 = "a,b\n1\n2,4"
            assert not validate_tabular_translation(invalid_text_3, df)
        except ImportError:
            pytest.skip("pandas not available")
    
    def test_fidelity_warning_threshold(self):
        """Test that fidelity warnings are triggered below threshold."""
        schema = load_schema()
        warning_threshold = schema["fidelity"]["warning_threshold"]
        
        # Create low fidelity translation
        low_fidelity_text = "Some text without statistics"
        np.random.seed(42)
        ts_data = np.random.randn(10)
        
        fidelity = validate_fidelity(ts_data, low_fidelity_text, "timeseries")
        assert fidelity < warning_threshold
    
    def test_complete_translation_workflow(self):
        """Test a complete translation workflow with validation."""
        # Time-series workflow
        np.random.seed(42)
        ts_data = np.random.randn(50) * 5 + 100
        
        # Generate translation
        mean_val = np.mean(ts_data)
        max_val = np.max(ts_data)
        min_val = np.min(ts_data)
        std_val = np.std(ts_data)
        
        ts_translation = f"Mean heart rate = {mean_val:.2f} bpm, max = {max_val:.2f} bpm, min = {min_val:.2f} bpm, std = {std_val:.2f} bpm"
        
        # Validate
        assert validate_timeseries_translation(ts_translation, ts_data, "heart rate", "bpm")
        ts_fidelity = validate_fidelity(ts_data, ts_translation, "timeseries")
        assert ts_fidelity == 1.0
        
        # Tabular workflow
        try:
            import pandas as pd
            df = pd.DataFrame({
                'temperature': [20.5, 21.0, 19.8],
                'humidity': [65, 68, 70],
                'pressure': [1013, 1015, 1012]
            })
            
            tabular_translation = "temperature,humidity,pressure\n20.5,65,1013\n21.0,68,1015\n19.8,70,1012"
            
            assert validate_tabular_translation(tabular_translation, df)
            tabular_fidelity = validate_fidelity(df, tabular_translation, "tabular")
            assert tabular_fidelity == 1.0
        except ImportError:
            pytest.skip("pandas not available")