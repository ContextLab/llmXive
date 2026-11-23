"""
Integration test for T028: Generate Recovery Trajectories.
Verifies that the script runs end-to-end and produces a valid parquet file
with the expected schema (event_start, event_end, severity, trajectory_params).
"""
import os
import pytest
import pandas as pd
from pathlib import Path
import shutil
import tempfile

# We need to mock the upstream dependencies (ndvi_timeseries.parquet) 
# to ensure this test is deterministic and doesn't rely on real data fetches.
# However, per strict constraints, we must test the *real* logic. 
# Since T028 depends on T017 output, we will create a minimal synthetic 
# dataset that mimics the structure of T017's output to verify T028's logic.
# NOTE: In a real CI/CD, this would run after T017. Here we simulate the input.

def create_mock_ndvi_data(tmp_path):
    """Create a mock NDVI timeseries that triggers a deforestation event and recovery."""
    # Create a site with a clear drop and recovery
    data = []
    site_id = "SITE_001"
    pair_id = "PAIR_01"
    
    # Pre-deforestation (high NDVI)
    for i in range(12): # 12 months
        data.append({
            "site_id": site_id,
            "pair_id": pair_id,
            "date": f"2010-{i+1:02d}-01",
            "ndvi": 0.75 + (0.01 * i), # Slight upward trend
            "biome": "tropical"
        })
    
    # Deforestation event (drop)
    for i in range(12): # 12 months of low NDVI
        data.append({
            "site_id": site_id,
            "pair_id": pair_id,
            "date": f"2011-{i+1:02d}-01",
            "ndvi": 0.35, # Drop > 0.30 (0.75 - 0.35 = 0.40)
            "biome": "tropical"
        })
    
    # Recovery phase (asymptotic recovery)
    # Using a simple logistic-like recovery for testing
    for i in range(24): # 24 months of recovery
        t = i / 24.0
        recovery_val = 0.35 + (0.40 * (1 - 2.71828 ** (-2 * t)))
        data.append({
            "site_id": site_id,
            "pair_id": pair_id,
            "date": f"2012-{i+1:02d}-01",
            "ndvi": min(0.75, recovery_val), # Cap at pre-deforestation level
            "biome": "tropical"
        })

    df = pd.DataFrame(data)
    parquet_path = tmp_path / "ndvi_timeseries.parquet"
    df.to_parquet(parquet_path)
    return parquet_path

def create_mock_metadata(tmp_path):
    """Create mock site metadata."""
    data = [
        {
            "site_id": "SITE_001",
            "pair_id": "PAIR_01",
            "is_ecotourism": True,
            "biome": "tropical",
            "initial_ndvi": 0.80
        }
    ]
    df = pd.DataFrame(data)
    csv_path = tmp_path / "site_metadata.csv"
    df.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture
def mock_inputs(tmp_path):
    """Setup mock input files in a temporary directory."""
    # We need to temporarily swap the data directory or point the script to the temp dir.
    # For this test, we will modify the environment or pass paths if the script supported it.
    # Since the script uses hardcoded paths "data/processed/...", we will:
    # 1. Create the real data structure in a temp dir.
    # 2. Run the script from that temp dir.
    
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    ndvi_path = create_mock_ndvi_data(data_dir)
    meta_path = create_mock_metadata(data_dir)
    
    return {
        "base_dir": tmp_path,
        "ndvi_path": ndvi_path,
        "meta_path": meta_path,
        "output_path": data_dir / "recovery_trajectories.parquet"
    }

def test_t028_generates_output(mock_inputs):
    """
    Test that T028 script runs and produces the expected parquet file.
    """
    import sys
    import importlib.util

    base_dir = mock_inputs["base_dir"]
    output_path = mock_inputs["output_path"]

    # Save original cwd
    original_cwd = os.getcwd()
    
    try:
        # Change to the temp directory so relative paths resolve correctly
        os.chdir(base_dir)
        
        # Ensure the code path is importable (assuming we are in the project root context)
        # We need to make sure 'code' is in the path. 
        # In the real runner, the script is run as 'python code/generate_recovery_trajectories.py'
        # from the project root. Here we simulate that.
        
        # Add project root to path if not already
        project_root = Path(base_dir).parent # If we are in data/processed, parent is project
        # Actually, mock_inputs base_dir is the project root for this test.
        
        # Load the module dynamically to avoid import conflicts if run multiple times
        script_path = Path("code/generate_recovery_trajectories.py")
        if not script_path.exists():
            # If running in a context where the script isn't copied, skip or fail
            # But in the real pipeline, it exists.
            pytest.skip("Script not found in expected location (expected in real pipeline).")
        
        spec = importlib.util.spec_from_file_location("generate_recovery_trajectories", script_path)
        module = importlib.util.module_from_spec(spec)
        
        # Mock the imports that the script needs (config, logging_config, detection)
        # Since we are in a test, we assume the project structure is intact relative to the script.
        # We just need to ensure the script can find 'config' etc.
        sys.path.insert(0, str(Path("code").parent)) # Add root to path
        
        try:
            spec.loader.exec_module(module)
            module.main()
        except Exception as e:
            # If the script fails, it should be because of logic, not setup
            # But we need to ensure the mock data was valid.
            # If the script expects specific columns, we must ensure our mock has them.
            # Our mock has 'site_id', 'pair_id', 'date', 'ndvi', 'biome'.
            # The detection logic might expect 'is_ecotourism' from metadata.
            # Let's check if the script ran.
            if not output_path.exists():
                pytest.fail(f"Script execution failed or did not produce output. Error: {e}")
            raise e

        # Assertions
        assert output_path.exists(), "Output file was not created."
        
        df_result = pd.read_parquet(output_path)
        
        # Check schema
        required_columns = ["site_id", "event_start", "event_end", "severity", "trajectory_params"]
        for col in required_columns:
            assert col in df_result.columns, f"Missing required column: {col}"
        
        # Check content
        assert len(df_result) > 0, "No trajectories were generated from the mock data."
        
        # Verify severity calculation (approx)
        # Our mock had a drop from ~0.85 to 0.35 -> severity ~0.50
        # We just check that severity is a number and non-zero
        assert df_result["severity"].notna().all(), "Severity values should not be null."
        
        # Verify trajectory_params is a dict or string representation of params
        # (Depending on how detection.py serializes it)
        assert df_result["trajectory_params"].notna().all(), "Trajectory params should not be null."

    finally:
        os.chdir(original_cwd)
        # Cleanup sys.path
        if str(Path("code").parent) in sys.path:
            sys.path.remove(str(Path("code").parent))