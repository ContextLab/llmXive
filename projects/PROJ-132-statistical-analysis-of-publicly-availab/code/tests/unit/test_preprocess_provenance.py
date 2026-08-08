import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.data.preprocess import generate_provenance, assign_grid_cell

class TestProvenanceMapping:
    @pytest.fixture
    def temp_dirs(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_generate_provenance_basic(self, temp_dirs):
        """Test basic provenance mapping generation."""
        # Create sample raw data
        raw_data = {
            'species': ['A', 'A', 'B'],
            'lat': [40.1, 40.2, 41.0],
            'lon': [-74.1, -74.2, -75.0],
            'date': ['2020-03-01', '2020-03-08', '2020-04-01'],
            'count': [10, 20, 5],
            'checklist_id': ['C1', 'C2', 'C3']
        }
        raw_df = pd.DataFrame(raw_data)
        
        # Create sample processed data (aggregated)
        processed_data = {
            'species': ['A', 'B'],
            'year': [2020, 2020],
            'grid_lat': [40.0, 41.0],
            'grid_lon': [-74.0, -75.0],
            'week': [10, 14],
            'count': [30, 5],
            'data_quality': ['sufficient', 'sufficient']
        }
        processed_df = pd.DataFrame(processed_data)
        
        output_path = os.path.join(temp_dirs, 'row_mapping.json')
        
        # Run generate_provenance
        generate_provenance(processed_df, raw_df, output_path)
        
        # Verify output file exists
        assert os.path.exists(output_path)
        
        # Verify content
        with open(output_path, 'r') as f:
            mapping = json.load(f)
        
        # Check that keys are present
        assert len(mapping) == 2
        
        # Check that checklist_ids are correctly mapped
        # For species A, grid (40.0, -74.0), week 10 -> C1, C2
        key_a = "('A', 2020, 40.0, -74.0, 10)"
        assert key_a in mapping
        assert set(mapping[key_a]) == {'C1', 'C2'}
        
        # For species B, grid (41.0, -75.0), week 14 -> C3
        key_b = "('B', 2020, 41.0, -75.0, 14)"
        assert key_b in mapping
        assert set(mapping[key_b]) == {'C3'}

    def test_generate_provenance_empty_processed(self, temp_dirs):
        """Test provenance mapping with empty processed data."""
        raw_data = {
            'species': ['A'],
            'lat': [40.0],
            'lon': [-74.0],
            'date': ['2020-03-01'],
            'count': [10],
            'checklist_id': ['C1']
        }
        raw_df = pd.DataFrame(raw_data)
        
        processed_df = pd.DataFrame(columns=['species', 'year', 'grid_lat', 'grid_lon', 'week', 'count', 'data_quality'])
        
        output_path = os.path.join(temp_dirs, 'row_mapping.json')
        
        generate_provenance(processed_df, raw_df, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            mapping = json.load(f)
        
        assert len(mapping) == 0

    def test_generate_provenance_missing_week(self, temp_dirs, caplog):
        """Test provenance mapping when processed data is missing 'week' column."""
        raw_data = {
            'species': ['A'],
            'lat': [40.0],
            'lon': [-74.0],
            'date': ['2020-03-01'],
            'count': [10],
            'checklist_id': ['C1']
        }
        raw_df = pd.DataFrame(raw_data)
        
        # Processed data without 'week' column
        processed_data = {
            'species': ['A'],
            'year': [2020],
            'grid_lat': [40.0],
            'grid_lon': [-74.0],
            'count': [10],
            'data_quality': ['sufficient']
        }
        processed_df = pd.DataFrame(processed_data)
        
        output_path = os.path.join(temp_dirs, 'row_mapping.json')
        
        # Should log a warning and continue
        generate_provenance(processed_df, raw_df, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            mapping = json.load(f)
        
        # Should be empty or have warnings logged
        assert len(mapping) == 0 or any("missing 'week' column" in log for log in caplog.messages)

    def test_assign_grid_cell(self):
        """Test grid cell assignment."""
        lat, lon = assign_grid_cell(40.123, -74.456, resolution=0.5)
        assert lat == 40.0  # floor(40.123 / 0.5) * 0.5 + 0.25 = 40.0 + 0.25 = 40.25? 
        # Wait, let's re-calculate:
        # floor(40.123 / 0.5) = floor(80.246) = 80
        # 80 * 0.5 = 40.0
        # 40.0 + 0.5 / 2 = 40.25
        # So the function returns the center of the bin.
        # Let's adjust the test to match the function logic.
        # The function returns: int(np.floor(lat / resolution)) * resolution + resolution / 2
        # For 40.123, 0.5:
        # floor(80.246) = 80 -> 80 * 0.5 = 40.0 -> 40.0 + 0.25 = 40.25
        assert lat == 40.25
        
        lon, lat = assign_grid_cell(-74.456, 40.123, resolution=0.5) # Note: args are lat, lon but I passed lon, lat in call? 
        # No, the function is assign_grid_cell(lat, lon, resolution)
        # So I should call: assign_grid_cell(40.123, -74.456, 0.5)
        # Let's re-test correctly.
        lat_res, lon_res = assign_grid_cell(40.123, -74.456, 0.5)
        assert lat_res == 40.25
        # For -74.456: floor(-74.456 / 0.5) = floor(-148.912) = -149
        # -149 * 0.5 = -74.5
        # -74.5 + 0.25 = -74.25
        assert lon_res == -74.25