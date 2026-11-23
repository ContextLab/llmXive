"""
Unit tests for T023: save_translations module.

These tests verify that:
1. Directory structure is created correctly.
2. JSON files are written with correct structure.
3. Metadata is preserved accurately.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from src.execution.save_translations import ensure_output_dirs, save_translation

@pytest.fixture
def temp_base_path():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

def test_ensure_output_dirs_creates_base(temp_base_path):
    """Test that ensure_output_dirs creates the base directory if it doesn't exist."""
    base = temp_base_path / "eval"
    assert not base.exists()
    
    ensure_output_dirs(base)
    
    assert base.exists()
    assert base.is_dir()

def test_ensure_output_dirs_uses_existing(temp_base_path):
    """Test that ensure_output_dirs handles existing directories gracefully."""
    base = temp_base_path / "eval"
    base.mkdir(parents=True)
    
    # Should not raise
    ensure_output_dirs(base)
    
    assert base.exists()

def test_save_translation_creates_condition_dir(temp_base_path):
    """Test that save_translation creates the condition subdirectory."""
    base = temp_base_path / "eval"
    condition = "zero_shot_basic"
    entry_id = "test_001"
    
    save_translation(
        condition=condition,
        entry_id=entry_id,
        translated_code="console.log('test');",
        base_path=base,
        prompt_text="Translate this code.",
        seed=42,
        timestamp="2023-01-01T00:00:00"
    )
    
    condition_dir = base / condition
    assert condition_dir.exists()
    assert condition_dir.is_dir()

def test_save_translation_writes_valid_json(temp_base_path):
    """Test that save_translation writes a valid JSON file with correct keys."""
    base = temp_base_path / "eval"
    condition = "few_shot_style"
    entry_id = "test_002"
    code = "function add(a, b) { return a + b; }"
    prompt = "Here is an example..."
    seed = 123
    ts = "2023-01-01T12:00:00"
    
    file_path = save_translation(
        condition=condition,
        entry_id=entry_id,
        translated_code=code,
        base_path=base,
        prompt_text=prompt,
        seed=seed,
        timestamp=ts
    )
    
    assert file_path.exists()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data["entry_id"] == entry_id
    assert data["condition"] == condition
    assert data["seed"] == seed
    assert data["timestamp"] == ts
    assert data["prompt"] == prompt
    assert data["raw_output"] == code
    assert data["status"] == "success"

def test_save_translation_file_naming(temp_base_path):
    """Test that the output file is named correctly based on entry_id."""
    base = temp_base_path / "eval"
    condition = "zero_shot_basic"
    entry_id = "python_func_123"
    
    file_path = save_translation(
        condition=condition,
        entry_id=entry_id,
        translated_code="var x = 1;",
        base_path=base,
        prompt_text="Prompt",
        seed=1,
        timestamp="2023-01-01"
    )
    
    expected_name = f"{entry_id}.json"
    assert file_path.name == expected_name
    assert file_path.parent.name == condition