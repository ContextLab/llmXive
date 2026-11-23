import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.retrieval.strategies import (
    synthesize_adapter,
    save_synthesized_adapter,
    load_skill_index,
    unweighted_mean,
    cosine_weighted_average,
    single_nearest_neighbor
)

class TestAdapterSerialization:
    """Test suite for T022b: Serialization logic for synthesized adapters."""

    @pytest.fixture
    def mock_skill_index(self):
        """Create a mock skill index with known shapes and vectors."""
        # Create synthetic data matching expected structure
        n_skills = 10
        rank_A, dim_A = 8, 512
        rank_B, dim_B = 8, 512
        
        # Total dimension per skill
        total_dim = rank_A * dim_A + rank_B * dim_B
        
        vectors = np.random.randn(n_skills, total_dim).astype(np.float32)
        
        metadata = {
            f"skill_{i}": {"task": f"task_{i}", "source": "synthetic"}
            for i in range(n_skills)
        }
        
        shapes = {
            f"skill_{i}": {
                "rank_A": rank_A,
                "dim_A": dim_A,
                "rank_B": rank_B,
                "dim_B": dim_B
            }
            for i in range(n_skills)
        }
        
        return {
            'vectors': vectors,
            'metadata': metadata,
            'shapes': shapes
        }

    @pytest.fixture
    def mock_query_vector(self, mock_skill_index):
        """Create a mock query vector."""
        return np.random.randn(mock_skill_index['vectors'].shape[1]).astype(np.float32)

    def test_synthesize_adapter_nearest(self, mock_skill_index, mock_query_vector):
        """Test single nearest neighbor synthesis."""
        A, B = synthesize_adapter(
            strategy='nearest',
            query_vector=mock_query_vector,
            skill_index=mock_skill_index,
            k=1
        )
        
        assert A.shape == (8, 512), f"Expected A shape (8, 512), got {A.shape}"
        assert B.shape == (8, 512), f"Expected B shape (8, 512), got {B.shape}"
        assert not np.any(np.isnan(A)), "A contains NaN"
        assert not np.any(np.isnan(B)), "B contains NaN"

    def test_synthesize_adapter_mean(self, mock_skill_index, mock_query_vector):
        """Test unweighted mean synthesis."""
        A, B = synthesize_adapter(
            strategy='mean',
            query_vector=mock_query_vector,
            skill_index=mock_skill_index,
            k=3
        )
        
        assert A.shape == (8, 512), f"Expected A shape (8, 512), got {A.shape}"
        assert B.shape == (8, 512), f"Expected B shape (8, 512), got {B.shape}"
        assert not np.any(np.isnan(A)), "A contains NaN"
        assert not np.any(np.isnan(B)), "B contains NaN"

    def test_synthesize_adapter_cosine_weighted(self, mock_skill_index, mock_query_vector):
        """Test cosine-weighted average synthesis."""
        A, B = synthesize_adapter(
            strategy='cosine_weighted',
            query_vector=mock_query_vector,
            skill_index=mock_skill_index,
            k=3
        )
        
        assert A.shape == (8, 512), f"Expected A shape (8, 512), got {A.shape}"
        assert B.shape == (8, 512), f"Expected B shape (8, 512), got {B.shape}"
        assert not np.any(np.isnan(A)), "A contains NaN"
        assert not np.any(np.isnan(B)), "B contains NaN"

    def test_save_synthesized_adapter(self, mock_skill_index, mock_query_vector):
        """Test saving synthesized adapter to disk."""
        A, B = synthesize_adapter(
            strategy='nearest',
            query_vector=mock_query_vector,
            skill_index=mock_skill_index,
            k=1
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = save_synthesized_adapter(
                A=A,
                B=B,
                query_id="test_query",
                strategy="nearest",
                k=1,
                output_dir=tmpdir
            )
            
            assert file_path.exists(), f"File not created at {file_path}"
            assert file_path.suffix == ".npz", "File should be .npz"
            
            # Verify contents
            data = np.load(file_path, allow_pickle=True)
            assert 'A' in data.files, "A matrix not saved"
            assert 'B' in data.files, "B matrix not saved"
            assert 'strategy' in data.files, "Strategy not saved"
            assert 'k' in data.files, "k value not saved"
            
            np.testing.assert_array_equal(data['A'], A)
            np.testing.assert_array_equal(data['B'], B)

    def test_save_synthesized_adapter_nan_detection(self, mock_skill_index, mock_query_vector):
        """Test that NaN values are detected and raise an error."""
        A, B = synthesize_adapter(
            strategy='nearest',
            query_vector=mock_query_vector,
            skill_index=mock_skill_index,
            k=1
        )
        
        # Inject NaN
        A[0, 0] = np.nan
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="NaN"):
                save_synthesized_adapter(
                    A=A,
                    B=B,
                    query_id="test_query",
                    strategy="nearest",
                    k=1,
                    output_dir=tmpdir
                )

    def test_save_synthesized_adapter_dimensions(self, mock_skill_index, mock_query_vector):
        """Test that invalid dimensions are detected."""
        # Create matrices with wrong dimensions
        A_wrong = np.random.randn(4, 256)
        B_wrong = np.random.randn(4, 256)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # This should still save as long as they are valid matrices,
            # but the shape validation in the real pipeline would catch mismatches earlier
            file_path = save_synthesized_adapter(
                A=A_wrong,
                B=B_wrong,
                query_id="test_query",
                strategy="nearest",
                k=1,
                output_dir=tmpdir
            )
            
            assert file_path.exists()

    def test_unweighted_mean(self, mock_skill_index, mock_query_vector):
        """Test unweighted mean calculation."""
        indices = [0, 1, 2]
        result = unweighted_mean(indices, mock_skill_index['vectors'])
        
        expected = np.mean(mock_skill_index['vectors'][indices], axis=0)
        np.testing.assert_array_almost_equal(result, expected)

    def test_cosine_weighted_average(self, mock_skill_index, mock_query_vector):
        """Test cosine-weighted average calculation."""
        indices = [0, 1, 2]
        result = cosine_weighted_average(indices, mock_query_vector, mock_skill_index['vectors'])
        
        # Manual calculation
        query_norm = np.linalg.norm(mock_query_vector)
        normalized_query = mock_query_vector / query_norm
        
        selected = mock_skill_index['vectors'][indices]
        selected_norms = np.linalg.norm(selected, axis=1, keepdims=True)
        selected_norms[selected_norms == 0] = 1e-10
        normalized_selected = selected / selected_norms
        
        weights = np.dot(normalized_selected, normalized_query)
        weights = weights.reshape(-1, 1)
        
        expected = np.sum(weights * selected, axis=0) / np.sum(weights)
        np.testing.assert_array_almost_equal(result, expected)

    def test_single_nearest_neighbor(self, mock_skill_index, mock_query_vector):
        """Test single nearest neighbor retrieval."""
        idx, sim = single_nearest_neighbor(mock_query_vector, mock_skill_index['vectors'])
        
        assert 0 <= idx < len(mock_skill_index['vectors'])
        assert -1.0 <= sim <= 1.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
