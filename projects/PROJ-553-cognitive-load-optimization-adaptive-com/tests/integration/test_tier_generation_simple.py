import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Import the functions to test
from code.generate_simple_tier import (
    load_moderate_tiers,
    simplify_text,
    iterative_simplify,
    generate_simple_tiers,
    save_simple_tiers
)
from code.utils import calculate_flesch_kincaid, calculate_jaccard_similarity

class TestSimpleTierGeneration:
    """Integration tests for simple tier generation."""

    @pytest.fixture
    def sample_moderate_data(self):
        """Create a sample moderate tiers dataframe."""
        data = {
            'instructional_unit_id': ['unit_001', 'unit_002', 'unit_003'],
            'text': [
                "The utilization of advanced methodologies demonstrates approximately significant subsequent consequences.",
                "Furthermore, the implementation of essential individual facilitation indicates a conclusion.",
                "The demonstration of approximately significant subsequent consequences facilitates implementation."
            ]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_simplify_text_reduces_complexity(self):
        """Test that simplify_text reduces Flesch-Kincaid score."""
        complex_text = "The utilization of advanced methodologies demonstrates approximately significant subsequent consequences."
        simple_text = simplify_text(complex_text, aggression=1)
        
        fk_complex = calculate_flesch_kincaid(complex_text)
        fk_simple = calculate_flesch_kincaid(simple_text)
        
        assert fk_simple <= fk_complex, "Simplified text should have lower or equal FK score"

    def test_iterative_simplify_meets_constraints(self):
        """Test that iterative_simplify attempts to meet constraints."""
        moderate_text = "The utilization of advanced methodologies demonstrates approximately significant subsequent consequences."
        simplified_text, success = iterative_simplify(moderate_text, moderate_text)
        
        fk_moderate = calculate_flesch_kincaid(moderate_text)
        fk_simple = calculate_flesch_kincaid(simplified_text)
        jaccard = calculate_jaccard_similarity(simplified_text, moderate_text)
        
        # Check if constraints are met or if we hit max iterations
        fk_diff = fk_moderate - fk_simple
        
        # Either constraints are met, or we tried our best (max iterations)
        assert (fk_diff >= 5.0 and jaccard >= 0.85) or not success

    def test_generate_simple_tiers_creates_output(self, sample_moderate_data, temp_output_dir):
        """Test that generate_simple_tiers processes all rows."""
        results = generate_simple_tiers(sample_moderate_data)
        
        assert len(results) == len(sample_moderate_data)
        assert all('instructional_unit_id' in r for r in results)
        assert all('text' in r for r in results)
        assert all('fk_score' in r for r in results)
        assert all('constraints_met' in r for r in results)

    def test_save_simple_tiers_creates_file(self, sample_moderate_data, temp_output_dir):
        """Test that save_simple_tiers writes a valid CSV."""
        results = generate_simple_tiers(sample_moderate_data)
        output_path = os.path.join(temp_output_dir, "simple_tiers.csv")
        
        save_simple_tiers(results, output_path)
        
        assert os.path.exists(output_path)
        
        df = pd.read_csv(output_path)
        assert len(df) == len(results)
        assert 'instructional_unit_id' in df.columns
        assert 'text' in df.columns
        assert 'fk_score' in df.columns
        assert 'jaccard_similarity' in df.columns

    def test_constraint_validation(self, sample_moderate_data):
        """Test that constraints are properly calculated."""
        results = generate_simple_tiers(sample_moderate_data)
        
        for result in results:
            if result['constraints_met']:
                assert result['fk_diff_from_moderate'] >= 5.0
                assert result['jaccard_similarity'] >= 0.85

    def test_empty_text_handling(self):
        """Test handling of empty text."""
        simplified, success = iterative_simplify("", "")
        assert simplified == ""
        assert success is True  # Empty text trivially meets constraints

    def test_long_text_simplification(self):
        """Test simplification of very long text."""
        long_text = "The utilization of advanced methodologies demonstrates approximately significant subsequent consequences. " * 10
        moderate_text = long_text
        
        simplified, success = iterative_simplify(long_text, moderate_text)
        
        assert len(simplified) <= len(long_text)
        fk_moderate = calculate_flesch_kincaid(moderate_text)
        fk_simple = calculate_flesch_kincaid(simplified)
        assert fk_simple <= fk_moderate