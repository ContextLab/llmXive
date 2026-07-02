"""
Contract test for data ingestion success rate (T009).

Asserts that the calculated success_rate meets or exceeds the configured
ingestion_success_threshold.
"""
import pytest
import tempfile
import pandas as pd
from pathlib import Path
from utils.config import get_config
from data.ingest import ingest_and_filter_dataset

def test_ingestion_success_rate_contract():
    """
    Contract test: Assert `success_rate` >= `config.ingestion_success_threshold`.
    
    This test simulates a pipeline run where some data is valid and some is invalid,
    calculates the success rate, and asserts it meets the contract threshold.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create a dataset where 80% of rows are valid
        # Total 10 rows, 8 valid, 2 invalid -> 80% success rate
        # Default threshold is typically 0.0 (or low), but we test against a specific threshold
        # to ensure the logic works.
        
        raw_data = []
        for i in range(10):
            if i < 8:
                # Valid row
                raw_data.append(f"S{i:03d},/raw/Pb.tif,/raw/I.tif,/raw/MA.tif,21.0,24.0,1.15,DEV_{i:03d}")
            else:
                # Invalid row (missing PCE)
                raw_data.append(f"S{i:03d},/raw/Pb.tif,/raw/I.tif,/raw/MA.tif,,24.0,1.15,DEV_{i:03d}")
        
        input_csv = tmp_path / "input.csv"
        input_csv.write_text("sample_id,Pb_map_path,I_map_path,MA_map_path,PCE,J_sc,V_oc,device_id\n" + "\n".join(raw_data))
        
        output_csv = tmp_path / "output.csv"
        
        config = get_config()
        
        # Run ingestion
        ingest_and_filter_dataset(
            input_path=str(input_csv),
            output_path=str(output_csv),
            config=config
        )
        
        # Calculate success rate manually for assertion
        input_count = 10
        output_df = pd.read_csv(output_csv)
        output_count = len(output_df)
        
        success_rate = output_count / input_count
        
        # The config threshold might be 0.0 by default, but we assert it is met.
        # If the config has a specific threshold (e.g., 0.5), this ensures we pass it.
        threshold = config.ingestion_success_threshold if hasattr(config, 'ingestion_success_threshold') else 0.0
        
        assert success_rate >= threshold, (
            f"Contract failed: Success rate ({success_rate:.2f}) is below "
            f"threshold ({threshold:.2f}). Ingestion process is not robust enough."
        )
        
        # Specific assertion for this scenario (80% success)
        assert success_rate == 0.8, "Success rate calculation is incorrect."

if __name__ == "__main__":
    test_ingestion_success_rate_contract()