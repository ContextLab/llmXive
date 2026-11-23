import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logging_config import setup_logging

class TestRegressionOutput:
    """
    Integration test for T027: Verify regression results generation.
    """
    
    @pytest.fixture(scope="class")
    def setup_paths(self):
        """Setup paths relative to project root."""
        root = Path(__file__).parent.parent.parent
        return {
            "data_derived": root / "data" / "derived",
            "state": root / "state"
        }

    def test_regression_results_file_exists(self, setup_paths):
        """Verify that regression_results.csv is generated."""
        output_file = setup_paths["data_derived"] / "regression_results.csv"
        assert output_file.exists(), f"Output file {output_file} does not exist. T027 may have failed."

    def test_regression_results_schema(self, setup_paths):
        """Verify the schema of the generated CSV."""
        output_file = setup_paths["data_derived"] / "regression_results.csv"
        
        if not output_file.exists():
            pytest.skip("Output file not found, skipping schema test.")
        
        df = pd.read_csv(output_file)
        
        required_columns = ['term', 'coefficient', 'std_err', 'p_value', 'ci_lower', 'ci_high']
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        assert not missing_cols, f"Missing required columns: {missing_cols}"
        
        # Check for at least one row
        assert len(df) > 0, "Regression results dataframe is empty."

    def test_interaction_term_present(self, setup_paths):
        """Verify that the three-way interaction term is present in the results."""
        output_file = setup_paths["data_derived"] / "regression_results.csv"
        
        if not output_file.exists():
            pytest.skip("Output file not found.")
        
        df = pd.read_csv(output_file)
        
        # Check if the interaction term exists (exact name may vary slightly)
        interaction_terms = df['term'].str.contains('fixation_duration.*valence.*cognitive_reflection_score', regex=True)
        
        assert interaction_terms.any(), "Three-way interaction term not found in regression results."

    def test_p_values_numeric(self, setup_paths):
        """Verify that p-values are numeric and within [0, 1] (after correction)."""
        output_file = setup_paths["data_derived"] / "regression_results.csv"
        
        if not output_file.exists():
            pytest.skip("Output file not found.")
        
        df = pd.read_csv(output_file)
        
        # Check p_value column
        assert pd.api.types.is_numeric_dtype(df['p_value']), "p_value column is not numeric."
        
        # Check range (allowing for slight floating point issues)
        assert (df['p_value'] >= 0).all() and (df['p_value'] <= 1.0001).all(), "p_values out of range [0, 1]."

    def test_causal_statement_exists(self, setup_paths):
        """Verify that the causal framing statement was generated."""
        statement_file = setup_paths["state"] / "causal_framing.json"
        
        assert statement_file.exists(), f"Causal framing statement file {statement_file} not found."
        
        import json
        with open(statement_file, 'r') as f:
            data = json.load(f)
        
        assert 'statement' in data, "Causal statement key missing in JSON."
        assert len(data['statement']) > 0, "Causal statement is empty."