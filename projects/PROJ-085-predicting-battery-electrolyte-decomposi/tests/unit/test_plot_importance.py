import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from visualization.plot_importance import load_importance_data, get_top_features, create_heatmap

class TestPlotImportance:
    
    def test_get_top_features_sorting(self):
        """Test that get_top_features correctly sorts and selects top N features."""
        data = {
            'feature': ['f1', 'f2', 'f3', 'f4', 'f5'],
            'low_importance': [0.1, 0.5, 0.2, 0.8, 0.3],
            'high_importance': [0.2, 0.4, 0.3, 0.7, 0.1]
        }
        df = pd.DataFrame(data)
        
        top_df = get_top_features(df, n_top=3)
        
        assert len(top_df) == 3
        # f4 has avg 0.75, f2 has avg 0.45, f3 has avg 0.25
        assert top_df.iloc[0]['feature'] == 'f4'
        assert top_df.iloc[1]['feature'] == 'f2'
        assert top_df.iloc[2]['feature'] == 'f3'

    def test_get_top_features_empty_input(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame()
        result = get_top_features(df)
        assert result.empty

    def test_create_heatmap_saves_file(self, tmp_path):
        """Test that create_heatmap successfully saves a PNG file."""
        data = {
            'feature': ['feat_a', 'feat_b'],
            'low_importance': [0.5, 0.2],
            'high_importance': [0.3, 0.6]
        }
        df = pd.DataFrame(data)
        
        output_file = tmp_path / "test_heatmap.png"
        
        success = create_heatmap(df, output_file)
        
        assert success is True
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_create_heatmap_invalid_input(self, tmp_path):
        """Test handling of None input."""
        output_file = tmp_path / "test_heatmap_none.png"
        success = create_heatmap(None, output_file)
        assert success is False
        
        output_file2 = tmp_path / "test_heatmap_empty.png"
        success2 = create_heatmap(pd.DataFrame(), output_file2)
        assert success2 is False