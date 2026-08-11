"""
Unit tests for src/validation/generate_eval_tasks.py
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
import yaml
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.validation.generate_eval_tasks import (
    load_task_descriptions_from_weights,
    generate_composite_descriptions,
    save_eval_tasks
)

class TestGenerateEvalTasks:
    
    def test_generate_composite_descriptions_basic(self):
        """Test that composite descriptions are generated correctly."""
        tasks = [
            {"id": "task_a", "desc": "Do X", "source": "src"},
            {"id": "task_b", "desc": "Do Y", "source": "src"},
            {"id": "task_c", "desc": "Do Z", "source": "src"}
        ]
        
        composites = generate_composite_descriptions(tasks)
        
        assert len(composites) >= 2
        assert any("Do X" in c["desc"] and "Do Y" in c["desc"] for c in composites)
        
        # Check IDs are deterministic (seed=42)
        # We can't easily test determinism without mocking random, but we check structure
        for comp in composites:
            assert "id" in comp
            assert "desc" in comp
            assert "base_tasks" in comp

    def test_generate_composite_descriptions_insufficient_tasks(self):
        """Test behavior with fewer than 2 tasks."""
        tasks = [{"id": "task_a", "desc": "Do X", "source": "src"}]
        
        composites = generate_composite_descriptions(tasks)
        
        # Should return original tasks if not enough to composite
        assert len(composites) == 1
        assert composites[0]["id"] == "task_a"

    def test_save_eval_tasks_creates_file(self, tmp_path):
        """Test that save_eval_tasks creates a valid YAML file."""
        tasks = [
            {"id": "eval_1", "desc": "Test task", "source": "test"}
        ]
        output_path = tmp_path / "eval_tasks.yaml"
        
        save_eval_tasks(tasks, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert "eval_tasks" in data
        assert len(data["eval_tasks"]) == 1
        assert data["eval_tasks"][0]["id"] == "eval_1"
        assert "metadata" in data
        assert data["metadata"]["generation_seed"] == 42

    def test_load_task_descriptions_from_weights_missing_file(self, caplog):
        """Test behavior when weights file is missing."""
        # This test relies on the function checking file existence
        # Since we can't easily mock the global path, we rely on the log
        tasks = load_task_descriptions_from_weights()
        # If files are missing (which they might be in test env), it returns empty list
        # and logs warnings.
        assert isinstance(tasks, list)
        # We don't assert count because it depends on test environment state
        # but we ensure it doesn't crash