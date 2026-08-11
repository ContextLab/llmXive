import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the function under test from the source module
# Note: The project structure uses 'code/' as the root for source files based on API surface
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data_acquisition import run_feasibility_gate, write_feasibility_gate_result

class TestFeasibilityGate:
    """
    Integration test for Feasibility Gate logic (T011).
    
    Verifies that T014 (run_feasibility_gate) correctly writes 
    data/feasibility_gate.json and halts execution in specific failure scenarios:
    1. TCGA < 3 tumor types
    2. GEO < 2 valid datasets (regardless of TCGA count)
    """

    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup a temporary project structure for each test."""
        self.tmp_dir = tmp_path
        self.data_dir = self.tmp_dir / "data"
        self.state_dir = self.tmp_dir / "state" / "projects"
        self.data_dir.mkdir(parents=True)
        self.state_dir.mkdir(parents=True)
        
        # Store original working directory
        self.original_cwd = os.getcwd()
        os.chdir(self.tmp_dir)
        
        yield
        
        # Restore working directory
        os.chdir(self.original_cwd)

    def _create_mock_tcga_data(self, count: int):
        """Create mock TCGA processed files to simulate specific tumor type counts."""
        if count <= 0:
            return []
        
        created_files = []
        # Create mock files for the specified number of tumor types
        for i in range(count):
            tumor_type = f"TCGA_TumorType_{i:02d}"
            filename = f"{tumor_type}_discovery_set.csv"
            file_path = self.data_dir / filename
            file_path.touch()  # Create empty file
            created_files.append(file_path)
        
        return created_files

    def _create_mock_geo_data(self, count: int):
        """Create mock GEO processed files to simulate specific dataset counts."""
        if count <= 0:
            return []
        
        created_files = []
        for i in range(count):
            geo_id = f"GEO_{i:04d}"
            filename = f"{geo_id}_discovery_set.csv"
            file_path = self.data_dir / filename
            file_path.touch()
            created_files.append(file_path)
        
        return created_files

    def test_tcga_insufficient_types(self):
        """
        Scenario 1: TCGA < 3 tumor types.
        Expected: Write feasibility_gate.json with status='halted', reason='insufficient_tcga_types'.
        """
        # Arrange: Create only 2 TCGA tumor types (less than required 3)
        self._create_mock_tcga_data(2)
        self._create_mock_geo_data(5)  # Ensure GEO is sufficient to isolate TCGA failure
        
        gate_file = self.data_dir / "feasibility_gate.json"
        
        # Act: Run the feasibility gate logic
        # We expect this to raise a SystemExit or similar, but we capture the file write first
        with pytest.raises(SystemExit) as exc_info:
            run_feasibility_gate(
                tcga_dir=str(self.data_dir),
                geo_dir=str(self.data_dir),
                state_file=str(self.state_dir / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml")
            )
        
        # Assert: Check exit code
        assert exc_info.value.code == 1, "Pipeline must exit with code 1 on failure"
        
        # Assert: Verify the JSON file was written correctly
        assert gate_file.exists(), "feasibility_gate.json must be created"
        
        with open(gate_file, 'r') as f:
            result = json.load(f)
        
        assert result['status'] == 'halted', "Status must be 'halted'"
        assert result['reason'] == 'insufficient_tcga_types', "Reason must be 'insufficient_tcga_types'"
        assert 'tcga_count' in result, "Result must include TCGA count"
        assert result['tcga_count'] == 2, "TCGA count must be 2"
        assert 'geo_count' in result, "Result must include GEO count"

    def test_geo_insufficient_datasets(self):
        """
        Scenario 2: GEO < 2 valid datasets (regardless of TCGA count).
        Expected: Write feasibility_gate.json with status='halted', reason='insufficient_geo_datasets'.
        This test must pass even if TCGA count is sufficient (>=3).
        """
        # Arrange: Create 3 TCGA types (sufficient) but only 1 GEO dataset (insufficient)
        self._create_mock_tcga_data(3)
        self._create_mock_geo_data(1)
        
        gate_file = self.data_dir / "feasibility_gate.json"
        
        # Act: Run the feasibility gate logic
        with pytest.raises(SystemExit) as exc_info:
            run_feasibility_gate(
                tcga_dir=str(self.data_dir),
                geo_dir=str(self.data_dir),
                state_file=str(self.state_dir / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml")
            )
        
        # Assert: Check exit code
        assert exc_info.value.code == 1, "Pipeline must exit with code 1 on failure"
        
        # Assert: Verify the JSON file was written correctly
        assert gate_file.exists(), "feasibility_gate.json must be created"
        
        with open(gate_file, 'r') as f:
            result = json.load(f)
        
        assert result['status'] == 'halted', "Status must be 'halted'"
        assert result['reason'] == 'insufficient_geo_datasets', "Reason must be 'insufficient_geo_datasets'"
        assert 'geo_count' in result, "Result must include GEO count"
        assert result['geo_count'] == 1, "GEO count must be 1"
        assert 'tcga_count' in result, "Result must include TCGA count"
        assert result['tcga_count'] == 3, "TCGA count must be 3 (sufficient but overridden by GEO)"

    def test_both_sufficient(self):
        """
        Scenario 3: Both TCGA >= 3 and GEO >= 2.
        Expected: Write feasibility_gate.json with status='ready'.
        """
        # Arrange: Create sufficient data for both
        self._create_mock_tcga_data(4)
        self._create_mock_geo_data(3)
        
        gate_file = self.data_dir / "feasibility_gate.json"
        
        # Act: Run the feasibility gate logic
        # This should NOT raise an exception
        try:
            run_feasibility_gate(
                tcga_dir=str(self.data_dir),
                geo_dir=str(self.data_dir),
                state_file=str(self.state_dir / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml")
            )
        except SystemExit:
            pytest.fail("Feasibility gate should not exit when data is sufficient")
        
        # Assert: Verify the JSON file was written correctly
        assert gate_file.exists(), "feasibility_gate.json must be created"
        
        with open(gate_file, 'r') as f:
            result = json.load(f)
        
        assert result['status'] == 'ready', "Status must be 'ready' when thresholds are met"
        assert result['tcga_count'] == 4, "TCGA count must be 4"
        assert result['geo_count'] == 3, "GEO count must be 3"

    def test_geographic_priority_over_tcga(self):
        """
        Verify that GEO < 2 halts the pipeline even if TCGA is extremely abundant.
        This ensures the 'Independent Test requirement for external validation' is enforced.
        """
        # Arrange: Create 10 TCGA types (plenty) but only 0 GEO datasets
        self._create_mock_tcga_data(10)
        self._create_mock_geo_data(0)
        
        gate_file = self.data_dir / "feasibility_gate.json"
        
        # Act
        with pytest.raises(SystemExit) as exc_info:
            run_feasibility_gate(
                tcga_dir=str(self.data_dir),
                geo_dir=str(self.data_dir),
                state_file=str(self.state_dir / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml")
            )
        
        # Assert
        assert exc_info.value.code == 1
        assert gate_file.exists()
        
        with open(gate_file, 'r') as f:
            result = json.load(f)
        
        # The reason MUST be GEO insufficient, not TCGA
        assert result['reason'] == 'insufficient_geo_datasets'
        assert result['status'] == 'halted'
        assert result['geo_count'] == 0