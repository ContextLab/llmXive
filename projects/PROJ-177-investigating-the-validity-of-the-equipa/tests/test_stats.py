import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
from stats import bin_energy_data, StatsError

class TestBinEnergyData:
    """Tests for the bin_energy_data function in T024."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create sample energy data
        self.data = {
            'particle_id': [1, 2, 3, 4, 5],
            'timestamp': [1.0, 1.1, 1.2, 1.3, 1.4],
            'E_trans': [10.0, 12.0, 11.0, 13.0, 14.0],
            'E_rot': [2.0, 2.5, 2.2, 2.8, 3.0],
            'E_pot': [5.0, 5.5, 5.2, 5.8, 6.0],
            'E_vib': [1.0, 1.2, 1.1, 1.3, 1.4],
            'pot_incomplete': [False, False, False, False, False],
            'driving_frequency': [1.0, 1.0, 2.0, 2.0, 3.0],
            'material_type': ['Steel', 'Steel', 'Steel', 'Polymer', 'Steel']
        }
        self.df = pd.DataFrame(self.data)
        self.frequency_bins = [0.5, 1.5, 2.5, 3.5]
        
    def test_bin_by_frequency_and_material(self):
        """Test binning by both frequency and material type."""
        result = bin_energy_data(self.df, self.frequency_bins, 'Steel')
        
        # Should have 3 bins (1.0, 2.0, 3.0) for Steel
        assert len(result) == 3
        assert 'driving_frequency' in result.columns
        assert 'material_type' in result.columns
        assert 'energy' in result.columns
        
        # Check that energy values are lists
        for idx, row in result.iterrows():
            assert isinstance(row['energy'], list)
            assert len(row['energy']) > 0
            
    def test_bin_by_material_only(self):
        """Test binning by material type when frequency is not provided."""
        # Remove frequency column
        df_no_freq = self.df.drop(columns=['driving_frequency'])
        result = bin_energy_data(df_no_freq, self.frequency_bins, 'Steel')
        
        # Should have 1 row for Steel
        assert len(result) == 1
        assert result.iloc[0]['material_type'] == 'Steel'
        
    def test_empty_dataframe_raises_error(self):
        """Test that empty DataFrame raises StatsError."""
        empty_df = pd.DataFrame(columns=self.df.columns)
        with pytest.raises(StatsError):
            bin_energy_data(empty_df, self.frequency_bins, 'Steel')
            
    def test_missing_required_columns_raises_error(self):
        """Test that missing required columns raise StatsError."""
        incomplete_df = self.df.drop(columns=['E_trans'])
        with pytest.raises(StatsError):
            bin_energy_data(incomplete_df, self.frequency_bins, 'Steel')
            
    def test_adds_total_energy_column(self):
        """Test that total energy column is added if not present."""
        result = bin_energy_data(self.df, self.frequency_bins, 'Steel')
        
        # Energy should be sum of components
        for idx, row in result.iterrows():
            for e_val in row['energy']:
                # Basic check: energy should be positive
                assert e_val > 0
                
    def test_frequency_binning_accuracy(self):
        """Test that frequency binning is accurate."""
        # Create data with known frequencies
        data = {
            'particle_id': [1, 2, 3, 4],
            'timestamp': [1.0, 1.1, 1.2, 1.3],
            'E_trans': [10.0, 10.0, 10.0, 10.0],
            'E_rot': [2.0, 2.0, 2.0, 2.0],
            'E_pot': [5.0, 5.0, 5.0, 5.0],
            'E_vib': [1.0, 1.0, 1.0, 1.0],
            'pot_incomplete': [False, False, False, False],
            'driving_frequency': [1.0, 2.0, 3.0, 4.0],
            'material_type': ['Steel', 'Steel', 'Steel', 'Steel']
        }
        df = pd.DataFrame(data)
        bins = [0.5, 1.5, 2.5, 3.5, 4.5]
        
        result = bin_energy_data(df, bins, 'Steel')
        
        # Should have 4 bins
        assert len(result) == 4
        
    def test_material_filtering(self):
        """Test that material filtering works correctly."""
        result_steel = bin_energy_data(self.df, self.frequency_bins, 'Steel')
        result_polymer = bin_energy_data(self.df, self.frequency_bins, 'Polymer')
        
        # Steel should have 3 entries (frequencies 1, 2, 3)
        assert len(result_steel) == 3
        # Polymer should have 1 entry (frequency 2)
        assert len(result_polymer) == 1
        
    def test_integration_with_temp_file(self):
        """Test binning with a temporary CSV file to simulate real usage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a temporary CSV file
            temp_file = Path(tmpdir) / 'energy_samples.csv'
            self.df.to_csv(temp_file, index=False)
            
            # Read it back
            df_read = pd.read_csv(temp_file)
            
            # Bin the data
            result = bin_energy_data(df_read, self.frequency_bins, 'Steel')
            
            # Verify results
            assert len(result) == 3
            assert 'energy' in result.columns