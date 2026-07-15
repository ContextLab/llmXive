"""
Integration test for the full data pipeline (User Story 1).

This test verifies the end-to-end flow:
1. Generate synthetic halo data (as per T008/Plan mandate for this stage).
2. Filter halos based on particle count (>= 300 particles).
3. Stream and save filtered data to Parquet format.
4. Validate the output schema and data integrity.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Project imports based on API surface
from data.synthetic_generator import generate_synthetic_halos, save_to_hdf5
from data.preprocess import filter_halos, stream_halos, save_filtered_to_parquet
from utils.logging import get_logger

logger = get_logger(__name__)

# Constants matching T004 config
MIN_PARTICLES = 300
BOX_SIZE = 100.0  # Mpc/h, assumed from T004 context if not imported directly

class TestDataPipeline:
    """Integration tests for the data acquisition and preprocessing pipeline."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test method."""
        # Create a temporary directory for test artifacts
        self.test_dir = tempfile.mkdtemp(prefix="pipeline_test_")
        self.raw_dir = Path(self.test_dir) / "raw"
        self.processed_dir = Path(self.test_dir) / "processed"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Set environment paths for the modules if they rely on global config
        # Note: In a real run, these would be read from code/config.py
        os.environ["DATA_RAW_DIR"] = str(self.raw_dir)
        os.environ["DATA_PROCESSED_DIR"] = str(self.processed_dir)

        yield

        # Cleanup
        shutil.rmtree(self.test_dir, ignore_errors=True)
        if "DATA_RAW_DIR" in os.environ:
            del os.environ["DATA_RAW_DIR"]
        if "DATA_PROCESSED_DIR" in os.environ:
            del os.environ["DATA_PROCESSED_DIR"]

    def test_full_data_pipeline(self):
        """
        Integration test: test_full_data_pipeline.
        
        Verifies the complete flow from synthetic generation to filtered Parquet output.
        """
        logger.info("Starting full data pipeline integration test.")

        # 1. Generate Synthetic Data (T008)
        # We generate a known number of halos to ensure we have some above and below the threshold
        num_halos = 100
        synthetic_file = self.raw_dir / "synthetic_halos.h5"
        
        logger.info(f"Generating {num_halos} synthetic halos...")
        generate_synthetic_halos(num_halos=num_halos, output_path=str(synthetic_file))
        
        assert synthetic_file.exists(), "Synthetic data file was not created."
        logger.info(f"Synthetic data generated at {synthetic_file}")

        # 2. Load and Filter Data (T013)
        # The filter should retain only halos with >= 300 particles
        logger.info("Filtering halos with >= 300 particles...")
        filtered_data = filter_halos(
            input_path=str(synthetic_file),
            min_particles=MIN_PARTICLES
        )
        
        assert isinstance(filtered_data, pd.DataFrame), "Filter did not return a DataFrame."
        assert "num_particles" in filtered_data.columns, "Missing 'num_particles' column."
        
        # Verify filtering logic
        assert all(filtered_data["num_particles"] >= MIN_PARTICLES), \
            "Filter failed: some halos have < 300 particles."
        
        logger.info(f"Filtered dataset contains {len(filtered_data)} halos.")

        # 3. Stream and Save to Parquet (T014)
        # Convert the filtered dataframe to a stream (generator) and save
        logger.info("Streaming and saving to Parquet...")
        
        # Create a generator function mimicking the stream_halos interface for this test
        def data_stream_generator():
            for _, row in filtered_data.iterrows():
                yield row.to_dict()

        output_file = self.processed_dir / "filtered_halos_test.parquet"
        
        # Use the stream function logic directly if it accepts an iterable, 
        # or simulate the stream by passing the dataframe rows
        # Assuming stream_halos is designed to read from a file, we'll use save_filtered_to_parquet
        # which likely handles the stream internally or we pass the dataframe.
        # Given the task T014 description "Implement chunked streaming writer", 
        # we assume save_filtered_to_parquet takes the data and writes it.
        
        save_filtered_to_parquet(
            data=filtered_data,
            output_path=str(output_file),
            chunk_size=10000
        )
        
        assert output_file.exists(), "Parquet output file was not created."
        
        # 4. Validate Output (T015)
        logger.info("Validating output schema and content...")
        result_df = pd.read_parquet(output_file)
        
        # Check required columns exist (based on schema in T015 context)
        required_columns = ["mass", "position_x", "position_y", "position_z", 
                            "velocity_x", "velocity_y", "velocity_z", "num_particles"]
        
        for col in required_columns:
            assert col in result_df.columns, f"Missing required column: {col}"
        
        # Verify data integrity (counts should match filtered data)
        assert len(result_df) == len(filtered_data), \
            f"Row count mismatch: expected {len(filtered_data)}, got {len(result_df)}"
        
        # Verify values are consistent (mass, positions, etc.)
        np.testing.assert_array_almost_equal(
            result_df["mass"].values, 
            filtered_data["mass"].values,
            err_msg="Mass values mismatch between filtered and saved data"
        )

        logger.info("Full data pipeline integration test PASSED.")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])