import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import pytest
import sys
import os

# Add parent directory to path to import classify module
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.classify import load_metadata, load_validation_results, classify_regime, apply_classification, main
from pathlib import Path

class TestLoadMetadata:
    def test_load_metadata_success(self, tmp_path):
        """Test loading valid metadata file."""
        metadata_path = tmp_path / "cbnrm_proxy_metadata.json"
        metadata_content = {"status": "success", "indicator": "AG.LND.FRST.CF", "threshold": 0.5}
        with open(metadata_path, 'w') as f:
            json.dump(metadata_content, f)
        
        # Mock the global path in classify module
        with patch('data.classify.PROCESSED_DATA_DIR', tmp_path):
            result = load_metadata()
            assert result == metadata_content
            assert result['threshold'] == 0.5

    def test_load_metadata_missing_file(self, tmp_path):
        """Test that load_metadata raises error when file is missing."""
        with patch('data.classify.PROCESSED_DATA_DIR', tmp_path):
            with pytest.raises(FileNotFoundError, match="CBNRM Proxy metadata missing"):
                load_metadata()

    def test_load_metadata_empty_file(self, tmp_path):
        """Test that load_metadata raises error when file is empty."""
        metadata_path = tmp_path / "cbnrm_proxy_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump({}, f)
        
        with patch('data.classify.PROCESSED_DATA_DIR', tmp_path):
            with pytest.raises(ValueError, match="CBNRM Proxy metadata missing"):
                load_metadata()

    def test_load_metadata_missing_threshold(self, tmp_path):
        """Test that load_metadata raises error when threshold is missing."""
        metadata_path = tmp_path / "cbnrm_proxy_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump({"status": "success"}, f)
        
        with patch('data.classify.PROCESSED_DATA_DIR', tmp_path):
            with pytest.raises(ValueError, match="CBNRM Proxy metadata missing"):
                load_metadata()

class TestClassifyRegime:
    def test_classifies_cbnrm_when_proxy_above_threshold(self):
        """Test that regime_type is 1 when proxy > threshold."""
        assert classify_regime(0.6, 0.5) == 1

    def test_classifies_state_led_when_proxy_below_threshold(self):
        """Test that regime_type is 0 when proxy <= threshold."""
        assert classify_regime(0.4, 0.5) == 0
        assert classify_regime(0.5, 0.5) == 0

    def test_classifies_nan_as_none(self):
        """Test that NaN values result in None."""
        assert classify_regime(float('nan'), 0.5) is None

class TestApplyClassification:
    def test_classifies_dataframe_correctly(self):
        """Test that apply_classification correctly adds regime_type column."""
        df = pd.DataFrame({
            'country': ['A', 'B', 'C'],
            'proxy_value': [0.6, 0.4, 0.5]
        })
        metadata = {'threshold': 0.5}
        
        result_df = apply_classification(df, metadata)
        
        assert 'regime_type' in result_df.columns
        assert result_df.loc[0, 'regime_type'] == 1
        assert result_df.loc[1, 'regime_type'] == 0
        assert result_df.loc[2, 'regime_type'] == 0

class TestMain:
    def test_main_halt_on_missing_metadata(self, tmp_path):
        """Test that main exits with code 1 if metadata is missing."""
        # Setup directories
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        
        # Create a dummy merged panel
        merged_df = pd.DataFrame({'proxy_value': [0.6]})
        merged_path = processed_dir / "merged_panel.csv"
        merged_df.to_csv(merged_path, index=False)
        
        with patch('data.classify.PROCESSED_DATA_DIR', processed_dir), \
             patch('data.classify.PROJECT_ROOT', tmp_path):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_main_success(self, tmp_path):
        """Test successful execution of main."""
        # Setup directories
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        # Create metadata
        metadata_path = processed_dir / "cbnrm_proxy_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump({"threshold": 0.5}, f)
        
        # Create validation results
        validation_path = processed_dir / "proxy_validation.json"
        with open(validation_path, 'w') as f:
            json.dump({"excluded_countries": []}, f)
        
        # Create merged panel
        merged_df = pd.DataFrame({
            'country': ['A', 'B'],
            'proxy_value': [0.6, 0.4]
        })
        merged_path = processed_dir / "merged_panel.csv"
        merged_df.to_csv(merged_path, index=False)
        
        with patch('data.classify.PROCESSED_DATA_DIR', processed_dir), \
             patch('data.classify.PROJECT_ROOT', tmp_path):
            try:
                main()
            except SystemExit as e:
                if e.code != 0:
                    raise
            
            # Verify output file exists
            output_path = processed_dir / "classified_panel.csv"
            assert output_path.exists()
            
            # Verify content
            result_df = pd.read_csv(output_path)
            assert len(result_df) == 2
            assert result_df.loc[0, 'regime_type'] == 1
            assert result_df.loc[1, 'regime_type'] == 0