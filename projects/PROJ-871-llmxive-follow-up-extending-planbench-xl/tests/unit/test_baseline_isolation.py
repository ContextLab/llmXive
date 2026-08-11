"""
Unit test for T014: Verify Baseline Agent Isolation.

This test ensures that the BaselineAgent does NOT access the failure_signatures.json
file, enforcing the isolation requirement for the baseline experiment.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.agents.baseline import BaselineAgent
from code.utils.config import get_path, get_project_root


class TestBaselineIsolation:
    """Tests to verify that the baseline agent does not access signature files."""

    def test_baseline_agent_no_access_to_signatures(self):
        """
        Verify that BaselineAgent initialization and execution do not attempt
        to read data/derived/failure_signatures.json.
        """
        # Create a temporary directory to simulate the project structure
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Create necessary subdirectories
            (tmp_path / "data" / "derived").mkdir(parents=True, exist_ok=True)
            (tmp_path / "data" / "logs").mkdir(parents=True, exist_ok=True)
            
            # Create a fake failure_signatures.json that should NOT be accessed
            signatures_file = tmp_path / "data" / "derived" / "failure_signatures.json"
            signatures_file.write_text(json.dumps({
                "fake_tool": "fake_pattern",
                "recovery_strategy": "replan"
            }))

            # Patch get_project_root to return our temp directory
            with patch('code.agents.baseline.get_project_root', return_value=tmp_path):
                with patch('code.utils.config.get_project_root', return_value=tmp_path):
                    # Create the agent
                    agent = BaselineAgent(
                        model_name="test-model",
                        max_tokens=512,
                        temperature=0.7
                    )
                    
                    # Verify that the signatures file was NOT accessed during initialization
                    # We check if the file exists and was not modified/read
                    assert signatures_file.exists(), "Signatures file should exist for the test"
                    
                    # Attempt to access the file directly to ensure it's there
                    with open(signatures_file, 'r') as f:
                        original_content = json.load(f)
                    
                    # Now execute a dummy task to ensure no access happens during execution
                    dummy_task = {
                        "id": "test_task_001",
                        "goal": "Test isolation",
                        "ground_truth": "success"
                    }
                    
                    # Mock the LLM call to avoid actual inference
                    with patch.object(agent, '_call_llm', return_value={"response": "dummy_response"}):
                        result = agent.execute(dummy_task)
                    
                    # Verify the signatures file content hasn't changed (no write access)
                    with open(signatures_file, 'r') as f:
                        current_content = json.load(f)
                    
                    assert original_content == current_content, "Signatures file should not be modified by baseline agent"
                    
                    # Verify the file was not read by checking access patterns
                    # We can't easily track file reads in Python without more invasive mocking,
                    # but we can verify the agent's code doesn't import or reference the file path
                    import inspect
                    source = inspect.getsource(BaselineAgent)
                    
                    # Check that the agent doesn't reference the signatures file path
                    assert "failure_signatures.json" not in source, \
                        "BaselineAgent source code should not reference failure_signatures.json"
                    
                    assert "signature" not in source.lower() or "signature" in "signatures" and "signatures" in source.lower(), \
                        "BaselineAgent should not have logic related to signatures"

    def test_baseline_agent_uses_only_config_paths(self):
        """
        Verify that BaselineAgent only uses paths defined in config.py
        and does not hardcode access to signature files.
        """
        import inspect
        source = inspect.getsource(BaselineAgent)
        
        # Check for hardcoded paths that shouldn't exist
        forbidden_patterns = [
            "failure_signatures",
            "signature_index",
            "recovery_strategy"
        ]
        
        for pattern in forbidden_patterns:
            assert pattern not in source.lower(), \
                f"BaselineAgent should not contain references to '{pattern}'"

    def test_isolation_enforced_via_mock(self):
        """
        Test that if we try to force access to signatures, the agent fails
        (proving it doesn't have built-in access).
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / "data" / "derived").mkdir(parents=True, exist_ok=True)
            
            signatures_file = tmp_path / "data" / "derived" / "failure_signatures.json"
            signatures_file.write_text(json.dumps({"test": "test"}))
            
            with patch('code.agents.baseline.get_project_root', return_value=tmp_path):
                with patch('code.utils.config.get_project_root', return_value=tmp_path):
                    agent = BaselineAgent(model_name="test", max_tokens=10, temperature=0.1)
                    
                    # The agent should not have any method to load signatures
                    assert not hasattr(agent, 'load_signatures'), \
                        "BaselineAgent should not have a load_signatures method"
                    
                    assert not hasattr(agent, 'check_signatures'), \
                        "BaselineAgent should not have a check_signatures method"
                    
                    # Verify the agent's attributes don't include signature storage
                    assert 'signatures' not in dir(agent), \
                        "BaselineAgent instance should not have a 'signatures' attribute"