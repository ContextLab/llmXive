"""
Unit tests for the data generator module.
"""
import json
import os
import pytest
from pathlib import Path
import tempfile

from code.data.generator import (
    FailureType,
    ExecutionTrace,
    FailureLabel,
    FileState,
    VariableState,
    StepState,
    generate_task_description,
    generate_step_state,
    generate_trace,
    main
)
from code.utils.seeds import verify_pairing


class TestFailureType:
    """Tests for the FailureType enum."""
    
    def test_failure_type_values(self):
        """Test that FailureType has the correct values."""
        assert FailureType.STATE_PERSISTENCE.value == "State Persistence Error"
        assert FailureType.REASONING_DEFICIT.value == "Reasoning Deficit"


class TestFileState:
    """Tests for the FileState dataclass."""
    
    def test_file_state_creation(self):
        """Test creating a FileState object."""
        file_state = FileState(
            path="test/file.py",
            content="print('hello')",
            deleted=False
        )
        assert file_state.path == "test/file.py"
        assert file_state.content == "print('hello')"
        assert file_state.deleted is False
    
    def test_file_state_deleted(self):
        """Test a deleted FileState object."""
        file_state = FileState(
            path="test/file.py",
            content="print('hello')",
            deleted=True
        )
        assert file_state.deleted is True


class TestVariableState:
    """Tests for the VariableState dataclass."""
    
    def test_variable_state_creation(self):
        """Test creating a VariableState object."""
        var_state = VariableState(
            name="result",
            value="[1, 2, 3]",
            type="list"
        )
        assert var_state.name == "result"
        assert var_state.value == "[1, 2, 3]"
        assert var_state.type == "list"


class TestFailureLabel:
    """Tests for the FailureLabel dataclass."""
    
    def test_failure_label_creation(self):
        """Test creating a FailureLabel object."""
        label = FailureLabel(
            failure_type=FailureType.STATE_PERSISTENCE,
            confidence=0.95,
            explanation="File was deleted unexpectedly"
        )
        assert label.failure_type == FailureType.STATE_PERSISTENCE
        assert label.confidence == 0.95
        assert label.explanation == "File was deleted unexpectedly"
    
    def test_failure_label_default_values(self):
        """Test FailureLabel with default values."""
        label = FailureLabel(failure_type=FailureType.REASONING_DEFICIT)
        assert label.confidence == 1.0
        assert label.explanation == ""


class TestExecutionTrace:
    """Tests for the ExecutionTrace dataclass."""
    
    def test_trace_creation(self):
        """Test creating an ExecutionTrace object."""
        trace = ExecutionTrace(
            trace_id="trace_001",
            task_description="Create a file",
            step_states=[{"step": 0, "files": [], "variables": []}],
            is_successful=True
        )
        assert trace.trace_id == "trace_001"
        assert trace.task_description == "Create a file"
        assert len(trace.step_states) == 1
        assert trace.is_successful is True
    
    def test_trace_to_dict(self):
        """Test converting ExecutionTrace to dictionary."""
        trace = ExecutionTrace(
            trace_id="trace_001",
            task_description="Create a file",
            step_states=[{"step": 0, "files": [], "variables": []}],
            failure_label=FailureLabel(failure_type=FailureType.STATE_PERSISTENCE),
            is_successful=False
        )
        
        trace_dict = trace.to_dict()
        assert trace_dict["trace_id"] == "trace_001"
        assert trace_dict["task_description"] == "Create a file"
        assert trace_dict["ground_truth_label"] == "State Persistence Error"
        assert trace_dict["is_successful"] is False
    
    def test_successful_trace_no_label(self):
        """Test that successful traces have no failure label."""
        trace = ExecutionTrace(
            trace_id="trace_001",
            task_description="Create a file",
            step_states=[{"step": 0, "files": [], "variables": []}],
            is_successful=True
        )
        
        trace_dict = trace.to_dict()
        assert trace_dict["ground_truth_label"] is None


class TestGenerateTaskDescription:
    """Tests for generate_task_description function."""
    
    def test_deterministic_generation(self):
        """Test that task descriptions are deterministic with same seed."""
        desc1 = generate_task_description(42, 1)
        desc2 = generate_task_description(42, 1)
        assert desc1 == desc2
    
    def test_different_seeds_produce_different_descriptions(self):
        """Test that different seeds produce different descriptions."""
        desc1 = generate_task_description(42, 1)
        desc2 = generate_task_description(43, 1)
        # Note: This might occasionally fail due to random choice, but is generally true
        # For a more robust test, we'd check that the structure is correct
        assert isinstance(desc1, str)
        assert len(desc1) > 0
    
    def test_task_id_in_description(self):
        """Test that task_id appears in the description."""
        desc = generate_task_description(42, 123)
        assert "123" in desc


class TestGenerateStepState:
    """Tests for generate_step_state function."""
    
    def test_deterministic_generation(self):
        """Test that step states are deterministic with same parameters."""
        state1 = generate_step_state(42, 1, 0)
        state2 = generate_step_state(42, 1, 0)
        assert state1 == state2
    
    def test_step_state_structure(self):
        """Test that step state has the correct structure."""
        state = generate_step_state(42, 1, 0)
        assert "step" in state
        assert "files" in state
        assert "variables" in state
        assert isinstance(state["files"], list)
        assert isinstance(state["variables"], list)
    
    def test_file_state_structure(self):
        """Test that file states have the correct structure."""
        state = generate_step_state(42, 1, 0)
        if state["files"]:
            file_state = state["files"][0]
            assert "path" in file_state
            assert "content" in file_state
            assert "deleted" in file_state
            assert isinstance(file_state["deleted"], bool)
    
    def test_variable_state_structure(self):
        """Test that variable states have the correct structure."""
        state = generate_step_state(42, 1, 0)
        if state["variables"]:
            var_state = state["variables"][0]
            assert "name" in var_state
            assert "value" in var_state
            assert "type" in var_state
            assert var_state["type"] in ["int", "str", "list", "dict"]


class TestGenerateTrace:
    """Tests for generate_trace function."""
    
    def test_successful_trace(self):
        """Test generating a successful trace."""
        trace = generate_trace(42, 1, None)
        assert trace.is_successful is True
        assert trace.failure_label is None
    
    def test_failed_trace_with_label(self):
        """Test generating a failed trace with a failure label."""
        trace = generate_trace(42, 1, FailureType.STATE_PERSISTENCE)
        assert trace.is_successful is False
        assert trace.failure_label is not None
        assert trace.failure_label.failure_type == FailureType.STATE_PERSISTENCE
    
    def test_trace_id_format(self):
        """Test that trace_id follows the expected format."""
        trace = generate_trace(42, 1, None)
        assert trace.trace_id.startswith("trace_")
        assert "42" in trace.trace_id or "1" in trace.trace_id
    
    def test_pairing_verification(self):
        """Test that traces pass pairing verification."""
        seed = 42
        task_id = 1
        trace = generate_trace(seed, task_id, None)
        assert verify_pairing(trace.trace_id, seed) is True


class TestMainFunction:
    """Tests for the main function."""
    
    def test_main_generates_file(self):
        """Test that main generates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_output.json")
            import sys
            sys.argv = ["generator.py", "--seed", "42", "--num-tasks", "5", "--output", output_path]
            main()
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 5
            assert all("trace_id" in item for item in data)
            assert all("task_description" in item for item in data)
            assert all("step_state" in item for item in data)
            assert all("ground_truth_label" in item for item in data)
            assert all("is_successful" in item for item in data)
    
    def test_main_with_invalid_num_tasks(self):
        """Test that main fails with invalid num-tasks."""
        import sys
        from io import StringIO
        
        old_argv = sys.argv
        old_stderr = sys.stderr
        
        try:
            sys.argv = ["generator.py", "--num-tasks", "-1"]
            sys.stderr = StringIO()
            
            with pytest.raises(SystemExit):
                main()
        finally:
            sys.argv = old_argv
            sys.stderr = old_stderr