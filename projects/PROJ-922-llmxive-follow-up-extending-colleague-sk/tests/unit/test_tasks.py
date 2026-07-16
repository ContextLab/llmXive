"""
Unit tests for task generation module.
"""
import json
import ast
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sympy as sp
from sympy import symbols, Eq
from z3 import Solver, sat

from data_generation.tasks import (
    generate_coding_task,
    generate_math_task,
    generate_logic_task,
    generate_creative_task,
    generate_factual_task,
    generate_tasks,
    validate_tasks,
    save_tasks,
    load_tasks,
    TASKS_PER_DOMAIN,
    DOMAINS,
    TOTAL_TASKS
)

class TestCodingTask:
    def test_coding_task_structure(self):
        """Test that coding task has required fields."""
        task = generate_coding_task(1)
        
        assert "id" in task
        assert task["domain"] == "coding"
        assert "description" in task
        assert "solution_code" in task
        assert "test_input" in task
        assert "validation_type" in task
        assert task["validation_type"] == "ast"
        assert "ast_valid" in task
        assert "metadata" in task

    def test_coding_ast_validation(self):
        """Test that generated coding task passes AST validation."""
        task = generate_coding_task(1)
        
        # Should be valid Python
        try:
            ast.parse(task["solution_code"])
            assert task["ast_valid"] is True
        except SyntaxError:
            assert task["ast_valid"] is False

    def test_coding_task_id_format(self):
        """Test that coding task ID follows correct format."""
        task = generate_coding_task(42)
        assert task["id"].startswith("coding_")
        assert len(task["id"]) == 10  # coding_XXX

class TestMathTask:
    def test_math_task_structure(self):
        """Test that math task has required fields."""
        task = generate_math_task(1)
        
        assert "id" in task
        assert task["domain"] == "math"
        assert "description" in task
        assert "expression" in task
        assert "validation_type" in task
        assert task["validation_type"] == "sympy"
        assert "sympy_valid" in task
        assert "metadata" in task

    def test_math_sympy_validation(self):
        """Test that generated math task can be parsed by SymPy."""
        task = generate_math_task(1)
        
        if task["sympy_valid"]:
            # Should be parseable by SymPy
            expr = sp.sympify(task["expression"].replace(" = ", " - "))
            assert expr is not None

    def test_math_task_id_format(self):
        """Test that math task ID follows correct format."""
        task = generate_math_task(42)
        assert task["id"].startswith("math_")
        assert len(task["id"]) == 9  # math_XXX

class TestLogicTask:
    def test_logic_task_structure(self):
        """Test that logic task has required fields."""
        task = generate_logic_task(1)
        
        assert "id" in task
        assert task["domain"] == "logic"
        assert "description" in task
        assert "validation_type" in task
        assert task["validation_type"] == "z3"
        assert "z3_satisfiable" in task
        assert "metadata" in task

    def test_logic_z3_validation(self):
        """Test that generated logic task can be checked by Z3."""
        task = generate_logic_task(1)
        
        # Should be a boolean
        assert isinstance(task["z3_satisfiable"], bool)

    def test_logic_task_id_format(self):
        """Test that logic task ID follows correct format."""
        task = generate_logic_task(42)
        assert task["id"].startswith("logic_")
        assert len(task["id"]) == 10  # logic_XXX

class TestCreativeTask:
    def test_creative_task_structure(self):
        """Test that creative task has required fields."""
        task = generate_creative_task(1)
        
        assert "id" in task
        assert task["domain"] == "creative"
        assert "description" in task
        assert "validation_pattern" in task
        assert "min_length" in task
        assert "validation_type" in task
        assert task["validation_type"] == "regex"
        assert "metadata" in task

    def test_creative_task_id_format(self):
        """Test that creative task ID follows correct format."""
        task = generate_creative_task(42)
        assert task["id"].startswith("creative_")
        assert len(task["id"]) == 13  # creative_XXX

class TestFactualTask:
    def test_factual_task_structure(self):
        """Test that factual task has required fields."""
        task = generate_factual_task(1)
        
        assert "id" in task
        assert task["domain"] == "factual"
        assert "description" in task
        assert "validation_pattern" in task
        assert "required_entities" in task
        assert "validation_type" in task
        assert task["validation_type"] == "regex"
        assert "metadata" in task

    def test_factual_task_id_format(self):
        """Test that factual task ID follows correct format."""
        task = generate_factual_task(42)
        assert task["id"].startswith("factual_")
        assert len(task["id"]) == 12  # factual_XXX

class TestGenerateTasks:
    def test_total_task_count(self):
        """Test that exactly 200 tasks are generated."""
        tasks = generate_tasks()
        assert len(tasks) == TOTAL_TASKS

    def test_stratified_distribution(self):
        """Test that tasks are evenly distributed across domains."""
        tasks = generate_tasks()
        
        domain_counts = {}
        for task in tasks:
            domain = task["domain"]
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        for domain in DOMAINS:
            assert domain_counts.get(domain, 0) == TASKS_PER_DOMAIN

    def test_all_domains_present(self):
        """Test that all domains are represented in generated tasks."""
        tasks = generate_tasks()
        
        domains_in_tasks = set(task["domain"] for task in tasks)
        assert domains_in_tasks == set(DOMAINS)

class TestValidateTasks:
    def test_validation_returns_counts(self):
        """Test that validation returns valid and invalid counts."""
        tasks = generate_tasks()
        valid_count, invalid_count = validate_tasks(tasks)
        
        assert isinstance(valid_count, int)
        assert isinstance(invalid_count, int)
        assert valid_count + invalid_count == len(tasks)

    def test_validation_coding_tasks(self):
        """Test validation of coding tasks specifically."""
        coding_tasks = [t for t in generate_tasks() if t["domain"] == "coding"]
        valid_count, invalid_count = validate_tasks(coding_tasks)
        
        # All coding tasks should have valid AST (or be marked invalid)
        assert valid_count + invalid_count == len(coding_tasks)

class TestSaveLoadTasks:
    def test_save_and_load_roundtrip(self, tmp_path):
        """Test that tasks can be saved and loaded correctly."""
        tasks = generate_tasks()
        output_path = tmp_path / "test_tasks.json"
        
        save_tasks(tasks, str(output_path))
        
        assert output_path.exists()
        
        loaded_tasks = load_tasks(str(output_path))
        
        assert len(loaded_tasks) == len(tasks)
        assert loaded_tasks[0]["id"] == tasks[0]["id"]
        assert loaded_tasks[0]["domain"] == tasks[0]["domain"]

    def test_save_creates_directory(self, tmp_path):
        """Test that save_tasks creates parent directories if needed."""
        tasks = generate_tasks()
        nested_path = tmp_path / "nested" / "dir" / "tasks.json"
        
        save_tasks(tasks, str(nested_path))
        
        assert nested_path.exists()

    def test_load_raises_on_missing_file(self):
        """Test that load_tasks raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_tasks("/nonexistent/path/tasks.json")

class TestTaskMetadata:
    def test_metadata_has_timestamp(self):
        """Test that task metadata includes creation timestamp."""
        task = generate_coding_task(1)
        assert "created_at" in task["metadata"]
    
    def test_metadata_has_seed(self):
        """Test that task metadata includes seed value."""
        task = generate_coding_task(1)
        assert "seed" in task["metadata"]
        assert task["metadata"]["seed"] == 42