"""
Tests for T016: Semantic Similarity Computation
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.data.compute_similarity import (
    compute_cosine_similarity,
    load_ingredient_pairs,
    load_embeddings,
    process_similarity
)

class TestCosineSimilarity:
    def test_identical_vectors(self):
        v1 = np.array([1.0, 2.0, 3.0])
        v2 = np.array([1.0, 2.0, 3.0])
        assert np.isclose(compute_cosine_similarity(v1, v2), 1.0)

    def test_orthogonal_vectors(self):
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([0.0, 1.0, 0.0])
        assert np.isclose(compute_cosine_similarity(v1, v2), 0.0)

    def test_opposite_vectors(self):
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([-1.0, 0.0, 0.0])
        assert np.isclose(compute_cosine_similarity(v1, v2), -1.0)

    def test_zero_vector(self):
        v1 = np.array([0.0, 0.0, 0.0])
        v2 = np.array([1.0, 2.0, 3.0])
        assert compute_cosine_similarity(v1, v2) == 0.0

class TestPairGeneration:
    def test_pair_count(self):
        # Create a temporary directory and file for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock unique_ingredients.parquet
            mock_data = pd.DataFrame({'ingredient_id': ['a', 'b', 'c']})
            mock_path = Path(tmpdir) / "unique_ingredients.parquet"
            mock_data.to_parquet(mock_path)
            
            # Temporarily override the DATA_DIR path in the module
            import code.data.compute_similarity as sim_module
            original_path = sim_module.PROCESSED_DIR
            sim_module.PROCESSED_DIR = Path(tmpdir)
            
            try:
                df = load_ingredient_pairs()
                # For 3 items, we expect 3 pairs: (a,b), (a,c), (b,c)
                assert len(df) == 3
                assert list(df.columns) == ['ingredient_id_1', 'ingredient_id_2']
            finally:
                sim_module.PROCESSED_DIR = original_path

class TestEmbeddingLoading:
    def test_load_embeddings_dict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock ingredient_embeddings.parquet
            data = {
                'ingredient_id': ['x', 'y'],
                'emb_0': [0.1, 0.4],
                'emb_1': [0.2, 0.5],
                'emb_2': [0.3, 0.6]
            }
            mock_df = pd.DataFrame(data)
            mock_path = Path(tmpdir) / "ingredient_embeddings.parquet"
            mock_df.to_parquet(mock_path)
            
            import code.data.compute_similarity as sim_module
            original_path = sim_module.PROCESSED_DIR
            sim_module.PROCESSED_DIR = Path(tmpdir)
            
            try:
                emb_dict = load_embeddings()
                assert 'x' in emb_dict
                assert 'y' in emb_dict
                assert len(emb_dict['x']) == 3
                assert np.allclose(emb_dict['x'], [0.1, 0.2, 0.3])
            finally:
                sim_module.PROCESSED_DIR = original_path

class TestIntegration:
    def test_end_to_end_similarity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup mock data
            # 1. Unique ingredients
            ingredients_df = pd.DataFrame({'ingredient_id': ['a', 'b']})
            ingredients_path = Path(tmpdir) / "unique_ingredients.parquet"
            ingredients_df.to_parquet(ingredients_path)
            
            # 2. Embeddings (orthogonal vectors for easy checking)
            embeddings_df = pd.DataFrame({
                'ingredient_id': ['a', 'b'],
                'emb_0': [1.0, 0.0],
                'emb_1': [0.0, 1.0]
            })
            embeddings_path = Path(tmpdir) / "ingredient_embeddings.parquet"
            embeddings_df.to_parquet(embeddings_path)
            
            import code.data.compute_similarity as sim_module
            original_path = sim_module.PROCESSED_DIR
            sim_module.PROCESSED_DIR = Path(tmpdir)
            
            try:
                pairs = load_ingredient_pairs()
                emb_dict = load_embeddings()
                result_df = process_similarity(pairs, emb_dict)
                
                assert len(result_df) == 1
                assert result_df.iloc[0]['ingredient_id_1'] == 'a'
                assert result_df.iloc[0]['ingredient_id_2'] == 'b'
                # Cosine similarity of orthogonal vectors should be 0
                assert np.isclose(result_df.iloc[0]['similarity_score'], 0.0)
            finally:
                sim_module.PROCESSED_DIR = original_path
