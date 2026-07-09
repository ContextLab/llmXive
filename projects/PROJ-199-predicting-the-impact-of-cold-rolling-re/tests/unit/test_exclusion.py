"""
Unit tests for exclusion logic (T014).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from data.exclusion import (
    calculate_reliability_metrics,
    apply_exclusion_logic,
    RELIABILITY_THRESHOLD
)

class TestCalculateReliabilityMetrics:
    def test_high_reliability(self):
        """Test sample with 10% points filtered (90% kept)."""
        result = calculate_reliability_metrics(1000, 900, "sample_001")
        assert result['is_low_reliability'] is False
        assert result['reliability_status'] == 'acceptable'
        assert result['points_remaining_ratio'] == 0.9
        assert result['points_filtered_ratio'] == 0.1
    
    def test_low_reliability(self):
        """Test sample with 60% points filtered (40% kept)."""
        result = calculate_reliability_metrics(1000, 400, "sample_002")
        assert result['is_low_reliability'] is True
        assert result['reliability_status'] == 'low_reliability'
        assert result['points_remaining_ratio'] == 0.4
        assert result['points_filtered_ratio'] == 0.6
    
    def test_exact_threshold_boundary(self):
        """Test sample exactly at 50% threshold."""
        # >50% is excluded. So 50% exactly is kept.
        result = calculate_reliability_metrics(1000, 500, "sample_003")
        assert result['is_low_reliability'] is False
        assert result['reliability_status'] == 'acceptable'
    
    def test_just_over_threshold(self):
        """Test sample just over 50% threshold."""
        result = calculate_reliability_metrics(1000, 499, "sample_004")
        assert result['is_low_reliability'] is True
        assert result['reliability_status'] == 'low_reliability'
    
    def test_empty_original(self):
        """Test sample with 0 original points."""
        result = calculate_reliability_metrics(0, 0, "sample_005")
        assert result['is_low_reliability'] is True
        assert result['points_remaining_ratio'] == 0.0

class TestApplyExclusionLogic:
    def setup_method(self):
        """Setup temporary directory and test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_path = Path(self.temp_dir) / "filtered.parquet"
        self.output_path = Path(self.temp_dir) / "cleaned.parquet"
        self.metadata_path = Path(self.temp_dir) / "exclusion_meta.csv"
        
        # Create test data
        data = {
            'sample_id': ['s1', 's1', 's1', 's2', 's2', 's2', 's3', 's3'],
            'original_point_count': [100, 100, 100, 1000, 1000, 1000, 100, 100], # 100, 1000, 100
            'orientation_x': [0.1, 0.2, 0.3, 0.1, 0.2, 0.3, 0.1, 0.2],
            'orientation_y': [0.1, 0.2, 0.3, 0.1, 0.2, 0.3, 0.1, 0.2],
            'orientation_z': [0.1, 0.2, 0.3, 0.1, 0.2, 0.3, 0.1, 0.2],
            'confidence': [0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9]
        }
        df = pd.DataFrame(data)
        # s1: 3 points kept, original 100 -> 3% kept (97% filtered) -> EXCLUDE
        # s2: 3 points kept, original 1000 -> 0.3% kept (99.7% filtered) -> EXCLUDE
        # s3: 2 points kept, original 100 -> 2% kept (98% filtered) -> EXCLUDE
        
        # Let's adjust to have one keepable sample
        # s4: 90 points kept, original 100 -> 90% kept -> KEEP
        data['sample_id'] = ['s1', 's1', 's1', 's2', 's2', 's2', 's3', 's3', 's4'] * 10
        data['original_point_count'] = [100] * 30 + [1000] * 30 + [100] * 20 + [100] * 10
        # Wait, simpler construction:
        
        rows = []
        # Sample s1: 10 original, 1 kept -> 10% kept -> EXCLUDE
        for i in range(10):
            rows.append({'sample_id': 's1', 'original_point_count': 10, 'val': i})
        # Remove 9 rows later? No, this is the *filtered* data.
        # The input to T014 is the *result* of filtering.
        # So if s1 had 10 original, and 1 kept, the input has 1 row for s1.
        
        # s1: 1 row, original=10 -> 10% kept -> EXCLUDE
        rows.append({'sample_id': 's1', 'original_point_count': 10, 'val': 1})
        
        # s2: 100 rows, original=100 -> 100% kept -> KEEP
        for i in range(100):
            rows.append({'sample_id': 's2', 'original_point_count': 100, 'val': i})
        
        # s3: 40 rows, original=100 -> 40% kept -> EXCLUDE
        for i in range(40):
            rows.append({'sample_id': 's3', 'original_point_count': 100, 'val': i})
        
        df = pd.DataFrame(rows)
        df.to_parquet(self.input_path)
    
    def test_exclusion_logic(self):
        """Test that low reliability samples are excluded."""
        summary = apply_exclusion_logic(
            self.input_path, 
            self.output_path, 
            self.metadata_path
        )
        
        # Load output
        df_out = pd.read_parquet(self.output_path)
        
        # s1 (10% kept) and s3 (40% kept) should be excluded
        # s2 (100% kept) should be kept
        assert 's1' not in df_out['sample_id'].values
        assert 's3' not in df_out['sample_id'].values
        assert 's2' in df_out['sample_id'].values
        
        # Check summary
        assert summary['excluded_samples'] == 2
        assert summary['kept_samples'] == 1
        assert summary['total_samples'] == 3
        
        # Check metadata file
        assert self.metadata_path.exists()
        meta = pd.read_csv(self.metadata_path)
        assert len(meta) == 2
        assert set(meta['sample_id']) == {'s1', 's3'}
    
    def test_missing_original_count(self):
        """Test error when original_point_count is missing."""
        # Create data without original_point_count
        df = pd.DataFrame({'sample_id': ['s1'], 'val': [1]})
        bad_path = Path(self.temp_dir) / "bad.parquet"
        df.to_parquet(bad_path)
        
        with pytest.raises(ValueError, match="missing 'original_point_count'"):
            apply_exclusion_logic(bad_path, self.output_path)
    
    def test_empty_input(self):
        """Test handling of empty input file."""
        empty_df = pd.DataFrame()
        empty_path = Path(self.temp_dir) / "empty.parquet"
        empty_df.to_parquet(empty_path)
        
        summary = apply_exclusion_logic(empty_path, self.output_path)
        assert summary['total_samples'] == 0
        assert summary['excluded_samples'] == 0
        assert self.output_path.exists()