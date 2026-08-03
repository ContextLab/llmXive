"""Unit tests for the event_log_executor (T021, T024a)."""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

from executors.event_log_executor import EventLogExecutor, ExecutionResult

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure."""
    root = tempfile.mkdtemp()
    output_dir = Path(root) / "data" / "processed" / "event_log"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    original_cwd = os.getcwd()
    os.chdir(root)
    yield root
    os.chdir(original_cwd)
    shutil.rmtree(root)

def test_event_log_executor_separate_files(temp_project_root):
    """Test that EventLogExecutor creates separate files for transcripts, snapshots, etc."""
    executor = EventLogExecutor(output_dir=str(Path(temp_project_root) / "data" / "processed" / "event_log"))
    workflow_id = "wf_event_test"
    
    result = executor.execute(workflow_id, {"steps": [{"tool": "test", "output": "data"}]})
    
    assert result.success is True
    # Check for existence of separate files
    base_path = Path(temp_project_root) / "data" / "processed" / "event_log" / workflow_id
    assert base_path.exists()
    # Assuming naming convention: {id}_transcript.json, {id}_snapshot.json
    assert (base_path / f"{workflow_id}_transcript.json").exists()
    assert (base_path / f"{workflow_id}_snapshot.json").exists()

def test_event_log_executor_jitter_recording(temp_project_root):
    """Test that jitter is recorded in the log metadata."""
    executor = EventLogExecutor(output_dir=str(Path(temp_project_root) / "data" / "processed" / "event_log"))
    workflow_id = "wf_event_jitter"
    
    result = executor.execute(workflow_id, {"steps": []}, jitter_ms=50)
    
    assert result.success is True
    # Check transcript file for jitter info
    transcript_path = Path(temp_project_root) / "data" / "processed" / "event_log" / workflow_id / f"{workflow_id}_transcript.json"
    import json
    with open(transcript_path) as f:
        data = json.load(f)
    assert "metadata" in data
    assert "jitter_ms" in data["metadata"]
