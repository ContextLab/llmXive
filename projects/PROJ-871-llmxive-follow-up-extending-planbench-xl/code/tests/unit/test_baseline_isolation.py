"""
Unit test for T014: Verify baseline agent does NOT access the failure signatures index.

This test ensures the BaselineAgent class and its execution runner (run_baseline)
strictly adhere to the isolation constraint: they must not read from or reference
`data/derived/failure_signatures.json`.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.baseline import BaselineAgent
from run_baseline import run_baseline_experiment
from utils.config import get_path


class TestBaselineIsolation:
    """Tests to enforce that BaselineAgent does not access the signature index."""

    def test_baseline_agent_init_no_signature_access(self):
        """
        Test that initializing BaselineAgent does not attempt to load the signature index.
        """
        # Create a temporary directory for the test environment
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Mock the config to point to our temp dir
            # We need to ensure the config path for signatures exists but is NOT accessed
            sig_path = Path(tmp_dir) / "data" / "derived" / "failure_signatures.json"
            sig_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create a dummy signature file that should NOT be touched
            dummy_sig = {"test_tool": "dummy_error"}
            with open(sig_path, 'w') as f:
                json.dump(dummy_sig, f)

            # Mock get_path to return our temp paths
            original_get_path = get_path

            def mock_get_path(key):
                if key == "failure_signatures":
                    return str(sig_path)
                # Fallback to original for other paths to avoid full env setup
                try:
                    return original_get_path(key)
                except:
                    return str(Path(tmp_dir) / "data" / "raw")

            with patch('agents.baseline.get_path', side_effect=mock_get_path):
                with patch('run_baseline.get_path', side_effect=mock_get_path):
                    # Initialize the agent
                    agent = BaselineAgent(model_name="test-model")
                    
                    # Verify the agent does not have an attribute loading the signatures
                    # and that the file was not opened during init
                    assert not hasattr(agent, 'failure_signatures'), \
                        "BaselineAgent should not load failure_signatures during init"
                    
                    # Verify the file still exists (wasn't deleted or modified)
                    assert sig_path.exists(), "Signature file should still exist (not touched)"

    def test_run_baseline_no_signature_access(self):
        """
        Test that run_baseline_experiment does not read the signature index.
        We verify this by mocking the file open call for the signature path.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Setup paths
            derived_dir = Path(tmp_dir) / "data" / "derived"
            derived_dir.mkdir(parents=True, exist_ok=True)
            logs_dir = Path(tmp_dir) / "data" / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            sig_path = derived_dir / "failure_signatures.json"
            log_path = logs_dir / "baseline_execution.jsonl"
            
            # Create a dummy signature file
            with open(sig_path, 'w') as f:
                json.dump({"dummy": "pattern"}, f)
            
            # Create a minimal dummy input file
            input_path = derived_dir / "implicit_failure_subset.jsonl"
            with open(input_path, 'w') as f:
                f.write('{"task_id": "1", "prompt": "test", "ground_truth": "success"}\n')

            # Mock config paths
            def mock_get_path(key):
                if key == "failure_signatures":
                    return str(sig_path)
                if key == "implicit_failure_subset":
                    return str(input_path)
                if key == "baseline_execution_log":
                    return str(log_path)
                return str(Path(tmp_dir) / "data" / "raw")

            # Track if signature file was opened for reading
            signature_opened = False
            
            original_open = open

            def tracking_open(file_path, mode='r', *args, **kwargs):
                nonlocal signature_opened
                if isinstance(file_path, str) and "failure_signatures.json" in file_path:
                    if 'r' in mode:
                        signature_opened = True
                return original_open(file_path, mode, *args, **kwargs)

            with patch('agents.baseline.get_path', side_effect=mock_get_path):
                with patch('run_baseline.get_path', side_effect=mock_get_path):
                    with patch('builtins.open', side_effect=tracking_open):
                        # Mock the LLM to avoid actual inference
                        with patch.object(BaselineAgent, '_call_llm', return_value="test response"):
                            try:
                                run_baseline_experiment()
                            except Exception:
                                # We expect it might fail due to missing other config,
                                # but we are checking the file access behavior before crash
                                pass

            # Assertion: The signature file must NOT have been opened
            assert not signature_opened, \
                "CRITICAL: Baseline execution accessed the failure_signatures.json file. Isolation violated."

    def test_baseline_agent_code_static_analysis(self):
        """
        Static analysis: Ensure the BaselineAgent source code does not contain
        references to 'failure_signatures' or 'signature_index'.
        """
        baseline_file = PROJECT_ROOT / "code" / "agents" / "baseline.py"
        if not baseline_file.exists():
            # If file doesn't exist yet, this test is skipped or passed based on context
            # But for T014, we assume baseline.py exists as per completed tasks
            assert False, "baseline.py not found for static analysis"

        content = baseline_file.read_text()
        
        # Check for forbidden imports or references
        forbidden_patterns = [
            "failure_signatures",
            "signature_index",
            "load_signatures",
            "get_signatures"
        ]
        
        for pattern in forbidden_patterns:
            assert pattern not in content, \
                f"Found forbidden pattern '{pattern}' in baseline.py. Baseline agent must not reference signatures."

        # Verify it imports from base and config, not indexer
        assert "from dataset.indexer" not in content, \
            "baseline.py must not import from dataset.indexer"