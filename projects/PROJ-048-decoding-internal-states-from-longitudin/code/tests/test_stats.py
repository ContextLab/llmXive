import pytest
import numpy as np
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports if running standalone
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.stats import (
    calculate_spearman_correlation,
    run_permutation_test,
    apply_bh_fdr_correction,
    generate_null_distribution,
    calculate_significance,
    write_correlation_report
)
from utils.logger import get_logger

logger = get_logger(__name__)

def generate_mock_correlation_results(
    n_components: int = 5,
    n_behaviors: int = 3,
    p_value_base: float = 0.01
) -> Dict[str, Any]:
    """
    Generate a mock correlation results dictionary.
    Used for schema validation and positive control tests.
    """
    components = [f"component_{i}" for i in range(n_components)]
    behaviors = [f"behavior_{j}" for j in range(n_behaviors)]

    correlations = {}
    for comp in components:
        correlations[comp] = {}
        for beh in behaviors:
            # Generate random stats
            rho = np.random.uniform(0.1, 0.9)
            p_val = np.random.uniform(0.001, 0.05)
            correlations[comp][beh] = {
                "rho": float(rho),
                "p_value": float(p_val),
                "n_samples": 1000,
                "significant": p_val < 0.05
            }

    return {
        "metadata": {
            "n_components": n_components,
            "n_behaviors": n_behaviors,
            "method": "spearman",
            "permutation_iterations": 1000
        },
        "results": correlations
    }

def validate_correlation_schema(data: Dict[str, Any]) -> bool:
    """
    Validate that correlation results match the expected schema.
    """
    if "metadata" not in data or "results" not in data:
        return False
    
    metadata = data["metadata"]
    required_meta_keys = ["n_components", "n_behaviors", "method", "permutation_iterations"]
    if not all(k in metadata for k in required_meta_keys):
        return False

    results = data["results"]
    if not isinstance(results, dict):
        return False

    for comp_key, beh_dict in results.items():
        if not isinstance(beh_dict, dict):
            return False
        for beh_key, stats in beh_dict.items():
            required_stats = ["rho", "p_value", "n_samples", "significant"]
            if not all(k in stats for k in required_stats):
                return False
            if not isinstance(stats["rho"], (int, float)):
                return False
            if not isinstance(stats["p_value"], (int, float)):
                return False
    
    return True

class TestCorrelationSchemaContract:
    """Tests for the schema structure of correlation outputs."""

    def test_valid_schema(self):
        """Verify that generated mock data passes schema validation."""
        data = generate_mock_correlation_results()
        assert validate_correlation_schema(data), "Generated mock data failed schema validation"

    def test_missing_metadata(self):
        """Verify that missing metadata keys fail validation."""
        data = {"results": {}}
        assert not validate_correlation_schema(data)

    def test_missing_stats_fields(self):
        """Verify that missing stats fields fail validation."""
        data = {
            "metadata": {
                "n_components": 1,
                "n_behaviors": 1,
                "method": "spearman",
                "permutation_iterations": 1000
            },
            "results": {
                "component_0": {
                    "behavior_0": {"rho": 0.5}  # Missing p_value, etc.
                }
            }
        }
        assert not validate_correlation_schema(data)

class TestPermutationTestSignificance:
    """
    Integration test for permutation test significance.
    Verifies that shuffled (null) data yields p > 0.05.
    """

    def test_shuffled_data_p_value_greater_than_005(self):
        """
        Verify that when behavioral data is shuffled (breaking any correlation),
        the permutation test returns a p-value > 0.05.
        """
        # Setup: Generate realistic-looking but uncorrelated data
        # We create two vectors that are explicitly uncorrelated
        np.random.seed(42)
        n_samples = 500
        
        # Component weights (simulated latent state)
        weights = np.random.normal(loc=0.5, scale=0.2, size=n_samples)
        weights = np.clip(weights, 0, 1) # Non-negative like NMF output
        
        # Behavioral metric (simulated behavior)
        # We deliberately make this independent of weights to simulate a null hypothesis
        behavior = np.random.normal(loc=0.5, scale=0.2, size=n_samples)
        behavior = np.clip(behavior, 0, 1)

        # Verify they are indeed uncorrelated initially
        initial_rho, _ = scipy.stats.spearmanr(weights, behavior)
        # Allow a small tolerance for randomness, but it should be low
        assert abs(initial_rho) < 0.2, "Initial data should be uncorrelated for this test"

        # Run permutation test
        # We simulate the null hypothesis: there is no relationship.
        # The permutation test should confirm this by producing a high p-value.
        
        # Import scipy here to avoid top-level dependency if not needed for other parts
        import scipy.stats
        
        # Run the permutation test logic directly
        # We use a smaller iteration count for speed in tests, but logic must hold
        n_permutations = 500 
        
        observed_rho, observed_p = scipy.stats.spearmanr(weights, behavior)
        
        # Generate null distribution by shuffling
        null_rhos = []
        for _ in range(n_permutations):
            shuffled_behavior = np.random.permutation(behavior)
            rho, _ = scipy.stats.spearmanr(weights, shuffled_behavior)
            null_rhos.append(rho)
        
        null_rhos = np.array(null_rhos)
        
        # Calculate p-value: proportion of null stats >= observed stat (absolute value for two-tailed)
        # Since we expect no correlation, we look at absolute values
        p_value = (np.abs(null_rhos) >= np.abs(observed_rho)).sum() / n_permutations

        # ASSERTION: The p-value must be > 0.05 for shuffled/uncorrelated data
        # If p < 0.05, it implies we falsely detected a correlation where none exists (Type I error)
        assert p_value > 0.05, (
            f"Permutation test failed: p-value ({p_value:.4f}) <= 0.05 on shuffled data. "
            "This indicates the test is incorrectly rejecting the null hypothesis."
        )

    def test_permutation_test_function_integration(self):
        """
        Test the actual run_permutation_test function from stats module
        with shuffled data to ensure it returns p > 0.05.
        """
        import scipy.stats
        
        np.random.seed(123)
        n = 300
        x = np.random.rand(n)
        y = np.random.rand(n) # Independent of x
        
        # Run the module's function
        result = run_permutation_test(x, y, n_permutations=1000, random_seed=42)
        
        # result should contain 'p_value'
        assert "p_value" in result, "Permutation test result missing 'p_value' key"
        
        p_val = result["p_value"]
        
        # With independent data, p should be > 0.05
        # We allow a small margin for statistical fluctuation in small tests, 
        # but generally it should be significant (non-rejection)
        assert p_val > 0.05, (
            f"Integration test failed: p-value {p_val} <= 0.05 on independent data. "
            "The permutation test implementation may be flawed."
        )

def test_write_report_schema_compliance(tmp_path):
    """
    Verify that the written report file is valid JSON and matches schema.
    """
    mock_data = generate_mock_correlation_results()
    output_path = tmp_path / "correlation_report.json"
    
    write_correlation_report(mock_data, str(output_path))
    
    assert output_path.exists(), "Report file was not created"
    
    with open(output_path, 'r') as f:
        loaded_data = json.load(f)
    
    assert validate_correlation_schema(loaded_data), "Loaded report failed schema validation"