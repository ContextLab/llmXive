import pytest
import numpy as np
from src.entities import RecommendationPath
from src.path_generator import apply_src, apply_psa

class TestSRC:
    """Unit tests for Stepwise Reward Centering (SRC)"""

    def test_src_basic_calculation(self):
        """Test that SRC correctly subtracts the batch mean from each score."""
        # Create two paths with known scores
        path1 = RecommendationPath(
            items=["A", "B", "C"],
            raw_scores=[10.0, 20.0, 30.0],
            source="test"
        )
        path2 = RecommendationPath(
            items=["D", "E", "F"],
            raw_scores=[10.0, 20.0, 30.0],
            source="test"
        )
        
        # Mean at pos 0: (10+10)/2 = 10 -> rectified: 0
        # Mean at pos 1: (20+20)/2 = 20 -> rectified: 0
        # Mean at pos 2: (30+30)/2 = 30 -> rectified: 0
        paths = [path1, path2]
        rectified = apply_src(paths)
        
        expected_scores = [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0]
        ]
        
        for i, p in enumerate(rectified):
            assert np.allclose(p.raw_scores, expected_scores[i])

    def test_src_uneven_batch(self):
        """Test SRC with paths of different lengths and values."""
        path1 = RecommendationPath(
            items=["A", "B"],
            raw_scores=[10.0, 20.0],
            source="test"
        )
        path2 = RecommendationPath(
            items=["C", "D", "E"],
            raw_scores=[30.0, 40.0, 50.0],
            source="test"
        )
        
        paths = [path1, path2]
        rectified = apply_src(paths)
        
        # Pos 0: Mean = (10 + 30)/2 = 20. Scores: [10-20, 30-20] = [-10, 10]
        # Pos 1: Mean = (20 + 40)/2 = 30. Scores: [20-30, 40-30] = [-10, 10]
        # Pos 2: Mean = 50 (only one path). Score: [50-50] = [0]
        
        assert np.isclose(rectified[0].raw_scores[0], -10.0)
        assert np.isclose(rectified[0].raw_scores[1], -10.0)
        
        assert np.isclose(rectified[1].raw_scores[0], 10.0)
        assert np.isclose(rectified[1].raw_scores[1], 10.0)
        assert np.isclose(rectified[1].raw_scores[2], 0.0)

    def test_src_empty_list(self):
        """Test that apply_src handles empty input gracefully."""
        result = apply_src([])
        assert result == []

class TestPSA:
    """Unit tests for Position-Specific Advantage (PSA)"""

    def test_psa_basic_calculation(self):
        """Test that PSA correctly applies position weighting."""
        # Input scores after SRC: [0, 0, 0]
        # Alpha = 0.1
        # Pos 0: 0 * (1 + 0.1*0) = 0
        # Pos 1: 0 * (1 + 0.1*1) = 0
        # Pos 2: 0 * (1 + 0.1*2) = 0
        # Let's use non-zero scores to verify
        path = RecommendationPath(
            items=["A", "B", "C"],
            raw_scores=[1.0, 1.0, 1.0],
            source="test"
        )
        
        alpha = 0.1
        result = apply_psa([path], alpha=alpha)
        
        # Expected:
        # Pos 0: 1.0 * (1 + 0) = 1.0
        # Pos 1: 1.0 * (1 + 0.1) = 1.1
        # Pos 2: 1.0 * (1 + 0.2) = 1.2
        expected = [1.0, 1.1, 1.2]
        
        assert np.allclose(result[0].raw_scores, expected)

    def test_psa_zero_alpha(self):
        """Test PSA with alpha=0 (no change)."""
        path = RecommendationPath(
            items=["A", "B"],
            raw_scores=[5.0, 10.0],
            source="test"
        )
        
        result = apply_psa([path], alpha=0.0)
        
        assert np.allclose(result[0].raw_scores, [5.0, 10.0])

    def test_psa_uneven_lengths(self):
        """Test PSA with paths of different lengths."""
        path1 = RecommendationPath(
            items=["A", "B"],
            raw_scores=[1.0, 1.0],
            source="test"
        )
        path2 = RecommendationPath(
            items=["C", "D", "E"],
            raw_scores=[1.0, 1.0, 1.0],
            source="test"
        )
        
        alpha = 0.5
        result = apply_psa([path1, path2], alpha=alpha)
        
        # Path 1: [1*(1+0), 1*(1+0.5)] = [1.0, 1.5]
        # Path 2: [1*(1+0), 1*(1+0.5), 1*(1+1.0)] = [1.0, 1.5, 2.0]
        assert np.allclose(result[0].raw_scores, [1.0, 1.5])
        assert np.allclose(result[1].raw_scores, [1.0, 1.5, 2.0])
