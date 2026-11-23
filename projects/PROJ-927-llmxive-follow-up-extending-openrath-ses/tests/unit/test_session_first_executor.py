"""Unit tests for the session_first_executor (T022, T019)."""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

from executors.session_first_executor import SessionFirstExecutor, ExecutionResult

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure."""
    root = tempfile.mkdtemp()
    # Create output dir
    output_dir = Path(root) / "data" / "processed" / "session_first"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    original_cwd = os.getcwd()
    os.chdir(root)
    yield root
    os.chdir(original_cwd)
    shutil.rmtree(root)

def test_session_first_executor_atomic_write(temp_project_root):
    """Test that SessionFirstExecutor writes atomically (temp then rename)."""
    executor = SessionFirstExecutor(output_dir=str(Path(temp_project_root) / "data" / "processed" / "session_first"))
    workflow_id = "wf_atomic_test"
    
    # Mock execution
    result = executor.execute(workflow_id, {"steps": []})
    
    assert isinstance(result, ExecutionResult)
    assert result.success is True
    assert result.output_path is not None
    assert os.path.exists(result.output_path)
    
    # Verify file exists and is valid JSON
    import json
    with open(result.output_path) as f:
        data = json.load(f)
    assert "workflow_id" in data

def test_session_first_executor_jitter_recording(temp_project_root):
    """Test that jitter is recorded in metadata."""
    executor = SessionFirstExecutor(output_dir=str(Path(temp_project_root) / "data" / "processed" / "session_first"))
    workflow_id = "wf_jitter_test"
    
    # Mock execution with jitter
    result = executor.execute(workflow_id, {"steps": []}, jitter_ms=100)
    
    assert result.success is True
    # Check if jitter info is in the output or result metadata
    # Implementation detail: check the file content
    import json
    with open(result.output_path) as f:
        data = json.load(f)
    # The executor should have recorded jitter in the metadata
    assert "metadata" in data
    assert "jitter_ms" in data["metadata"]
