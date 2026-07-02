"""
Integration test for missing metric exclusion (T010).

Verifies that samples with missing performance metrics are:
1. Excluded from the final dataset.
2. Logged with specific sample IDs.
"""
import os
import tempfile
import logging
import pandas as pd
from pathlib import Path
from io import StringIO
import sys
import io

# Import the actual implementation from the project
# We need to ensure the code/ directory is in the path for imports to work
# when running this test standalone or via pytest from the project root.
# However, the task description implies this file is in tests/integration/
# and the imports are relative to the project root structure.
# To be safe, we adjust sys.path if running directly.
if 'code' not in sys.path:
    code_path = Path(__file__).parent.parent.parent / 'code'
    if code_path.exists():
        sys.path.insert(0, str(code_path))

from data.ingest import ingest_and_filter_dataset
from utils.config import get_config

# Setup logging to capture output for verification
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def test_missing_metrics_exclusion():
    """
    Integration test: Assert samples with missing metrics are excluded and logged.
    """
    # Create a temporary directory for this test run
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Prepare a synthetic "raw" dataset with missing metrics
        # This simulates the output of a download/parse step before filtering
        # We create a CSV that mimics the structure expected by ingest_and_filter_dataset
        # but includes rows with NaN in critical performance columns (PCE, J_sc, V_oc)
        raw_data = """sample_id,Pb_map_path,I_map_path,MA_map_path,PCE,J_sc,V_oc,device_id
S001,/raw/S001_Pb.tif,/raw/S001_I.tif,/raw/S001_MA.tif,21.5,24.1,1.15,DEV_001
S002,/raw/S002_Pb.tif,/raw/S002_I.tif,/raw/S002_MA.tif,,23.5,1.10,DEV_002
S003,/raw/S003_Pb.tif,/raw/S003_I.tif,/raw/S003_MA.tif,20.8,,1.12,DEV_003
S004,/raw/S004_Pb.tif,/raw/S004_I.tif,/raw/S004_MA.tif,19.5,22.0,,DEV_004
S005,/raw/S005_Pb.tif,/raw/S005_I.tif,/raw/S005_MA.tif,22.1,24.5,1.18,DEV_005
S006,/raw/S006_Pb.tif,/raw/S006_I.tif,/raw/S006_MA.tif,NaN,23.0,1.14,DEV_006
"""
        
        input_csv_path = tmp_path / "raw_input.csv"
        input_csv_path.write_text(raw_data)
        
        output_csv_path = tmp_path / "filtered_output.csv"
        
        # Mock the config to ensure we have a threshold (default behavior)
        # We rely on the default config if not explicitly overridden
        config = get_config()
        
        # Capture log output to verify logging behavior
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        
        # Execute the ingestion pipeline logic
        # This function is expected to read the input, filter missing metrics,
        # and write the result.
        try:
            ingest_and_filter_dataset(
                input_path=str(input_csv_path),
                output_path=str(output_csv_path),
                config=config
            )
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            raise
        finally:
            logger.removeHandler(handler)
        
        # Verify the output file exists
        assert output_csv_path.exists(), "Output CSV was not created."
        
        # Load the output
        df_output = pd.read_csv(output_csv_path)
        
        # Load the original input for comparison
        df_input = pd.read_csv(input_csv_path)
        
        # 1. Assert Exclusion:
        # The output should NOT contain samples S002, S003, S004, S006
        # Only S001 and S005 should remain (rows with no NaN in PCE, J_sc, V_oc)
        expected_remaining_ids = {"S001", "S005"}
        actual_remaining_ids = set(df_output['sample_id'].tolist())
        
        assert actual_remaining_ids == expected_remaining_ids, (
            f"Exclusion logic failed. Expected IDs {expected_remaining_ids}, "
            f"but got {actual_remaining_ids}. Rows with missing metrics were not excluded."
        )
        
        # 2. Assert Logging:
        # Verify that the missing samples were logged.
        log_contents = log_capture.getvalue()
        
        # Check that the dropped IDs match the missing IDs
        dropped_ids = set(df_input[~df_input['sample_id'].isin(df_output['sample_id'])]['sample_id'])
        missing_ids = set(df_input[df_input[['PCE', 'J_sc', 'V_oc']].isnull().any(axis=1)]['sample_id'])
        
        assert dropped_ids == missing_ids, (
            f"Dropped IDs {dropped_ids} do not match missing IDs {missing_ids}."
        )
        
        # Verify logging of excluded sample IDs
        for sample_id in sorted(dropped_ids):
            assert sample_id in log_contents, f"Sample {sample_id} was not logged as excluded."
        
        logger.info(f"Test passed: {len(dropped_ids)} samples with missing metrics were correctly excluded.")
        logger.info(f"Excluded sample IDs: {sorted(dropped_ids)}")

if __name__ == "__main__":
    test_missing_metrics_exclusion()
