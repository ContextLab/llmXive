"""
Unit tests for T022: generate_baseline_comparison.py
"""
import pytest
import pandas as pd
import json
import os
from pathlib import Path
import tempfile
import shutil

# Import the functions to test
from generate_baseline_comparison import generate_baseline_comparison, load_simulation_data

class TestGenerateBaselineComparison:
    
    def test_generate_baseline_comparison_valid_input(self):
        """Test aggregation logic with valid input."""
        data = {
            'condition': ['Dynamic', 'Static', 'Random', 'Dynamic'],
            'win_rate': [0.8, 0.5, 0.3, 0.9],
            'tokens': [1000, 2000, 500, 1200]
        }
        df = pd.DataFrame(data)
        
        result = generate_baseline_comparison(df)
        
        assert 'condition' in result.columns
        assert 'win_rate' in result.columns
        assert 'avg_tokens' in result.columns
        
        # Check Dynamic aggregation
        dynamic_row = result[result['condition'] == 'Dynamic']
        assert len(dynamic_row) == 1
        assert dynamic_row['win_rate'].values[0] == pytest.approx(0.85, rel=1e-4) # (0.8+0.9)/2
        assert dynamic_row['avg_tokens'].values[0] == pytest.approx(1100.0, rel=1e-4) # (1000+1200)/2
        
        # Check Static
        static_row = result[result['condition'] == 'Static']
        assert static_row['win_rate'].values[0] == 0.5
        assert static_row['avg_tokens'].values[0] == 2000.0

    def test_generate_baseline_comparison_missing_columns(self):
        """Test that missing columns raise ValueError."""
        data = {
            'condition': ['Dynamic'],
            'win_rate': [0.8]
            # Missing 'tokens'
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="Missing required columns"):
            generate_baseline_comparison(df)

    def test_generate_baseline_comparison_empty_input(self):
        """Test handling of empty dataframe."""
        df = pd.DataFrame(columns=['condition', 'win_rate', 'tokens'])
        
        result = generate_baseline_comparison(df)
        assert len(result) == 0
        assert list(result.columns) == ['condition', 'win_rate', 'avg_tokens']

class TestLoadSimulationData:
    
    def setup_method(self):
        """Setup temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        # Create data/processed structure
        Path("data/processed").mkdir(parents=True)

    def teardown_method(self):
        """Cleanup temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_load_from_individual_logs(self):
        """Test loading from individual CSV logs if no summary exists."""
        processed_dir = Path("data/processed")
        
        # Create individual logs
        dynamic_df = pd.DataFrame({
            'win_rate': [0.8],
            'tokens': [1000]
        })
        dynamic_df.to_csv(processed_dir / "dynamic_simulation_log.csv", index=False)
        
        static_df = pd.DataFrame({
            'win_rate': [0.5],
            'tokens': [2000]
        })
        static_df.to_csv(processed_dir / "static_simulation_log.csv", index=False)
        
        random_df = pd.DataFrame({
            'win_rate': [0.3],
            'tokens': [500]
        })
        random_df.to_csv(processed_dir / "random_simulation_log.csv", index=False)
        
        # Mock the function to use the temp dir logic
        # Note: The actual function uses hardcoded "data/processed" which we set up
        result = load_simulation_data()
        
        assert len(result) == 3
        conditions = set(result['condition'])
        assert conditions == {'Dynamic', 'Static', 'Random'}

    def test_load_from_raw_summary(self):
        """Test loading from a JSON summary file."""
        processed_dir = Path("data/processed")
        
        summary_data = [
            {'condition': 'Dynamic', 'win_rate': 0.9, 'tokens': 1500},
            {'condition': 'Static', 'win_rate': 0.6, 'tokens': 2500}
        ]
        
        with open(processed_dir / "simulation_summary_raw.json", 'w') as f:
            json.dump(summary_data, f)
        
        result = load_simulation_data()
        
        assert len(result) == 2
        assert result['condition'].tolist() == ['Dynamic', 'Static']
        
    def test_load_no_data_found(self):
        """Test that FileNotFoundError is raised if no data exists."""
        # Ensure no files exist
        processed_dir = Path("data/processed")
        for f in processed_dir.glob("*"):
            f.unlink()
        
        with pytest.raises(FileNotFoundError, match="No simulation data found"):
            load_simulation_data()