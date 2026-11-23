"""
Integration tests to verify that the execution order in tasks.md
matches the data flow (extraction -> analysis -> visualization).
"""
import pytest
from pathlib import Path
import re

from utils.config import get_project_root
from verify_execution_order import (
    verify_file_exists,
    verify_imports,
    verify_tasks_md_dependencies,
    run_verification
)


class TestExecutionOrder:
    """Tests for execution order verification."""

    @pytest.fixture
    def project_root(self):
        return get_project_root()

    @pytest.fixture
    def tasks_md_path(self, project_root):
        return project_root / "tasks.md"

    def test_tasks_md_exists(self, tasks_md_path):
        """Test that tasks.md exists."""
        assert verify_file_exists(tasks_md_path), "tasks.md must exist"

    def test_main_py_imports(self, project_root):
        """Test that main.py contains references to all phases."""
        success = verify_imports()
        assert success, "main.py must reference extraction, analysis, and visualization"

    def test_tasks_md_ordering(self, tasks_md_path):
        """Test that tasks.md has correct ordering of phases."""
        success, issues = verify_tasks_md_dependencies(tasks_md_path)
        assert success, f"tasks.md ordering issues found: {issues}"

    def test_full_verification(self, project_root):
        """Test the full verification pipeline."""
        success = run_verification()
        assert success, "Full verification must pass"

    def test_data_flow_phases_defined(self, project_root):
        """Test that data flow phases are properly defined."""
        from verify_execution_order import DATA_FLOW_PHASES

        assert "extraction" in DATA_FLOW_PHASES
        assert "analysis" in DATA_FLOW_PHASES
        assert "visualization" in DATA_FLOW_PHASES

        # Ensure no overlap between phases
        all_tasks = set()
        for phase, tasks in DATA_FLOW_PHASES.items():
            for task in tasks:
                assert task not in all_tasks, f"Task {task} appears in multiple phases"
                all_tasks.add(task)

    def test_infrastructure_tasks_defined(self, project_root):
        """Test that infrastructure tasks are defined."""
        from verify_execution_order import INFRASTRUCTURE_TASKS

        assert len(INFRASTRUCTURE_TASKS) > 0, "Infrastructure tasks must be defined"

    def test_specific_task_positions(self, tasks_md_path):
        """Test that specific key tasks appear in the correct order."""
        content = tasks_md_path.read_text()
        lines = content.split('\n')

        # Find line numbers for key tasks
        extraction_line = None
        analysis_line = None
        visualization_line = None

        for i, line in enumerate(lines):
            if "T013" in line and "parser" in line.lower():
                extraction_line = i
            if "T014" in line and "meta_analysis" in line.lower():
                analysis_line = i
            if "T027" in line and "plots" in line.lower():
                visualization_line = i

        # All key tasks should be found
        assert extraction_line is not None, "Extraction task T013 not found"
        assert analysis_line is not None, "Analysis task T014 not found"
        assert visualization_line is not None, "Visualization task T027 not found"

        # They should be in order
        assert extraction_line < analysis_line, "Extraction must come before analysis"
        assert analysis_line < visualization_line, "Analysis must come before visualization"

    def test_dependency_statements_present(self, tasks_md_path):
        """Test that dependency statements are present in tasks.md."""
        content = tasks_md_path.read_text()

        # Check for "Depends on:" statements
        assert "Depends on:" in content, "tasks.md must contain 'Depends on:' statements"

        # Check for specific dependencies
        assert "T013" in content, "T013 must be referenced as a dependency"
        assert "T014" in content, "T014 must be referenced as a dependency"

    def test_no_placeholder_tasks(self, tasks_md_path):
        """Test that there are no obvious placeholder tasks in the main flow."""
        content = tasks_md_path.read_text()

        # Check for common placeholder patterns in key tasks
        key_tasks = ["T013", "T014", "T027"]
        for task_id in key_tasks:
            # Find the task block
            pattern = rf'-\s*\[.\]\s*{task_id}.*?(?=\n-|\Z)'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                task_block = match.group(0)
                # Check for placeholder text
                assert "TODO" not in task_block.upper(), f"Task {task_id} contains TODO"
                assert "placeholder" not in task_block.lower(), f"Task {task_id} contains placeholder"