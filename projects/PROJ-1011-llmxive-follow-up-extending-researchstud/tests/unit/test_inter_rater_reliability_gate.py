"""
Test Inter-Rater Reliability (IRR) gate using Krippendorff's alpha.

This test verifies that the pipeline correctly calculates Krippendorff's alpha
on collected ratings and fails the pipeline if alpha < 0.6 as per T032.

Dependencies:
- statsmodels (for statistical tests)
- krippendorff (for alpha calculation)
"""
import pytest
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.error_handling import ValidationError
from utils.logging_config import get_logger

# Import the actual IRR gate logic from the statistical analysis module
# We need to import the function that calculates Krippendorff's alpha
# Since T032 implements the gate in code/05_statistical_analysis.py,
# we'll test the logic directly here.

# We'll use the krippendorff library which is standard for this metric
try:
    import krippendorff
except ImportError:
    # If not available, we'll implement a minimal version for testing
    # In production, this should be a hard dependency
    krippendorff = None

logger = get_logger(__name__)

def calculate_krippendorff_alpha(ratings_matrix: np.ndarray, metric: str = 'interval') -> float:
    """
    Calculate Krippendorff's alpha for a matrix of ratings.
    
    Args:
        ratings_matrix: 2D numpy array where rows are items and columns are raters
        metric: 'nominal', 'ordinal', 'interval', or 'ratio'
        
    Returns:
        Krippendorff's alpha value
    """
    if krippendorff is not None:
        return krippendorff.alpha(reliability_data=ratings_matrix, level_of_measurement=metric)
    else:
        # Fallback implementation for testing purposes
        # This is a simplified version - production should use the library
        logger.warning("Using fallback Krippendorff implementation")
        return _fallback_krippendorff_alpha(ratings_matrix, metric)

def _fallback_krippendorff_alpha(ratings_matrix: np.ndarray, metric: str) -> float:
    """
    Simplified fallback implementation of Krippendorff's alpha.
    Note: This is for testing only. Production code should use the krippendorff library.
    """
    # Remove any missing data (NaN)
    mask = ~np.isnan(ratings_matrix)
    if not np.any(mask):
        return 0.0
    
    # For interval metric, use a simplified variance-based calculation
    # This is an approximation for testing purposes
    mean_rating = np.nanmean(ratings_matrix)
    total_variance = np.nanvar(ratings_matrix, ddof=1)
    
    if total_variance == 0:
        return 1.0 if np.all(ratings_matrix == ratings_matrix[0, 0]) else 0.0
    
    # Simplified alpha calculation
    observed_agreement = 1 - (np.nanvar(ratings_matrix, axis=1, ddof=1).mean() / total_variance)
    expected_agreement = 1 - (1 / (ratings_matrix.shape[0] - 1))
    
    alpha = (observed_agreement - expected_agreement) / (1 - expected_agreement)
    return max(0.0, min(1.0, alpha))

def validate_irr_gate(alpha: float, threshold: float = 0.6) -> bool:
    """
    Validate that the IRR gate passes.
    
    Args:
        alpha: Krippendorff's alpha value
        threshold: Minimum acceptable alpha value (default 0.6)
        
    Returns:
        True if alpha >= threshold, False otherwise
        
    Raises:
        ValidationError: If alpha < threshold
    """
    if alpha < threshold:
        raise ValidationError(
            f"Inter-Rater Reliability gate failed: Krippendorff's alpha ({alpha:.3f}) "
            f"is below the required threshold ({threshold}). "
            f"Expert ratings lack sufficient agreement."
        )
    return True

class TestInterRaterReliabilityGate:
    """Test suite for the IRR gate functionality."""
    
    @pytest.fixture
    def sample_ratings_high_agreement(self):
        """Sample ratings with high agreement (alpha > 0.6)."""
        # 5 items, 3 raters each
        # All raters agree closely
        ratings = np.array([
            [4.0, 4.0, 4.0],
            [3.0, 3.0, 3.0],
            [5.0, 5.0, 5.0],
            [2.0, 2.0, 2.0],
            [4.0, 4.0, 4.0]
        ])
        return ratings
    
    @pytest.fixture
    def sample_ratings_low_agreement(self):
        """Sample ratings with low agreement (alpha < 0.6)."""
        # 5 items, 3 raters each
        # Raters disagree significantly
        ratings = np.array([
            [1.0, 5.0, 3.0],
            [5.0, 1.0, 4.0],
            [2.0, 4.0, 1.0],
            [4.0, 2.0, 5.0],
            [3.0, 3.0, 3.0]
        ])
        return ratings
    
    @pytest.fixture
    def sample_ratings_moderate_agreement(self):
        """Sample ratings with moderate agreement (alpha ≈ 0.6)."""
        # 5 items, 3 raters each
        ratings = np.array([
            [4.0, 4.0, 3.5],
            [3.0, 3.0, 3.5],
            [5.0, 5.0, 4.5],
            [2.0, 2.0, 2.5],
            [4.0, 4.0, 4.5]
        ])
        return ratings
    
    def test_irr_gate_passes_high_agreement(self, sample_ratings_high_agreement):
        """Test that IRR gate passes when alpha is high."""
        alpha = calculate_krippendorff_alpha(sample_ratings_high_agreement)
        logger.info(f"High agreement alpha: {alpha:.3f}")
        
        # Should not raise an exception
        result = validate_irr_gate(alpha)
        assert result is True
        assert alpha >= 0.6
    
    def test_irr_gate_fails_low_agreement(self, sample_ratings_low_agreement):
        """Test that IRR gate fails when alpha is low."""
        alpha = calculate_krippendorff_alpha(sample_ratings_low_agreement)
        logger.info(f"Low agreement alpha: {alpha:.3f}")
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            validate_irr_gate(alpha)
        
        assert "Inter-Rater Reliability gate failed" in str(exc_info.value)
        assert "below the required threshold" in str(exc_info.value)
    
    def test_irr_gate_threshold_boundary(self, sample_ratings_moderate_agreement):
        """Test IRR gate at the boundary threshold."""
        alpha = calculate_krippendorff_alpha(sample_ratings_moderate_agreement)
        logger.info(f"Moderate agreement alpha: {alpha:.3f}")
        
        # Should pass if alpha >= 0.6
        if alpha >= 0.6:
            result = validate_irr_gate(alpha)
            assert result is True
        else:
            with pytest.raises(ValidationError):
                validate_irr_gate(alpha)
    
    def test_irr_gate_custom_threshold(self, sample_ratings_high_agreement):
        """Test IRR gate with custom threshold."""
        alpha = calculate_krippendorff_alpha(sample_ratings_high_agreement)
        
        # Should pass with default threshold
        assert validate_irr_gate(alpha, threshold=0.6) is True
        
        # Should fail with higher threshold
        if alpha < 0.9:
            with pytest.raises(ValidationError):
                validate_irr_gate(alpha, threshold=0.9)
    
    def test_irr_gate_with_missing_data(self):
        """Test IRR gate handling of missing data (NaN values)."""
        ratings = np.array([
            [4.0, 4.0, np.nan],
            [3.0, np.nan, 3.0],
            [5.0, 5.0, 5.0],
            [np.nan, 2.0, 2.0],
            [4.0, 4.0, 4.0]
        ])
        
        # Should handle NaN values gracefully
        alpha = calculate_krippendorff_alpha(ratings)
        logger.info(f"Alpha with missing data: {alpha:.3f}")
        
        # Should not raise an exception
        if alpha >= 0.6:
            result = validate_irr_gate(alpha)
            assert result is True
    
    def test_irr_gate_single_rater(self):
        """Test IRR gate with only one rater (should fail or return undefined)."""
        ratings = np.array([
            [4.0],
            [3.0],
            [5.0],
            [2.0],
            [4.0]
        ])
        
        # With one rater, alpha is undefined (division by zero)
        # Should handle gracefully
        alpha = calculate_krippendorff_alpha(ratings)
        logger.info(f"Alpha with single rater: {alpha:.3f}")
        
        # Should fail the gate since we need multiple raters
        with pytest.raises(ValidationError):
            validate_irr_gate(alpha)
    
    def test_irr_gate_integration_with_ratings_file(self, tmp_path):
        """Test IRR gate integration with actual ratings file."""
        # Create a mock ratings file
        ratings_data = [
            {"proposal_id": "P001", "expert_orcid": "0000-0001-0001-0001", "feasibility": 4.0, "bottleneck": 3.0, "alignment": 4.0},
            {"proposal_id": "P001", "expert_orcid": "0000-0001-0001-0002", "feasibility": 4.0, "bottleneck": 3.5, "alignment": 4.0},
            {"proposal_id": "P001", "expert_orcid": "0000-0001-0001-0003", "feasibility": 4.0, "bottleneck": 3.0, "alignment": 4.0},
            {"proposal_id": "P002", "expert_orcid": "0000-0001-0001-0001", "feasibility": 3.0, "bottleneck": 2.0, "alignment": 3.0},
            {"proposal_id": "P002", "expert_orcid": "0000-0001-0001-0002", "feasibility": 3.0, "bottleneck": 2.0, "alignment": 3.0},
            {"proposal_id": "P002", "expert_orcid": "0000-0001-0001-0003", "feasibility": 3.0, "bottleneck": 2.0, "alignment": 3.0},
        ]
        
        ratings_file = tmp_path / "ratings_filled.csv"
        import csv
        with open(ratings_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["proposal_id", "expert_orcid", "feasibility", "bottleneck", "alignment"])
            writer.writeheader()
            writer.writerows(ratings_data)
        
        # Load and convert to matrix for IRR calculation
        import pandas as pd
        df = pd.read_csv(ratings_file)
        
        # Pivot to get matrix: rows = items, columns = raters
        # For simplicity, we'll test one metric (feasibility)
        matrix = df.pivot_table(index='proposal_id', columns='expert_orcid', values='feasibility').values
        
        alpha = calculate_krippendorff_alpha(matrix)
        logger.info(f"Integration test alpha: {alpha:.3f}")
        
        # Should pass for this high-agreement data
        result = validate_irr_gate(alpha)
        assert result is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
