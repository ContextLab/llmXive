import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.generate_complex_tier import (
    load_moderate_tiers,
    generate_complex_tiers,
    MIN_FK_DIFFERENCE,
    MIN_JACCARD_SIMILARITY
)
from code.utils import calculate_flesch_kincaid, calculate_jaccard_similarity

class TestTierGenerationIntegration:
    """Integration tests for tier generation pipeline."""

    def test_full_complex_tier_generation_pipeline(self, tmp_path):
        """Test the complete complex tier generation pipeline."""
        # Create sample moderate tiers
        moderate_data = [
            {'interaction_id': 'test_001', 'text': 'The student completed the exercise.'},
            {'interaction_id': 'test_002', 'text': 'Understanding the concept requires practice.'},
            {'interaction_id': 'test_003', 'text': 'The algorithm processes data efficiently.'}
        ]
        
        moderate_file = tmp_path / "moderate_tiers.csv"
        pd.DataFrame(moderate_data).to_csv(moderate_file, index=False)
        
        output_file = tmp_path / "complex_tiers.csv"
        
        # Run generation
        results = generate_complex_tiers(
            load_moderate_tiers(str(moderate_file)),
            str(output_file)
        )
        
        # Verify output file exists
        assert output_file.exists()
        
        # Load and verify results
        df = pd.read_csv(output_file)
        assert len(df) == 3
        
        # Verify each tier meets constraints
        for _, row in df.iterrows():
            fk_diff = row['fk_difference']
            jaccard = row['jaccard_similarity']
            
            # Check FK difference
            assert fk_diff >= MIN_FK_DIFFERENCE, \
                f"FK difference {fk_diff:.2f} < {MIN_FK_DIFFERENCE} for {row['interaction_id']}"
            
            # Check Jaccard similarity
            assert jaccard >= MIN_JACCARD_SIMILARITY, \
                f"Jaccard {jaccard:.2f} < {MIN_JACCARD_SIMILARITY} for {row['interaction_id']}"
            
            # Verify FK calculation
            calculated_fk = calculate_flesch_kincaid(row['complex_text'])
            assert abs(calculated_fk - row['complex_fk']) < 0.1, \
                f"FK mismatch for {row['interaction_id']}: {calculated_fk} vs {row['complex_fk']}"

    def test_tier_progression_monotonicity(self, tmp_path):
        """Test that simple < moderate < complex in terms of FK scores."""
        # Create moderate tiers
        moderate_data = [
            {'interaction_id': 'prog_001', 'text': 'Basic concept explanation.'}
        ]
        
        moderate_file = tmp_path / "moderate_tiers.csv"
        pd.DataFrame(moderate_data).to_csv(moderate_file, index=False)
        
        # Generate complex tiers
        complex_results = generate_complex_tiers(
            load_moderate_tiers(str(moderate_file)),
            str(tmp_path / "complex_tiers.csv")
        )
        
        # Verify monotonic progression
        for result in complex_results:
            moderate_fk = result['moderate_fk']
            complex_fk = result['complex_fk']
            
            assert complex_fk > moderate_fk, \
                f"Complex FK {complex_fk} should be > Moderate FK {moderate_fk}"
            
            # Verify difference meets threshold
            assert (complex_fk - moderate_fk) >= MIN_FK_DIFFERENCE, \
                f"FK difference {(complex_fk - moderate_fk):.2f} < {MIN_FK_DIFFERENCE}"

    def test_large_batch_processing(self, tmp_path):
        """Test processing a larger batch of tiers."""
        # Create 10 moderate tiers
        moderate_data = [
            {'interaction_id': f'batch_{i:03d}', 'text': f'Sample text number {i} for testing.'}
            for i in range(10)
        ]
        
        moderate_file = tmp_path / "moderate_tiers.csv"
        pd.DataFrame(moderate_data).to_csv(moderate_file, index=False)
        
        output_file = tmp_path / "complex_tiers.csv"
        
        # Generate complex tiers
        results = generate_complex_tiers(
            load_moderate_tiers(str(moderate_file)),
            str(output_file)
        )
        
        # Verify all tiers processed
        assert len(results) == 10
        
        # Verify output file
        df = pd.read_csv(output_file)
        assert len(df) == 10
        
        # Verify constraints for all
        for _, row in df.iterrows():
            assert row['fk_difference'] >= MIN_FK_DIFFERENCE
            assert row['jaccard_similarity'] >= MIN_JACCARD_SIMILARITY

    def test_error_handling_in_pipeline(self, tmp_path):
        """Test error handling when processing invalid data."""
        # Create moderate tiers with empty text
        moderate_data = [
            {'interaction_id': 'err_001', 'text': ''},
            {'interaction_id': 'err_002', 'text': 'Valid text here.'}
        ]
        
        moderate_file = tmp_path / "moderate_tiers.csv"
        pd.DataFrame(moderate_data).to_csv(moderate_file, index=False)
        
        output_file = tmp_path / "complex_tiers.csv"
        
        # Should handle empty text gracefully
        results = generate_complex_tiers(
            load_moderate_tiers(str(moderate_file)),
            str(output_file)
        )
        
        # Verify we still get results
        assert len(results) == 2
        
        # Verify valid text was processed
        valid_result = next(r for r in results if r['interaction_id'] == 'err_002')
        assert valid_result['complex_text'] != ''
        assert valid_result['fk_difference'] >= MIN_FK_DIFFERENCE
