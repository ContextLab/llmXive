"""
Unit tests for the dependency link validator.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from code.data_generation.validator import (
    load_trajectories,
    validate_dependency_links,
    validate_benchmark,
    run_validation
)


class TestValidateDependencyLinks:
    """Tests for the validate_dependency_links function."""

    def test_empty_trajectory(self):
        """Test that a trajectory with no steps fails validation."""
        trajectory = {"id": "test_1", "steps": []}
        is_valid, errors = validate_dependency_links(trajectory)

        assert is_valid is False
        assert len(errors) == 1
        assert "no steps" in errors[0].lower()

    def test_trajectory_without_dependencies(self):
        """Test that a trajectory with steps but no dependencies passes."""
        trajectory = {
            "id": "test_2",
            "steps": [
                {"id": "step_1", "content": "first step", "dependencies": []},
                {"id": "step_2", "content": "second step", "dependencies": []},
                {"id": "step_3", "content": "third step", "dependencies": []}
            ]
        }
        is_valid, errors = validate_dependency_links(trajectory)

        assert is_valid is True
        assert len(errors) == 0

    def test_valid_dependency_link(self):
        """Test that a valid dependency link (source > 10 steps back) passes."""
        # Create a trajectory with 15 steps
        steps = [
            {"id": f"step_{i}", "content": f"content {i}", "dependencies": []}
            for i in range(15)
        ]
        # Add a valid dependency from step 14 to step 3 (11 steps back)
        steps[14]["dependencies"] = [{"source_step": 3, "type": "context"}]

        trajectory = {"id": "test_3", "steps": steps}
        is_valid, errors = validate_dependency_links(trajectory)

        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_dependency_too_recent(self):
        """Test that a dependency from <=10 steps back fails."""
        steps = [
            {"id": f"step_{i}", "content": f"content {i}", "dependencies": []}
            for i in range(15)
        ]
        # Add an invalid dependency from step 14 to step 10 (4 steps back)
        steps[14]["dependencies"] = [{"source_step": 10, "type": "context"}]

        trajectory = {"id": "test_4", "steps": steps}
        is_valid, errors = validate_dependency_links(trajectory)

        assert is_valid is False
        assert len(errors) == 1
        assert "only 4 steps back" in errors[0]

    def test_invalid_source_step_out_of_range(self):
        """Test that a source_step >= current step fails."""
        steps = [
            {"id": f"step_{i}", "content": f"content {i}", "dependencies": []}
            for i in range(5)
        ]
        # Add an invalid dependency pointing to a future step
        steps[2]["dependencies"] = [{"source_step": 5, "type": "context"}]

        trajectory = {"id": "test_5", "steps": steps}
        is_valid, errors = validate_dependency_links(trajectory)

        assert is_valid is False
        assert len(errors) == 1
        assert "out of range" in errors[0]

    def test_invalid_source_step_negative(self):
        """Test that a negative source_step fails."""
        steps = [
            {"id": f"step_{i}", "content": f"content {i}", "dependencies": []}
            for i in range(5)
        ]
        steps[2]["dependencies"] = [{"source_step": -1, "type": "context"}]

        trajectory = {"id": "test_6", "steps": steps}
        is_valid, errors = validate_dependency_links(trajectory)

        assert is_valid is False
        assert len(errors) == 1
        assert "out of range" in errors[0]

    def test_invalid_source_step_type(self):
        """Test that a non-integer source_step fails."""
        steps = [
            {"id": f"step_{i}", "content": f"content {i}", "dependencies": []}
            for i in range(5)
        ]
        steps[2]["dependencies"] = [{"source_step": "invalid", "type": "context"}]

        trajectory = {"id": "test_7", "steps": steps}
        is_valid, errors = validate_dependency_links(trajectory)

        assert is_valid is False
        assert len(errors) == 1
        assert "Invalid source_step type" in errors[0]

    def test_multiple_dependencies_mixed_validity(self):
        """Test trajectory with multiple dependencies of varying validity."""
        steps = [
            {"id": f"step_{i}", "content": f"content {i}", "dependencies": []}
            for i in range(20)
        ]
        # Valid: step 19 -> step 5 (14 steps back)
        steps[19]["dependencies"].append({"source_step": 5, "type": "context"})
        # Invalid: step 19 -> step 15 (4 steps back)
        steps[19]["dependencies"].append({"source_step": 15, "type": "context"})

        trajectory = {"id": "test_8", "steps": steps}
        is_valid, errors = validate_dependency_links(trajectory)

        assert is_valid is False
        assert len(errors) == 1
        assert "only 4 steps back" in errors[0]


class TestLoadTrajectories:
    """Tests for the load_trajectories function."""

    def test_load_valid_jsonl(self):
        """Test loading a valid JSONL file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": "1", "steps": []}\n')
            f.write('{"id": "2", "steps": [{"id": "s1"}]}\n')
            temp_path = f.name

        try:
            trajectories = load_trajectories(temp_path)
            assert len(trajectories) == 2
            assert trajectories[0]["id"] == "1"
            assert trajectories[1]["id"] == "2"
        finally:
            Path(temp_path).unlink()

    def test_load_empty_lines(self):
        """Test that empty lines are skipped."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": "1", "steps": []}\n')
            f.write('\n')
            f.write('{"id": "2", "steps": []}\n')
            temp_path = f.name

        try:
            trajectories = load_trajectories(temp_path)
            assert len(trajectories) == 2
        finally:
            Path(temp_path).unlink()

    def test_load_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_trajectories("/nonexistent/path/file.jsonl")

    def test_load_invalid_json(self):
        """Test that JSONDecodeError is raised for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": "1", "steps": []}\n')
            f.write('not valid json\n')
            temp_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                load_trajectories(temp_path)
        finally:
            Path(temp_path).unlink()


class TestValidateBenchmark:
    """Tests for the validate_benchmark function."""

    def test_validate_all_pass(self):
        """Test validation when all trajectories are valid."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            # Create 3 valid trajectories
            for i in range(3):
                steps = [{"id": f"step_{j}", "dependencies": []} for j in range(15)]
                # Add valid dependency
                steps[14]["dependencies"] = [{"source_step": 3, "type": "context"}]
                f.write(json.dumps({"id": str(i), "steps": steps}) + "\n")
            temp_path = f.name

        try:
            results = validate_benchmark(temp_path, min_success_rate=0.95)
            assert results["total_trajectories"] == 3
            assert results["valid_trajectories"] == 3
            assert results["success_rate"] == 1.0
            assert results["passed"] is True
            assert len(results["errors_by_trajectory"]) == 0
        finally:
            Path(temp_path).unlink()

    def test_validate_some_fail(self):
        """Test validation when some trajectories fail."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            # Create 2 valid and 1 invalid trajectory
            for i in range(3):
                steps = [{"id": f"step_{j}", "dependencies": []} for j in range(15)]
                if i == 2:
                    # Invalid dependency
                    steps[14]["dependencies"] = [{"source_step": 10, "type": "context"}]
                else:
                    steps[14]["dependencies"] = [{"source_step": 3, "type": "context"}]
                f.write(json.dumps({"id": str(i), "steps": steps}) + "\n")
            temp_path = f.name

        try:
            results = validate_benchmark(temp_path, min_success_rate=0.5)
            assert results["total_trajectories"] == 3
            assert results["valid_trajectories"] == 2
            assert results["success_rate"] == pytest.approx(0.666, rel=0.01)
            assert results["passed"] is True
            assert len(results["errors_by_trajectory"]) == 1
        finally:
            Path(temp_path).unlink()

    def test_validate_below_threshold(self):
        """Test validation when success rate is below threshold."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            # Create 1 valid and 2 invalid trajectories
            for i in range(3):
                steps = [{"id": f"step_{j}", "dependencies": []} for j in range(15)]
                if i == 0:
                    steps[14]["dependencies"] = [{"source_step": 3, "type": "context"}]
                else:
                    steps[14]["dependencies"] = [{"source_step": 10, "type": "context"}]
                f.write(json.dumps({"id": str(i), "steps": steps}) + "\n")
            temp_path = f.name

        try:
            results = validate_benchmark(temp_path, min_success_rate=0.95)
            assert results["total_trajectories"] == 3
            assert results["valid_trajectories"] == 1
            assert results["success_rate"] == pytest.approx(0.333, rel=0.01)
            assert results["passed"] is False
        finally:
            Path(temp_path).unlink()

    def test_empty_file(self):
        """Test validation of an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            temp_path = f.name

        try:
            results = validate_benchmark(temp_path)
            assert results["total_trajectories"] == 0
            assert results["passed"] is False
            assert "No trajectories found" in results.get("message", "")
        finally:
            Path(temp_path).unlink()