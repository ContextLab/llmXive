"""
Contract test for LLM generation logic (T013).
Defines the interface expected by the implementation.
"""
import pytest
from pathlib import Path
import json
import sys

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_config
from utils.data_models import CodeSample

def test_llm_generation_interface():
    """
    Verifies that the LLM generation module produces the expected artifacts:
    1. Code files in data/raw/llm_samples/
    2. Metadata JSON sidecars for each code file
    3. Metadata contains required fields: sample_id, source_type, repository_id, etc.
    """
    config = get_config()
    llm_dir = config["llm_samples_dir"]
    
    # Check if directory exists (might be empty if no data yet, but structure should be there)
    assert llm_dir.exists(), f"LLM samples directory {llm_dir} does not exist."
    
    # If we have run the script, verify content
    json_files = list(llm_dir.glob("*.json"))
    
    if json_files:
        for json_file in json_files:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Verify required fields
            required_fields = [
                "source_type", "repository_id", "issue_id", "task_id",
                "language", "file_path", "function_name", "sample_id"
            ]
            
            for field in required_fields:
                assert field in data, f"Missing required field '{field}' in {json_file}"
            
            # Verify source type is 'llm'
            assert data["source_type"] == "llm", f"Expected source_type 'llm', got '{data['source_type']}' in {json_file}"
            
            # Verify corresponding code file exists
            code_file = llm_dir / data["file_path"]
            assert code_file.exists(), f"Code file {code_file} referenced in {json_file} does not exist."

def test_llm_generation_quantity():
    """
    Verifies that the generation logic attempts to produce the target number of samples.
    Target: 3 samples per task.
    """
    config = get_config()
    llm_dir = config["llm_samples_dir"]
    
    if not llm_dir.exists():
        pytest.skip("LLM directory not populated yet.")
    
    json_files = list(llm_dir.glob("*.json"))
    
    # Group by task_id to check samples per task
    task_counts = {}
    for json_file in json_files:
        with open(json_file, 'r') as f:
            data = json.load(f)
        task_id = data.get("task_id")
        if task_id:
            task_counts[task_id] = task_counts.get(task_id, 0) + 1
    
    # Verify at least some tasks have the expected count (3)
    # Note: In a real run, we expect 3 per task. In a partial run, we check consistency.
    for task_id, count in task_counts.items():
        assert count == 3, f"Task {task_id} has {count} samples, expected 3."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])