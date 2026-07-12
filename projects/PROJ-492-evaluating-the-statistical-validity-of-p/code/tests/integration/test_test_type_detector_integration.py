"""
Integration tests for outcome type detection in the audit pipeline.
"""
import json
import pytest
from pathlib import Path
from code.src.audit.test_type_detector import detect_outcome_type, detect_outcome_types_batch
from code.src.utils.logger import get_default_logger

@pytest.fixture
def logger():
    return get_default_logger()

class TestOutcomeTypeDetectorIntegration:
    """Integration tests for outcome type detection."""
    
    def test_detection_consistency_with_reconstructor(self, logger):
        """
        Test that outcome type detection is consistent with what the 
        reconstructor would expect for statistical tests.
        """
        # Binary test case - should use z-test or Fisher's exact
        binary_summary = {
            "conversion_rate": 0.05,
            "baseline_conversion_rate": 0.04,
            "sample_size_control": 10000,
            "sample_size_treatment": 10000,
            "p_value": 0.03,
            "effect_size": 0.01
        }
        
        detected_type = detect_outcome_type(binary_summary, logger)
        assert detected_type == 'binary', "Binary summary should be detected as binary"
        
        # Continuous test case - should use Welch's t-test
        continuous_summary = {
            "mean_control": 12.5,
            "mean_treatment": 15.2,
            "std_control": 3.1,
            "std_treatment": 3.4,
            "sample_size_control": 500,
            "sample_size_treatment": 500,
            "p_value": 0.01,
            "effect_size": 0.85
        }
        
        detected_type = detect_outcome_type(continuous_summary, logger)
        assert detected_type == 'continuous', "Continuous summary should be detected as continuous"
    
    def test_detection_with_real_world_like_data(self, logger):
        """Test detection with data resembling real-world A/B test summaries."""
        # Simulating various real-world scenarios
        real_world_summaries = [
            {
                "url": "https://example.com/checkout-test",
                "conversion_rate": 0.032,
                "baseline_conversion_rate": 0.028,
                "sample_size_control": 50000,
                "sample_size_treatment": 50000,
                "p_value": 0.001,
                "test_type": "z-test"
            },
            {
                "url": "https://example.com/pricing-test",
                "mean_control": 45.20,
                "mean_treatment": 52.10,
                "std_control": 12.30,
                "std_treatment": 14.50,
                "sample_size_control": 2000,
                "sample_size_treatment": 2000,
                "p_value": 0.0001,
                "test_type": "welch t-test"
            },
            {
                "url": "https://example.com/email-open-test",
                "conversion_rate": 0.22,
                "baseline_conversion_rate": 0.19,
                "sample_size_control": 10000,
                "sample_size_treatment": 10000,
                "p_value": 0.02,
                "metric_type": "binary"
            }
        ]
        
        results = detect_outcome_types_batch(real_world_summaries, logger)
        
        # First should be binary (conversion rate)
        assert results[0][1] == 'binary', "Checkout test should be binary"
        
        # Second should be continuous (revenue)
        assert results[1][1] == 'continuous', "Pricing test should be continuous"
        
        # Third should be binary (explicit metric type)
        assert results[2][1] == 'binary', "Email open test should be binary"
    
    def test_edge_cases_detection(self, logger):
        """Test detection with edge cases and ambiguous data."""
        edge_cases = [
            # Case 1: Only p-value provided
            {"p_value": 0.05},
            
            # Case 2: Effect size exactly 1.0 (boundary)
            {"effect_size": 1.0, "sample_size_control": 1000, "sample_size_treatment": 1000},
            
            # Case 3: Negative effect size
            {"effect_size": -0.05, "sample_size_control": 5000, "sample_size_treatment": 5000},
            
            # Case 4: Very small effect size
            {"effect_size": 0.001, "sample_size_control": 100000, "sample_size_treatment": 100000}
        ]
        
        results = detect_outcome_types_batch(edge_cases, logger)
        
        # First should be unknown
        assert results[0][1] == 'unknown', "P-value only should be unknown"
        
        # Second (effect size 1.0) with sample sizes should be binary
        assert results[1][1] == 'binary', "Effect size 1.0 with samples should be binary"
        
        # Third (negative effect) with samples should be binary
        assert results[2][1] == 'binary', "Negative effect with samples should be binary"
        
        # Fourth (small effect) with samples should be binary
        assert results[3][1] == 'binary', "Small effect with samples should be binary"
    
    def test_detection_with_missing_fields(self, logger):
        """Test detection when some expected fields are missing."""
        partial_summaries = [
            # Missing sample sizes but has conversion rate
            {"conversion_rate": 0.05, "p_value": 0.03},
            
            # Missing conversion rate but has means
            {"mean_control": 10.0, "mean_treatment": 12.0},
            
            # Only effect size, no sample sizes
            {"effect_size": 0.5},
            
            # Has both conversion rate and means (should prefer conversion rate)
            {"conversion_rate": 0.05, "mean_control": 10.0, "mean_treatment": 12.0}
        ]
        
        results = detect_outcome_types_batch(partial_summaries, logger)
        
        assert results[0][1] == 'binary', "Conversion rate should indicate binary"
        assert results[1][1] == 'continuous', "Mean fields should indicate continuous"
        assert results[2][1] == 'unknown', "Effect size alone should be unknown"
        assert results[3][1] == 'binary', "Conversion rate should take precedence over means"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
