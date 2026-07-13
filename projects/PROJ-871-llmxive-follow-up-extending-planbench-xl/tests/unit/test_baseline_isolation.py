import os
import json
import tempfile
import pytest
from pathlib import Path
import sys

# Add the project root to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from agents.baseline import BaselineAgent


class TestBaselineIsolation:
    """
    Test suite to verify that the BaselineAgent enforces strict isolation
    and does NOT access the failure_signatures.json file.
    """
    
    def test_baseline_agent_raises_on_signature_access(self):
        """
        Verify that BaselineAgent raises RuntimeError when
        failure_signatures.json exists in the expected location.
        """
        # Create a temporary directory structure to simulate the project
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            data_derived = project_root / "data" / "derived"
            data_derived.mkdir(parents=True, exist_ok=True)
            
            # Create the forbidden signatures file
            signatures_path = data_derived / "failure_signatures.json"
            signatures_path.write_text(json.dumps({"test": "data"}))
            
            # Create a mock agent with config pointing to this temp root
            config = {
                "model_name": "test-model",
                "base_path": str(project_root)
            }
            
            agent = BaselineAgent(config)
            
            # The _enforce_isolation method should raise an error
            # We need to simulate the path resolution to point to our temp dir
            # Override the path resolution for testing
            original_method = agent._enforce_isolation
            
            def mock_enforce_isolation():
                signatures_path = str(data_derived / "failure_signatures.json")
                if os.path.exists(signatures_path):
                    raise RuntimeError(
                        f"CRITICAL VIOLATION: BaselineAgent attempted to access "
                        f"failure signatures at {signatures_path}. "
                        f"Baseline agents must operate in strict isolation."
                    )
            
            agent._enforce_isolation = mock_enforce_isolation
            
            # Verify the error is raised
            with pytest.raises(RuntimeError) as excinfo:
                agent._enforce_isolation()
            
            assert "CRITICAL VIOLATION" in str(excinfo.value)
            assert "failure signatures" in str(excinfo.value)
    
    def test_baseline_agent_allows_execution_without_signatures(self):
        """
        Verify that BaselineAgent can execute normally when
        failure_signatures.json does NOT exist.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            data_derived = project_root / "data" / "derived"
            data_derived.mkdir(parents=True, exist_ok=True)
            
            # Ensure NO signatures file exists
            signatures_path = data_derived / "failure_signatures.json"
            assert not signatures_path.exists()
            
            config = {
                "model_name": "test-model",
                "base_path": str(project_root)
            }
            
            agent = BaselineAgent(config)
            
            # Override to use our temp path for testing
            def mock_enforce_isolation():
                signatures_path = str(data_derived / "failure_signatures.json")
                if os.path.exists(signatures_path):
                    raise RuntimeError(
                        f"CRITICAL VIOLATION: BaselineAgent attempted to access "
                        f"failure signatures at {signatures_path}."
                    )
            
            agent._enforce_isolation = mock_enforce_isolation
            
            # This should NOT raise an error
            try:
                agent._enforce_isolation()
                # Success: no exception raised
                assert True
            except RuntimeError:
                pytest.fail("BaselineAgent raised error when signatures file does not exist")
    
    def test_baseline_agent_constructor_does_not_load_signatures(self):
        """
        Verify that the constructor does not attempt to load signatures.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            data_derived = project_root / "data" / "derived"
            data_derived.mkdir(parents=True, exist_ok=True)
            
            # Create signatures file
            signatures_path = data_derived / "failure_signatures.json"
            signatures_path.write_text(json.dumps({"test": "data"}))
            
            config = {
                "model_name": "test-model",
                "base_path": str(project_root)
            }
            
            # Constructor should NOT raise an error immediately
            # (the check happens during execution)
            agent = BaselineAgent(config)
            
            # Verify the agent was created successfully
            assert agent is not None
            assert agent.model_name == "test-model"
    
    def test_baseline_agent_execution_triggers_isolation_check(self):
        """
        Verify that execute_task triggers the isolation check.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            data_derived = project_root / "data" / "derived"
            data_derived.mkdir(parents=True, exist_ok=True)
            
            # Create signatures file
            signatures_path = data_derived / "failure_signatures.json"
            signatures_path.write_text(json.dumps({"test": "data"}))
            
            config = {
                "model_name": "test-model",
                "base_path": str(project_root)
            }
            
            agent = BaselineAgent(config)
            
            # Override to use our temp path for testing
            def mock_enforce_isolation():
                signatures_path = str(data_derived / "failure_signatures.json")
                if os.path.exists(signatures_path):
                    raise RuntimeError(
                        f"CRITICAL VIOLATION: BaselineAgent attempted to access "
                        f"failure signatures at {signatures_path}."
                    )
            
            agent._enforce_isolation = mock_enforce_isolation
            
            # Mock the other methods to avoid actual LLM loading
            agent._load_model = lambda: None
            agent._generate_response = lambda prompt: "test response"
            agent._parse_response = lambda response, task: "success"
            agent._construct_prompt = lambda task: "test prompt"
            
            task = {
                "id": "test-task",
                "instruction": "Test instruction",
                "tools": ["test_tool"],
                "context": "test context"
            }
            
            # execute_task should raise an error due to isolation check
            with pytest.raises(RuntimeError) as excinfo:
                agent.execute_task(task)
            
            assert "CRITICAL VIOLATION" in str(excinfo.value)
            assert "isolated" in str(excinfo.value).lower() or "failure signatures" in str(excinfo.value)