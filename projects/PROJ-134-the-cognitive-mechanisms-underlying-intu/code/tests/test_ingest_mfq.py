"""
Unit tests for the synthetic MFQ generator interface.

This test suite defines the expected interface and behavior for the 
`code/data/simulation_mfq.py` module before it is implemented.

It validates that:
1. The generator accepts valid Gervais et al. (2011) norm parameters.
2. The output adheres to the `MFQDataset` Pydantic schema defined in `code/utils/schema.py`.
3. The generated data respects the specified sample size and random seed.
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.schema import MFQDataset, MFQResponse, SalienceLevel
from code.config import ensure_directories

# Import the module under test. 
# Note: This will fail if T013 (simulation_mfq.py) is not implemented yet,
# which is expected behavior for a "Test First" approach.
try:
    from code.data.simulation_mfq import generate_synthetic_mfq
    SIMULATION_MODULE_AVAILABLE = True
except ImportError:
    SIMULATION_MODULE_AVAILABLE = False

# Constants for testing
TEST_SEED = 42
TEST_SAMPLE_SIZE = 100
TEST_OUTPUT_PATH = "data/processed/test_mfq_output.json"

# Mock Gervais et al. (2011) Norm Parameters (Simplified for testing)
# These represent the mean and covariance for the multivariate normal distribution
MOCK_MEANS = {
    "Care": 0.8,
    "Fairness": 0.7,
    "Loyalty": 0.5,
    "Authority": 0.4,
    "Purity": 0.3
}

MOCK_COVARIANCE = np.eye(5) * 0.1  # Identity matrix scaled for simplicity

MOCK_NORMS = {
    "means": MOCK_MEANS,
    "cov": MOCK_COVARIANCE.tolist()
}

class TestMFQGeneratorInterface:
    """Tests for the interface defined by the MFQ generator."""

    def test_generator_not_implemented_yet(self):
        """
        If the simulation module is not yet implemented, this test ensures
        we fail loudly with a clear message rather than passing silently.
        """
        if not SIMULATION_MODULE_AVAILABLE:
            pytest.fail(
                "The module 'code.data.simulation_mfq' is not yet implemented. "
                "This test defines the interface that T013 must satisfy."
            )

    def test_generate_synthetic_mfq_returns_valid_dataset(self):
        """
        Test that the generator returns an object conforming to the MFQDataset schema.
        """
        # Ensure directories exist for potential file output
        ensure_directories()

        result = generate_synthetic_mfq(
            sample_size=TEST_SAMPLE_SIZE,
            seed=TEST_SEED,
            norms=MOCK_NORMS,
            output_path=TEST_OUTPUT_PATH
        )

        # Validate return type
        assert isinstance(result, MFQDataset), \
            f"Expected MFQDataset, got {type(result)}"

        # Validate that the dataset contains the expected number of responses
        assert len(result.responses) == TEST_SAMPLE_SIZE, \
            f"Expected {TEST_SAMPLE_SIZE} responses, got {len(result.responses)}"

        # Validate that the output file was written (if path provided)
        output_file = Path(TEST_OUTPUT_PATH)
        assert output_file.exists(), \
            f"Output file was not created at {TEST_OUTPUT_PATH}"

    def test_generate_synthetic_mfq_respects_seed(self):
        """
        Test that running the generator twice with the same seed produces identical data.
        """
        # Run 1
        result1 = generate_synthetic_mfq(
            sample_size=50,
            seed=TEST_SEED,
            norms=MOCK_NORMS
        )

        # Run 2
        result2 = generate_synthetic_mfq(
            sample_size=50,
            seed=TEST_SEED,
            norms=MOCK_NORMS
        )

        # Compare scores
        for i, resp1 in enumerate(result1.responses):
            resp2 = result2.responses[i]
            # Compare Care scores as a proxy for all dimensions
            assert resp1.scores["Care"] == resp2.scores["Care"], \
                "Seed did not produce deterministic results"

    def test_generate_synthetic_mfq_handles_invalid_sample_size(self):
        """
        Test that the generator raises an error for non-positive sample sizes.
        """
        with pytest.raises(ValueError):
            generate_synthetic_mfq(
                sample_size=0,
                seed=TEST_SEED,
                norms=MOCK_NORMS
            )

        with pytest.raises(ValueError):
            generate_synthetic_mfq(
                sample_size=-5,
                seed=TEST_SEED,
                norms=MOCK_NORMS
            )

    def test_generated_data_matches_norm_distribution(self):
        """
        Test that the generated data roughly matches the input norms (within statistical variance).
        This is a sanity check for the multivariate normal generation logic.
        """
        large_sample_size = 10000
        result = generate_synthetic_mfq(
            sample_size=large_sample_size,
            seed=TEST_SEED,
            norms=MOCK_NORMS
        )

        # Extract scores for 'Care'
        care_scores = [r.scores["Care"] for r in result.responses]
        calculated_mean = np.mean(care_scores)

        # The generated mean should be close to the norm mean (allowing for sampling variance)
        # Using a loose tolerance for a sanity check
        expected_mean = MOCK_MEANS["Care"]
        tolerance = 0.05 
        
        assert abs(calculated_mean - expected_mean) < tolerance, \
            f"Generated mean ({calculated_mean:.4f}) deviates significantly from norm mean ({expected_mean})"