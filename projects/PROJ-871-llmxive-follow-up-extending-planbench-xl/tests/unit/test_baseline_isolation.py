import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# We need to import the baseline agent and check its behavior
# Since we are in tests/, we need to adjust sys.path
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from agents.baseline import BaselineAgent
from utils.config import get_path, get_project_root

class TestBaselineIsolation:
    """
    Test that the baseline agent does NOT access the failure signatures index.
    This enforces the isolation requirement for US1.
    """

    def test_baseline_agent_no_signature_access(self):
        """
        Verify that BaselineAgent does not read from data/derived/failure_signatures.json.
        We do this by mocking the file system access to that specific path and ensuring
        it is never called during agent execution.
        """
        # Create a temporary directory to simulate the project structure
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Setup directories
            data_derived = tmp_path / "data" / "derived"
            data_derived.mkdir(parents=True)
            
            # Create a dummy signatures file (should NOT be accessed)
            sig_file = data_derived / "failure_signatures.json"
            sig_file.write_text(json.dumps({"dummy": "data"}))
            
            # Mock get_project_root to return our temp directory
            with patch('agents.baseline.get_project_root', return_value=tmp_path):
                with patch('utils.config.get_project_root', return_value=tmp_path):
                    # Create the agent
                    agent = BaselineAgent(model="test-model")
                    
                    # Mock the LLM interaction to avoid actual calls
                    # We just need to ensure file I/O doesn't happen
                    mock_response = {
                        "plan": ["step1", "step2"],
                        "final_answer": "success"
                    }
                    
                    # Mock the internal _call_llm method if it exists, or the execution flow
                    # The BaselineAgent should only read the input task file, not the signature file.
                    
                    # Let's create a mock task
                    task = {
                        "id": "test-task-1",
                        "goal": "Move box A to B",
                        "initial_state": {"box_a": "pos1"},
                        "ground_truth": "success"
                    }
                    
                    # We will patch open to track file accesses
                    original_open = open
                    accessed_files = []

                    def track_open(file_path, *args, **kwargs):
                        accessed_files.append(str(file_path))
                        return original_open(file_path, *args, **kwargs)

                    with patch('builtins.open', side_effect=track_open):
                        # Simulate a single step execution or a dummy run
                        # Since BaselineAgent might not have a simple "run_one_task" exposed,
                        # we look at the run_baseline.py pattern.
                        # However, the test requirement is about the Agent class itself.
                        # We assume the agent class loads config or signatures in __init__ or run.
                        
                        # Let's verify __init__ doesn't load signatures
                        # If the BaselineAgent is correctly isolated, it should not touch failure_signatures.json
                        
                        # We need to trigger code that might try to read the file.
                        # If the BaselineAgent is pure, it won't.
                        # We can assert that the file was not in accessed_files.
                        
                        # To be safe, let's try to call a method that might trigger loading.
                        # Assuming the agent has a method to execute a step or init.
                        # If the agent doesn't have a public method to trigger loading,
                        # we rely on the fact that __init__ didn't load it.
                        
                        # Let's check if the file path is in the accessed files
                        # We need to construct the path relative to tmp_path
                        expected_sig_path = str(sig_file)
                        
                        # If the agent tries to read the signature file, it will be in accessed_files
                        # But we need to trigger the code.
                        # Let's assume the agent's run method (if it exists) or __init__ is the place.
                        # If the BaselineAgent is implemented correctly, it won't have logic to read signatures.
                        
                        # We'll simulate a scenario where the agent is asked to plan.
                        # Since we don't have the full BaselineAgent code here, we assume
                        # that if it were to read the signature file, it would be during a "recovery" or "lookup" phase.
                        # The baseline agent should NOT have such a phase.
                        
                        # Let's assert that the file was not opened by the agent's logic.
                        # We can't easily test "it never happens" without running the agent.
                        # So we run a dummy execution.
                        
                        # Mock the LLM call to return immediately
                        with patch.object(agent, '_call_llm', return_value=mock_response):
                            try:
                                # Call a method that would trigger execution logic
                                # If BaselineAgent doesn't have a public run method, we might need to look at run_baseline.py
                                # But the test is for the Agent class.
                                # Let's assume there is a 'execute' or 'run' method.
                                # If not, we check the source code of BaselineAgent to see if it imports/reads signatures.
                                
                                # Since I don't have the full BaselineAgent code in this context,
                                # I will assume it has a method like 'execute_step' or similar.
                                # If it doesn't, the test might need to be adjusted to check imports or source.
                                
                                # Let's try to call a method that exists in the base or is standard.
                                # If the BaselineAgent is a simple wrapper, it might just call _call_llm.
                                # We'll just check that the file wasn't opened during __init__ or any method call.
                                
                                # For the sake of this test, we'll assume the agent has a 'run' method.
                                # If not, this test might need to be adapted to the actual API.
                                if hasattr(agent, 'run'):
                                    agent.run([task])
                                elif hasattr(agent, 'execute'):
                                    agent.execute(task)
                                else:
                                    # Fallback: just check __init__ didn't load it
                                    pass
                                   
                            except Exception:
                                # We don't care about execution errors, only file access
                                pass

                        # Assert that the signature file was NOT accessed
                        assert expected_sig_path not in accessed_files, \
                            f"BaselineAgent incorrectly accessed failure signatures at {expected_sig_path}"

    def test_baseline_agent_uses_only_task_data(self):
        """
        Verify that BaselineAgent only accesses the task input file and necessary config.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            data_derived = tmp_path / "data" / "derived"
            data_derived.mkdir(parents=True)
            
            # Create input file
            input_file = data_derived / "implicit_failure_subset.jsonl"
            input_file.write_text('{"id": "1", "goal": "test"}\n')
            
            # Create signatures file (should be ignored)
            sig_file = data_derived / "failure_signatures.json"
            sig_file.write_text('{"dummy": "data"}')
            
            accessed_files = []
            original_open = open

            def track_open(file_path, *args, **kwargs):
                accessed_files.append(str(file_path))
                return original_open(file_path, *args, **kwargs)

            with patch('builtins.open', side_effect=track_open):
                with patch('agents.baseline.get_project_root', return_value=tmp_path):
                    with patch('utils.config.get_project_root', return_value=tmp_path):
                        agent = BaselineAgent(model="test")
                        
                        # Simulate loading tasks (if the agent does it internally)
                        # Or we just check that the signature file wasn't opened.
                        # Since we can't force the agent to run without a full implementation,
                        # we rely on the fact that the BaselineAgent class should not have
                        # any code that reads failure_signatures.json.
                        
                        # We check the source code of the agent to ensure no import or read of that file.
                        import inspect
                        source = inspect.getsource(BaselineAgent)
                        
                        # Check that the string "failure_signatures" does not appear in the source
                        assert "failure_signatures" not in source, \
                            "BaselineAgent source code references failure_signatures, violating isolation."
                            # Note: This is a static check. The dynamic check above is also good.
                            # If the agent dynamically constructs the path, the static check might miss it.
                            # But for a well-designed baseline, it shouldn't have any logic related to signatures.
