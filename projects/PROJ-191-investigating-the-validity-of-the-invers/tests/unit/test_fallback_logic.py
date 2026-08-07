import pytest
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
import tempfile
import shutil

from data.fallback_logic import detect_independent_runs, main
from data.loaders import HarmonizedDataset

class TestDetectIndependentRuns:
    @pytest.fixture
    def setup_temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_single_run(self):
        """Test detection when there is only 1 run."""
        df = pd.DataFrame({
            'source': ['exp1', 'exp1', 'exp1'],
            'force': [1.0, 2.0, 3.0],
            'distance': [0.1, 0.2, 0.3]
        })
        dataset = HarmonizedDataset(data=df)
        assert detect_independent_runs(dataset) == 1

    def test_multiple_runs(self):
        """Test detection when there are 3 runs."""
        df = pd.DataFrame({
            'source': ['exp1', 'exp1', 'exp2', 'exp2', 'exp3', 'exp3'],
            'force': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            'distance': [0.1, 0.2, 0.1, 0.2, 0.1, 0.2]
        })
        dataset = HarmonizedDataset(data=df)
        assert detect_independent_runs(dataset) == 3

    def test_no_run_column(self):
        """Test behavior when no run identifier column is present."""
        df = pd.DataFrame({
            'force': [1.0, 2.0, 3.0],
            'distance': [0.1, 0.2, 0.3]
        })
        dataset = HarmonizedDataset(data=df)
        # Should return 1 as per fallback logic in implementation
        assert detect_independent_runs(dataset) == 1

    def test_empty_dataset(self):
        """Test behavior on empty dataset."""
        df = pd.DataFrame()
        dataset = HarmonizedDataset(data=df)
        assert detect_independent_runs(dataset) == 0

class TestMain:
    @pytest.fixture
    def setup_temp_state(self):
        temp_dir = tempfile.mkdtemp()
        processed_dir = Path(temp_dir) / "processed"
        processed_dir.mkdir()
        
        # Create a dummy harmonized data file with 2 runs (should trigger bootstrap)
        data = {
            'source': ['exp1', 'exp1', 'exp2', 'exp2'],
            'force': [1.0, 2.0, 3.0, 4.0],
            'distance': [0.1, 0.2, 0.1, 0.2]
        }
        df = pd.DataFrame(data)
        df.to_csv(processed_dir / "harmonized.csv", index=False)
        
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_main_triggers_bootstrap(self, setup_temp_state, monkeypatch):
        """Test that main writes USE_BOOTSTRAP: true when runs < 3."""
        temp_dir = setup_temp_state
        processed_dir = Path(temp_dir) / "processed"
        state_file = processed_dir / "state.json"
        
        # Mock the ProjectConfig to use our temp dir
        from config import ProjectConfig
        original_init = ProjectConfig.__init__
        
        def mock_init(self):
            original_init(self)
            self.data_dir = temp_dir
        
        monkeypatch.setattr(ProjectConfig, "__init__", mock_init)
        
        result = main()
        
        assert result == 0
        assert state_file.exists()
        
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        assert state['USE_BOOTSTRAP'] is True
        assert state['detected_runs'] == 2

    @pytest.fixture
    def setup_temp_state_3_runs(self):
        temp_dir = tempfile.mkdtemp()
        processed_dir = Path(temp_dir) / "processed"
        processed_dir.mkdir()
        
        # Create a dummy harmonized data file with 3 runs (should NOT trigger bootstrap)
        data = {
            'source': ['exp1', 'exp1', 'exp2', 'exp2', 'exp3', 'exp3'],
            'force': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            'distance': [0.1, 0.2, 0.1, 0.2, 0.1, 0.2]
        }
        df = pd.DataFrame(data)
        df.to_csv(processed_dir / "harmonized.csv", index=False)
        
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_main_no_bootstrap(self, setup_temp_state_3_runs, monkeypatch):
        """Test that main writes USE_BOOTSTRAP: false when runs >= 3."""
        temp_dir = setup_temp_state_3_runs
        processed_dir = Path(temp_dir) / "processed"
        state_file = processed_dir / "state.json"
        
        from config import ProjectConfig
        original_init = ProjectConfig.__init__
        
        def mock_init(self):
            original_init(self)
            self.data_dir = temp_dir
        
        monkeypatch.setattr(ProjectConfig, "__init__", mock_init)
        
        result = main()
        
        assert result == 0
        assert state_file.exists()
        
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        assert state['USE_BOOTSTRAP'] is False
        assert state['detected_runs'] == 3
