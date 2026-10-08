import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path
import sys

# Add project root to path for imports if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.preprocessing import estimate_rarefaction_loss
from code.config import get_output_path, ensure_directories

class TestRarefactionLossEstimation:
    
    @pytest.fixture
    def mock_otu_table(self):
        """Create a mock OTU table with varying depths."""
        data = {
            'sample_1': [100, 200, 300], # Depth 600
            'sample_2': [50, 50, 50],    # Depth 150
            'sample_3': [1000, 1000, 1000], # Depth 3000
            'sample_4': [10, 10, 10],    # Depth 30
            'sample_5': [500, 500, 500]  # Depth 1500
        }
        df = pd.DataFrame(data, index=['taxon_A', 'taxon_B', 'taxon_C']).T
        # Add a non-numeric column to test filtering
        df['sample_id'] = df.index
        return df

    @pytest.fixture
    def mock_median_depth_file(self, mock_otu_table):
        """Create a temporary median depth file."""
        # Median of [600, 150, 3000, 30, 1500] -> sorted: [30, 150, 600, 1500, 3000] -> 600
        median_val = 600.0
        data = {
            "median_depth": median_val,
            "total_samples": 5,
            "samples_with_nonzero_depth": 5,
            "min_depth": 30.0,
            "max_depth": 3000.0
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            return f.name

    def test_estimate_rarefaction_loss_calculation(self, mock_otu_table, mock_median_depth_file):
        """
        Test that loss is calculated correctly.
        Depths: [600, 150, 3000, 30, 1500]
        Median Depth: 600
        Samples lost (depth < 600): sample_2 (150), sample_4 (30). Count = 2.
        Total: 5.
        Loss Rate: 2/5 = 0.4
        """
        # Save mock OTU to temp parquet
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            temp_path = f.name
            mock_otu_table.to_parquet(temp_path)
        
        try:
            result = estimate_rarefaction_loss(temp_path, mock_median_depth_file)
            
            assert result['total_samples'] == 5
            assert result['samples_lost'] == 2
            assert abs(result['loss_rate'] - 0.4) < 0.001
            assert result['exceeds_threshold'] == True # 0.4 > 0.2
            assert result['rarefaction_depth'] == 600.0
        finally:
            os.unlink(temp_path)
            os.unlink(mock_median_depth_file)

    def test_estimate_rarefaction_loss_no_loss(self, mock_otu_table, mock_median_depth_file):
        """
        Test scenario where no samples are lost.
        Change median depth to 100.
        """
        # Create a new median file with depth 100
        data = {
            "median_depth": 100.0,
            "total_samples": 5,
            "samples_with_nonzero_depth": 5,
            "min_depth": 30.0,
            "max_depth": 3000.0
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            new_median_path = f.name
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
                temp_path = f.name
                mock_otu_table.to_parquet(temp_path)
            
            try:
                result = estimate_rarefaction_loss(temp_path, new_median_path)
                
                # Only sample_4 (depth 30) is < 100
                assert result['samples_lost'] == 1
                assert abs(result['loss_rate'] - 0.2) < 0.001
                assert result['exceeds_threshold'] == False # 0.2 is not > 0.2
            finally:
                os.unlink(temp_path)
        finally:
            os.unlink(new_median_path)

    def test_missing_median_depth_file(self, mock_otu_table):
        """Test that missing median depth file raises error."""
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            temp_path = f.name
            mock_otu_table.to_parquet(temp_path)
        
        try:
            with pytest.raises(FileNotFoundError):
                estimate_rarefaction_loss(temp_path, "non_existent_path.json")
        finally:
            os.unlink(temp_path)

    def test_zero_depth_samples_handling(self):
        """Test handling of samples with zero depth."""
        data = {
            'sample_1': [100, 0, 0], # Depth 100
            'sample_2': [0, 0, 0],   # Depth 0
            'sample_3': [200, 200, 200] # Depth 600
        }
        df = pd.DataFrame(data).T
        df['sample_id'] = df.index
        
        median_data = {"median_depth": 100.0}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(median_data, f)
            median_path = f.name
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
                temp_path = f.name
                df.to_parquet(temp_path)
            
            try:
                result = estimate_rarefaction_loss(temp_path, median_path)
                # sample_2 has depth 0, which is < 100, so it is lost.
                # sample_1 has depth 100, which is NOT < 100, so it is kept.
                assert result['samples_lost'] == 1
            finally:
                os.unlink(temp_path)
        finally:
            os.unlink(median_path)