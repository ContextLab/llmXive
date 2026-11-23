import pytest
import os
import sys
from pathlib import Path
import csv
import pandas as pd

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from generate_complex_tier import (
    load_moderate_tiers,
    insert_jargon,
    increase_complexity,
    generate_complex_tier,
    generate_complex_tiers
)
from utils import calculate_flesch_kincaid, calculate_jaccard_similarity

class TestComplexTierGenerationContract:
    """Contract tests for complex tier generation."""

    def test_load_moderate_tiers_file_exists(self):
        """Test that load_moderate_tiers raises error if file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_moderate_tiers("non_existent_file.csv")

    def test_insert_jargon_replaces_words(self):
        """Test that insert_jargon replaces common words with jargon."""
        text = "The user can understand the concept."
        result = insert_jargon(text, jargon_density=1.0)
        
        # Should contain jargon replacements
        assert "operator" in result.lower() or "utilize" in result.lower() or \
               "comprehend" in result.lower() or "construct" in result.lower()

    def test_increase_complexity_adds_clauses(self):
        """Test that increase_complexity adds subordinate clauses."""
        text = "The student learns the material."
        result = increase_complexity(text, nesting_depth=1)
        
        # Should contain introductory clause markers
        assert any(marker in result for marker in [
            "Given that", "Considering that", "In light of", "Due to"
        ])

    def test_generate_complex_tier_meets_fk_diff(self):
        """Test that generate_complex_tier achieves target FK difference."""
        moderate_text = "The student can understand the concept and learn the material."
        
        complex_text, iterations = generate_complex_tier(
            moderate_text, 
            target_fk_diff=5.0, 
            min_jaccard=0.85, 
            max_iterations=10
        )
        
        moderate_fk = calculate_flesch_kincaid(moderate_text)
        complex_fk = calculate_flesch_kincaid(complex_text)
        
        assert complex_fk - moderate_fk >= 5.0, \
            f"FK difference {complex_fk - moderate_fk:.2f} < 5.0"

    def test_generate_complex_tier_meets_jaccard(self):
        """Test that generate_complex_tier maintains Jaccard similarity."""
        moderate_text = "The student can understand the concept and learn the material."
        
        complex_text, iterations = generate_complex_tier(
            moderate_text, 
            target_fk_diff=5.0, 
            min_jaccard=0.85, 
            max_iterations=10
        )
        
        jaccard = calculate_jaccard_similarity(moderate_text, complex_text)
        
        assert jaccard >= 0.85, f"Jaccard similarity {jaccard:.2f} < 0.85"

    def test_generate_complex_tiers_creates_csv(self, tmp_path):
        """Test that generate_complex_tiers creates output CSV."""
        # Create sample moderate tiers
        sample_data = [
            {'interaction_id': '1', 'moderate_tier': 'The student learns the concept.'},
            {'interaction_id': '2', 'moderate_tier': 'The user understands the material.'}
        ]
        
        output_path = tmp_path / "complex_tiers.csv"
        
        results = generate_complex_tiers(
            sample_data,
            str(output_path),
            target_fk_diff=5.0,
            min_jaccard=0.85,
            max_iterations=10
        )
        
        assert output_path.exists(), "Output CSV file was not created"
        
        # Verify CSV structure
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == len(sample_data), "Row count mismatch"
        assert 'complex_tier' in rows[0], "Missing complex_tier column"
        assert 'status' in rows[0], "Missing status column"

    def test_generate_complex_tier_raises_on_failure(self):
        """Test that generate_complex_tier raises ValueError when constraints can't be met."""
        # Use very short text that might be hard to complexify
        short_text = "OK."
        
        with pytest.raises(ValueError):
            generate_complex_tier(
                short_text,
                target_fk_diff=5.0,
                min_jaccard=0.85,
                max_iterations=2  # Low iteration count to force failure
            )

    def test_iterative_refinement_terminates(self):
        """Test that iterative refinement terminates within max_iterations."""
        moderate_text = "The student can understand the concept and learn the material."
        
        complex_text, iterations = generate_complex_tier(
            moderate_text,
            target_fk_diff=5.0,
            min_jaccard=0.85,
            max_iterations=10
        )
        
        assert iterations <= 10, f"Exceeded max iterations: {iterations}"
        assert iterations >= 1, f"Invalid iteration count: {iterations}"

    def test_output_contains_required_columns(self, tmp_path):
        """Test that output CSV contains all required columns."""
        sample_data = [
            {'interaction_id': '1', 'moderate_tier': 'Test text.'}
        ]
        
        output_path = tmp_path / "complex_tiers.csv"
        
        generate_complex_tiers(
            sample_data,
            str(output_path),
            target_fk_diff=5.0,
            min_jaccard=0.85,
            max_iterations=10
        )
        
        df = pd.read_csv(output_path)
        
        required_columns = ['interaction_id', 'moderate_tier', 'complex_tier', 
                          'iterations_used', 'status']
        
        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"