import pytest
import os
import csv
import base64
import torch
import json
from pathlib import Path

# Assuming the output path is defined in config or fixed
BASELINE_VECTORS_PATH = Path("data/processed/baseline_vectors.csv")

class TestBaselineVectorContract:
    """
    Contract test for the baseline_vectors.csv output schema.
    Verifies that the file structure, column names, and data types match the spec.
    """

    @pytest.fixture
    def mock_data(self, tmp_path):
        """Create a mock baseline_vectors.csv for testing the contract logic."""
        # We don't run the full pipeline here, just verify the contract logic
        # against a known good structure.
        pass

    def test_file_exists(self):
        """
        Contract: The baseline extraction task MUST produce data/processed/baseline_vectors.csv.
        Note: This test might fail in CI if the pipeline hasn't run yet.
        It validates the existence requirement.
        """
        # In a real CI/CD flow, this would run after T015 execution.
        # For now, we assert the path is correct.
        assert BASELINE_VECTORS_PATH.exists(), "baseline_vectors.csv must exist after T015 execution."

    def test_schema_columns(self):
        """
        Contract: Verify the CSV has the required columns:
        pair_id, task_type, vector_base64, norm_status
        """
        if not BASELINE_VECTORS_PATH.exists():
            pytest.skip("baseline_vectors.csv not found; run T015 first.")

        with open(BASELINE_VECTORS_PATH, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            required_columns = {'pair_id', 'task_type', 'vector_base64', 'norm_status'}
            assert required_columns.issubset(set(headers)), f"Missing columns. Expected {required_columns}, got {headers}"

    def test_vector_base64_decodes_and_matches_hidden_size(self, model_config_fixture=None):
        """
        Contract: The 'vector_base64' column must contain valid base64-encoded floats
        that, when decoded, match the model's hidden dimension.
        """
        if not BASELINE_VECTORS_PATH.exists():
            pytest.skip("baseline_vectors.csv not found; run T015 first.")

        # Mock model config if not provided (or load from config.py if available)
        # For this contract test, we assume a standard hidden size or read from a config.
        # In a real scenario, we'd import from config.ModelConfig.
        expected_hidden_size = 4096 # Placeholder, should be dynamic in real test

        with open(BASELINE_VECTORS_PATH, 'r') as f:
            reader = csv.DictReader(f)
            row_count = 0
            for row in reader:
                row_count += 1
                try:
                    vector_bytes = base64.b64decode(row['vector_base64'])
                    # Decode as float32
                    vector = torch.frombuffer(vector_bytes, dtype=torch.float32)
                    
                    # Check dimension
                    assert vector.shape[0] == expected_hidden_size, \
                        f"Vector dimension {vector.shape[0]} does not match expected {expected_hidden_size}"
                    
                    # Check norm status logic (optional but good for contract)
                    norm = torch.linalg.norm(vector).item()
                    if row['norm_status'] == 'normalized':
                        assert math.isclose(norm, 1.0, rel_tol=1e-5), \
                            f"Vector marked as normalized but norm is {norm}"
                except Exception as e:
                    pytest.fail(f"Failed to decode or validate vector in row {row_count}: {e}")

    def test_norm_status_values(self):
        """
        Contract: The 'norm_status' column should only contain valid status strings.
        """
        if not BASELINE_VECTORS_PATH.exists():
            pytest.skip("baseline_vectors.csv not found; run T015 first.")

        valid_statuses = {'normalized', 'error', 'skipped'}
        
        with open(BASELINE_VECTORS_PATH, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                status = row['norm_status']
                assert status in valid_statuses, f"Invalid norm_status '{status}'. Expected one of {valid_statuses}"
