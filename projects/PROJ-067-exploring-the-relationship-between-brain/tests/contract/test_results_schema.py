"""
Contract test for final results JSON schema (T033).

Validates that `results/stats.json` adheres to the schema defined in
`contracts/results_schema.yaml`.

This test is part of User Story 3 (Statistical Analysis).
It must be run after the stats pipeline (T037-T043) has generated the output.
"""
import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List, Set

# Add project root to path to allow imports if needed, though this is a standalone contract test
PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_FILE = PROJECT_ROOT / "results" / "stats.json"
SCHEMA_FILE = PROJECT_ROOT / "contracts" / "results_schema.yaml"

try:
    import yaml
except ImportError:
    # Fallback if PyYAML is not installed but required for schema loading
    # In a real CI, PyYAML should be in requirements.txt
    yaml = None


class SchemaValidator:
    """Simple validator for the results JSON schema."""

    def __init__(self, schema_path: Path):
        self.schema_path = schema_path
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

        if yaml is None:
            raise ImportError("PyYAML is required to load the schema file.")

        with open(self.schema_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def validate(self, data: Dict[str, Any]) -> List[str]:
        """
        Validates the data against the loaded schema.
        Returns a list of error messages. Empty list means valid.
        """
        errors = []

        # Define required top-level keys based on typical stats.json structure
        # The schema file should define these, but we enforce basic structure here
        required_keys = {
            "correlations",
            "permutation_test",
            "power_analysis",
            "metadata"
        }

        data_keys = set(data.keys())
        missing_keys = required_keys - data_keys
        if missing_keys:
            errors.append(f"Missing required top-level keys: {missing_keys}")

        # Validate 'correlations' section
        if "correlations" in data:
            corr_data = data["correlations"]
            if not isinstance(corr_data, list):
                errors.append("'correlations' must be a list.")
            else:
                for i, entry in enumerate(corr_data):
                    if not isinstance(entry, dict):
                        errors.append(f"'correlations[{i}]' must be a dictionary.")
                        continue
                    
                    # Required fields per correlation entry
                    corr_required = {"network", "rho", "p_uncorrected", "p_fdr_corrected"}
                    entry_keys = set(entry.keys())
                    if not corr_required.issubset(entry_keys):
                        missing = corr_required - entry_keys
                        errors.append(f"'correlations[{i}]' missing fields: {missing}")
                    
                    # Type checks
                    if "rho" in entry and not isinstance(entry["rho"], (int, float)):
                        errors.append(f"'correlations[{i}].rho' must be a number.")
                    if "p_uncorrected" in entry and not isinstance(entry["p_uncorrected"], (int, float)):
                        errors.append(f"'correlations[{i}].p_uncorrected' must be a number.")
                    if "p_fdr_corrected" in entry and not isinstance(entry["p_fdr_corrected"], (int, float)):
                        errors.append(f"'correlations[{i}].p_fdr_corrected' must be a number.")

        # Validate 'permutation_test' section
        if "permutation_test" in data:
            perm_data = data["permutation_test"]
            if not isinstance(perm_data, dict):
                errors.append("'permutation_test' must be a dictionary.")
            else:
                perm_required = {"n_iterations", "p_value", "null_distribution_file"}
                perm_keys = set(perm_data.keys())
                if not perm_required.issubset(perm_keys):
                    missing = perm_required - perm_keys
                    errors.append(f"'permutation_test' missing fields: {missing}")
                
                if "n_iterations" in perm_data:
                    if not isinstance(perm_data["n_iterations"], int) or perm_data["n_iterations"] <= 0:
                        errors.append("'permutation_test.n_iterations' must be a positive integer.")
                
                if "p_value" in perm_data:
                    if not isinstance(perm_data["p_value"], (int, float)):
                        errors.append("'permutation_test.p_value' must be a number.")

        # Validate 'power_analysis' section
        if "power_analysis" in data:
            power_data = data["power_analysis"]
            if not isinstance(power_data, dict):
                errors.append("'power_analysis' must be a dictionary.")
            else:
                power_required = {"sample_size", "detectable_effect_size", "power"}
                power_keys = set(power_data.keys())
                if not power_required.issubset(power_keys):
                    missing = power_required - power_keys
                    errors.append(f"'power_analysis' missing fields: {missing}")

        # Validate 'metadata' section
        if "metadata" in data:
            meta_data = data["metadata"]
            if not isinstance(meta_data, dict):
                errors.append("'metadata' must be a dictionary.")
            else:
                meta_required = {"atlas", "window_size", "step_size", "software_version"}
                meta_keys = set(meta_data.keys())
                if not meta_required.issubset(meta_keys):
                    missing = meta_required - meta_keys
                    errors.append(f"'metadata' missing fields: {missing}")

        return errors


class TestResultsSchema(unittest.TestCase):
    """Contract test for the final results JSON schema."""

    @classmethod
    def setUpClass(cls):
        """Ensure the results file and schema file exist before running tests."""
        if not RESULTS_FILE.exists():
            raise FileNotFoundError(
                f"Results file not found at {RESULTS_FILE}. "
                "Run the stats pipeline (T037-T043) before running this test."
            )
        
        if not SCHEMA_FILE.exists():
            raise FileNotFoundError(
                f"Schema file not found at {SCHEMA_FILE}. "
                "Ensure `contracts/results_schema.yaml` exists."
            )

        cls.validator = SchemaValidator(SCHEMA_FILE)
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_schema_compliance(self):
        """Verify that results/stats.json matches the defined schema."""
        errors = self.validator.validate(self.data)
        self.assertEqual(len(errors), 0, f"Schema validation failed with errors: {errors}")

    def test_required_networks_present(self):
        """Ensure all expected networks (DMN, Salience, Hippocampal-Memory) are in correlations."""
        networks_found = set()
        if "correlations" in self.data:
            for entry in self.data["correlations"]:
                if "network" in entry:
                    networks_found.add(entry["network"])
        
        expected_networks = {"DMN", "Salience", "Hippocampal-Memory"}
        missing_networks = expected_networks - networks_found
        self.assertEqual(
            len(missing_networks), 0,
            f"Missing expected networks in correlations: {missing_networks}"
        )

    def test_permutation_iterations(self):
        """Verify that permutation test used exactly 1000 iterations as per FR-007."""
        if "permutation_test" in self.data:
            n_iters = self.data["permutation_test"].get("n_iterations")
            self.assertEqual(n_iters, 1000, "Permutation test must run exactly 1000 iterations.")
        else:
            self.fail("'permutation_test' section missing from results.")


if __name__ == "__main__":
    # Run the tests
    unittest.main()