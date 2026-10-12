import pytest
import json
from pathlib import Path
import pandas as pd
import numpy as np

from llmxive_toolkit import paths


class TestT103:
    """Integration tests for T103: Derive descriptors and build unified DataFrame."""
    
    def test_alignment_metrics_exists(self):
        """Verify alignment_metrics.json exists and contains alignment_rate."""
        metrics_path = paths.outputs("alignment_metrics.json")
        assert metrics_path.exists(), f"alignment_metrics.json not found at {metrics_path}"
        
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        assert 'alignment_rate' in metrics, "alignment_rate not in metrics"
        assert isinstance(metrics['alignment_rate'], (int, float)), "alignment_rate should be numeric"
        assert 0 <= metrics['alignment_rate'] <= 1, "alignment_rate should be between 0 and 1"
    
    def test_unified_dataset_exists(self):
        """Verify unified_dataset.parquet exists."""
        dataset_path = paths.data("processed", "unified_dataset.parquet")
        assert dataset_path.exists(), f"unified_dataset.parquet not found at {dataset_path}"
    
    def test_unified_dataset_has_minimum_entries(self):
        """Verify unified dataset has >= 500 matched entries."""
        dataset_path = paths.data("processed", "unified_dataset.parquet")
        df = pd.read_parquet(dataset_path)
        
        assert len(df) >= 500, f"Unified dataset has {len(df)} entries, expected >= 500"
    
    def test_unified_dataset_has_required_descriptors(self):
        """Verify unified dataset contains all required descriptor columns."""
        dataset_path = paths.data("processed", "unified_dataset.parquet")
        df = pd.read_parquet(dataset_path)
        
        required_descriptors = [
            'd_band_center',
            'p_band_center',
            'bader_charges',
            'activation_barrier',
            'reaction_energy'
        ]
        
        for desc in required_descriptors:
            assert desc in df.columns, f"Required descriptor '{desc}' not in dataset"
    
    def test_unified_dataset_has_target(self):
        """Verify unified dataset has experimental_tof target column."""
        dataset_path = paths.data("processed", "unified_dataset.parquet")
        df = pd.read_parquet(dataset_path)
        
        assert 'experimental_tof' in df.columns, "experimental_tof column not found"
    
    def test_alignment_metrics_consistency(self):
        """Verify alignment metrics are consistent with unified dataset."""
        metrics_path = paths.outputs("alignment_metrics.json")
        dataset_path = paths.data("processed", "unified_dataset.parquet")
        
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        df = pd.read_parquet(dataset_path)
        
        # Aligned entries should match dataset length
        assert metrics['aligned_entries'] == len(df), \
            f"Aligned entries ({metrics['aligned_entries']}) != dataset rows ({len(df)})"
    
    def test_no_nan_in_target(self):
        """Verify no NaN values in experimental_tof target."""
        dataset_path = paths.data("processed", "unified_dataset.parquet")
        df = pd.read_parquet(dataset_path)
        
        nan_count = df['experimental_tof'].isna().sum()
        assert nan_count == 0, f"Found {nan_count} NaN values in experimental_tof"