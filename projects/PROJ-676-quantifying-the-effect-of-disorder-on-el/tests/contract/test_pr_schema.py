"""
Contract test for Participation Ratio (PR) calculation output schema.

This test validates that the output of the PR calculation pipeline
adheres to the expected schema defined in the project contracts.
It ensures that:
1. The output is a valid JSON-serializable dictionary.
2. All required fields (xi, uncertainty, fit_params, metadata) are present.
3. Data types match the specification (floats, dicts, lists).
4. Numerical values are within physically reasonable bounds.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pytest

# Add project root to path to import local modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analyze_pr import finite_size_scaling, compute_participation_ratio
from code.config import get_config
from code.generate_hamiltonian import generate_hamiltonian


# --- Schema Definitions (Contract) ---

SCHEMA_VERSION = "1.0.0"

EXPECTED_OUTPUT_KEYS = {
    "xi",               # Localization length (float)
    "uncertainty",      # Uncertainty in xi (float)
    "fit_params",       # Dictionary of fit parameters (dict)
    "metadata",         # Metadata about the calculation (dict)
    "pr_values",        # List of PR values for each L (list of floats)
    "system_sizes"      # List of system sizes used (list of ints)
}

REQUIRED_METADATA_KEYS = {
    "disorder_width",   # W value used (float)
    "num_realizations", # Number of realizations averaged (int)
    "energy_window",    # Energy window used for PR (dict: {"min", "max"})
    "method",           # Method used ("finite_size_scaling") (str)
    "schema_version"    # Schema version string (str)
}

REQUIRED_FIT_PARAMS_KEYS = {
    "r_squared",        # R^2 of the fit (float)
    "convergence",      # Whether fit converged (bool)
    "residual_norm"     # Norm of residuals (float)
}


# --- Helper Functions ---

def generate_test_realization(L: int, W: float, seed: int) -> np.ndarray:
    """Generate a single Hamiltonian realization for testing."""
    np.random.seed(seed)
    return generate_hamiltonian(L, W)


def compute_test_pr(H: np.ndarray, E_min: float = -0.1, E_max: float = 0.1) -> float:
    """Compute PR for a single Hamiltonian."""
    eigenvalues, eigenvectors = np.linalg.eigh(H)
    return compute_participation_ratio(eigenvalues, eigenvectors, E_min, E_max)


def run_pr_scaling_test(W: float, Ls: List[int], num_samples: int = 5, seed_base: int = 42) -> Dict[str, Any]:
    """
    Run a minimal finite-size scaling analysis to generate output for schema validation.
    Uses a small number of samples and system sizes to keep execution fast.
    """
    pr_values = []
    
    for L in Ls:
        sample_prs = []
        for i in range(num_samples):
            H = generate_test_realization(L, W, seed_base + i)
            pr = compute_test_pr(H)
            sample_prs.append(pr)
        pr_values.append(np.mean(sample_prs))
    
    # Run the scaling analysis
    result = finite_size_scaling(Ls, pr_values, W)
    return result


# --- Contract Tests ---

class TestPRSchemaContract:
    """
    Contract tests ensuring PR calculation output matches the expected schema.
    """

    @pytest.fixture
    def scaling_result(self):
        """Generate a sample scaling result for testing."""
        Ls = [100, 200, 400]
        W = 1.0
        return run_pr_scaling_test(W, Ls, num_samples=3)

    def test_output_is_dict(self, scaling_result):
        """Verify the output is a dictionary."""
        assert isinstance(scaling_result, dict), "Output must be a dictionary."

    def test_required_top_level_keys_present(self, scaling_result):
        """Verify all required top-level keys are present."""
        missing_keys = EXPECTED_OUTPUT_KEYS - set(scaling_result.keys())
        assert not missing_keys, f"Missing required keys: {missing_keys}"

    def test_xi_is_float(self, scaling_result):
        """Verify xi is a float."""
        assert isinstance(scaling_result["xi"], (int, float)), "xi must be a numeric type."
        assert scaling_result["xi"] > 0, "xi must be positive."

    def test_uncertainty_is_float(self, scaling_result):
        """Verify uncertainty is a float."""
        assert isinstance(scaling_result["uncertainty"], (int, float)), "uncertainty must be numeric."
        assert scaling_result["uncertainty"] >= 0, "uncertainty must be non-negative."

    def test_fit_params_is_dict(self, scaling_result):
        """Verify fit_params is a dictionary."""
        assert isinstance(scaling_result["fit_params"], dict), "fit_params must be a dictionary."

    def test_fit_params_required_keys(self, scaling_result):
        """Verify fit_params contains required keys."""
        missing_keys = REQUIRED_FIT_PARAMS_KEYS - set(scaling_result["fit_params"].keys())
        assert not missing_keys, f"Missing required fit_params keys: {missing_keys}"

    def test_metadata_is_dict(self, scaling_result):
        """Verify metadata is a dictionary."""
        assert isinstance(scaling_result["metadata"], dict), "metadata must be a dictionary."

    def test_metadata_required_keys(self, scaling_result):
        """Verify metadata contains required keys."""
        missing_keys = REQUIRED_METADATA_KEYS - set(scaling_result["metadata"].keys())
        assert not missing_keys, f"Missing required metadata keys: {missing_keys}"

    def test_metadata_schema_version(self, scaling_result):
        """Verify metadata contains correct schema version."""
        assert scaling_result["metadata"]["schema_version"] == SCHEMA_VERSION, \
            f"Schema version mismatch: expected {SCHEMA_VERSION}, got {scaling_result['metadata']['schema_version']}"

    def test_pr_values_is_list_of_numbers(self, scaling_result):
        """Verify pr_values is a list of numbers."""
        assert isinstance(scaling_result["pr_values"], list), "pr_values must be a list."
        assert all(isinstance(v, (int, float)) for v in scaling_result["pr_values"]), \
            "All pr_values must be numeric."

    def test_system_sizes_is_list_of_ints(self, scaling_result):
        """Verify system_sizes is a list of integers."""
        assert isinstance(scaling_result["system_sizes"], list), "system_sizes must be a list."
        assert all(isinstance(s, int) for s in scaling_result["system_sizes"]), \
            "All system_sizes must be integers."

    def test_json_serializability(self, scaling_result):
        """Verify the output can be serialized to JSON."""
        try:
            json_str = json.dumps(scaling_result)
            parsed = json.loads(json_str)
            # Verify round-trip integrity for critical fields
            assert parsed["xi"] == scaling_result["xi"]
            assert parsed["metadata"]["disorder_width"] == scaling_result["metadata"]["disorder_width"]
        except (TypeError, ValueError) as e:
            pytest.fail(f"Output is not JSON serializable: {e}")

    def test_physical_reasonableness(self, scaling_result):
        """
        Verify values are physically reasonable.
        For W=1.0 and L up to 400, xi should be positive and finite.
        """
        xi = scaling_result["xi"]
        uncertainty = scaling_result["uncertainty"]
        
        # xi should be positive and not excessively large (e.g., > 10*L_max)
        max_L = max(scaling_result["system_sizes"])
        assert 0 < xi < max_L * 10, f"xi={xi} is physically unreasonable for L={max_L}"
        
        # Uncertainty should be less than xi
        assert uncertainty < xi, f"Uncertainty {uncertainty} exceeds xi {xi}"

    def test_r_squared_range(self, scaling_result):
        """Verify R^2 is between 0 and 1."""
        r2 = scaling_result["fit_params"]["r_squared"]
        assert 0 <= r2 <= 1.0, f"R^2={r2} is outside valid range [0, 1]"

    def test_disorder_width_matches_input(self, scaling_result):
        """Verify metadata records the correct disorder width."""
        # We hardcoded W=1.0 in the fixture
        assert scaling_result["metadata"]["disorder_width"] == 1.0

    def test_energy_window_in_metadata(self, scaling_result):
        """Verify energy window is recorded in metadata."""
        ew = scaling_result["metadata"]["energy_window"]
        assert "min" in ew and "max" in ew, "Energy window must have min and max keys."
        assert ew["min"] < 0 and ew["max"] > 0, "Energy window must span E=0."

    def test_method_recorded_in_metadata(self, scaling_result):
        """Verify method is recorded in metadata."""
        assert scaling_result["metadata"]["method"] == "finite_size_scaling"


# --- Execution Entry Point ---

def main():
    """Run the contract tests if executed as a script."""
    import subprocess
    import sys
    
    print("Running PR Schema Contract Tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd=project_root,
        capture_output=False
    )
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()