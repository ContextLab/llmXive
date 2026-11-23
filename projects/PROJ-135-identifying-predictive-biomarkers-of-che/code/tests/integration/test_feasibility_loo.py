import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

# Add the project root to the path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.feasibility import count_available_tumor_types, write_feasibility_gate_result, main
from src.config import get_project_root

class TestLOOFeasibility:
    """
    Integration tests for the Pre-Check LOO Feasibility task (T009).
    """

    @pytest.fixture
    def temp_processed_dir(self, tmp_path):
        """Create a temporary processed data directory with mock files."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        # Create mock discovery/training files for 5 tumor types
        tumor_types = ["BRCA", "LUAD", "COAD", "PRAD", "HNSC"]
        for t_type in tumor_types:
            (processed_dir / f"{t_type}_discovery_set.csv").touch()
            (processed_dir / f"{t_type}_training_set.csv").touch()
        
        return processed_dir

    @pytest.fixture
    def temp_insufficient_dir(self, tmp_path):
        """Create a temporary directory with only 2 tumor types."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        # Only 2 types
        for t_type in ["BRCA", "LUAD"]:
            (processed_dir / f"{t_type}_discovery_set.csv").touch()
        
        return processed_dir

    def test_count_available_tumor_types_sufficient(self, temp_processed_dir):
        """Test that count_available_tumor_types correctly counts >= 3 types."""
        count = count_available_tumor_types(temp_processed_dir)
        assert count == 5, f"Expected 5 tumor types, got {count}"

    def test_count_available_tumor_types_insufficient(self, temp_insufficient_dir):
        """Test that count_available_tumor_types correctly counts < 3 types."""
        count = count_available_tumor_types(temp_insufficient_dir)
        assert count == 2, f"Expected 2 tumor types, got {count}"

    def test_count_available_tumor_types_empty(self, tmp_path):
        """Test counting in an empty directory."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        count = count_available_tumor_types(processed_dir)
        assert count == 0

    def test_write_feasibility_gate_result_halted(self, tmp_path):
        """Test writing a halted gate result."""
        gate_path = tmp_path / "data" / "feasibility_gate_loo.json"
        
        write_feasibility_gate_result(
            gate_path=gate_path,
            status="halted",
            reason="insufficient_loo_types",
            tumor_type_count=2,
            tumor_types=["BRCA", "LUAD"]
        )
        
        assert gate_path.exists()
        with open(gate_path) as f:
            result = json.load(f)
        
        assert result["status"] == "halted"
        assert result["reason"] == "insufficient_loo_types"
        assert result["tumor_type_count"] == 2
        assert "BRCA" in result["tumor_types"]

    def test_write_feasibility_gate_result_ready(self, tmp_path):
        """Test writing a ready gate result."""
        gate_path = tmp_path / "data" / "feasibility_gate_loo.json"
        
        write_feasibility_gate_result(
            gate_path=gate_path,
            status="ready",
            reason="sufficient_loo_types",
            tumor_type_count=5,
            tumor_types=["BRCA", "LUAD", "COAD", "PRAD", "HNSC"]
        )
        
        assert gate_path.exists()
        with open(gate_path) as f:
            result = json.load(f)
        
        assert result["status"] == "ready"
        assert result["reason"] == "sufficient_loo_types"
        assert result["tumor_type_count"] == 5

    def test_main_halts_on_insufficient_types(self, temp_insufficient_dir, tmp_path, monkeypatch):
        """Test that main() exits with code 1 when types < 3."""
        # We cannot easily test sys.exit in a normal way without pytest.raises,
        # but we can verify the file is written and the logic path is correct.
        # Instead, we test the internal logic directly.
        
        # Mock get_project_root to return a temp dir
        original_get_project_root = get_project_root
        
        def mock_get_project_root():
            return tmp_path / "mock_project"
        
        # We need to patch the module where get_project_root is used
        # Since main() calls get_project_root() directly, we patch it in src.feasibility
        import src.feasibility
        src.feasibility.get_project_root = mock_get_project_root
        
        # Also ensure the processed dir exists in the mock structure
        mock_project = tmp_path / "mock_project"
        mock_processed = mock_project / "data" / "processed"
        mock_processed.mkdir(parents=True)
        
        # Copy the insufficient files there
        for f in temp_insufficient_dir.iterdir():
            (mock_processed / f.name).touch()
        
        # Now run main and catch the exit
        with pytest.raises(SystemExit) as excinfo:
            main()
        
        assert excinfo.value.code == 1
        
        # Verify the gate file was written
        gate_path = mock_project / "data" / "feasibility_gate_loo.json"
        assert gate_path.exists()
        with open(gate_path) as f:
            result = json.load(f)
        assert result["status"] == "halted"
        assert result["reason"] == "insufficient_loo_types"
        
        # Restore
        src.feasibility.get_project_root = original_get_project_root

    def test_main_proceeds_on_sufficient_types(self, temp_processed_dir, tmp_path, monkeypatch):
        """Test that main() returns 0 when types >= 3."""
        import src.feasibility
        original_get_project_root = get_project_root
        
        def mock_get_project_root():
            return tmp_path / "mock_project"
        
        src.feasibility.get_project_root = mock_get_project_root
        
        mock_project = tmp_path / "mock_project"
        mock_processed = mock_project / "data" / "processed"
        mock_processed.mkdir(parents=True)
        
        # Copy sufficient files
        for f in temp_processed_dir.iterdir():
            (mock_processed / f.name).touch()
        
        result_code = main()
        
        assert result_code == 0
        
        gate_path = mock_project / "data" / "feasibility_gate_loo.json"
        assert gate_path.exists()
        with open(gate_path) as f:
            result = json.load(f)
        assert result["status"] == "ready"
        assert result["reason"] == "sufficient_loo_types"
        
        src.feasibility.get_project_root = original_get_project_root