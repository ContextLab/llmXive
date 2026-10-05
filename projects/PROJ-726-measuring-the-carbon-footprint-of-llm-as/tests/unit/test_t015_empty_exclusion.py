"""
Unit tests for T015: Validation to exclude prompts that failed to generate code 
or resulted in empty strings from the output file.

This task ensures that the logic implemented in T014 (process_results/save_results)
correctly filters out invalid generations before writing to disk.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from aggregate_results import process_results, validate_schema, save_results


class TestEmptyExclusion:
    """Tests for filtering empty or failed code generations."""

    def test_excludes_empty_string_code(self):
        """Verify that records with empty string code are excluded."""
        test_data = [
            {
                "prompt_id": "valid_001",
                "model_used": "gpt2-medium",
                "energy_kWh": 0.001,
                "co2_kg": 0.0005,
                "generated_code": "def hello():\n    pass",
                "loc_count": 2
            },
            {
                "prompt_id": "empty_001",
                "model_used": "gpt2-medium",
                "energy_kWh": 0.0001,
                "co2_kg": 0.00005,
                "generated_code": "",  # Empty string
                "loc_count": 0
            }
        ]

        # Process results (this should filter out the empty one)
        processed = process_results(test_data)

        # Verify only valid record remains
        assert len(processed) == 1
        assert processed[0]["prompt_id"] == "valid_001"
        assert not any(r["prompt_id"] == "empty_001" for r in processed)

    def test_excludes_whitespace_only_code(self):
        """Verify that records with whitespace-only code are excluded."""
        test_data = [
            {
                "prompt_id": "valid_001",
                "model_used": "gpt2-medium",
                "energy_kWh": 0.001,
                "co2_kg": 0.0005,
                "generated_code": "x = 1",
                "loc_count": 1
            },
            {
                "prompt_id": "whitespace_001",
                "model_used": "gpt2-medium",
                "energy_kWh": 0.0001,
                "co2_kg": 0.00005,
                "generated_code": "   \n\n  ",  # Whitespace only
                "loc_count": 3  # Note: count_loc might count these, but we filter by stripped
            }
        ]

        processed = process_results(test_data)

        # Verify only valid record remains
        assert len(processed) == 1
        assert processed[0]["prompt_id"] == "valid_001"
        assert not any(r["prompt_id"] == "whitespace_001" for r in processed)

    def test_excludes_failed_generation_marker(self):
        """Verify that records with explicit failure markers are excluded."""
        test_data = [
            {
                "prompt_id": "valid_001",
                "model_used": "gpt2-medium",
                "energy_kWh": 0.001,
                "co2_kg": 0.0005,
                "generated_code": "print('hello')",
                "loc_count": 1
            },
            {
                "prompt_id": "failed_001",
                "model_used": "gpt2-medium",
                "energy_kWh": 0.0,
                "co2_kg": 0.0,
                "generated_code": None,  # None indicates failure
                "loc_count": 0
            }
        ]

        processed = process_results(test_data)

        assert len(processed) == 1
        assert processed[0]["prompt_id"] == "valid_001"
        assert not any(r["prompt_id"] == "failed_001" for r in processed)

    def test_all_valid_records_preserved(self):
        """Verify that all valid records are preserved."""
        test_data = [
            {
                "prompt_id": "valid_001",
                "model_used": "gpt2-medium",
                "energy_kWh": 0.001,
                "co2_kg": 0.0005,
                "generated_code": "def func():\n    return 1",
                "loc_count": 2
            },
            {
                "prompt_id": "valid_002",
                "model_used": "gpt2-medium",
                "energy_kWh": 0.002,
                "co2_kg": 0.001,
                "generated_code": "import os",
                "loc_count": 1
            }
        ]

        processed = process_results(test_data)

        assert len(processed) == 2
        prompt_ids = [r["prompt_id"] for r in processed]
        assert "valid_001" in prompt_ids
        assert "valid_002" in prompt_ids

    def test_integration_with_save_results(self):
        """Test that save_results only writes valid records to disk."""
        test_data = [
            {
                "prompt_id": "valid_001",
                "model_used": "gpt2-medium",
                "energy_kWh": 0.001,
                "co2_kg": 0.0005,
                "generated_code": "x = 1",
                "loc_count": 1
            },
            {
                "prompt_id": "invalid_001",
                "model_used": "gpt2-medium",
                "energy_kWh": 0.0,
                "co2_kg": 0.0,
                "generated_code": "",
                "loc_count": 0
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.json"
            
            # Save results
            save_results(test_data, str(output_path))
            
            # Read back and verify
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            assert len(saved_data) == 1
            assert saved_data[0]["prompt_id"] == "valid_001"
            assert "invalid_001" not in [r["prompt_id"] for r in saved_data]

    def test_schema_validation_after_filtering(self):
        """Verify that filtered results still pass schema validation."""
        test_data = [
            {
                "prompt_id": "valid_001",
                "model_used": "gpt2-medium",
                "energy_kWh": 0.001,
                "co2_kg": 0.0005,
                "generated_code": "print('test')",
                "loc_count": 1
            },
            {
                "prompt_id": "empty_001",
                "model_used": "gpt2-medium",
                "energy_kWh": 0.0,
                "co2_kg": 0.0,
                "generated_code": "",
                "loc_count": 0
            }
        ]

        processed = process_results(test_data)
        
        # Should pass schema validation
        is_valid, errors = validate_schema(processed)
        assert is_valid, f"Schema validation failed: {errors}"
        assert len(processed) == 1