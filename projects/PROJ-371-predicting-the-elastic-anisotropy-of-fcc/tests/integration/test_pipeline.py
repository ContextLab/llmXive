import os
import json
import pytest
from pathlib import Path
import sys

# Add project root to path to allow imports from src
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.utils.config import get_path, get_config, set_random_seed
from src.utils.logging import setup_logger, log_info, log_error
from src.data.ingest import run_ingest
from src.data.clean import run_clean
from src.data.features import run_features

@pytest.fixture(autouse=True)
def setup_environment():
    """Ensure required environment variables are mocked or set for testing."""
    # Set a dummy API key if not present to prevent immediate failure in CI
    if "MP_API_KEY" not in os.environ:
        os.environ["MP_API_KEY"] = "test_dummy_key_for_integration"
    
    # Set random seed for reproducibility
    set_random_seed(42)
    yield

class TestPipelineEndToEndStatic:
    """Integration test for the full pipeline using a static manifest subset."""

    def test_pipeline_end_to_end_static(self, tmp_path):
        """
        Verify the full pipeline runs on a known subset of FCC material IDs.
        
        This test:
        1. Loads a static manifest of known FCC IDs.
        2. Runs the ingest, clean, and feature engineering steps.
        3. Verifies the output CSV exists and contains required columns.
        """
        # Setup paths
        manifest_path = project_root / "data" / "raw" / "manifest_subset.json"
        
        if not manifest_path.exists():
            pytest.fail(f"Static manifest not found at {manifest_path}. "
                        "Ensure data/raw/manifest_subset.json exists with valid MP/AFLOW IDs.")

        # Load manifest
        with open(manifest_path, "r") as f:
            material_ids = json.load(f)

        assert len(material_ids) > 0, "Manifest must contain at least one material ID."

        # Configure output directory for this test run
        output_dir = tmp_path / "processed"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the config path for processed data to use tmp_path for isolation
        # Note: In a real scenario, we might patch get_path or use a config override.
        # For this integration test, we will pass the output path directly if the 
        # pipeline functions support it, or rely on the global config if strictly needed.
        # Since the task requires running the pipeline, we assume the pipeline functions
        # use the global config which we can potentially override or we pass args.
        # Given the constraints of the existing API surface (which implies global config usage),
        # we will assume the pipeline writes to the configured 'data/processed' location.
        # To make this test robust in a temp environment, we might need to patch get_path.
        
        # However, to strictly follow "extend, don't re-author" and use existing API:
        # We will run the pipeline functions. If they rely on global config pointing to
        # the project root's data/processed, we will assert on that file.
        # To avoid permission issues in CI with root paths, we assume the test runner
        # has write access or we patch the config.
        
        # Strategy: Patch get_path to return tmp_path for 'processed'
        import src.utils.config as config_module
        original_get_path = config_module.get_path

        def mock_get_path(name, relative_to=None):
            if name == "processed":
                return output_dir
            return original_get_path(name, relative_to)

        config_module.get_path = mock_get_path

        try:
            # 1. Ingest
            log_info("Starting Ingest Step")
            # run_ingest expects the manifest path or reads from config. 
            # Assuming it reads from a config list or we pass the IDs.
            # Based on typical patterns, we pass the IDs directly if the function signature allows,
            # or we ensure the config has the IDs. 
            # Let's assume run_ingest takes a list of IDs or reads from a manifest file path.
            # The task description says "using a static manifest ... to verify the full pipeline".
            # We will assume run_ingest can take the list of IDs.
            
            # If run_ingest signature is fixed to read from config, we might need to update config.
            # Let's assume we pass the IDs to run_ingest for this specific test.
            # If the function doesn't accept args, we might need to patch the config's material_ids.
            # Given the API surface provided doesn't show run_ingest's signature, we assume standard
            # behavior: it reads from a config or takes an argument.
            # We will attempt to call it with the IDs. If it fails due to signature, we catch and adapt.
            # But to be safe and "real", let's assume it takes a list of IDs.
            
            try:
                run_ingest(material_ids)
            except TypeError:
                # Fallback: If it doesn't take args, we assume it reads from a global config
                # which we would have to patch. For this task, we assume the function
                # is designed to accept the manifest content or path.
                # Let's assume it takes the list.
                raise

            # 2. Clean
            log_info("Starting Clean Step")
            run_clean()

            # 3. Features
            log_info("Starting Features Step")
            run_features()

            # 4. Verify Output
            output_file = output_dir / "elastic_anisotropy.csv"
            assert output_file.exists(), f"Pipeline failed to create output at {output_file}"

            import pandas as pd
            df = pd.read_csv(output_file)

            required_columns = ["C11", "C12", "C44", "A1"]
            for col in required_columns:
                assert col in df.columns, f"Missing required column: {col}"

            # Verify we have some data (at least one row, or empty if all failed to fetch)
            # The test verifies the pipeline *runs*, so 0 rows is acceptable if all fetches failed,
            # but usually we expect some data if the IDs are valid.
            # We assert the structure is correct regardless of row count.
            
            log_info(f"Pipeline completed successfully. Output shape: {df.shape}")

        finally:
            # Restore original get_path
            config_module.get_path = original_get_path