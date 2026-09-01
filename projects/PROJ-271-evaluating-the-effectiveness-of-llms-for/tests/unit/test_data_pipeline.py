import os
import sys
import pytest
import pandas as pd
import json
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.data_pipeline import (
    load_sampled_functions,
    compute_radon_metrics,
    run_pylint_analysis,
    normalize_pylint_smells,
    process_functions,
    save_to_csv,
    validate_output,
    REQUIRED_COLUMNS,
    COMPLETENESS_THRESHOLD
)
from code.config import get_path

class TestDataPipeline:

    @pytest.fixture
    def sample_code(self):
        return """
    def example_function(x, y):
        '''This is a docstring.'''
        return x + y
    """

    @pytest.fixture
    def sample_invalid_code(self):
        return "def invalid_function( x, y : "

    def test_compute_radon_metrics_valid_code(self, sample_code):
        """Test radon metrics computation on valid code."""
        loc, cc = compute_radon_metrics(sample_code)
        assert loc > 0, "LOC should be positive"
        assert cc >= 0, "Cyclomatic complexity should be non-negative"

    def test_compute_radon_metrics_invalid_code(self, sample_invalid_code):
        """Test radon metrics computation on invalid code raises error."""
        with pytest.raises(Exception):
            compute_radon_metrics(sample_invalid_code)

    def test_normalize_pylint_smells(self):
        """Test normalization of Pylint codes to smell names."""
        mock_output = "C0114: Missing module docstring\nR0913: Too many arguments"
        smells = normalize_pylint_smells(mock_output)
        assert "missing_module_docstring" in smells
        assert "too_many_arguments" in smells
        assert len(smells) == 2

    def test_pylint_normalization_mapping(self):
        """
        Verify Pylint codes map correctly to canonical smell names using
        contracts/smell_mapping.json (FR-003).
        """
        # Get the path to the mapping file defined in config
        mapping_path = get_path("contracts", "smell_mapping.json")
        
        # Ensure the file exists
        assert os.path.exists(mapping_path), f"Mapping file not found at {mapping_path}"

        # Load the mapping
        with open(mapping_path, 'r') as f:
            smell_mapping = json.load(f)

        # Define a set of known Pylint codes to test against the mapping
        # These are common codes expected in the dataset based on T009
        test_cases = [
            ("C0114", "missing_module_docstring"),
            ("C0116", "missing_function_docstring"),
            ("C0103", "naming_convention"),
            ("R0913", "too_many_arguments"),
            ("R0915", "too_many_statements"),
            ("W0613", "unused_argument"),
            ("W0612", "unused_variable"),
            ("E1101", "attribute_error"),
            ("R1705", "redundant_return_else"),
            ("R1710", "inconsistent_return_statement"),
        ]

        # Validate that the mapping contains the expected keys and values
        for code, expected_smell in test_cases:
            assert code in smell_mapping, f"Pylint code {code} not found in smell_mapping.json"
            assert smell_mapping[code] == expected_smell, (
                f"Mapping for {code} is '{smell_mapping[code]}', expected '{expected_smell}'"
            )

        # Test the normalize_pylint_smells function with a mock output containing these codes
        mock_pylint_output = "\n".join([f"{code}: Some message" for code, _ in test_cases])
        normalized_smells = normalize_pylint_smells(mock_pylint_output)

        # Verify that all expected canonical names are present in the result
        for _, expected_smell in test_cases:
            assert expected_smell in normalized_smells, (
                f"Normalized smells missing expected canonical smell: {expected_smell}"
            )

        # Verify that the function handles unmapped codes gracefully (logs warning or returns empty for that code)
        # We simulate this by adding a fake code that shouldn't be in the mapping
        fake_code = "Z9999"
        mock_with_fake = f"{fake_code}: Fake message\nC0114: Missing module docstring"
        # We expect this not to crash, and for the real code to still be normalized
        result_with_fake = normalize_pylint_smells(mock_with_fake)
        assert "missing_module_docstring" in result_with_fake, (
            "Real code should still be normalized even if fake code is present"
        )
        # The fake code should not appear in the result (or should be handled as per implementation)
        # Assuming the implementation filters out unmapped codes or logs them
        assert fake_code not in result_with_fake, (
            "Fake code should not appear in normalized smells"
        )

    def test_validate_output_missing_columns(self, tmp_path):
        """Test validation fails when required columns are missing."""
        df = pd.DataFrame({
            'id': [1, 2],
            'code': ['def f(): pass', 'def g(): pass']
            # Missing loc, cyclomatic_complexity, static_smell_labels
        })
        csv_path = tmp_path / "test.csv"
        df.to_csv(csv_path, index=False)

        result = validate_output(str(csv_path))
        assert result is False

    def test_validate_output_empty_file(self, tmp_path):
        """Test validation fails on empty file."""
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("")

        result = validate_output(str(csv_path))
        assert result is False

    def test_validate_output_not_found(self):
        """Test validation fails when file doesn't exist."""
        result = validate_output("/nonexistent/path/file.csv")
        assert result is False

    def test_validate_output_success(self, tmp_path):
        """Test validation passes when all conditions are met."""
        # Create a DataFrame with all required columns
        data = {
            'id': [1, 2, 3],
            'code': ['def f(): pass', 'def g(): pass', 'def h(): pass'],
            'loc': [1, 2, 3],
            'cyclomatic_complexity': [1, 1, 1],
            'static_smell_labels': ['[]', '[]', '[]']
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "valid.csv"
        df.to_csv(csv_path, index=False)

        result = validate_output(str(csv_path))
        assert result is True

    def test_validate_output_below_threshold(self, tmp_path):
        """Test validation fails when completeness is below threshold."""
        # Create data where only 50% rows are complete
        data = {
            'id': [1, 2],
            'code': ['def f(): pass', 'def g(): pass'],
            'loc': [1, None],  # Second row missing loc
            'cyclomatic_complexity': [1, None],
            'static_smell_labels': ['[]', None]
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "incomplete.csv"
        df.to_csv(csv_path, index=False)

        result = validate_output(str(csv_path))
        assert result is False