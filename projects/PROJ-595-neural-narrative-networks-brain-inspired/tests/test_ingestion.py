import os
import json
import pytest
from pathlib import Path
from config import get_config

def test_rocstories_file_exists():
    """
    Contract test for T015: Verify the existence of the sampled ROCStories file.
    """
    config = get_config()
    output_dir = Path(config.get("data_dir", "data")) / "text"
    file_path = output_dir / "rocstories_sample.jsonl"
    
    assert file_path.exists(), f"Expected file {file_path} does not exist. Task T015 may not have run successfully."
    assert file_path.stat().st_size > 0, f"File {file_path} is empty."

def test_rocstories_file_format():
    """
    Contract test for T015: Verify the JSONL format and content structure.
    """
    config = get_config()
    output_dir = Path(config.get("data_dir", "data")) / "text"
    file_path = output_dir / "rocstories_sample.jsonl"
    
    if not file_path.exists():
        pytest.skip("File does not exist yet. Run T015 first.")

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    assert len(lines) > 0, "File contains no lines."
    
    # Check the first line
    first_line = json.loads(lines[0])
    assert "story_id" in first_line, "Missing 'story_id' key in JSON object."
    assert "text" in first_line, "Missing 'text' key in JSON object."
    assert isinstance(first_line["story_id"], int), "'story_id' must be an integer."
    assert isinstance(first_line["text"], str), "'text' must be a string."
    assert len(first_line["text"]) > 0, "'text' field cannot be empty."

def test_rocstories_sample_size():
    """
    Contract test for T015: Verify we have a representative subset (at least 100).
    """
    config = get_config()
    output_dir = Path(config.get("data_dir", "data")) / "text"
    file_path = output_dir / "rocstories_sample.jsonl"
    
    if not file_path.exists():
        pytest.skip("File does not exist yet. Run T015 first.")

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Task T015 requests a representative subset. 1000 is the target, 
    # but we assert a minimum to ensure it's not just a few lines.
    assert len(lines) >= 100, f"Sample size ({len(lines)}) is too small. Expected at least 100."