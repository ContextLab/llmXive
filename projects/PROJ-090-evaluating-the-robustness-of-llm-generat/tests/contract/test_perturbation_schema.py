"""
Contract test for perturbation output schema (T011).

This test verifies that the perturbation generation pipeline produces
output that conforms to the expected schema, including required fields,
data types, and semantic similarity constraints.
"""
import pytest
import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.data.perturbations import substitute_synonyms, inject_typos, rephrase_syntax
from code.data.semantic_validator import validate_perturbation
from code.data.generate_perturbations import generate_and_filter_perturbations
import jsonschema


SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "perturbation_schema.json"


def load_schema():
    """Load the JSON schema from disk."""
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


class TestPerturbationSchema:
    """Test suite for perturbation output schema validation."""

    def test_synonym_perturbation_schema(self):
        """Verify synonym substitution output conforms to expected schema."""
        original_prompt = "Write a function to sort a list in ascending order."
        
        # Generate perturbation
        perturbed, perturbation_type = substitute_synonyms(original_prompt)
        
        # Validate schema
        assert isinstance(perturbed, str), "Perturbed prompt must be a string"
        assert len(perturbed) > 0, "Perturbed prompt must not be empty"
        assert isinstance(perturbation_type, str), "Perturbation type must be a string"
        assert perturbation_type == "synonym", "Type must be 'synonym'"
        
        # Check that perturbation is different from original
        assert perturbed != original_prompt, "Perturbation must differ from original"

    def test_typo_perturbation_schema(self):
        """Verify typo injection output conforms to expected schema."""
        original_prompt = "Write a function to calculate the factorial of a number."
        
        # Generate perturbation
        perturbed, perturbation_type = inject_typos(original_prompt)
        
        # Validate schema
        assert isinstance(perturbed, str), "Perturbed prompt must be a string"
        assert len(perturbed) > 0, "Perturbed prompt must not be empty"
        assert isinstance(perturbation_type, str), "Perturbation type must be a string"
        assert perturbation_type == "typo", "Type must be 'typo'"

    def test_rephrase_perturbation_schema(self):
        """Verify rephrasing output conforms to expected schema."""
        original_prompt = "Create a function that returns the sum of two numbers."
        
        # Generate perturbation
        perturbed, perturbation_type = rephrase_syntax(original_prompt)
        
        # Validate schema
        assert isinstance(perturbed, str), "Perturbed prompt must be a string"
        assert len(perturbed) > 0, "Perturbed prompt must not be empty"
        assert isinstance(perturbation_type, str), "Perturbation type must be a string"
        assert perturbation_type == "rephrase", "Type must be 'rephrase'"

    def test_semantic_similarity_threshold(self):
        """Verify that generated perturbations meet semantic similarity threshold."""
        original_prompt = "Write a function to find the maximum element in a list."
        
        # Generate multiple perturbations
        perturbations = [
            substitute_synonyms(original_prompt),
            inject_typos(original_prompt),
            rephrase_syntax(original_prompt)
        ]
        
        # Validate each perturbation
        for perturbed, pert_type in perturbations:
            similarity = validate_perturbation(original_prompt, perturbed)
            
            # Schema requirement: similarity must be a float between 0 and 1
            assert isinstance(similarity, float), "Similarity must be a float"
            assert 0.0 <= similarity <= 1.0, "Similarity must be between 0 and 1"
            
            # Semantic preservation requirement: similarity > 0.95
            assert similarity > 0.95, f"Perturbation {pert_type} failed semantic threshold: {similarity}"

    def test_full_perturbation_pipeline_output(self):
        """Verify the complete perturbation pipeline output schema."""
        # Use a simple mock task
        mock_task = {
            "task_id": "mock_task_001",
            "prompt": "Write a function to reverse a string.",
            "test": "assert reverse_string('hello') == 'olleh'"
        }
        
        # Generate perturbations
        results = generate_and_filter_perturbations(mock_task, max_variants=3)
        
        # Validate output structure
        assert isinstance(results, list), "Output must be a list"
        assert len(results) <= 3, "Must have at most 3 variants"
        
        schema = load_schema()
        
        for result in results:
            # Each result must have required fields
            assert "task_id" in result, "Missing task_id"
            assert "original_prompt" in result, "Missing original_prompt"
            assert "perturbed_prompt" in result, "Missing perturbed_prompt"
            assert "perturbation_type" in result, "Missing perturbation_type"
            assert "raw_score" in result, "Missing raw_score"
            assert "is_valid" in result, "Missing is_valid"
            
            # Validate data types
            assert isinstance(result["task_id"], str)
            assert isinstance(result["original_prompt"], str)
            assert isinstance(result["perturbed_prompt"], str)
            assert isinstance(result["perturbation_type"], str)
            assert isinstance(result["raw_score"], float)
            assert isinstance(result["is_valid"], bool)
            
            # Validate against full JSON schema
            jsonschema.validate(instance=result, schema=schema["definitions"]["PerturbationRecord"])
            
            # Validate semantic constraint
            if result["is_valid"]:
                assert result["raw_score"] > 0.95, "Valid perturbations must have similarity > 0.95"

    def test_schema_definition_fields(self):
        """Verify the schema definition contains all required fields."""
        schema = load_schema()
        record_def = schema["definitions"]["PerturbationRecord"]
        
        required_fields = ["task_id", "perturbation_type", "raw_score", "is_valid"]
        
        for field in required_fields:
            assert field in record_def["required"], f"Required field '{field}' missing from schema"
            assert field in record_def["properties"], f"Field '{field}' missing from properties"