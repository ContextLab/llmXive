"""
Unit tests for the governance state update functionality.
"""
import pytest
from pathlib import Path
import tempfile
import yaml
import sys
import os

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.state_manager import load_state_file, update_project_state


class TestUpdateGovernanceState:
    """Test cases for governance state updates."""

    def test_update_state_creates_required_sections(self, tmp_path):
        """Test that update_project_state creates required sections if missing."""
        # Create a minimal state file
        state_file = tmp_path / "test_project.yaml"
        initial_state = {"project_id": "TEST-001"}
        
        with open(state_file, 'w') as f:
            yaml.dump(initial_state, f)
        
        # Update the state
        update_project_state(
            state_file_path=state_file,
            project_id="TEST-001",
            completed_tasks=["T001"],
            current_task="T002",
            status="in_progress"
        )
        
        # Load and verify
        updated_state = load_state_file(state_file)
        
        assert "artifact_hashes" in updated_state
        assert "tasks" in updated_state
        assert "governance" in updated_state
        assert updated_state["status"] == "in_progress"

    def test_update_state_records_completed_tasks(self, tmp_path):
        """Test that completed tasks are properly recorded."""
        state_file = tmp_path / "test_project.yaml"
        initial_state = {
            "project_id": "TEST-001",
            "artifact_hashes": {},
            "tasks": {},
            "governance": {}
        }
        
        with open(state_file, 'w') as f:
            yaml.dump(initial_state, f)
        
        # Update with completed tasks
        completed = ["T001", "T002", "T003"]
        update_project_state(
            state_file_path=state_file,
            project_id="TEST-001",
            completed_tasks=completed,
            current_task="T004"
        )
        
        updated_state = load_state_file(state_file)
        
        # Verify all completed tasks are recorded
        for task_id in completed:
            assert task_id in updated_state["tasks"]
            assert updated_state["tasks"][task_id]["status"] == "completed"
            assert "completed_at" in updated_state["tasks"][task_id]

    def test_update_state_computes_artifact_hashes(self, tmp_path):
        """Test that artifact hashes are computed for existing files."""
        # Create test governance files
        constitution = tmp_path / "constitution.md"
        spec = tmp_path / "spec.md"
        
        constitution.write_text("Principle VI: FFT-based homogenization is permitted.")
        spec.write_text("FR-001: 128x128 pixels required.")
        
        state_file = tmp_path / "test_project.yaml"
        initial_state = {
            "project_id": "TEST-001",
            "artifact_hashes": {},
            "tasks": {},
            "governance": {}
        }
        
        with open(state_file, 'w') as f:
            yaml.dump(initial_state, f)
        
        # Update state (this should compute hashes for existing files)
        update_project_state(
            state_file_path=state_file,
            project_id="TEST-001",
            completed_tasks=["T001"]
        )
        
        updated_state = load_state_file(state_file)
        
        # Verify hashes were computed
        assert "constitution.md" in updated_state["artifact_hashes"]
        assert "spec.md" in updated_state["artifact_hashes"]
        # Hash should be a 64-character hex string (SHA-256)
        assert len(updated_state["artifact_hashes"]["constitution.md"]) == 64
        assert len(updated_state["artifact_hashes"]["spec.md"]) == 64

    def test_update_state_adds_timestamp(self, tmp_path):
        """Test that updated_at timestamp is set."""
        state_file = tmp_path / "test_project.yaml"
        initial_state = {
            "project_id": "TEST-001",
            "artifact_hashes": {},
            "tasks": {},
            "governance": {}
        }
        
        with open(state_file, 'w') as f:
            yaml.dump(initial_state, f)
        
        update_project_state(
            state_file_path=state_file,
            project_id="TEST-001",
            completed_tasks=["T001"]
        )
        
        updated_state = load_state_file(state_file)
        
        assert "updated_at" in updated_state
        # Should be an ISO format timestamp
        assert "T" in updated_state["updated_at"]

    def test_update_state_adds_notes(self, tmp_path):
        """Test that notes are properly added."""
        state_file = tmp_path / "test_project.yaml"
        initial_state = {
            "project_id": "TEST-001",
            "artifact_hashes": {},
            "tasks": {},
            "governance": {}
        }
        
        with open(state_file, 'w') as f:
            yaml.dump(initial_state, f)
        
        notes_text = "Governance verification complete"
        update_project_state(
            state_file_path=state_file,
            project_id="TEST-001",
            completed_tasks=["T001"],
            notes=notes_text
        )
        
        updated_state = load_state_file(state_file)
        
        assert "notes" in updated_state
        assert len(updated_state["notes"]) >= 1
        assert updated_state["notes"][-1]["content"] == notes_text
        assert "timestamp" in updated_state["notes"][-1]

    def test_update_state_handles_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing state file."""
        non_existent = tmp_path / "non_existent.yaml"
        
        with pytest.raises(FileNotFoundError):
            update_project_state(
                state_file_path=non_existent,
                project_id="TEST-001",
                completed_tasks=["T001"]
            )

    def test_update_governance_specifics(self, tmp_path):
        """Test specific governance verification scenario."""
        # Create mock governance files
        constitution = tmp_path / "constitution.md"
        spec = tmp_path / "spec.md"
        plan = tmp_path / "plan.md"
        
        constitution.write_text("Principle VI: FFT-based numerical homogenization is permitted.")
        spec.write_text("FR-001: 128x128 pixels. FR-007: One-way ANOVA and Tukey HSD.")
        plan.write_text("Methodology: One-way ANOVA and Tukey HSD.")
        
        state_file = tmp_path / "PROJ-506-test.yaml"
        initial_state = {
            "project_id": "PROJ-506-test",
            "artifact_hashes": {},
            "tasks": {},
            "governance": {}
        }
        
        with open(state_file, 'w') as f:
            yaml.dump(initial_state, f)
        
        # Simulate governance verification completion
        update_project_state(
            state_file_path=state_file,
            project_id="PROJ-506-test",
            completed_tasks=["T002v", "T004v", "T005v"],
            current_task="T002d",
            status="completed",
            notes="Governance verification complete: Constitution Principle VI, Spec Resolution (128x128), and Spec/Plan Alignment (ANOVA) verified."
        )
        
        updated_state = load_state_file(state_file)
        
        # Verify governance section
        assert updated_state["governance"]["constitution_verified"] is True
        assert updated_state["governance"]["spec_verified"] is True
        assert updated_state["governance"]["plan_verified"] is True
        
        # Verify tasks
        assert updated_state["tasks"]["T002v"]["status"] == "completed"
        assert updated_state["tasks"]["T004v"]["status"] == "completed"
        assert updated_state["tasks"]["T005v"]["status"] == "completed"
        assert updated_state["tasks"]["T002d"]["status"] == "completed"
        
        # Verify notes
        assert len(updated_state["notes"]) >= 1
        assert "Governance verification complete" in updated_state["notes"][-1]["content"]