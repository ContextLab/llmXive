"""
Unit tests for entanglement_scores.py (T022a)

Tests per-sample statistical calculations:
- Variance
- Shannon Entropy
- Skewness
- Kurtosis
- Zero-variance edge cases
"""
import os
import sys
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from entanglement_scores import (
    calculate_entropy,
    compute_per_sample_stats,
    load_cleaned_data,
    extract_teacher_scores_matrix,
    integrate_features,
)

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

@pytest.fixture
def sample_df():
    """Create a sample DataFrame with teacher scores."""
    data = {
        "prompt": ["prompt1", "prompt2", "prompt3"],
        "image_url": ["url1", "url2", "url3"],
        "teacher_scores": [
            {"Alignment": 5.0, "Realism": 4.0, "Aesthetics": 3.0, "Plausibility": 2.0},
            {"Alignment": 4.0, "Realism": 4.0, "Aesthetics": 4.0, "Plausibility": 4.0},  # Zero variance
            {"Alignment": 1.0, "Realism": 5.0, "Aesthetics": 3.0, "Plausibility": 4.0},
        ],
        "primary_dimension": ["Alignment", "Realism", "Aesthetics"],
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_parquet_file(sample_df):
    """Create a temporary parquet file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        sample_df.to_parquet(f.name)
        yield f.name
    os.unlink(f.name)

# --------------------------------------------------------------------------
# Test Cases
# --------------------------------------------------------------------------

class TestCalculateEntropy:
    def test_uniform_distribution(self):
        """Uniform distribution should have maximum entropy."""
        probs = np.array([0.25, 0.25, 0.25, 0.25])
        entropy = calculate_entropy(probs)
        # Max entropy for 4 categories is log2(4) = 2
        assert abs(entropy - 2.0) < 1e-6

    def test_deterministic_distribution(self):
        """Single outcome should have zero entropy."""
        probs = np.array([1.0, 0.0, 0.0, 0.0])
        entropy = calculate_entropy(probs)
        assert entropy == 0.0

    def test_all_zeros(self):
        """All zeros should return zero entropy."""
        probs = np.array([0.0, 0.0, 0.0, 0.0])
        entropy = calculate_entropy(probs)
        assert entropy == 0.0

    def test_nan_handling(self):
        """NaN values should be handled gracefully."""
        probs = np.array([np.nan, 0.0, 0.0, 0.0])
        entropy = calculate_entropy(probs)
        assert entropy == 0.0

class TestComputePerSampleStats:
    def test_normal_case(self):
        """Test variance, entropy, skewness, kurtosis for normal data."""
        scores = np.array([
            [5.0, 4.0, 3.0, 2.0],
            [1.0, 5.0, 3.0, 4.0],
        ])
        variances, entropies, skewnesses, kurtoses = compute_per_sample_stats(scores)
        
        assert len(variances) == 2
        assert len(entropies) == 2
        assert len(skewnesses) == 2
        assert len(kurtoses) == 2
        
        # First row: [5, 4, 3, 2]
        # Mean = 3.5, Variance = ((1.5)^2 + (0.5)^2 + (-0.5)^2 + (-1.5)^2) / 4 = 5/4 = 1.25
        expected_var = 1.25
        assert abs(variances[0] - expected_var) < 1e-6

    def test_zero_variance(self):
        """Zero variance should result in zero entropy, skewness, kurtosis."""
        scores = np.array([
            [4.0, 4.0, 4.0, 4.0],
        ])
        variances, entropies, skewnesses, kurtoses = compute_per_sample_stats(scores)
        
        assert variances[0] == 0.0
        assert entropies[0] == 0.0
        assert skewnesses[0] == 0.0
        assert kurtoses[0] == 0.0

    def test_nan_handling(self):
        """NaN values should result in zero statistics."""
        scores = np.array([
            [np.nan, 4.0, 3.0, 2.0],
        ])
        variances, entropies, skewnesses, kurtoses = compute_per_sample_stats(scores)
        
        assert variances[0] == 0.0
        assert entropies[0] == 0.0
        assert skewnesses[0] == 0.0
        assert kurtoses[0] == 0.0

class TestLoadCleanedData:
    def test_load_valid_file(self, temp_parquet_file):
        """Should load a valid parquet file."""
        logger = type('Logger', (), {'info': lambda *args: None, 'warning': lambda *args: None})()
        df = load_cleaned_data(temp_parquet_file, logger)
        assert len(df) == 3
        assert "teacher_scores" in df.columns

    def test_missing_file(self):
        """Should raise FileNotFoundError for missing file."""
        logger = type('Logger', (), {'info': lambda *args: None, 'warning': lambda *args: None})()
        with pytest.raises(FileNotFoundError):
            load_cleaned_data("nonexistent.parquet", logger)

    def test_missing_columns(self, temp_parquet_file):
        """Should raise ValueError for missing required columns."""
        df = pd.DataFrame({"other_col": [1, 2, 3]})
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
            df.to_parquet(f.name)
            temp_path = f.name
        
        logger = type('Logger', (), {'info': lambda *args: None, 'warning': lambda *args: None})()
        with pytest.raises(ValueError):
            load_cleaned_data(temp_path, logger)
        os.unlink(temp_path)

class TestExtractTeacherScoresMatrix:
    def test_dict_format(self, sample_df):
        """Should extract scores from dict format."""
        logger = type('Logger', (), {'info': lambda *args: None, 'warning': lambda *args: None})()
        matrix = extract_teacher_scores_matrix(sample_df, logger)
        
        assert matrix.shape == (3, 4)
        assert matrix[0, 0] == 5.0  # Alignment
        assert matrix[0, 1] == 4.0  # Realism

    def test_list_format(self):
        """Should handle list format."""
        df = pd.DataFrame({
            "teacher_scores": [[1, 2, 3, 4], [5, 6, 7, 8]],
        })
        logger = type('Logger', (), {'info': lambda *args: None, 'warning': lambda *args: None})()
        matrix = extract_teacher_scores_matrix(df, logger)
        
        assert matrix.shape == (2, 4)
        assert matrix[0, 0] == 1

    def test_invalid_format(self, caplog):
        """Should handle invalid format with warning."""
        df = pd.DataFrame({
            "teacher_scores": ["invalid", [1, 2, 3, 4]],
        })
        logger = type('Logger', (), {'info': lambda *args: None, 'warning': lambda *args: None})()
        matrix = extract_teacher_scores_matrix(df, logger)
        
        assert matrix.shape == (2, 4)
        assert np.all(np.isnan(matrix[0]))  # First row should be NaN

class TestIntegrateFeatures:
    def test_write_csv(self, sample_df):
        """Should write features to CSV."""
        variances = np.array([1.0, 0.0, 2.0])
        entropies = np.array([1.5, 0.0, 1.8])
        skewnesses = np.array([0.1, 0.0, -0.2])
        kurtoses = np.array([0.05, 0.0, -0.1])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.csv")
            logger = type('Logger', (), {'info': lambda *args: None, 'warning': lambda *args: None})()
            
            integrate_features(sample_df, variances, entropies, skewnesses, kurtoses, output_path, logger)
            
            assert os.path.exists(output_path)
            result_df = pd.read_csv(output_path)
            assert "variance" in result_df.columns
            assert "entropy" in result_df.columns
            assert "skewness" in result_df.columns
            assert "kurtosis" in result_df.columns
            assert len(result_df) == 3
            assert result_df["variance"].iloc[1] == 0.0  # Zero variance case
