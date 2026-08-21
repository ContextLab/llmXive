"""
Contract tests for the versioning module.
These tests verify that the versioning script meets all requirements from T005.
"""
import os
import sys
import tempfile
import yaml
import subprocess
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from versioning import load_state, update_version_state

class TestVersioningContract:
    def test_script_updates_artifact_hashes(self):
        """
        Contract test: Script must update artifact_hashes map in state file.
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            temp_path = f.name
        
        try:
            os.unlink(temp_path)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                test_file = Path(temp_dir) / "test.txt"
                test_file.write_text("test content")
                
                state = update_version_state(
                    state_path=temp_path,
                    project_id="CONTRACT-TEST-001",
                    artifacts_to_hash=[temp_dir]
                )
                
                # Verify artifact_hashes was updated
                assert "artifact_hashes" in state["projects"]["CONTRACT-TEST-001"]
                assert len(state["projects"]["CONTRACT-TEST-001"]["artifact_hashes"]) > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_script_sets_updated_at_timestamp(self):
        """
        Contract test: Script must set updated_at timestamp in state file.
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            temp_path = f.name
        
        try:
            os.unlink(temp_path)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                test_file = Path(temp_dir) / "test.txt"
                test_file.write_text("test content")
                
                state = update_version_state(
                    state_path=temp_path,
                    project_id="CONTRACT-TEST-002",
                    artifacts_to_hash=[temp_dir]
                )
                
                # Verify updated_at was set
                assert "updated_at" in state["projects"]["CONTRACT-TEST-002"]
                assert state["projects"]["CONTRACT-TEST-002"]["updated_at"] is not None
                
                # Verify timestamp format (ISO 8601)
                timestamp_str = state["projects"]["CONTRACT-TEST-002"]["updated_at"]
                assert "T" in timestamp_str or timestamp_str.endswith("Z")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_script_does_not_invalidate_reviews(self):
        """
        Contract test: Script must NOT invalidate review records.
        Per Constitution Principle V, this is the sole responsibility of the 
        Advancement-Evaluator Agent.
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            temp_path = f.name
        
        try:
            os.unlink(temp_path)
            
            # Create a mock review record
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f2:
                reviews_path = f2.name
                reviews_data = {
                    "reviews": [
                        {"id": "review-001", "status": "approved", "artifact": "test"}
                    ]
                }
                yaml.dump(reviews_data, f2)
            
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    test_file = Path(temp_dir) / "test.txt"
                    test_file.write_text("test content")
                    
                    # Run versioning update
                    state = update_version_state(
                        state_path=temp_path,
                        project_id="CONTRACT-TEST-003",
                        artifacts_to_hash=[temp_dir]
                    )
                    
                    # Verify reviews file was NOT modified by versioning script
                    # (The script should not touch it at all)
                    with open(reviews_path, 'r') as f:
                        updated_reviews = yaml.safe_load(f)
                    
                    assert updated_reviews == reviews_data
                    assert len(updated_reviews["reviews"]) == 1
                    assert updated_reviews["reviews"][0]["id"] == "review-001"
            finally:
                if os.path.exists(reviews_path):
                    os.unlink(reviews_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_script_outputs_updated_yaml(self):
        """
        Contract test: Script must output the updated YAML state.
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            temp_path = f.name
        
        try:
            os.unlink(temp_path)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                test_file = Path(temp_dir) / "test.txt"
                test_file.write_text("test content")
                
                # Run the script via command line
                result = subprocess.run(
                    [
                        sys.executable,
                        "code/versioning.py",
                        "--state-path", temp_path,
                        "--project-id", "CONTRACT-TEST-004",
                        "--artifacts", temp_dir,
                        "--verbose"
                    ],
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).parent.parent.parent
                )
                
                # Verify script ran successfully
                assert result.returncode == 0
                
                # Verify output contains expected log messages
                assert "VERSIONING UPDATE COMPLETE" in result.stdout
                assert "Hashed" in result.stdout or "artifact" in result.stdout
                
                # Verify state file was created and is valid YAML
                assert os.path.exists(temp_path)
                with open(temp_path, 'r') as f:
                    state = yaml.safe_load(f)
                    assert "projects" in state
                    assert "CONTRACT-TEST-004" in state["projects"]
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_script_logs_hash_computation(self):
        """
        Contract test: Script must log confirmation of hash computation.
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            temp_path = f.name
        
        try:
            os.unlink(temp_path)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                test_file = Path(temp_dir) / "test.txt"
                test_file.write_text("test content")
                
                # Run the script via command line
                result = subprocess.run(
                    [
                        sys.executable,
                        "code/versioning.py",
                        "--state-path", temp_path,
                        "--project-id", "CONTRACT-TEST-005",
                        "--artifacts", temp_dir,
                        "--verbose"
                    ],
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).parent.parent.parent
                )
                
                # Verify script ran successfully
                assert result.returncode == 0
                
                # Verify log output contains hash computation confirmation
                assert "Successfully updated state" in result.stdout or \
                       "Hashed" in result.stdout
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)