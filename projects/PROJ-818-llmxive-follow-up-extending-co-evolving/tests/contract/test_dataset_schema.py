"""
Contract tests for dataset schema validation.
Ensures generated data conforms to the defined JSON schema.
"""
import json
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports if running as script
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.contract.schemas import validate_dataset, DATASET_SCHEMA

class TestDatasetSchema:
    """Tests for the dataset schema validator."""

    def test_valid_logic_proof_dataset(self):
        """Test a valid dataset containing logic proofs."""
        valid_data = {
            "metadata": {
                "version": "1.0.0",
                "seed": 42,
                "generator": "LogicProofGenerator",
                "timestamp": "2023-10-27T10:00:00Z",
                "checksum": "abc123"
            },
            "data": [
                {
                    "type": "logic_proof",
                    "id": "proof_001",
                    "axioms": ["A", "A -> B"],
                    "conclusion": "B",
                    "proof_steps": [
                        {"step": 1, "rule": "Modus Ponens", "derived": "B"}
                    ]
                }
            ]
        }
        result = validate_dataset(valid_data)
        assert result.valid, f"Validation failed: {result.errors}"

    def test_valid_grid_world_dataset(self):
        """Test a valid dataset containing grid worlds."""
        valid_data = {
            "metadata": {
                "version": "1.0.0",
                "seed": 123,
                "generator": "GridWorldGenerator",
                "timestamp": "2023-10-27T10:00:00Z",
                "checksum": "def456"
            },
            "data": [
                {
                    "type": "grid_world",
                    "id": "grid_001",
                    "grid_size": [5, 5],
                    "start": [0, 0],
                    "end": [4, 4],
                    "obstacles": [[1, 1], [2, 2]],
                    "rules": ["avoid_red", "diagonal_allowed"]
                }
            ]
        }
        result = validate_dataset(valid_data)
        assert result.valid, f"Validation failed: {result.errors}"

    def test_invalid_missing_metadata(self):
        """Test that missing metadata causes validation failure."""
        invalid_data = {
            "data": []
        }
        result = validate_dataset(invalid_data)
        assert not result.valid
        assert any("Missing required property 'metadata'" in str(e.message) for e in result.errors)

    def test_invalid_wrong_type_in_data(self):
        """Test that wrong type in data items causes validation failure."""
        invalid_data = {
            "metadata": {
                "version": "1.0.0",
                "seed": 42,
                "generator": "Test",
                "timestamp": "2023-10-27T10:00:00Z",
                "checksum": "xyz"
            },
            "data": [
                {
                    "type": "logic_proof",
                    "id": 123, # Should be string
                    "axioms": [],
                    "conclusion": "X",
                    "proof_steps": []
                }
            ]
        }
        result = validate_dataset(invalid_data)
        assert not result.valid
        assert any("Expected type 'string'" in str(e.message) for e in result.errors)

    def test_invalid_mixed_types_in_data(self):
        """Test mixed valid types in data array."""
        valid_data = {
            "metadata": {
                "version": "1.0.0",
                "seed": 42,
                "generator": "Test",
                "timestamp": "2023-10-27T10:00:00Z",
                "checksum": "xyz"
            },
            "data": [
                {
                    "type": "logic_proof",
                    "id": "p1",
                    "axioms": ["A"],
                    "conclusion": "B",
                    "proof_steps": []
                },
                {
                    "type": "grid_world",
                    "id": "g1",
                    "grid_size": [3, 3],
                    "start": [0, 0],
                    "end": [2, 2],
                    "obstacles": [],
                    "rules": []
                }
            ]
        }
        result = validate_dataset(valid_data)
        assert result.valid

    def test_invalid_missing_required_proof_fields(self):
        """Test missing required fields in a logic proof."""
        invalid_data = {
            "metadata": {
                "version": "1.0.0",
                "seed": 42,
                "generator": "Test",
                "timestamp": "2023-10-27T10:00:00Z",
                "checksum": "xyz"
            },
            "data": [
                {
                    "type": "logic_proof",
                    "id": "p1",
                    # Missing axioms, conclusion, proof_steps
                }
            ]
        }
        result = validate_dataset(invalid_data)
        assert not result.valid
        assert any("Missing required property" in str(e.message) for e in result.errors)
