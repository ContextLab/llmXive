"""
Contract test for LLM generation logic (T013).
Defines the interface expected by the implementation.

This test suite verifies that the LLM generation module (generate_llm_samples.py)
adheres to the following contract:
1. Produces code files in the configured `llm_samples_dir`.
2. Produces a JSON metadata sidecar for every code file.
3. Ensures metadata contains all required traceability fields (task_id, model_id, prompt, etc.).
4. Ensures the correct sample count (3 per task) is generated.
"""
import pytest
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_config
from utils.data_models import CodeSample


def test_llm_samples_directory_exists():
    """
    Verifies that the LLM samples directory structure is created by the pipeline.
    """
    config = get_config()
    llm_dir = Path(config.get("llm_samples_dir"))
    
    # The directory must exist after the pipeline runs. 
    # If it doesn't exist yet, it means the data collection phase hasn't run.
    # We assert existence to ensure the infrastructure is ready.
    assert llm_dir.exists(), f"LLM samples directory {llm_dir} does not exist. Ensure T012.5 and T013 have run."


def test_llm_generation_metadata_schema():
    """
    Verifies that every generated sample has a corresponding JSON sidecar with 
    the required traceability fields as per Constitution Principle VI.
    """
    config = get_config()
    llm_dir = Path(config.get("llm_samples_dir"))
    
    if not llm_dir.exists():
        pytest.skip("LLM directory not populated yet.")

    json_files = list(llm_dir.glob("*.json"))
    
    if not json_files:
        pytest.skip("No JSON sidecars found. Ensure T013 has generated samples.")

    required_fields = [
        "source_type", 
        "repository_id", 
        "issue_id", 
        "task_id",
        "language", 
        "file_path", 
        "function_name", 
        "sample_id",
        # T013 Specific Traceability Fields (Constitution Principle VI)
        "model_id", 
        "model_version", 
        "api_endpoint", 
        "exact_prompt", 
        "prompt_hash", 
        "generation_seed"
    ]

    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                pytest.fail(f"Invalid JSON in metadata file: {json_file}")
        
        # Verify source type is 'llm'
        assert data.get("source_type") == "llm", \
            f"Expected source_type 'llm', got '{data.get('source_type')}' in {json_file.name}"

        # Verify all required fields exist
        missing_fields = [field for field in required_fields if field not in data]
        assert not missing_fields, \
            f"Missing required traceability fields {missing_fields} in {json_file.name}"

        # Verify corresponding code file exists
        code_file_path = llm_dir / data["file_path"]
        assert code_file_path.exists(), \
            f"Code file {code_file_path} referenced in {json_file.name} does not exist."


def test_llm_generation_quantity_per_task():
    """
    Verifies that the generation logic produces exactly 3 samples per task 
    as defined in T013 requirements.
    """
    config = get_config()
    llm_dir = Path(config.get("llm_samples_dir"))
    
    if not llm_dir.exists():
        pytest.skip("LLM directory not populated yet.")

    json_files = list(llm_dir.glob("*.json"))
    
    if not json_files:
        pytest.skip("No JSON sidecars found.")

    task_counts: Dict[str, int] = {}
    
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        task_id = data.get("task_id")
        if task_id:
            task_counts[task_id] = task_counts.get(task_id, 0) + 1

    # If we have processed tasks, they must have exactly 3 samples
    for task_id, count in task_counts.items():
        assert count == 3, \
            f"Task {task_id} has {count} samples, but the contract requires exactly 3 samples per task."


def test_llm_generation_sample_id_uniqueness():
    """
    Verifies that every generated sample has a unique sample_id.
    """
    config = get_config()
    llm_dir = Path(config.get("llm_samples_dir"))
    
    if not llm_dir.exists():
        pytest.skip("LLM directory not populated yet.")

    json_files = list(llm_dir.glob("*.json"))
    
    if not json_files:
        pytest.skip("No JSON sidecars found.")

    sample_ids = []
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        sample_ids.append(data.get("sample_id"))

    # Check for duplicates
    if len(sample_ids) != len(set(sample_ids)):
        duplicates = [x for x in sample_ids if sample_ids.count(x) > 1]
        pytest.fail(f"Duplicate sample_ids found: {set(duplicates)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])