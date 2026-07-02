"""
Unit tests for the data ingestion module.
"""
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the function to test
from code.data.ingest import ingest_and_filter_dataset

def test_ingest_creates_output():
    """
    Test that ingest_and_filter_dataset creates the output CSV with correct columns.
    """
    # Create a temporary directory for raw data
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "raw"
        raw_dir.mkdir()
        output_path = Path(tmpdir) / "output" / "unified_dataset.csv"
        
        # Create fake map files
        sample_id = "TEST_001"
        pb_data = np.random.rand(10, 10)
        i_data = np.random.rand(10, 10)
        ma_data = np.random.rand(10, 10)
        
        # Save maps
        pb_path = raw_dir / f"{sample_id}_Pb_processed.npy" # We will mock the saving, but need source
        # Actually, the function expects raw files. Let's create raw files.
        pb_raw = raw_dir / f"{sample_id}_Pb_map.npy"
        i_raw = raw_dir / f"{sample_id}_I_map.npy"
        ma_raw = raw_dir / f"{sample_id}_MA_map.npy"
        
        np.save(pb_raw, pb_data)
        np.save(i_raw, i_raw)
        np.save(ma_raw, ma_data)
        
        # Create metadata
        meta_df = pd.DataFrame({
            'sample_id': [sample_id],
            'PCE': [20.5],
            'J_sc': [22.1],
            'V_oc': [1.1],
            'Pb_map_path': [str(pb_raw)],
            'I_map_path': [str(i_raw)],
            'MA_map_path': [str(ma_raw)]
        })
        meta_df.to_csv(raw_dir / "metadata.csv", index=False)
        
        # Run ingestion
        result = ingest_and_filter_dataset(str(raw_dir), str(output_path))
        
        # Assertions
        assert output_path.exists(), "Output CSV was not created."
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert 'sample_id' in result.columns
        assert 'Pb_map_path' in result.columns
        assert 'I_map_path' in result.columns
        assert 'MA_map_path' in result.columns
        assert 'PCE' in result.columns
        assert 'J_sc' in result.columns
        assert 'V_oc' in result.columns
        
        # Check values
        assert result.iloc[0]['sample_id'] == sample_id
        assert result.iloc[0]['PCE'] == 20.5

def test_ingest_filters_missing_metrics():
    """
    Test that samples with missing PCE, J_sc, or V_oc are excluded.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "raw"
        raw_dir.mkdir()
        output_path = Path(tmpdir) / "output" / "unified_dataset.csv"
        
        # Create two samples, one with missing data
        samples = ["S1", "S2"]
        pb_data = np.random.rand(5, 5)
        i_data = np.random.rand(5, 5)
        ma_data = np.random.rand(5, 5)
        
        paths = []
        for s in samples:
            pb = raw_dir / f"{s}_Pb_map.npy"
            i = raw_dir / f"{s}_I_map.npy"
            m = raw_dir / f"{s}_MA_map.npy"
            np.save(pb, pb_data)
            np.save(i, i_data)
            np.save(m, ma_data)
            paths.append((s, pb, i, m))
        
        # Metadata: S1 valid, S2 missing V_oc
        meta_df = pd.DataFrame({
            'sample_id': ['S1', 'S2'],
            'PCE': [20.0, 19.5],
            'J_sc': [22.0, 21.0],
            'V_oc': [1.1, np.nan], # Missing
            'Pb_map_path': [str(p[1]) for p in paths],
            'I_map_path': [str(p[2]) for p in paths],
            'MA_map_path': [str(p[3]) for p in paths]
        })
        meta_df.to_csv(raw_dir / "metadata.csv", index=False)
        
        # Run ingestion
        result = ingest_and_filter_dataset(str(raw_dir), str(output_path))
        
        # S2 should be excluded
        assert len(result) == 1
        assert result.iloc[0]['sample_id'] == 'S1'
        assert 'S2' not in result['sample_id'].values