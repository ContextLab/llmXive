import os
import sys
import yaml
import pytest
from pathlib import Path

# Base path for contracts relative to project root
CONTRACTS_DIR = Path("contracts")

REQUIRED_CONTRACTS = [
    "download_contract.yaml",
    "preprocess_contract.yaml",
    "graph_contract.yaml",
    "stats_contract.yaml"
]

class TestContractsExist:
    """Test that all required contract files exist."""

    @pytest.mark.parametrize("contract_file", REQUIRED_CONTRACTS)
    def test_contract_file_exists(self, contract_file):
        """Verify each contract file exists."""
        contract_path = CONTRACTS_DIR / contract_file
        assert contract_path.exists(), f"Contract file missing: {contract_path}"

    @pytest.mark.parametrize("contract_file", REQUIRED_CONTRACTS)
    def test_contract_is_valid_yaml(self, contract_file):
        """Verify each contract file contains valid YAML."""
        contract_path = CONTRACTS_DIR / contract_file
        with open(contract_path, 'r') as f:
            try:
                data = yaml.safe_load(f)
                assert isinstance(data, dict), f"Contract {contract_file} is not a valid YAML dictionary"
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {contract_file}: {e}")

class TestContractSchemas:
    """Test that contracts define required input/output schemas."""

    def test_download_contract_schema(self):
        """Verify download_contract.yaml has required input/output keys."""
        contract_path = CONTRACTS_DIR / "download_contract.yaml"
        with open(contract_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert "input" in data, "download_contract missing 'input' section"
        assert "output" in data, "download_contract missing 'output' section"
        
        input_keys = set(data["input"].keys())
        assert "dataset_id" in input_keys, "download_contract input missing 'dataset_id'"
        assert "output_dir" in input_keys, "download_contract input missing 'output_dir'"
        assert "n_subjects" in input_keys, "download_contract input missing 'n_subjects'"
        
        output_keys = set(data["output"].keys())
        assert "valid_subjects_json" in output_keys, "download_contract output missing 'valid_subjects_json'"
        assert "error_log" in output_keys, "download_contract output missing 'error_log'"

    def test_preprocess_contract_schema(self):
        """Verify preprocess_contract.yaml has required input/output keys."""
        contract_path = CONTRACTS_DIR / "preprocess_contract.yaml"
        with open(contract_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert "input" in data, "preprocess_contract missing 'input' section"
        assert "output" in data, "preprocess_contract missing 'output' section"
        
        input_keys = set(data["input"].keys())
        assert "bids_dir" in input_keys, "preprocess_contract input missing 'bids_dir'"
        assert "subject_id" in input_keys, "preprocess_contract input missing 'subject_id'"
        
        output_keys = set(data["output"].keys())
        assert "preprocessed_nifti" in output_keys, "preprocess_contract output missing 'preprocessed_nifti'"
        assert "motion_log" in output_keys, "preprocess_contract output missing 'motion_log'"

    def test_graph_contract_schema(self):
        """Verify graph_contract.yaml has required input/output keys."""
        contract_path = CONTRACTS_DIR / "graph_contract.yaml"
        with open(contract_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert "input" in data, "graph_contract missing 'input' section"
        assert "output" in data, "graph_contract missing 'output' section"
        
        input_keys = set(data["input"].keys())
        assert "preprocessed_nifti" in input_keys, "graph_contract input missing 'preprocessed_nifti'"
        assert "atlas_file" in input_keys, "graph_contract input missing 'atlas_file'"
        
        output_keys = set(data["output"].keys())
        assert "connectivity_matrix" in output_keys, "graph_contract output missing 'connectivity_matrix'"
        assert "graph_metrics_csv" in output_keys, "graph_contract output missing 'graph_metrics_csv'"

    def test_stats_contract_schema(self):
        """Verify stats_contract.yaml has required input/output keys."""
        contract_path = CONTRACTS_DIR / "stats_contract.yaml"
        with open(contract_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert "input" in data, "stats_contract missing 'input' section"
        assert "output" in data, "stats_contract missing 'output' section"
        
        input_keys = set(data["input"].keys())
        assert "graph_metrics_csv" in input_keys, "stats_contract input missing 'graph_metrics_csv'"
        assert "behavioral_scores_csv" in input_keys, "stats_contract input missing 'behavioral_scores_csv'"
        
        output_keys = set(data["output"].keys())
        assert "correlation_results_csv" in output_keys, "stats_contract output missing 'correlation_results_csv'"
        assert "report_pdf" in output_keys, "stats_contract output missing 'report_pdf'"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])