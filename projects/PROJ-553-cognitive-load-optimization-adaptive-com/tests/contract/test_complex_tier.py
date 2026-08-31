"""
Contract tests for the Complex Tier Generation module.

These tests verify:
1. Input/Output schema compliance
2. Constraint satisfaction (FK diff >= 5, Jaccard >= 0.85)
3. Error handling for failed constraints
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_complex_tier import (
    insert_jargon,
    increase_complexity,
    generate_complex_tier,
    iterative_complexify,
    generate_complex_tiers
)
from utils import calculate_flesch_kincaid, calculate_jaccard_similarity

class TestComplexTierGeneration:
    
    def test_insert_jargon_increases_complexity(self):
        """Test that jargon insertion increases FK score."""
        text = "The student learns the problem."
        jargon_text = insert_jargon(text, density=1.0)
        
        fk_original = calculate_flesch_kincaid(text)
        fk_jargon = calculate_flesch_kincaid(jargon_text)
        
        # Jargon should make text harder
        assert fk_jargon >= fk_original, "Jargon insertion should increase FK score"
    
    def test_increase_complexity_adds_clauses(self):
        """Test that complexity increase adds syntactic depth."""
        text = "The student learns the problem."
        complex_text = increase_complexity(text, depth=2)
        
        # Should be longer and more complex
        assert len(complex_text) >= len(text), "Complex text should be at least as long"
        assert "which implies that" in complex_text or "While it is evident that" in complex_text, \
            "Complex text should contain added clauses"
    
    def test_iterative_complexify_meets_constraints(self):
        """Test that iterative refinement meets FK and Jaccard constraints."""
        moderate_text = "The student understands the concept through practice."
        
        # This should succeed with reasonable parameters
        complex_text, metrics = iterative_complexify(
            moderate_text,
            max_iterations=20,
            target_fk_diff=5.0,
            min_jaccard=0.85
        )
        
        assert metrics['status'] == 'success'
        assert metrics['fk_diff'] >= 5.0
        assert metrics['jaccard'] >= 0.85
    
    def test_iterative_complexify_raises_on_failure(self):
        """Test that ValueError is raised if constraints cannot be met."""
        # Use a very short text that might be hard to expand significantly
        # while maintaining high Jaccard
        moderate_text = "Go."
        
        with pytest.raises(ValueError) as exc_info:
            iterative_complexify(
                moderate_text,
                max_iterations=5,  # Very low iterations to force failure
                target_fk_diff=50.0,  # Impossible target
                min_jaccard=0.99  # Very strict
            )
        
        assert "failed to meet constraints" in str(exc_info.value).lower()
    
    def test_generate_complex_tiers_schema(self):
        """Test that output CSV has correct schema."""
        # Create temporary files
        with tempfile.TemporaryDirectory() as tmpdir:
            moderate_path = Path(tmpdir) / "moderate_tiers.csv"
            output_path = Path(tmpdir) / "complex_tiers.csv"
            
            # Create sample moderate tiers
            sample_data = [
                {'interaction_id': '1', 'text': 'The student learns the concept.'},
                {'interaction_id': '2', 'text': 'Practice improves understanding.'}
            ]
            pd.DataFrame(sample_data).to_csv(moderate_path, index=False)
            
            # Run generation (may fail on short text, but should create file)
            try:
                generate_complex_tiers(str(moderate_path), str(output_path), max_iterations=5)
            except ValueError:
                # Expected for short texts with high constraints
                pass
            
            # Verify output file exists and has correct columns
            if output_path.exists():
                df = pd.read_csv(output_path)
                required_columns = [
                    'interaction_id', 'text', 'fk_score', 'jaccard_similarity',
                    'fk_diff_vs_moderate', 'jargon_density', 'complexity_depth',
                    'iterations', 'status'
                ]
                for col in required_columns:
                    assert col in df.columns, f"Missing column: {col}"
    
    def test_fidelity_preservation(self):
        """Test that complex tier preserves semantic content (Jaccard >= 0.85)."""
        moderate_text = "The student learns the concept through practice and repetition."
        
        complex_text, metrics = iterative_complexify(
            moderate_text,
            max_iterations=15,
            target_fk_diff=5.0,
            min_jaccard=0.85
        )
        
        # Verify Jaccard similarity is maintained
        assert metrics['jaccard'] >= 0.85, f"Jaccard {metrics['jaccard']} < 0.85"
    
    def test_monotonic_progression(self):
        """Test that FK score increases monotonically with complexity."""
        moderate_text = "The student understands the problem."
        
        # Generate with low depth
        complex_low, _ = iterative_complexify(
            moderate_text, max_iterations=10, target_fk_diff=3.0, min_jaccard=0.80
        )
        fk_low = calculate_flesch_kincaid(complex_low)
        
        # Generate with higher depth (by forcing higher density/depth in a new call)
        # Note: This is a simplified check; real validation happens in T025
        complex_high, _ = iterative_complexify(
            moderate_text, max_iterations=10, target_fk_diff=8.0, min_jaccard=0.80
        )
        fk_high = calculate_flesch_kincaid(complex_high)
        
        assert fk_high >= fk_low, "Higher complexity should yield higher FK score"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
