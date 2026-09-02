import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.generate_complex_tier import (
    load_moderate_tiers,
    generate_complex_tier,
    generate_complex_tiers,
    save_complex_tiers,
    MIN_FK_DIFFERENCE,
    MIN_JACCARD_SIMILARITY
)
from code.utils import calculate_flesch_kincaid, calculate_jaccard_similarity

class TestComplexTierGeneration:
    """Contract tests for complex tier generation."""

    def test_load_moderate_tiers(self, tmp_path):
        """Test loading moderate tiers from CSV."""
        # Create a test moderate tiers file
        test_data = [
            {'interaction_id': '1', 'text': 'This is a simple sentence.'},
            {'interaction_id': '2', 'text': 'Another example text here.'}
        ]
        
        input_file = tmp_path / "moderate_tiers.csv"
        df = pd.DataFrame(test_data)
        df.to_csv(input_file, index=False)
        
        # Load and verify
        tiers = load_moderate_tiers(str(input_file))
        assert len(tiers) == 2
        assert tiers[0]['interaction_id'] == '1'
        assert tiers[1]['text'] == 'Another example text here.'

    def test_generate_complex_tier_fk_increase(self):
        """Test that complex tier has increased Flesch-Kincaid score."""
        moderate_text = "The student solved the problem correctly."
        
        complex_text, metrics = generate_complex_tier(moderate_text)
        
        # Verify FK increase
        assert metrics['fk_difference'] >= MIN_FK_DIFFERENCE, \
            f"FK difference {metrics['fk_difference']:.2f} should be >= {MIN_FK_DIFFERENCE}"
        assert metrics['complex_fk'] > metrics['moderate_fk']

    def test_generate_complex_tier_jaccard_similarity(self):
        """Test that complex tier maintains high Jaccard similarity."""
        moderate_text = "The algorithm efficiently processes the data structure."
        
        complex_text, metrics = generate_complex_tier(moderate_text)
        
        # Verify Jaccard similarity
        assert metrics['jaccard_similarity'] >= MIN_JACCARD_SIMILARITY, \
            f"Jaccard similarity {metrics['jaccard_similarity']:.2f} should be >= {MIN_JACCARD_SIMILARITY}"

    def test_generate_complex_tiers_batch(self, tmp_path):
        """Test generating complex tiers for multiple items."""
        # Create test data
        moderate_tiers = [
            {'interaction_id': '1', 'text': 'Simple text one.'},
            {'interaction_id': '2', 'text': 'Simple text two.'},
            {'interaction_id': '3', 'text': 'Simple text three.'}
        ]
        
        output_file = tmp_path / "complex_tiers.csv"
        
        # Generate complex tiers
        results = generate_complex_tiers(moderate_tiers, str(output_file))
        
        # Verify output file exists and has correct structure
        assert output_file.exists()
        assert len(results) == 3
        
        # Verify each result has required fields
        for result in results:
            assert 'interaction_id' in result
            assert 'complex_text' in result
            assert 'complex_fk' in result
            assert 'fk_difference' in result
            assert 'jaccard_similarity' in result

    def test_save_complex_tiers(self, tmp_path):
        """Test saving complex tiers to CSV."""
        results = [
            {
                'interaction_id': '1',
                'original_text': 'Original',
                'moderate_text': 'Moderate',
                'complex_text': 'Complex',
                'moderate_fk': 5.0,
                'complex_fk': 10.0,
                'fk_difference': 5.0,
                'jaccard_similarity': 0.9
            }
        ]
        
        output_file = tmp_path / "complex_tiers.csv"
        save_complex_tiers(results, str(output_file))
        
        # Verify file exists and can be read
        assert output_file.exists()
        df = pd.read_csv(output_file)
        assert len(df) == 1
        assert df['interaction_id'].iloc[0] == '1'
        assert df['complex_text'].iloc[0] == 'Complex'

    def test_complex_tier_constraints_validation(self):
        """Test that generated tiers meet all constraints."""
        moderate_text = "The learning process involves multiple cognitive stages."
        
        complex_text, metrics = generate_complex_tier(moderate_text)
        
        # Verify both constraints are met
        assert metrics['fk_difference'] >= MIN_FK_DIFFERENCE
        assert metrics['jaccard_similarity'] >= MIN_JACCARD_SIMILARITY
        assert metrics['complex_fk'] > metrics['moderate_fk']
        
        # Verify Flesch-Kincaid calculation is correct
        calculated_fk = calculate_flesch_kincaid(complex_text)
        assert abs(calculated_fk - metrics['complex_fk']) < 0.01
