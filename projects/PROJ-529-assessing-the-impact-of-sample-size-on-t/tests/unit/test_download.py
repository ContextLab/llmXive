import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Import the functions to test
from download import (
    generate_synthetic_meta_analysis,
    save_synthetic_data,
    run_simulation_fallback,
    IOANNIDIS_PARAMS
)
from utils.exceptions import DataAcquisitionError

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

class TestGenerateSyntheticMetaAnalysis:
    def test_generate_synthetic_meta_analysis_basic(self):
        """Test basic generation of synthetic meta-analysis."""
        studies = generate_synthetic_meta_analysis(
            meta_id="test_001",
            study_count=10,
            tau_squared=0.04,
            mean_effect=0.3,
            bias=0.1,
            seed=42
        )
        
        assert len(studies) == 10
        assert all("study_id" in s for s in studies)
        assert all("effect_size" in s for s in studies)
        assert all("se" in s for s in studies)
        assert all("n" in s for s in studies)
        
        # Check that effect sizes are reasonable
        effect_sizes = [s["effect_size"] for s in studies]
        assert all(isinstance(e, float) for e in effect_sizes)
        
        # Check that SEs are positive
        ses = [s["se"] for s in studies]
        assert all(se > 0 for se in ses)

    def test_generate_synthetic_meta_analysis_reproducibility(self):
        """Test that same seed produces same results."""
        studies1 = generate_synthetic_meta_analysis(
            meta_id="test_001",
            study_count=10,
            seed=42
        )
        
        studies2 = generate_synthetic_meta_analysis(
            meta_id="test_001",
            study_count=10,
            seed=42
        )
        
        assert studies1 == studies2

    def test_generate_synthetic_meta_analysis_study_count_range(self):
        """Test that study count matches requested number."""
        for count in [3, 10, 50]:
            studies = generate_synthetic_meta_analysis(
                meta_id="test_001",
                study_count=count,
                seed=42
            )
            assert len(studies) == count

class TestSaveSyntheticData:
    def test_save_synthetic_data_creates_files(self, temp_data_dir):
        """Test that save_synthetic_data creates the expected files."""
        params = IOANNIDIS_PARAMS.copy()
        params["seed"] = 42
        
        files = save_synthetic_data(
            data_dir=temp_data_dir,
            params=params,
            num_meta_analyses=3
        )
        
        assert len(files) == 3
        
        # Check that parameter file exists
        params_file = temp_data_dir / "simulation_params.json"
        assert params_file.exists()
        
        # Check that data files exist
        for i in range(1, 4):
            data_file = temp_data_dir / f"sim_meta_{i:03d}.csv"
            assert data_file.exists()

    def test_save_synthetic_data_content(self, temp_data_dir):
        """Test that saved data files have correct content."""
        params = IOANNIDIS_PARAMS.copy()
        params["seed"] = 42
        
        save_synthetic_data(
            data_dir=temp_data_dir,
            params=params,
            num_meta_analyses=1
        )
        
        # Read the first data file
        data_file = temp_data_dir / "sim_meta_001.csv"
        with open(data_file, 'r') as f:
            lines = f.readlines()
        
        # Check header
        assert lines[0].strip() == "study_id,effect_size,se,n"
        
        # Check that we have the right number of data rows
        assert len(lines) == 51  # 1 header + 50 data rows

    def test_save_synthetic_data_parameters(self, temp_data_dir):
        """Test that parameters are saved correctly."""
        params = IOANNIDIS_PARAMS.copy()
        params["seed"] = 42
        
        save_synthetic_data(
            data_dir=temp_data_dir,
            params=params,
            num_meta_analyses=1
        )
        
        # Read the parameters file
        params_file = temp_data_dir / "simulation_params.json"
        with open(params_file, 'r') as f:
            saved_params = json.load(f)
        
        assert saved_params == params

class TestRunSimulationFallback:
    def test_run_simulation_fallback_success(self, temp_data_dir):
        """Test that run_simulation_fallback succeeds."""
        params = IOANNIDIS_PARAMS.copy()
        params["seed"] = 42
        
        success = run_simulation_fallback(
            data_dir=temp_data_dir,
            params=params,
            num_meta_analyses=3
        )
        
        assert success is True
        
        # Verify files were created
        assert (temp_data_dir / "simulation_params.json").exists()
        assert (temp_data_dir / "sim_meta_001.csv").exists()
        assert (temp_data_dir / "sim_meta_002.csv").exists()
        assert (temp_data_dir / "sim_meta_003.csv").exists()

    def test_run_simulation_fallback_default_params(self, temp_data_dir):
        """Test that run_simulation_fallback works with default params."""
        success = run_simulation_fallback(
            data_dir=temp_data_dir,
            num_meta_analyses=2
        )
        
        assert success is True
        
        # Verify files were created
        assert (temp_data_dir / "simulation_params.json").exists()
        assert (temp_data_dir / "sim_meta_001.csv").exists()
        assert (temp_data_dir / "sim_meta_002.csv").exists()