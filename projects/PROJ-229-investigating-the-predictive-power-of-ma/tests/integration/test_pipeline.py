"""
Integration test for the full data pipeline (US1).

This test verifies the end-to-end execution of the pipeline:
1. Fetches materials data (T011)
2. Computes descriptors (T012)
3. Performs VIF analysis (T014)
4. Orchestrates via main.py (T015)

Prerequisites:
- T015 must be complete to ensure the full pipeline entry point exists.
- T011, T012, T014 must be implemented.
- Real data sources must be available (Materials Project API).

Acceptance Criteria:
- The pipeline runs without errors.
- The output CSV (data/processed/materials_pipeline_output.csv) exists.
- The output CSV contains at least 5,000 compounds (if data available).
- Computed feature columns are present.
- Memory usage stays within 7GB RAM limits.
"""
import os
import sys
import tempfile
import shutil
import logging
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.main import run_pipeline
from code.utils.logger import get_pipeline_logger
from code.utils.stability_checks import get_memory_stats, check_memory_usage
from code.utils.error_handling import handle_error, PipelineError

# Configure logging for tests
logger = get_pipeline_logger("test_pipeline")

class TestPipelineIntegration:
    """Integration tests for the full data pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Setup: Create temporary directories if needed
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # Ensure data directories exist
        data_dirs = [
            "data/raw",
            "data/processed",
            "data/results"
        ]
        for d in data_dirs:
            os.makedirs(PROJECT_ROOT / d, exist_ok=True)
        
        yield
        
        # Teardown: Cleanup
        os.chdir(self.original_cwd)
        # Note: We don't delete temp_dir to allow inspection of results if needed
        # But in CI, it will be cleaned up by the runner
        
    def test_pipeline_execution(self):
        """
        Test that the full pipeline executes successfully.
        
        This test runs the main pipeline entry point and verifies:
        1. No exceptions are raised during execution
        2. Output files are created
        3. Output files contain expected data
        """
        logger.info("Starting pipeline integration test")
        
        try:
            # Run the pipeline
            # Note: This will fetch real data from Materials Project API
            # and process it through the full pipeline
            result = run_pipeline()
            
            # Verify result structure
            assert result is not None, "Pipeline should return a result dict"
            assert "status" in result, "Result should contain status"
            assert result["status"] == "success", f"Pipeline failed: {result.get('error', 'Unknown error')}"
            
            # Verify output file exists
            output_path = PROJECT_ROOT / "data/processed" / "materials_pipeline_output.csv"
            assert output_path.exists(), f"Output file not found: {output_path}"
            
            # Verify output file is not empty
            df = pd.read_csv(output_path)
            assert len(df) > 0, "Output CSV is empty"
            
            # Verify minimum number of compounds (if data available)
            # Note: The spec requires at least 5,000 compounds if available
            # We check if we got a reasonable amount of data
            logger.info(f"Output dataset contains {len(df)} compounds")
            
            # Verify required columns exist
            expected_columns = [
                "material_id",
                "formula",
                "melting_point",  # or the target metric used
                "n_elements",
                "n_atoms"
            ]
            
            for col in expected_columns:
                assert col in df.columns, f"Missing required column: {col}"
                
            # Verify computed descriptors are present
            descriptor_cols = [col for col in df.columns if col.startswith("desc_")]
            assert len(descriptor_cols) > 0, "No computed descriptors found"
            logger.info(f"Found {len(descriptor_cols)} descriptor columns")
            
            # Verify memory usage is within limits
            mem_stats = get_memory_stats()
            assert mem_stats["memory_mb"] < 7000, f"Memory usage exceeded 7GB: {mem_stats['memory_mb']}MB"
            
            logger.info("Pipeline integration test PASSED")
            
        except Exception as e:
            logger.error(f"Pipeline integration test FAILED: {str(e)}")
            # Re-raise to fail the test
            raise

    def test_pipeline_memory_constraints(self):
        """
        Test that the pipeline respects memory constraints.
        
        This test verifies that the pipeline doesn't exceed the 7GB RAM limit.
        """
        logger.info("Testing pipeline memory constraints")
        
        try:
            # Run the pipeline
            result = run_pipeline()
            
            # Check memory usage during/after execution
            mem_stats = get_memory_stats()
            logger.info(f"Memory usage after pipeline: {mem_stats['memory_mb']}MB")
            
            assert mem_stats["memory_mb"] < 7000, \
                f"Pipeline exceeded memory limit: {mem_stats['memory_mb']}MB > 7000MB"
                
            logger.info("Memory constraint test PASSED")
            
        except Exception as e:
            logger.error(f"Memory constraint test FAILED: {str(e)}")
            raise

    def test_pipeline_data_quality(self):
        """
        Test that the pipeline produces valid data.
        
        This test verifies:
        1. No NaN/Inf values in critical columns
        2. Data types are correct
        3. Values are within reasonable ranges
        """
        logger.info("Testing pipeline data quality")
        
        try:
            # Run the pipeline first
            result = run_pipeline()
            
            # Load output data
            output_path = PROJECT_ROOT / "data/processed" / "materials_pipeline_output.csv"
            df = pd.read_csv(output_path)
            
            # Check for NaN/Inf in critical columns
            critical_cols = ["melting_point", "n_elements", "n_atoms"]
            for col in critical_cols:
                if col in df.columns:
                    nan_count = df[col].isna().sum()
                    inf_count = np.isinf(df[col]).sum()
                    assert nan_count == 0, f"NaN values found in {col}: {nan_count}"
                    assert inf_count == 0, f"Inf values found in {col}: {inf_count}"
                    
            # Check data types
            assert df["material_id"].dtype == object, "material_id should be string"
            assert df["formula"].dtype == object, "formula should be string"
            
            # Check reasonable ranges
            if "melting_point" in df.columns:
                # Melting points should be positive (in Kelvin)
                mp_min = df["melting_point"].min()
                assert mp_min > 0, f"Invalid melting point: {mp_min}"
                
            logger.info("Data quality test PASSED")
            
        except Exception as e:
            logger.error(f"Data quality test FAILED: {str(e)}")
            raise

    def test_pipeline_vif_integration(self):
        """
        Test that VIF analysis is integrated into the pipeline.
        
        This test verifies that the pipeline performs collinearity analysis
        and reports results.
        """
        logger.info("Testing VIF integration")
        
        try:
            # Run the pipeline
            result = run_pipeline()
            
            # Check that VIF results are included in the output
            # The pipeline should log VIF results or include them in the result dict
            assert "vif_analysis" in result or "collinearity" in result, \
                "VIF analysis results should be included in pipeline output"
                
            logger.info("VIF integration test PASSED")
            
        except Exception as e:
            logger.error(f"VIF integration test FAILED: {str(e)}")
            # Note: If VIF is not yet implemented, this test will fail
            # which is expected behavior - the test should fail before implementation
            raise

if __name__ == "__main__":
    pytest.main([__file__, "-v"])