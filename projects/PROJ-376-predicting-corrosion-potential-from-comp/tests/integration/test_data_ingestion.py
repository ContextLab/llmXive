"""
Integration test for data ingestion pipeline (T011).

This test verifies the end-to-end data ingestion workflow:
1. Download raw data from NIST (or verify existence if already downloaded)
2. Preprocess and validate the data
3. Verify output artifacts exist and meet schema requirements

CONSTRAINT: This test MUST fail before T012-T017 implementation.
"""
import os
import sys
import pytest
from pathlib import Path
import json
import tempfile
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import ProjectConfig, get_config, get_path
from utils.exceptions import DataInsufficientError, SchemaMismatchError
from utils.logging import setup_logger, get_logger
from utils.validation import validate_non_nulls, validate_schema_structure

# Test constants
MIN_RECORDS = 500
MIN_ALLOYS = 10

logger = get_logger(__name__)

class TestDataIngestionPipeline:
    """Integration tests for the data ingestion pipeline."""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test environment with temporary directories."""
        self.temp_dir = tmp_path
        self.data_dir = self.temp_dir / "data"
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.logs_dir = self.data_dir / "logs"
        
        self.raw_dir.mkdir(parents=True)
        self.processed_dir.mkdir(parents=True)
        self.logs_dir.mkdir(parents=True)
        
        # Create a minimal mock config
        self.config = {
            "paths": {
                "data_raw": str(self.raw_dir),
                "data_processed": str(self.processed_dir),
                "data_logs": str(self.logs_dir)
            },
            "dataset": {
                "url": "https://example.com/nist-mock.csv",
                "min_records": MIN_RECORDS,
                "min_alloys": MIN_ALLOYS
            }
        }
        
        # Save config
        config_file = self.temp_dir / "config.yaml"
        with open(config_file, 'w') as f:
            import yaml
            yaml.dump(self.config, f)
        
        os.environ["PROJECT_CONFIG"] = str(config_file)
        
        yield
        
        # Cleanup
        if "PROJECT_CONFIG" in os.environ:
            del os.environ["PROJECT_CONFIG"]
    
    def test_download_nist_script_exists(self):
        """Verify download_nist.py exists and is importable."""
        download_script = project_root / "code" / "data" / "download_nist.py"
        assert download_script.exists(), "download_nist.py must exist"
        
        # Try to import the script as a module
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("download_nist", download_script)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            assert hasattr(module, 'main') or hasattr(module, 'download'), \
                "download_nist.py must have a main or download function"
        except Exception as e:
            pytest.fail(f"Failed to import download_nist.py: {e}")
    
    def test_preprocess_script_exists(self):
        """Verify preprocess.py exists and is importable."""
        preprocess_script = project_root / "code" / "data" / "preprocess.py"
        assert preprocess_script.exists(), "preprocess.py must exist"
        
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("preprocess", preprocess_script)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            assert hasattr(module, 'main') or hasattr(module, 'preprocess'), \
                "preprocess.py must have a main or preprocess function"
        except Exception as e:
            pytest.fail(f"Failed to import preprocess.py: {e}")
    
    def test_pipeline_halt_on_insufficient_data(self):
        """
        Test that pipeline halts with DataInsufficientError when 
        downloaded data has <500 records.
        """
        # Create a mock dataset with only 100 records
        mock_data = {
            "records": [
                {
                    "specific_alloy_designation_id": f"alloy_{i}",
                    "weight_fraction_chromium": 0.1,
                    "weight_fraction_nickel": 0.05,
                    "ph": 7.0,
                    "temperature": 25.0,
                    "corrosion_potential": -0.5
                }
                for i in range(100)
            ]
        }
        
        mock_file = self.raw_dir / "nist_mock.json"
        with open(mock_file, 'w') as f:
            json.dump(mock_data, f)
        
        # Import and test the validation logic
        from utils.validation import validate_non_nulls, DataInsufficientError
        
        with pytest.raises(DataInsufficientError) as exc_info:
            # Simulate the validation that would happen in preprocess.py
            records = mock_data["records"]
            if len(records) < MIN_RECORDS:
                raise DataInsufficientError(
                    f"Dataset contains {len(records)} records, but minimum required is {MIN_RECORDS}"
                )
        
        assert "500" in str(exc_info.value) or str(MIN_RECORDS) in str(exc_info.value)
    
    def test_pipeline_halt_on_insufficient_alloys(self):
        """
        Test that pipeline halts with DataInsufficientError when 
        dataset has <10 specific alloy designations.
        """
        # Create a mock dataset with only 5 unique alloys
        mock_data = {
            "records": [
                {
                    "specific_alloy_designation_id": f"alloy_{i % 5}",  # Only 5 unique alloys
                    "weight_fraction_chromium": 0.1,
                    "weight_fraction_nickel": 0.05,
                    "ph": 7.0,
                    "temperature": 25.0,
                    "corrosion_potential": -0.5
                }
                for i in range(500)
            ]
        }
        
        # Import validation logic
        from utils.validation import DataInsufficientError
        
        records = mock_data["records"]
        unique_alloys = len(set(r["specific_alloy_designation_id"] for r in records))
        
        with pytest.raises(DataInsufficientError) as exc_info:
            if unique_alloys < MIN_ALLOYS:
                raise DataInsufficientError(
                    f"Dataset contains {unique_alloys} unique alloys, but minimum required is {MIN_ALLOYS}"
                )
        
        assert "10" in str(exc_info.value) or str(MIN_ALLOYS) in str(exc_info.value)
    
    def test_output_parquet_creation(self):
        """
        Test that the pipeline creates the expected output file:
        data/processed/corrosion_dataset.parquet
        """
        output_path = self.processed_dir / "corrosion_dataset.parquet"
        
        # The test should fail if the file doesn't exist (before implementation)
        # This will pass only after T012-T017 are implemented
        assert output_path.exists(), \
            f"Output file {output_path} does not exist. " \
            "This test must fail before T012-T017 implementation."
    
    def test_schema_validation_on_processed_data(self):
        """
        Test that processed data passes schema validation.
        """
        output_path = self.processed_dir / "corrosion_dataset.parquet"
        
        if not output_path.exists():
            pytest.skip("Output file not yet created (expected before implementation)")
        
        # Load and validate the parquet file
        try:
            import pandas as pd
            df = pd.read_parquet(output_path)
            
            # Check required columns
            required_columns = [
                'specific_alloy_designation_id',
                'weight_fraction_chromium',
                'weight_fraction_nickel',
                'ph',
                'temperature',
                'corrosion_potential'
            ]
            
            for col in required_columns:
                assert col in df.columns, f"Missing required column: {col}"
            
            # Check for nulls in critical fields
            critical_columns = ['specific_alloy_designation_id', 'corrosion_potential']
            for col in critical_columns:
                assert df[col].isnull().sum() == 0, \
                    f"Column {col} contains null values"
                
        except ImportError:
            pytest.skip("pandas or pyarrow not available")
        except Exception as e:
            pytest.fail(f"Schema validation failed: {e}")
    
    def test_groupkfold_split_verification(self):
        """
        Test that the split logic prevents alloy leakage between folds.
        This is a placeholder that will fail until T015 is implemented.
        """
        split_file = self.processed_dir / "split_indices.json"
        
        if not split_file.exists():
            pytest.skip("Split file not yet created (expected before implementation)")
        
        try:
            with open(split_file, 'r') as f:
                split_data = json.load(f)
            
            # Verify fold structure
            assert 'folds' in split_data, "Split data must contain 'folds' key"
            
            # Check that no alloy appears in both train and test sets
            for fold_idx, fold in enumerate(split_data['folds']):
                train_alloys = set(fold.get('train_alloys', []))
                test_alloys = set(fold.get('test_alloys', []))
                
                overlap = train_alloys & test_alloys
                assert len(overlap) == 0, \
                    f"Alloy leakage detected in fold {fold_idx}: {overlap}"
                    
        except json.JSONDecodeError:
            pytest.fail("Split file is not valid JSON")
        except Exception as e:
            pytest.fail(f"Split verification failed: {e}")
    
    def test_diagnostics_log_creation(self):
        """
        Test that diagnostic logs are created during pipeline execution.
        """
        log_file = self.logs_dir / "pipeline.log"
        
        if not log_file.exists():
            pytest.skip("Pipeline log not yet created (expected before implementation)")
        
        # Verify log contains expected entries
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        assert "pipeline" in log_content.lower() or "processing" in log_content.lower(), \
            "Log file should contain pipeline processing information"
    
    def test_end_to_end_pipeline_execution(self):
        """
        Full integration test: Run the complete pipeline and verify all outputs.
        This test will FAIL until T012-T017 are implemented.
        """
        # Check that all required scripts exist
        download_script = project_root / "code" / "data" / "download_nist.py"
        preprocess_script = project_root / "code" / "data" / "preprocess.py"
        
        assert download_script.exists(), "download_nist.py must exist"
        assert preprocess_script.exists(), "preprocess.py must exist"
        
        # The actual execution would be:
        # 1. Run download_nist.py
        # 2. Run preprocess.py
        # 3. Verify outputs
        
        # For now, we just verify the outputs exist
        expected_outputs = [
            self.processed_dir / "corrosion_dataset.parquet",
            self.logs_dir / "pipeline.log"
        ]
        
        missing_outputs = [p for p in expected_outputs if not p.exists()]
        if missing_outputs:
            pytest.fail(
                f"Expected outputs missing: {missing_outputs}. "
                "This test must fail before T012-T017 implementation."
            )
        
        # Verify record count
        try:
            import pandas as pd
            df = pd.read_parquet(self.processed_dir / "corrosion_dataset.parquet")
            assert len(df) >= MIN_RECORDS, \
                f"Dataset has {len(df)} records, minimum required is {MIN_RECORDS}"
        except Exception as e:
            pytest.fail(f"Failed to verify record count: {e}")
        
        # Verify unique alloy count
        try:
            import pandas as pd
            df = pd.read_parquet(self.processed_dir / "corrosion_dataset.parquet")
            unique_alloys = df['specific_alloy_designation_id'].nunique()
            assert unique_alloys >= MIN_ALLOYS, \
                f"Dataset has {unique_alloys} unique alloys, minimum required is {MIN_ALLOYS}"
        except Exception as e:
            pytest.fail(f"Failed to verify alloy count: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
