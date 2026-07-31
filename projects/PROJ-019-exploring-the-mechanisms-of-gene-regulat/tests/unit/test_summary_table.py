"""
Unit tests for code/summary_table.py (T033).
"""
import os
import json
import tempfile
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock the config paths to use a temporary directory
import sys
from code import config
from code import summary_table

def test_load_chip_overlap_stats_missing_file():
    """Test that load_chip_overlap_stats raises FileNotFoundError if report is missing."""
    # Ensure the path doesn't exist in the mock
    with patch.object(summary_table, 'CHIP_OVERLAP_REPORT_PATH', Path('/nonexistent/path.json')):
        try:
            summary_table.load_chip_overlap_stats()
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError:
            pass

def test_generate_summary_table_missing_enrichment():
    """Test that generate_summary_table raises FileNotFoundError if enrichment matrix is missing."""
    with patch.object(summary_table, 'ENRICHMENT_MATRIX_PATH', Path('/nonexistent/enrichment.csv')):
        with patch.object(summary_table, 'load_chip_overlap_stats', return_value={}):
            try:
                summary_table.generate_summary_table()
                assert False, "Expected FileNotFoundError"
            except FileNotFoundError:
                pass

def test_generate_summary_table_success():
    """Test successful generation of summary table."""
    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Mock paths
        enrichment_path = tmp_path / "enrichment.csv"
        overlap_path = tmp_path / "validation.json"
        output_path = tmp_path / "summary.csv"
        
        # Create mock enrichment data
        mock_enrichment = pd.DataFrame({
            'motif_id': ['MA0001', 'MA0002', 'MA0001'],
            'cell_type': ['GM', 'GM', 'K562'],
            'p_value': [1e-10, 1e-5, 1e-8],
            'q_value': [1e-8, 1e-3, 1e-6]
        })
        mock_enrichment.to_csv(enrichment_path, index=False)
        
        # Create mock overlap data
        mock_overlap = {
            "motif_overlaps": [
                {"motif_id": "MA0001", "overlap_pct": 0.85},
                {"motif_id": "MA0002", "overlap_pct": 0.45}
            ]
        }
        with open(overlap_path, 'w') as f:
            json.dump(mock_overlap, f)
        
        # Patch the module-level paths
        with patch.object(summary_table, 'ENRICHMENT_MATRIX_PATH', enrichment_path):
            with patch.object(summary_table, 'CHIP_OVERLAP_REPORT_PATH', overlap_path):
                with patch.object(summary_table, 'DATA_PROCESSED_DIR', tmp_path):
                    df_result = summary_table.generate_summary_table()
                    
                    # Check columns
                    expected_cols = ['motif_id', 'p_value_raw', 'q_value_adj', 'chip_overlap_pct']
                    assert list(df_result.columns) == expected_cols
                    
                    # Check row count (should be unique motifs: 2)
                    assert len(df_result) == 2
                    
                    # Check specific values
                    # MA0001 should have p_value 1e-10 (min) and overlap 0.85
                    row_0001 = df_result[df_result['motif_id'] == 'MA0001'].iloc[0]
                    assert row_0001['p_value_raw'] == 1e-10
                    assert row_0001['chip_overlap_pct'] == 0.85
                    
                    # MA0002 should have p_value 1e-5 and overlap 0.45
                    row_0002 = df_result[df_result['motif_id'] == 'MA0002'].iloc[0]
                    assert row_0002['p_value_raw'] == 1e-5
                    assert row_0002['chip_overlap_pct'] == 0.45

def test_main_execution():
    """Test the main() function execution flow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create mock files
        enrichment_path = tmp_path / "enrichment.csv"
        overlap_path = tmp_path / "validation.json"
        
        pd.DataFrame({
            'motif_id': ['MA0001'],
            'p_value': [1e-10],
            'q_value': [1e-8]
        }).to_csv(enrichment_path, index=False)
        
        with open(overlap_path, 'w') as f:
            json.dump({"motif_overlaps": [{"motif_id": "MA0001", "overlap_pct": 0.9}]}, f)
        
        with patch.object(summary_table, 'ENRICHMENT_MATRIX_PATH', enrichment_path):
            with patch.object(summary_table, 'CHIP_OVERLAP_REPORT_PATH', overlap_path):
                with patch.object(summary_table, 'DATA_PROCESSED_DIR', tmp_path):
                    # Mock the output path to be in tmpdir
                    output_path = tmp_path / "summary_table.csv"
                    with patch.object(summary_table, 'SUMMARY_TABLE_PATH', output_path):
                        ret = summary_table.main()
                        assert ret == 0
                        assert output_path.exists()
                        
                        # Verify content
                        df = pd.read_csv(output_path)
                        assert 'motif_id' in df.columns
                        assert 'chip_overlap_pct' in df.columns