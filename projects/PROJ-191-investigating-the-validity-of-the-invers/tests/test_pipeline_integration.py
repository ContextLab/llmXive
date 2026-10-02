import os
import sys
import json
import yaml
import pytest
from pathlib import Path
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import ProjectConfig
from data.state_manager import get_state_path, read_state, write_state
from pipeline_runner import ensure_state_file, update_stage_status, run_full_pipeline

class TestPipelineIntegration:
    """Integration tests for the full pipeline execution."""
    
    @pytest.fixture
    def temp_config(self, tmp_path):
        """Create a temporary project configuration."""
        # Create a temporary directory structure
        config = ProjectConfig()
        # Override paths to use temp directory
        config.project_root = tmp_path
        config.data_dir = tmp_path / "data"
        config.state_dir = tmp_path / "state" / "projects"
        
        # Create directories
        config.data_dir.mkdir(parents=True, exist_ok=True)
        config.state_dir.mkdir(parents=True, exist_ok=True)
        
        return config
    
    def test_state_file_creation(self, temp_config):
        """Test that the state file is created if it doesn't exist."""
        state_path = get_state_path(temp_config)
        assert not state_path.exists()
        
        # Create state file
        result = ensure_state_file(temp_config)
        
        assert result.exists()
        assert result == state_path
        
        # Verify content
        state = read_state(temp_config)
        assert "project_id" in state
        assert "stages" in state
        assert len(state["stages"]) > 0
    
    def test_stage_status_updates(self, temp_config):
        """Test that stage status updates work correctly."""
        ensure_state_file(temp_config)
        
        # Update stage status
        update_stage_status(temp_config, "data_acquisition", "running")
        
        state = read_state(temp_config)
        assert state["stages"]["data_acquisition"]["status"] == "running"
        assert state["stages"]["data_acquisition"]["started"] is not None
        
        # Mark as completed
        update_stage_status(temp_config, "data_acquisition", "completed")
        
        state = read_state(temp_config)
        assert state["stages"]["data_acquisition"]["status"] == "completed"
        assert state["stages"]["data_acquisition"]["completed"] is not None
    
    def test_pipeline_runner_imports(self):
        """Test that all required imports in pipeline_runner work."""
        from pipeline_runner import (
            ensure_state_file,
            update_stage_status,
            run_data_acquisition,
            run_harmonization,
            run_inference,
            run_robustness,
            run_verification,
            run_full_pipeline,
            main
        )
        assert callable(ensure_state_file)
        assert callable(update_stage_status)
        assert callable(run_full_pipeline)
        assert callable(main)
    
    def test_state_file_structure(self, temp_config):
        """Test that the state file has the correct structure."""
        state_path = ensure_state_file(temp_config)
        state = read_state(temp_config)
        
        # Check required top-level keys
        assert "project_id" in state
        assert "version" in state
        assert "started_at" in state
        assert "stages" in state
        assert "artifacts" in state
        assert "metrics" in state
        
        # Check stage structure
        required_stages = [
            "setup", "foundational", "data_acquisition", 
            "harmonization", "inference", "robustness", 
            "verification", "validation"
        ]
        for stage in required_stages:
            assert stage in state["stages"]
            assert "status" in state["stages"][stage]
            assert "started" in state["stages"][stage]
            assert "completed" in state["stages"][stage]
    
    def test_yaml_serialization(self, temp_config):
        """Test that the state can be properly serialized to YAML."""
        ensure_state_file(temp_config)
        
        # Read the raw file content
        state_path = get_state_path(temp_config)
        with open(state_path, 'r') as f:
            content = f.read()
        
        # Verify it's valid YAML
        try:
            parsed = yaml.safe_load(content)
            assert isinstance(parsed, dict)
        except yaml.YAMLError as e:
            pytest.fail(f"State file is not valid YAML: {e}")
    
    def test_atomic_operations(self, temp_config):
        """Test atomic state updates."""
        from utils.versioning import atomic_update_json, atomic_save_json
        
        state_path = get_state_path(temp_config)
        
        # Test atomic save
        test_data = {"test": "value", "number": 42}
        success = atomic_save_json(state_path, test_data)
        assert success
        
        # Verify content
        with open(state_path, 'r') as f:
            loaded = json.load(f)
        assert loaded == test_data
        
        # Test atomic update
        def update_func(current):
            current["updated"] = True
            return current
        
        success = atomic_update_json(state_path, update_func)
        assert success
        
        with open(state_path, 'r') as f:
            loaded = json.load(f)
        assert loaded["updated"] is True
    
    def test_bootstrap_flag_management(self, temp_config):
        """Test bootstrap flag setting and checking."""
        from data.state_manager import check_bootstrap_flag, set_bootstrap_flag
        
        ensure_state_file(temp_config)
        
        # Initially should be False
        assert not check_bootstrap_flag(temp_config)
        
        # Set to True
        set_bootstrap_flag(temp_config, True)
        assert check_bootstrap_flag(temp_config)
        
        # Set back to False
        set_bootstrap_flag(temp_config, False)
        assert not check_bootstrap_flag(temp_config)
    
    def test_full_pipeline_execution_mock(self, temp_config, monkeypatch):
        """Mock test for full pipeline execution (without actual data download)."""
        # Mock the individual stage functions to avoid actual execution
        def mock_run_data_acquisition(cfg):
            return True
        
        def mock_run_harmonization(cfg):
            return True
        
        def mock_run_inference(cfg):
            return True
        
        def mock_run_robustness(cfg):
            return True
        
        def mock_run_verification(cfg):
            return True
        
        # Patch the functions
        monkeypatch.setattr("pipeline_runner.run_data_acquisition", mock_run_data_acquisition)
        monkeypatch.setattr("pipeline_runner.run_harmonization", mock_run_harmonization)
        monkeypatch.setattr("pipeline_runner.run_inference", mock_run_inference)
        monkeypatch.setattr("pipeline_runner.run_robustness", mock_run_robustness)
        monkeypatch.setattr("pipeline_runner.run_verification", mock_run_verification)
        
        # Run pipeline
        success = run_full_pipeline(temp_config)
        assert success
        
        # Verify all stages completed
        state = read_state(temp_config)
        for stage_name, stage_data in state["stages"].items():
            if stage_name in ["data_acquisition", "harmonization", "inference", "robustness", "verification"]:
                assert stage_data["status"] == "completed"
