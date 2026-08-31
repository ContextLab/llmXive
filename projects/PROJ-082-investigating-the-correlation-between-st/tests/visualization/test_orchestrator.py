"""
Unit tests for the Visualization Orchestrator (T015).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.visualization.orchestrator import (
    run_visualization_orchestrator,
    load_json,
    save_json,
    SCRIPTS
)
from code.utils.config import set_project_root

class TestOrchestrator:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup a temporary project structure."""
        self.tmp_dir = tmp_path
        self.data_raw = self.tmp_dir / "data" / "raw"
        self.data_processed = self.tmp_dir / "data" / "processed"
        self.data_derived = self.tmp_dir / "data" / "derived"
        
        self.data_raw.mkdir(parents=True)
        self.data_processed.mkdir(parents=True)
        self.data_derived.mkdir(parents=True)
        
        # Set project root for the module
        set_project_root(str(self.tmp_dir))
        yield

    def test_skips_if_meta_status_missing(self, caplog):
        """Test that orchestrator skips if meta_status.json is missing."""
        status = run_visualization_orchestrator()
        assert status["status"] == "skipped"
        assert "not found" in status["reason"]
        assert not self.data_derived.joinpath("visualization_status.json").exists()

    def test_skips_if_meta_status_not_completed(self, caplog):
        """Test that orchestrator skips if meta_status.json status != 'completed'."""
        # Create meta_status.json with 'skipped' status
        meta_status_path = self.data_processed / "meta_status.json"
        with open(meta_status_path, 'w') as f:
            json.dump({"status": "skipped", "reason": "Insufficient studies"}, f)
        
        status = run_visualization_orchestrator()
        assert status["status"] == "skipped"
        assert "skipped" in status["reason"]

    @patch('code.visualization.orchestrator.run_script')
    def test_generates_plots_on_success(self, mock_run_script, caplog):
        """Test that orchestrator runs all scripts and records success."""
        # Setup meta_status
        meta_status_path = self.data_processed / "meta_status.json"
        with open(meta_status_path, 'w') as f:
            json.dump({"status": "completed"}, f)
        
        # Mock run_script to return True
        mock_run_script.return_value = True
        
        # Mock file existence check
        original_exists = Path.exists
        def mock_exists(self):
            if "visualization_status.json" in str(self):
                return True
            if str(self).endswith(".png"):
                return True
            return original_exists(self)
        
        with patch.object(Path, 'exists', mock_exists):
            status = run_visualization_orchestrator()
        
        assert status["status"] == "completed"
        assert len(status["plots_generated"]) == len(SCRIPTS)
        assert len(status["plots_failed"]) == 0
        assert mock_run_script.call_count == len(SCRIPTS)

    @patch('code.visualization.orchestrator.run_script')
    def test_records_partial_failure(self, mock_run_script, caplog):
        """Test that orchestrator handles partial failure correctly."""
        # Setup meta_status
        meta_status_path = self.data_processed / "meta_status.json"
        with open(meta_status_path, 'w') as f:
            json.dump({"status": "completed"}, f)
        
        # Mock run_script to fail on the second script
        def side_effect(script_path, *args, **kwargs):
            return "forest" not in script_path and "funnel" not in script_path
        
        mock_run_script.side_effect = lambda x: x != SCRIPTS[1][0]
        
        # Mock file existence
        original_exists = Path.exists
        def mock_exists(self):
            if "visualization_status.json" in str(self):
                return True
            if str(self).endswith(".png"):
                return True
            return original_exists(self)
        
        with patch.object(Path, 'exists', mock_exists):
            status = run_visualization_orchestrator()
        
        assert status["status"] == "partial"
        assert len(status["plots_failed"]) == 1
