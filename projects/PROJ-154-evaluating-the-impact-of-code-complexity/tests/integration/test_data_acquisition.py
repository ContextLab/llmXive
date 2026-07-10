"""
Integration test for data download and extraction (T011).

Prerequisites: T001 (project structure), T002 (requirements installed).

This test verifies that the data acquisition script (code/01_data_acquisition.py)
successfully downloads the CodeSearchNet Python subset from HuggingFace,
extracts it, and produces the expected raw data file and metadata log.

It ensures the pipeline can handle real external data sources without
fabricating results.
"""
import os
import sys
import json
import pytest
import shutil
import tempfile
from pathlib import Path

# Add project root to path to import code modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.logging_config import set_seed, get_logger

# Set seed for reproducibility in case any randomness is involved
set_seed(42)
logger = get_logger(__name__)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for data to avoid polluting the repo."""
    # We use a temp dir but expect the script to write to the standard
    # project paths relative to the repo root. For this test, we will
    # patch the output paths or run the script in a way that respects
    # the project structure.
    # However, the task requires the script to write to `data/raw/` and `data/processed/`.
    # To be safe and not pollute the repo during CI, we create a temp structure
    # and copy it back, or we rely on the fact that the test environment
    # might have a writable `data/` directory.
    # Given the strict "real data" constraint, we assume the `data/` directory
    # exists or will be created by the script.
    
    original_data = project_root / "data"
    temp_base = Path(tempfile.mkdtemp())
    temp_data = temp_base / "data"
    temp_data.mkdir(parents=True)
    
    # We will run the script and check if it creates the files in the temp location
    # by modifying the script's internal paths or by mocking.
    # Since we cannot modify the script's hardcoded paths easily without a refactor,
    # and the task says "Stay inside the project tree", we assume the test runs
    # in an environment where `data/` is writable.
    # To be safe, we create the `data` folder in the project root if it doesn't exist,
    # and clean it up afterwards if it was empty.
    
    yield temp_data
    
    # Cleanup
    if temp_base.exists():
        shutil.rmtree(temp_base)


def test_data_acquisition_integration():
    """
    Integration test: Run 01_data_acquisition.py and verify outputs.
    
    This test:
    1. Ensures `data/raw/` and `data/processed/` directories exist.
    2. Runs the acquisition script.
    3. Verifies `data/raw/codesearchnet_python.parquet` (or similar) exists.
    4. Verifies `data/processed/metadata.json` exists and contains `total_raw_snippets`.
    5. Verifies the raw file is not empty and has valid structure.
    """
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Import the main function from the acquisition script
    # We need to run the script logic. Since it's a script, we can import its main logic
    # or exec it. The script likely has a `if __name__ == "__main__":` block.
    # Let's import the module and call the main function if it exists,
    # or run the script via subprocess to ensure it runs as intended.
    
    # Strategy: Run the script via subprocess to ensure it executes fully
    # and writes to the correct paths relative to the project root.
    import subprocess
    
    script_path = project_root / "code" / "01_data_acquisition.py"
    
    if not script_path.exists():
        pytest.fail(f"Script not found: {script_path}. T012 must be completed first.")
    
    logger.info(f"Running data acquisition script: {script_path}")
    
    # Run the script
    # Note: This might take a while depending on network speed and dataset size.
    # The test assumes the dataset is downloadable.
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )
        
        if result.returncode != 0:
            logger.error(f"Script failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            pytest.fail(f"Data acquisition script failed. See logs for details.")
        
        logger.info("Script completed successfully.")
        
    except subprocess.TimeoutExpired:
        pytest.fail("Data acquisition script timed out.")
    
    # Verify outputs
    
    # 1. Check for metadata.json
    metadata_path = processed_dir / "metadata.json"
    assert metadata_path.exists(), f"Metadata file not found: {metadata_path}"
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    assert "total_raw_snippets" in metadata, "metadata.json missing 'total_raw_snippets'"
    assert isinstance(metadata["total_raw_snippets"], int), "total_raw_snippets must be an integer"
    assert metadata["total_raw_snippets"] > 0, "total_raw_snippets must be > 0"
    
    logger.info(f"Metadata verified: total_raw_snippets = {metadata['total_raw_snippets']}")
    
    # 2. Check for raw data file
    # The script should download to data/raw/. The filename depends on implementation.
    # Assuming it saves as 'codesearchnet_python.parquet' or similar.
    # We look for any parquet or csv file in data/raw/
    raw_files = list(raw_dir.glob("*"))
    assert len(raw_files) > 0, "No raw data files found in data/raw/"
    
    # Find the main data file (likely parquet)
    data_file = None
    for f in raw_files:
        if f.suffix == '.parquet' or f.name.endswith('.csv'):
            data_file = f
            break
    
    assert data_file is not None, "No parquet or csv file found in data/raw/"
    
    logger.info(f"Raw data file found: {data_file.name}")
    
    # 3. Verify data integrity (sample check)
    # Load a few rows to ensure it's valid
    try:
        import pandas as pd
        df = pd.read_parquet(data_file) if data_file.suffix == '.parquet' else pd.read_csv(data_file)
        
        assert len(df) > 0, "Data file is empty"
        assert "code" in df.columns or "func_code" in df.columns, "Data file missing 'code' column"
        
        logger.info(f"Data file loaded successfully. Rows: {len(df)}, Columns: {list(df.columns)}")
        
    except Exception as e:
        pytest.fail(f"Failed to load or validate raw data file: {e}")
    
    logger.info("Integration test passed: Data acquisition and extraction verified.")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
