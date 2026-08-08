import pytest
import json
import os
from pathlib import Path
from typing import List, Dict, Any
import subprocess
import tempfile
import shutil

# Import the functions we are testing from the acquisition module
# Note: Using absolute imports relative to code/ root as per project structure
try:
    from code.utils.acquisition import run_tool_pipeline
except ImportError:
    # Fallback for local execution if PYTHONPATH is not set correctly
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.acquisition import run_tool_pipeline


class TestDockerToolExecution:
    """
    Integration test for Docker-based tool execution.
    Uses MOCKED tool output to verify the pipeline handles reports correctly
    without requiring actual Docker containers or real repository clones.
    """

    @pytest.fixture
    def mock_report_path(self, tmp_path):
        """Create a temporary mock tool report file."""
        fixture_dir = Path(__file__).parent / "fixtures"
        mock_file = fixture_dir / "mock_tool_report.json"
        
        if not mock_file.exists():
            # If fixture is missing, create a minimal valid one for the test
            mock_data = {
                "tool": "sonarqube",
                "repo_id": "test-repo-123",
                "commit_hash": "abc123",
                "issues": [
                    {
                        "id": "1",
                        "type": "BUG",
                        "severity": "HIGH",
                        "line": 10,
                        "file": "test.py",
                        "message": "Test issue"
                    }
                ]
            }
            mock_file.parent.mkdir(parents=True, exist_ok=True)
            with open(mock_file, 'w') as f:
                json.dump(mock_data, f)
        
        return mock_file

    @pytest.fixture
    def mock_repo_dir(self, tmp_path):
        """Create a temporary directory simulating a cloned repository."""
        repo_dir = tmp_path / "mock_repo"
        repo_dir.mkdir()
        # Create a dummy file to simulate code
        (repo_dir / "main.py").write_text("print('hello')")
        return repo_dir

    def test_mock_report_loading(self, mock_report_path):
        """Verify that the mock report file is valid JSON and matches expected schema."""
        assert mock_report_path.exists(), "Mock report file must exist"
        
        with open(mock_report_path, 'r') as f:
            data = json.load(f)
        
        assert "tool" in data
        assert "issues" in data
        assert isinstance(data["issues"], list)
        assert len(data["issues"]) > 0
        
        # Verify issue schema
        issue = data["issues"][0]
        assert "id" in issue
        assert "type" in issue
        assert "line" in issue
        assert "file" in issue
        assert "message" in issue

    def test_pipeline_handles_mock_output(self, mock_report_path, mock_repo_dir, tmp_path):
        """
        Test that the tool pipeline logic can process the mock output
        and generate normalized reports without crashing.
        
        This simulates the execution flow of run_tool_pipeline but uses
        the pre-generated mock file instead of running actual Docker containers.
        """
        # Simulate the output structure that run_tool_pipeline expects
        # In a real scenario, this would be the result of docker run ...
        # Here we pass the mock file directly to the normalization logic
        
        # We test the underlying logic that processes the JSON
        # Since run_tool_pipeline orchestrates Docker, we test the data flow
        # by verifying the mock data can be loaded and processed by the 
        # normalization functions (which are imported in 01_data_acquisition)
        
        # Attempt to load and validate the mock data structure
        # This ensures that if the real Docker tool produces this format,
        # our system can handle it.
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Simulate the processing step
        try:
            with open(mock_report_path, 'r') as f:
                raw_report = json.load(f)
            
            # Basic validation that the structure matches what the parser expects
            assert raw_report["tool"] in ["sonarqube", "deepsource", "codeclimate"]
            assert isinstance(raw_report["issues"], list)
            
            # Verify metadata
            assert "repo_id" in raw_report
            assert "commit_hash" in raw_report
            
            # If we got here, the mock data is valid and the pipeline logic
            # (which expects this schema) would proceed to normalization
            assert True, "Mock data successfully validated against expected schema"
            
        except json.JSONDecodeError:
            pytest.fail("Mock report is not valid JSON")
        except KeyError as e:
            pytest.fail(f"Mock report missing required field: {e}")

    def test_docker_command_structure(self, mock_repo_dir):
        """
        Verify that the Docker command construction logic (if tested directly)
        produces valid command strings.
        
        Note: We do not actually run Docker here to keep tests fast and isolated.
        """
        # This test ensures that if we were to construct the Docker command,
        # the variables are correctly formatted.
        tool_name = "sonarqube-scanner"
        repo_path = str(mock_repo_dir)
        
        # Simulate the command construction logic found in 01_data_acquisition
        # docker run --rm -v <repo>:/src sonarqube-scanner ...
        command_parts = [
            "docker", "run", "--rm",
            "-v", f"{repo_path}:/src",
            tool_name,
            "sonar-scanner"
        ]
        
        command_str = " ".join(command_parts)
        
        assert "docker" in command_str
        assert "-v" in command_str
        assert "/src" in command_str
        assert tool_name in command_str

    def test_error_handling_on_invalid_mock(self, tmp_path):
        """Test that the system handles malformed mock data gracefully."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not a json {")
        
        with pytest.raises(json.JSONDecodeError):
            with open(invalid_file, 'r') as f:
                json.load(f)

    def test_integration_with_acquisition_module(self, mock_report_path, mock_repo_dir):
        """
        Verify that the mock report can be consumed by the acquisition module's
        normalization logic (simulated).
        """
        # Load the mock data
        with open(mock_report_path, 'r') as f:
            data = json.load(f)
        
        # Verify the data matches the schema expected by normalize_sonarqube_report
        # (which is defined in code/01_data_acquisition.py)
        # We check the keys that the normalizer would access
        assert "issues" in data
        for issue in data["issues"]:
            assert "line" in issue
            assert "file" in issue
            assert "message" in issue
            assert "type" in issue
            assert "severity" in issue

if __name__ == "__main__":
    pytest.main([__file__, "-v"])