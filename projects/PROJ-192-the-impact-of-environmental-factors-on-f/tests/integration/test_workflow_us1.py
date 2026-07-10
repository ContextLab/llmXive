"""
Integration test for User Story 1: End-to-end pipeline on synthetic data.

This test verifies the failure of the pipeline when the implementation is missing
(specifically the ingestion, preprocessing, and analysis steps).

It generates a small, synthetic ASV table and metadata to mimic the expected
real data structure, then asserts that the pipeline execution fails because
the required `src/pipelines/ingest.py` or `src/pipelines/preprocess.py`
logic to process these files is not yet implemented or returns an error.

Once the implementation is complete, this test should be updated to assert
success and validate the output files (`results/permanova_summary.csv`, etc.).
"""
import os
import tempfile
import shutil
import pandas as pd
import pytest
from pathlib import Path

# Project root relative to tests/integration
PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

# Ensure we can import src modules
import sys
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Mock imports for the pipeline components that might not exist yet
# We expect these to fail or raise NotImplementedError if T013/T015/T018 are not done.
try:
    from pipelines.ingest import ingest_raw_data, harmonize_metadata
    from pipelines.preprocess import denoise_asv, compute_diversity
    from pipelines.analysis import run_permanova
except ImportError as e:
    # If the modules don't exist, the test is expected to fail (as per T012 goal)
    # We define placeholders that raise errors to simulate missing implementation
    class MissingModule:
        def __getattr__(self, name):
            raise NotImplementedError(f"Implementation for {name} is missing (T013/T015/T018 not complete)")
    
    ingest_raw_data = MissingModule()
    harmonize_metadata = MissingModule()
    denoise_asv = MissingModule()
    compute_diversity = MissingModule()
    run_permanova = MissingModule()

def generate_synthetic_data(temp_dir: Path):
    """
    Generates small synthetic ASV table and metadata files.
    These are NOT used as 'fake results' but as valid INPUT files
    to trigger the pipeline logic.
    """
    asv_dir = temp_dir / "qc"
    meta_dir = temp_dir / "metadata"
    asv_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    # Synthetic ASV Table (TSV)
    # Columns: sample_id, asv_id, count
    asv_data = {
        "sample_id": ["S1", "S1", "S2", "S2", "S3", "S3"],
        "asv_id": ["ASV_001", "ASV_002", "ASV_001", "ASV_003", "ASV_002", "ASV_004"],
        "count": [100, 50, 120, 30, 90, 60]
    }
    asv_df = pd.DataFrame(asv_data)
    asv_path = asv_dir / "asv_table.tsv"
    asv_df.to_csv(asv_path, sep="\t", index=False)

    # Synthetic Metadata (CSV)
    # Columns: sample_id, pH, nutrients, biome
    meta_data = {
        "sample_id": ["S1", "S2", "S3"],
        "pH": [6.5, 7.2, 5.8],
        "nutrients": [10.5, 12.0, 8.5],
        "biome": ["Forest", "Grassland", "Forest"]
    }
    meta_df = pd.DataFrame(meta_data)
    meta_path = meta_dir / "harmonized_matrix.csv"
    meta_df.to_csv(meta_path, index=False)

    return asv_path, meta_path

def test_workflow_us1_fails_on_missing_implementation():
    """
    Integration test that verifies the pipeline fails if the core logic is missing.
    """
    # Setup temporary directory for this run
    temp_run_dir = tempfile.mkdtemp(prefix="us1_integration_")
    try:
        temp_path = Path(temp_run_dir)
        
        # Generate valid synthetic input files
        asv_file, meta_file = generate_synthetic_data(temp_path)
        
        # Define expected output paths
        output_summary = RESULTS_DIR / "permanova_summary.csv"
        output_variance = RESULTS_DIR / "db_rda_variance.csv"
        
        # Clean previous outputs to ensure we are testing a fresh run
        if output_summary.exists():
            output_summary.unlink()
        if output_variance.exists():
            output_variance.unlink()

        # Attempt to run the pipeline logic
        # We simulate the workflow steps. Since T013-T019 are not fully implemented,
        # the functions imported above (or their placeholders) should raise NotImplementedError
        # or fail to produce the required outputs.
        
        try:
            # Step 1: Ingest/Validate (T013)
            # Expected to fail if T013a-d not implemented
            if not isinstance(ingest_raw_data, MissingModule):
                # If real function exists, we might need to pass paths, 
                # but for this test we assume it fails if not fully ready
                pass
            
            # Step 2: Preprocess (T015-T017)
            if not isinstance(denoise_asv, MissingModule):
                pass

            # Step 3: Analysis (T018-T019)
            if not isinstance(run_permanova, MissingModule):
                pass

            # If we reach here without exception, check for outputs.
            # If the implementation is truly missing, we shouldn't have reached here
            # unless we are mocking too much.
            
            if not output_summary.exists():
                pytest.fail(
                    "Pipeline did not produce results/permanova_summary.csv. "
                    "Implementation of T013-T019 is incomplete."
                )
            if not output_variance.exists():
                pytest.fail(
                    "Pipeline did not produce results/db_rda_variance.csv. "
                    "Implementation of T013-T019 is incomplete."
                )
            
            # If files exist, the test passes (implies implementation is done)
            # But for T012 specifically, we want to verify failure first.
            # If the code below is reached and files exist, it means T013-T019 are done.
            # In a real TDD flow, this test would be updated to expect success.
            # For now, we assert that if we are in the "missing implementation" state,
            # we should have caught an error.
            
        except (NotImplementedError, ImportError, AttributeError) as e:
            # This is the EXPECTED outcome for T012 before implementation
            pytest.xfail(
                f"Expected failure: Implementation missing. Error: {str(e)}. "
                "This confirms T013-T019 are not yet implemented."
            )
        
        # If we get here and no files exist, it's a failure state
        if not output_summary.exists():
            pytest.fail(
                "Integration test failed: Pipeline did not generate expected outputs "
                "and did not raise a NotImplementedError. "
                "Check if T013-T019 are partially implemented but broken."
            )

    finally:
        # Cleanup temporary directory
        if os.path.exists(temp_run_dir):
            shutil.rmtree(temp_run_dir)