import json
import os
import sys
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.contract_validation import validate_schema, load_contract, ContractValidationError

class TestDecompositionResultsSchema:
    """Contract test for decomposition output schema validating Ljung-Box result."""
    
    @pytest.fixture
    def result_path(self):
        """Path to decomposition_results.json"""
        return project_root / "data" / "processed" / "decomposition_results.json"
    
    def test_file_exists(self, result_path):
        """Test that the decomposition results file exists."""
        assert result_path.exists(), f"File not found: {result_path}"
    
    def test_valid_json(self, result_path):
        """Test that the file contains valid JSON."""
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert isinstance(data, dict), "Root element must be a dictionary"
    
    def test_required_metadata(self, result_path):
        """Test that metadata section contains required fields."""
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "metadata" in data, "Missing 'metadata' section"
        metadata = data["metadata"]
        
        assert "generated_from" in metadata, "Missing 'generated_from' in metadata"
        assert "description" in metadata, "Missing 'description' in metadata"
        assert "fr_references" in metadata, "Missing 'fr_references' in metadata"
        
        # Verify FR references include FR-009 and FR-012
        assert "FR-009" in metadata["fr_references"], "FR-009 reference missing"
        assert "FR-012" in metadata["fr_references"], "FR-012 reference missing"
    
    def test_results_structure(self, result_path):
        """Test that results section exists and has expected structure."""
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "results" in data, "Missing 'results' section"
        assert isinstance(data["results"], dict), "'results' must be a dictionary"
    
    def test_ljung_box_tests_present(self, result_path):
        """Test that Ljung-Box test results are present."""
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "ljung_box_tests" in data, "Missing 'ljung_box_tests' section"
        assert isinstance(data["ljung_box_tests"], list), "'ljung_box_tests' must be a list"
        
        if len(data["ljung_box_tests"]) > 0:
            # Check structure of first test result
            first_test = data["ljung_box_tests"][0]
            assert "tag" in first_test, "Missing 'tag' in Ljung-Box test result"
            assert "statistic" in first_test, "Missing 'statistic' in Ljung-Box test result"
            assert "p_value" in first_test, "Missing 'p_value' in Ljung-Box test result"
            assert "lag" in first_test, "Missing 'lag' in Ljung-Box test result"
    
    def test_rayleigh_tests_present(self, result_path):
        """Test that Rayleigh test results are present."""
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "rayleigh_tests" in data, "Missing 'rayleigh_tests' section"
        assert isinstance(data["rayleigh_tests"], list), "'rayleigh_tests' must be a list"
        
        if len(data["rayleigh_tests"]) > 0:
            # Check structure of first test result
            first_test = data["rayleigh_tests"][0]
            assert "tag" in first_test, "Missing 'tag' in Rayleigh test result"
            assert "r_statistic" in first_test, "Missing 'r_statistic' in Rayleigh test result"
            assert "p_value" in first_test, "Missing 'p_value' in Rayleigh test result"
            assert "alignment" in first_test, "Missing 'alignment' in Rayleigh test result"
    
    def test_summary_statistics(self, result_path):
        """Test that summary statistics are present and valid."""
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "summary" in data, "Missing 'summary' section"
        summary = data["summary"]
        
        required_fields = [
            "total_tags_analyzed",
            "seasonal_tags",
            "non_seasonal_tags",
            "significant_ljung_box",
            "significant_rayleigh_alignment"
        ]
        
        for field in required_fields:
            assert field in summary, f"Missing '{field}' in summary"
            assert isinstance(summary[field], (int, float)), f"'{field}' must be numeric"
        
        # Verify counts make sense
        assert summary["total_tags_analyzed"] >= 0, "Total tags cannot be negative"
        assert summary["seasonal_tags"] + summary["non_seasonal_tags"] <= summary["total_tags_analyzed"], \
            "Seasonal + non-seasonal cannot exceed total"
    
    def test_ljung_box_contract(self, result_path):
        """Validate Ljung-Box test results against contract schema."""
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        ljung_box_tests = data.get("ljung_box_tests", [])
        
        for test in ljung_box_tests:
            # Each test must have valid structure
            assert "tag" in test and isinstance(test["tag"], str), "Invalid tag format"
            assert "statistic" in test and isinstance(test["statistic"], (int, float)), "Invalid statistic format"
            assert "p_value" in test and isinstance(test["p_value"], (int, float)), "Invalid p_value format"
            assert "lag" in test and isinstance(test["lag"], int), "Invalid lag format"
            
            # P-value must be between 0 and 1
            assert 0 <= test["p_value"] <= 1, f"P-value out of range for tag {test['tag']}"
            
            # Lag should be 12 as per FR-009
            assert test["lag"] == 12, f"Expected lag=12, got {test['lag']} for tag {test['tag']}"
    
    def test_rayleigh_contract(self, result_path):
        """Validate Rayleigh test results against contract schema."""
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        rayleigh_tests = data.get("rayleigh_tests", [])
        
        for test in rayleigh_tests:
            # Each test must have valid structure
            assert "tag" in test and isinstance(test["tag"], str), "Invalid tag format"
            assert "r_statistic" in test and isinstance(test["r_statistic"], (int, float)), "Invalid r_statistic format"
            assert "p_value" in test and isinstance(test["p_value"], (int, float)), "Invalid p_value format"
            assert "alignment" in test and isinstance(test["alignment"], str), "Invalid alignment format"
            
            # P-value must be between 0 and 1
            assert 0 <= test["p_value"] <= 1, f"P-value out of range for tag {test['tag']}"
            
            # Alignment should be one of the expected values
            valid_alignments = ["aligned", "not_aligned", "insufficient_data"]
            assert test["alignment"] in valid_alignments, \
                f"Invalid alignment '{test['alignment']}' for tag {test['tag']}"
    
    def test_sha256_in_state(self):
        """Test that the decomposition_results.json hash is in the state file."""
        result_path = project_root / "data" / "processed" / "decomposition_results.json"
        state_path = project_root / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"
        
        assert result_path.exists(), "decomposition_results.json not found"
        assert state_path.exists(), "State file not found"
        
        from utils.hygiene import calculate_sha256, load_state
        
        expected_hash = calculate_sha256(result_path)
        state = load_state(state_path)
        
        assert "artifacts" in state, "Missing 'artifacts' in state file"
        
        # Check if our file is in the artifacts with correct hash
        found = False
        for artifact_path, artifact_hash in state["artifacts"].items():
            if "decomposition_results.json" in artifact_path:
                assert artifact_hash == expected_hash, \
                    f"Hash mismatch for decomposition_results.json: expected {expected_hash}, got {artifact_hash}"
                found = True
                break
        
        assert found, "decomposition_results.json not found in state file artifacts"
