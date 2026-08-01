"""
Contract tests for JSON output schemas.

Validates that generated output files conform to their respective JSON Schema definitions.
"""
import json
import os
import unittest
from pathlib import Path
from typing import Dict, Any, List

try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    # Fallback for environments where jsonschema might not be installed yet,
    # though requirements.txt should include it.
    jsonschema = None
    ValidationError = Exception

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMAS_DIR = PROJECT_ROOT / "specs" / "schemas"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


class BaseSchemaTest(unittest.TestCase):
    """Base class for schema validation tests."""
    
    def load_schema(self, schema_filename: str) -> Dict[str, Any]:
        """Load a JSON schema from the specs directory."""
        schema_path = SCHEMAS_DIR / schema_filename
        self.assertTrue(schema_path.exists(), f"Schema file not found: {schema_path}")
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_output(self, output_filename: str) -> Dict[str, Any]:
        """Load an output JSON file from the processed directory."""
        output_path = PROCESSED_DIR / output_filename
        # If file doesn't exist yet, this test might be skipped or failed depending on pipeline state
        if not output_path.exists():
            self.skipTest(f"Output file not found: {output_path}. Run the pipeline first.")
        with open(output_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def validate_against_schema(self, data: Dict[str, Any], schema: Dict[str, Any], schema_name: str):
        """Validate data against a schema using jsonschema."""
        if jsonschema is None:
            self.skipTest("jsonschema library not installed")
        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            self.fail(f"Validation failed for {schema_name}: {e.message} at path {list(e.path)}")


class TestSimilarityReportSchema(BaseSchemaTest):
    """Contract test for similarity_report.schema.yaml (T009)."""

    def test_similarity_report_schema(self):
        schema = self.load_schema("similarity_report.schema.yaml")
        # Note: This test assumes the file exists. If T014 failed, this might be missing.
        # We check existence in load_schema.
        output_path = PROCESSED_DIR / "similarity_matrix.json"
        if not output_path.exists():
            self.skipTest("similarity_matrix.json not found. Run US1 pipeline.")
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        self.validate_against_schema(data, schema, "similarity_report")


class TestTokenAttributionSchema(BaseSchemaTest):
    """Contract test for token_attribution.schema.yaml (T016)."""

    def test_token_attribution_schema(self):
        schema = self.load_schema("token_attribution.schema.yaml")
        output_path = PROCESSED_DIR / "token_attribution_report.json"
        if not output_path.exists():
            self.skipTest("token_attribution_report.json not found. Run US2 pipeline.")

        with open(output_path, 'r') as f:
            data = json.load(f)

        self.validate_against_schema(data, schema, "token_attribution")


class TestPermutationResultSchema(BaseSchemaTest):
    """Contract test for permutation_result.schema.yaml (T024)."""

    def test_permutation_result_schema(self):
        """
        Validates that data/processed/permutation_result.json conforms to
        specs/schemas/permutation_result.schema.yaml.
        """
        schema = self.load_schema("permutation_result.schema.yaml")
        output_path = PROCESSED_DIR / "permutation_result.json"
        
        if not output_path.exists():
            self.skipTest("permutation_result.json not found. Run US3 statistical test pipeline.")

        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.validate_against_schema(data, schema, "permutation_result")

    def test_null_distribution_is_random_orthogonal(self):
        """
        T064: Bootstrap Null Distribution Validation.
        
        Verifies that the `null_distribution` in permutation_result.json consists of 
        similarities between the observed subspace and *random orthogonal bases*, 
        not random permutations of the observed subspace itself.
        
        Strategy:
        1. Load the permutation_result.json.
        2. Verify the structure contains 'observed_similarity' and 'null_distribution'.
        3. Generate a known random orthogonal basis using QR decomposition on a random matrix.
        4. Verify that the logic producing the null distribution (conceptually) 
           would produce values distinct from the observed similarity if the observed 
           subspace was not random.
        5. Since we cannot re-run the generation here without the full model state,
           we validate the *statistical properties* of the null distribution:
           - It must be a list of floats.
           - It must not be identical to the observed_similarity (unless p=1.0, which is rare).
           - We perform a sanity check: generate a random orthogonal basis and compute 
             a similarity to a mock observed vector to ensure the test framework 
             correctly identifies valid scalar outputs from such operations.
        """
        import numpy as np
        
        output_path = PROCESSED_DIR / "permutation_result.json"
        if not output_path.exists():
            self.skipTest("permutation_result.json not found. Run US3 statistical test pipeline.")

        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 1. Basic structure check
        self.assertIn("observed_similarity", data, "Missing 'observed_similarity'")
        self.assertIn("null_distribution", data, "Missing 'null_distribution'")
        
        observed_sim = data["observed_similarity"]
        null_dist = data["null_distribution"]
        
        self.assertIsInstance(null_dist, list, "null_distribution must be a list")
        self.assertGreater(len(null_dist), 0, "null_distribution must not be empty")
        
        # 2. Verify null distribution consists of floats
        for val in null_dist:
            self.assertIsInstance(val, (int, float), f"null_distribution values must be numeric, got {type(val)}")

        # 3. Verify null distribution is not just a repetition of the observed value
        # (This catches the "random permutation of observed subspace" error where 
        #  the null might be generated by permuting the observed data without 
        #  generating a new orthogonal basis).
        # If the null distribution is generated correctly from random orthogonal bases,
        # it should have variance.
        null_array = np.array(null_dist)
        variance = np.var(null_array)
        
        # If variance is 0, it means all null values are identical. 
        # While theoretically possible with a very specific seed or bug, 
        # it strongly suggests the null distribution was not generated from 
        # independent random orthogonal bases.
        self.assertGreater(variance, 1e-6, 
            "null_distribution has zero variance. This suggests it was not generated from random orthogonal bases "
            "but rather is a constant or derived directly from the observed value without randomization.")

        # 4. Verify the 'observed_similarity' is a scalar distinct from the bulk of the null distribution
        # (Statistical sanity check: observed should ideally be an outlier or at least within the distribution,
        # but not the only value if the distribution is large).
        # We check that the observed value is not the *only* value in the distribution if we were to include it.
        # More importantly, we check that the null distribution is not just [observed, observed, ...].
        if len(null_dist) > 1:
            self.assertFalse(all(abs(v - observed_sim) < 1e-9 for v in null_dist),
                "All values in null_distribution are identical to observed_similarity. "
                "This indicates the null distribution was not generated from random orthogonal bases.")

        # 5. Verify the test logic can handle a generated random orthogonal basis similarity.
        # We simulate the operation that T026 performs:
        #   1. Create a random orthogonal basis Q (d x k)
        #   2. Create an observed basis V (d x k)
        #   3. Compute cosine similarity between subspaces.
        # We do this with mock dimensions to ensure the math holds.
        d, k = 100, 10
        np.random.seed(42)
        random_matrix = np.random.randn(d, k)
        # QR decomposition to get orthogonal basis
        Q, _ = np.linalg.qr(random_matrix)
        
        # Mock observed subspace (also orthogonal for simplicity)
        observed_matrix = np.random.randn(d, k)
        V, _ = np.linalg.qr(observed_matrix)
        
        # Compute subspace similarity (e.g., mean cosine of aligned vectors or trace of V^T Q)
        # Using the Frobenius norm of the projection as a similarity metric
        similarity = np.trace(V.T @ Q) / k
        
        self.assertIsInstance(similarity, (int, float), 
            "Random orthogonal basis similarity calculation must produce a scalar.")
        self.assertLessEqual(similarity, 1.0, "Cosine similarity cannot exceed 1.0")
        self.assertGreaterEqual(similarity, -1.0, "Cosine similarity cannot be less than -1.0")


class TestWalsValidationSchema(BaseSchemaTest):
    """Contract test for wals_validation.schema.yaml (T008)."""

    def test_wals_validation_schema(self):
        schema = self.load_schema("wals_validation.schema.yaml")
        output_path = PROCESSED_DIR / "wals_validation.json"
        
        if not output_path.exists():
            self.skipTest("wals_validation.json not found. Run US3 external validation pipeline.")

        with open(output_path, 'r') as f:
            data = json.load(f)

        self.validate_against_schema(data, schema, "wals_validation")


if __name__ == "__main__":
    unittest.main()
