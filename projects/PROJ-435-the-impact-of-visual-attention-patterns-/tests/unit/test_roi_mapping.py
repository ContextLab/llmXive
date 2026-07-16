"""
Unit tests for ROI Mapping utilities.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.roi_mapping import (
    map_single_point_to_roi,
    map_gaze_to_rois,
    aggregate_fixation_roi_stats,
    handle_zero_fixation_roi,
    DEFAULT_ROIS
)

class TestROIMapping:
    
    def test_map_single_point_to_roi_inside(self):
        """Test mapping a point inside a known ROI."""
        # Point inside headline ROI (0.5, 0.2)
        roi = map_single_point_to_roi(0.5, 0.2, DEFAULT_ROIS)
        assert roi == "headline"
    
    def test_map_single_point_to_roi_source(self):
        """Test mapping a point inside source attribution ROI."""
        # Point inside source attribution (0.1, 0.05)
        roi = map_single_point_to_roi(0.1, 0.05, DEFAULT_ROIS)
        assert roi == "source_attribution"
    
    def test_map_single_point_to_roi_outside(self):
        """Test mapping a point outside all ROIs."""
        # Point outside all ROIs (0.5, 1.5)
        roi = map_single_point_to_roi(0.5, 1.5, DEFAULT_ROIS)
        assert roi is None
    
    def test_map_gaze_to_rois_basic(self):
        """Test basic ROI mapping on a DataFrame."""
        data = {
            'x': [0.1, 0.5, 0.5, 0.1],
            'y': [0.05, 0.2, 0.5, 0.05],
            'participant_id': ['P1', 'P1', 'P1', 'P2']
        }
        df = pd.DataFrame(data)
        
        mapped_df, excluded_count = map_gaze_to_rois(df)
        
        # Check assignments
        assert mapped_df.loc[0, 'roi_assigned'] == 'source_attribution'
        assert mapped_df.loc[1, 'roi_assigned'] == 'headline'
        assert mapped_df.loc[2, 'roi_assigned'] == 'body_text'
        assert mapped_df.loc[3, 'roi_assigned'] == 'source_attribution'
        
        assert excluded_count == 0
    
    def test_map_gaze_to_rois_exclusions(self):
        """Test ROI mapping with points outside all ROIs."""
        data = {
            'x': [0.5, 0.5, 2.0],  # 2.0 is outside
            'y': [0.5, 0.5, 0.5],
            'participant_id': ['P1', 'P1', 'P1']
        }
        df = pd.DataFrame(data)
        
        mapped_df, excluded_count = map_gaze_to_rois(df)
        
        assert mapped_df.loc[0, 'roi_assigned'] == 'body_text'
        assert mapped_df.loc[1, 'roi_assigned'] == 'body_text'
        assert pd.isna(mapped_df.loc[2, 'roi_assigned'])
        assert excluded_count == 1
    
    def test_aggregate_fixation_roi_stats(self):
        """Test aggregation of fixation stats by ROI."""
        data = {
            'x': [0.1, 0.5, 0.5],
            'y': [0.05, 0.2, 0.5],
            'duration': [100, 200, 300],
            'participant_id': ['P1', 'P1', 'P1'],
            'stimulus_id': ['S1', 'S1', 'S1'],
            'roi_assigned': ['source_attribution', 'headline', 'body_text']
        }
        df = pd.DataFrame(data)
        
        agg_df = aggregate_fixation_roi_stats(df)
        
        assert len(agg_df) == 3
        assert agg_df.loc[0, 'total_duration'] == 100
        assert agg_df.loc[0, 'fixation_count'] == 1
    
    def test_handle_zero_fixation_roi(self):
        """Test handling of zero-fixation cases."""
        # Data missing 'source_attribution' for P1-S1
        data = {
            'participant_id': ['P1', 'P1'],
            'stimulus_id': ['S1', 'S1'],
            'roi_assigned': ['headline', 'body_text'],
            'total_duration': [200, 300],
            'fixation_count': [1, 1],
            'avg_duration': [200.0, 300.0]
        }
        df = pd.DataFrame(data)
        
        # Mock the full grid to include source_attribution
        complete_df = handle_zero_fixation_roi(df)
        
        # Should now have 3 rows (headline, body_text, source_attribution)
        assert len(complete_df) == 3
        
        # Check that source_attribution has zero values
        source_row = complete_df[complete_df['roi_assigned'] == 'source_attribution'].iloc[0]
        assert source_row['total_duration'] == 0
        assert source_row['fixation_count'] == 0
        assert source_row['avg_duration'] == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])