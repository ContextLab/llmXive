import pytest
import sys
from pathlib import Path
from unittest.mock import mock_open, patch

# Import the checker
from verify_consistency import ConsistencyChecker

class TestConsistencyChecker:
    """Contract tests for the consistency verification logic."""

    @pytest.fixture
    def mock_project_root(self, tmp_path):
        """Create a temporary project structure with mock files."""
        # Create tasks.md
        tasks_content = """
        # Tasks: Influence of Network Topology on Thermal Conductivity in Nanomaterials

        - [X] T001 Create project structure per implementation plan.
        - [X] T002 Initialize a Python project with dependencies.
        - [X] T041 Verify tasks.md and plan.md consistency against spec.md requirements.
        """
        (tmp_path / "tasks.md").write_text(tasks_content)

        # Create spec.md
        spec_content = """
        # Specification Document

        ## Functional Requirements
        - FR-001: Generate synthetic nanowire networks.
        - FR-002: Assign thermal resistance.
        - FR-010: Validate material properties.

        ## System Constraints
        - SC-001: CPU-only execution.
        - SC-005: Runtime/Quality constraints.
        """
        specs_dir = tmp_path / "specs" / "001-network-topology-thermal"
        specs_dir.mkdir(parents=True)
        (specs_dir / "spec.md").write_text(spec_content)

        # Create plan.md (optional)
        plan_content = """
        # Implementation Plan

        ## Phase 1: Setup
        ## Phase 2: Foundational
        """
        (tmp_path / "plan.md").write_text(plan_content)

        return tmp_path

    def test_load_files_success(self, mock_project_root):
        """Test that all files are loaded successfully."""
        checker = ConsistencyChecker(mock_project_root)
        assert checker.load_files() is True
        assert len(checker.tasks) > 0
        assert checker.spec is not None

    def test_missing_tasks_file(self, tmp_path):
        """Test error handling when tasks.md is missing."""
        checker = ConsistencyChecker(tmp_path)
        assert checker.load_files() is False
        assert "Missing required file" in checker.errors[0]

    def test_missing_spec_file(self, mock_project_root):
        """Test error handling when spec.md is missing."""
        # Remove spec file
        (mock_project_root / "specs" / "001-network-topology-thermal" / "spec.md").unlink()
        
        checker = ConsistencyChecker(mock_project_root)
        assert checker.load_files() is False
        assert any("Missing required file" in e for e in checker.errors)

    def test_requirement_traceability_valid(self, mock_project_root):
        """Test that valid requirements are accepted."""
        checker = ConsistencyChecker(mock_project_root)
        checker.load_files()
        checker.check_requirement_traceability()
        # Should have no warnings for valid requirements
        fr_warnings = [w for w in checker.warnings if "FR-" in w]
        assert len(fr_warnings) == 0

    def test_requirement_traceability_invalid(self, mock_project_root):
        """Test that invalid requirements trigger warnings."""
        # Inject an invalid requirement into tasks
        tasks_content = (mock_project_root / "tasks.md").read_text()
        tasks_content += "\n- [X] T099 Test invalid FR-999 reference."
        (mock_project_root / "tasks.md").write_text(tasks_content)

        checker = ConsistencyChecker(mock_project_root)
        checker.load_files()
        checker.check_requirement_traceability()
        
        assert any("FR-999" in w for w in checker.warnings)

    def test_dependency_validity(self, mock_project_root):
        """Test that valid dependencies are accepted."""
        checker = ConsistencyChecker(mock_project_root)
        checker.load_files()
        checker.check_dependency_validity()
        # With current mock data, no invalid deps should be found
        assert len([e for e in checker.errors if "depends on non-existent task" in e]) == 0

    def test_task_id_presence(self, mock_project_root):
        """Test that T041 is present in tasks."""
        checker = ConsistencyChecker(mock_project_root)
        checker.load_files()
        checker.check_task_id_presence()
        assert "Task T041 not found in tasks.md" not in checker.errors

    def test_main_execution(self, mock_project_root, capsys):
        """Test the main entry point execution."""
        checker = ConsistencyChecker(mock_project_root)
        
        # Run checks
        success = checker.run_checks()
        checker.print_report()
        
        captured = capsys.readouterr()
        assert "CONSISTENCY CHECK REPORT" in captured.out
        assert "Status: PASSED" in captured.out or "Status: FAILED" in captured.out
        assert success is True