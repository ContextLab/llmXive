"""
Tests for compute_similarity.py (T016).
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.compute_similarity import (
    compute_cosine_similarity,
    process_similarity,
    load_ingredient_pairs,
    load_embeddings
)


class TestCosineSimilarity:
    """Unit tests for cosine similarity computation."""

    def test_identical_vectors(self):
        """Test that identical vectors have similarity 1.0."""
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([1.0, 2.0, 3.0])
        sim = compute_cosine_similarity(vec1, vec2)
        assert np.isclose(sim, 1.0)

    def test_orthogonal_vectors(self):
        """Test that orthogonal vectors have similarity 0.0."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])
        sim = compute_cosine_similarity(vec1, vec2)
        assert np.isclose(sim, 0.0)

    def test_opposite_vectors(self):
        """Test that opposite vectors have similarity -1.0."""
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([-1.0, -2.0, -3.0])
        sim = compute_cosine_similarity(vec1, vec2)
        assert np.isclose(sim, -1.0)

    def test_different_scales(self):
        """Test that scale doesn't affect similarity."""
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([2.0, 4.0, 6.0])  # 2x vec1
        sim = compute_cosine_similarity(vec1, vec2)
        assert np.isclose(sim, 1.0)

    def test_none_inputs(self):
        """Test handling of None inputs."""
        vec1 = np.array([1.0, 2.0, 3.0])
        sim = compute_cosine_similarity(vec1, None)
        assert np.isnan(sim)

        sim = compute_cosine_similarity(None, vec1)
        assert np.isnan(sim)

        sim = compute_cosine_similarity(None, None)
        assert np.isnan(sim)

    def test_zero_vectors(self):
        """Test handling of zero vectors."""
        vec1 = np.array([0.0, 0.0, 0.0])
        vec2 = np.array([1.0, 2.0, 3.0])
        sim = compute_cosine_similarity(vec1, vec2)
        assert sim == 0.0  # Defined as 0 for zero vectors

    def test_list_input(self):
        """Test handling of list inputs."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0, 3.0]
        sim = compute_cosine_similarity(vec1, vec2)
        assert np.isclose(sim, 1.0)


class TestProcessSimilarity:
    """Integration tests for process_similarity function."""

    @pytest.fixture
    def sample_pairs(self):
        """Create sample ingredient pairs."""
        return pd.DataFrame({
            'ingredient_1': ['salt', 'sugar', 'flour', 'missing_1'],
            'ingredient_2': ['pepper', 'honey', 'rice', 'missing_2']
        })

    @pytest.fixture
    def sample_embeddings(self):
        """Create sample embeddings."""
        return pd.DataFrame({
            'ingredient': ['salt', 'sugar', 'flour', 'pepper', 'honey', 'rice'],
            'embedding_vec': [
                np.array([1.0, 0.0, 0.0]),
                np.array([0.0, 1.0, 0.0]),
                np.array([0.0, 0.0, 1.0]),
                np.array([1.0, 0.0, 0.0]),  # Same as salt
                np.array([0.0, 1.0, 0.0]),  # Same as sugar
                np.array([0.0, 0.0, 1.0])   # Same as flour
            ]
        })

    def test_compute_similarities(self, sample_pairs, sample_embeddings):
        """Test that similarities are computed correctly."""
        log_events = []
        result_df = process_similarity(sample_pairs, sample_embeddings, log_events)
        
        # Check output structure
        assert 'cosine_similarity' in result_df.columns
        assert 'status' in result_df.columns
        assert len(result_df) == len(sample_pairs)
        
        # Check specific values
        # salt vs pepper: [1,0,0] vs [1,0,0] -> 1.0
        salt_pepper = result_df[(result_df['ingredient_1'] == 'salt') & 
                                (result_df['ingredient_2'] == 'pepper')]
        assert len(salt_pepper) == 1
        assert np.isclose(salt_pepper.iloc[0]['cosine_similarity'], 1.0)
        
        # sugar vs honey: [0,1,0] vs [0,1,0] -> 1.0
        sugar_honey = result_df[(result_df['ingredient_1'] == 'sugar') & 
                                (result_df['ingredient_2'] == 'honey')]
        assert len(sugar_honey) == 1
        assert np.isclose(sugar_honey.iloc[0]['cosine_similarity'], 1.0)
        
        # flour vs rice: [0,0,1] vs [0,0,1] -> 1.0
        flour_rice = result_df[(result_df['ingredient_1'] == 'flour') & 
                               (result_df['ingredient_2'] == 'rice')]
        assert len(flour_rice) == 1
        assert np.isclose(flour_rice.iloc[0]['cosine_similarity'], 1.0)
        
        # missing_1 vs missing_2: should be NaN
        missing_row = result_df[(result_df['ingredient_1'] == 'missing_1') & 
                                (result_df['ingredient_2'] == 'missing_2')]
        assert len(missing_row) == 1
        assert np.isnan(missing_row.iloc[0]['cosine_similarity'])
        assert missing_row.iloc[0]['status'] == 'missing_embedding'
        
        # Check log events
        assert len(log_events) > 0
        assert any(e['event'] == 'similarity_computation_complete' for e in log_events)

    def test_empty_pairs(self, sample_embeddings):
        """Test handling of empty pairs dataframe."""
        empty_pairs = pd.DataFrame(columns=['ingredient_1', 'ingredient_2'])
        log_events = []
        result_df = process_similarity(empty_pairs, sample_embeddings, log_events)
        
        assert len(result_df) == 0
        assert 'cosine_similarity' in result_df.columns

    def test_no_embeddings(self, sample_pairs):
        """Test handling when no embeddings are found."""
        empty_embeddings = pd.DataFrame(columns=['ingredient', 'embedding_vec'])
        log_events = []
        result_df = process_similarity(sample_pairs, empty_embeddings, log_events)
        
        # All should be NaN
        assert result_df['cosine_similarity'].isna().all()
        assert all(result_df['status'] == 'missing_embedding')