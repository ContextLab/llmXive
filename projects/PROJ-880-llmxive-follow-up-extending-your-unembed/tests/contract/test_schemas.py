"""
Contract tests for JSON output schemas.
Ensures that generated artifacts conform to their defined YAML schemas.
"""
import json
import os
import unittest
from pathlib import Path
from typing import Any, Dict

import yaml

# Ensure we can import from the project root if running via python -m
try:
    from config import get_path
except ImportError:
    # Fallback for direct execution in tests directory
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from config import get_path


def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a schema from the contracts directory."""
    schema_path = Path("contracts") / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_json_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Basic JSON Schema validation (subset implementation for required fields and types).
    Since PyYAML doesn't validate, we implement a minimal validator for the critical
    fields defined in the schemas to ensure contract compliance.
    """
    # Check required top-level keys
    required = schema.get("required", [])
    for key in required:
        if key not in data:
            raise AssertionError(f"Missing required top-level field: {key}")

    # Check property types and required sub-fields for specific schemas
    properties = schema.get("properties", {})

    # --- Specific validation for similarity_report.schema.yaml ---
    if schema.get("title") == "SimilarityReport":
        if "metadata" in data:
            meta_req = properties["metadata"].get("required", [])
            for key in meta_req:
                if key not in data["metadata"]:
                    raise AssertionError(f"Missing required field in metadata: {key}")
        if "results" in data:
            if not isinstance(data["results"], list):
                raise AssertionError("Results must be a list")

    # --- Specific validation for token_attribution.schema.yaml ---
    elif schema.get("title") == "TokenAttributionReport":
        if "metadata" in data:
            meta_req = properties["metadata"].get("required", [])
            for key in meta_req:
                if key not in data["metadata"]:
                    raise AssertionError(f"Missing required field in metadata: {key}")
        
        if "results" in data:
            if not isinstance(data["results"], list):
                raise AssertionError("Results must be a list")
            
            item_schema = properties["results"]["items"]
            item_req = item_schema.get("required", [])
            
            for i, item in enumerate(data["results"]):
                if not isinstance(item, dict):
                    raise AssertionError(f"Result item {i} must be an object")
                for key in item_req:
                    if key not in item:
                        raise AssertionError(f"Missing required field in result item {i}: {key}")
                
                # Type checks
                if "token_id" in item and not isinstance(item["token_id"], int):
                    raise AssertionError(f"token_id in item {i} must be an integer")
                if "projection_score" in item and not isinstance(item["projection_score"], (int, float)):
                    raise AssertionError(f"projection_score in item {i} must be a number")
                if "frequency" in item and not isinstance(item["frequency"], (int, float)):
                    raise AssertionError(f"frequency in item {i} must be a number")
    
    # --- Specific validation for permutation_result.schema.yaml ---
    elif schema.get("title") == "PermutationResult":
        if "metadata" in data:
            meta_req = properties["metadata"].get("required", [])
            for key in meta_req:
                if key not in data["metadata"]:
                    raise AssertionError(f"Missing required field in metadata: {key}")
        if "null_distribution" in data:
            if not isinstance(data["null_distribution"], list):
                raise AssertionError("null_distribution must be a list")
        if "p_value" in data:
            if not isinstance(data["p_value"], (int, float)):
                raise AssertionError("p_value must be a number")
    
    return True


class TestSimilarityReportSchema(unittest.TestCase):
    """Contract test for similarity_report.schema.yaml"""
    
    def test_schema_file_exists(self):
        schema_path = Path("contracts") / "similarity_report.schema.yaml"
        self.assertTrue(schema_path.exists(), "similarity_report.schema.yaml must exist")
    
    def test_output_conforms_to_schema(self):
        """
        Validates the actual generated similarity matrix if it exists.
        If the file doesn't exist yet (T014 not run), this test is skipped.
        """
        schema = load_schema("similarity_report.schema.yaml")
        output_path = Path("data") / "processed" / "similarity_matrix.json"
        
        if not output_path.exists():
            self.skipTest(f"Output file {output_path} not found. Run T014 first.")
        
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.assertTrue(validate_json_against_schema(data, schema))


class TestTokenAttributionSchema(unittest.TestCase):
    """Contract test for token_attribution.schema.yaml"""
    
    def test_schema_file_exists(self):
        schema_path = Path("contracts") / "token_attribution.schema.yaml"
        self.assertTrue(schema_path.exists(), "token_attribution.schema.yaml must exist")
    
    def test_output_conforms_to_schema(self):
        """
        Validates the actual generated token attribution report if it exists.
        If the file doesn't exist yet, this test is skipped.
        """
        schema = load_schema("token_attribution.schema.yaml")
        output_path = Path("data") / "processed" / "token_attribution_report.json"
        
        if not output_path.exists():
            self.skipTest(f"Output file {output_path} not found. Run T023 first.")
        
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.assertTrue(validate_json_against_schema(data, schema))


class TestPermutationResultSchema(unittest.TestCase):
    """Contract test for permutation_result.schema.yaml"""
    
    def test_schema_file_exists(self):
        schema_path = Path("contracts") / "permutation_result.schema.yaml"
        self.assertTrue(schema_path.exists(), "permutation_result.schema.yaml must exist")
    
    def test_output_conforms_to_schema(self):
        """
        Validates the actual generated permutation result if it exists.
        If the file doesn't exist yet, this test is skipped.
        """
        schema = load_schema("permutation_result.schema.yaml")
        output_path = Path("data") / "processed" / "permutation_result.json"
        
        if not output_path.exists():
            self.skipTest(f"Output file {output_path} not found. Run T030 first.")
        
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.assertTrue(validate_json_against_schema(data, schema))


if __name__ == "__main__":
    unittest.main()