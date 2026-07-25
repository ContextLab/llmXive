import pytest
import numpy as np
import math
from code.features import (
    calculate_variance_and_range,
    calculate_entropy,
    calculate_skewness_and_kurtosis,
    calculate_per_sample_stats,
    calculate_global_entanglement_score,
    calculate_dimensional_fidelity_loss
)

def test_calculate_variance_and_range():
    """Test variance and range calculation."""
    values = [1.0, 2.0, 3.0, 4.0]
    result = calculate_variance_and_range(values)
    
    # Manual calculation:
    # Mean = 2.5
    # Variance = ((1-2.5)^2 + (2-2.5)^2 + (3-2.5)^2 + (4-2.5)^2) / 4
    #          = (2.25 + 0.25 + 0.25 + 2.25) / 4 = 5.0 / 4 = 1.25
    expected_variance = 1.25
    expected_range = 3.0
    
    assert abs(result["variance"] - expected_variance) < 1e-6
    assert abs(result["range"] - expected_range) < 1e-6

def test_calculate_variance_and_range_zero_variance():
    """Test zero-variance case."""
    values = [5.0, 5.0, 5.0]
    result = calculate_variance_and_range(values)
    assert result["variance"] == 0.0
    assert result["range"] == 0.0

def test_calculate_entropy():
    """Test entropy calculation."""
    # Uniform distribution [1, 1, 1, 1] -> probabilities [0.25, 0.25, 0.25, 0.25]
    # Entropy = -4 * (0.25 * log2(0.25)) = -4 * (0.25 * -2) = 2.0
    values = [1.0, 1.0, 1.0, 1.0]
    result = calculate_entropy(values)
    assert abs(result - 2.0) < 1e-6

def test_calculate_entropy_zero_variance():
    """Test entropy with zero variance (all same values)."""
    values = [2.0, 2.0, 2.0]
    result = calculate_entropy(values)
    assert result == 0.0

def test_calculate_skewness_and_kurtosis():
    """Test skewness and kurtosis calculation."""
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = calculate_skewness_and_kurtosis(values)
    
    # For a symmetric distribution, skewness should be ~0
    # Kurtosis for uniform-like distribution is negative (platykurtic)
    assert isinstance(result["skewness"], float)
    assert isinstance(result["kurtosis"], float)

def test_calculate_per_sample_stats():
    """Test per-sample stats calculation (T022a)."""
    # 4-dimensional sample (typical teacher logits)
    teacher_logits = [0.1, 0.4, 0.3, 0.2]
    result = calculate_per_sample_stats(teacher_logits)
    
    assert "variance" in result
    assert "entropy" in result
    assert "skewness" in result
    assert "kurtosis" in result
    
    # Variance should be positive
    assert result["variance"] >= 0
    # Entropy should be non-negative
    assert result["entropy"] >= 0

def test_calculate_per_sample_stats_zero_variance():
    """Test per-sample stats with zero variance (T022a validation)."""
    teacher_logits = [0.5, 0.5, 0.5, 0.5]
    result = calculate_per_sample_stats(teacher_logits)
    
    assert result["variance"] == 0.0
    assert result["entropy"] == 0.0
    assert result["skewness"] == 0.0
    assert result["kurtosis"] == 0.0

def test_calculate_global_entanglement_score():
    """Test global dominant eigenvalue calculation (T022b)."""
    # Create a simple 4x4 dataset (4 samples, 4 dimensions each)
    all_logits = [
        [0.1, 0.4, 0.3, 0.2],
        [0.2, 0.3, 0.4, 0.1],
        [0.3, 0.2, 0.1, 0.4],
        [0.4, 0.1, 0.2, 0.3]
    ]
    
    result = calculate_global_entanglement_score(all_logits)
    
    # Should return a finite scalar
    assert isinstance(result, float)
    assert np.isfinite(result)
    assert result >= 0

def test_calculate_dimensional_fidelity_loss():
    """Test fidelity loss calculation (T024)."""
    student_scalar = 0.75
    human_annotations = {
        "Alignment": 0.8,
        "Realism": 0.6,
        "Aesthetics": 0.9,
        "Plausibility": 0.7
    }
    primary_dimension = "Alignment"
    
    result = calculate_dimensional_fidelity_loss(
        student_scalar, human_annotations, primary_dimension
    )
    
    expected = abs(0.75 - 0.8)
    assert abs(result - expected) < 1e-6

def test_calculate_dimensional_fidelity_loss_missing_dimension():
    """Test fidelity loss with missing dimension."""
    student_scalar = 0.75
    human_annotations = {
        "Realism": 0.6
    }
    primary_dimension = "Alignment"
    
    with pytest.raises(ValueError):
        calculate_dimensional_fidelity_loss(
            student_scalar, human_annotations, primary_dimension
        )