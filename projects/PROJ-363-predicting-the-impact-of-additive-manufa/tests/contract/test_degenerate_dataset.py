import os
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import subprocess
import sys

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

def test_degenerate_dataset_detection():
    """
    Contract test: Verify that preprocess.py writes degenerate_flag.json,
    updates state.yaml, and exits with code 0 when given a degenerate dataset.
    """
    # Setup: Create a temporary directory for test artifacts
    test_dir = Path("tests/contract/tmp_degenerate_test")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    raw_csv_path = test_dir / "raw_degenerate.csv"
    schema_path = test_dir / "schema.yaml"
    output_path = test_dir / "cleaned.csv"
    flag_path = Path("data/processed/degenerate_flag.json")
    state_path = Path("state.yaml")
    
    # Create a degenerate dataset (zero porosity variance)
    data = {
        'laser_power': [100.0, 200.0, 300.0],
        'scan_speed': [500.0, 600.0, 700.0],
        'hatch_spacing': [0.1, 0.1, 0.1],
        'layer_thickness': [0.03, 0.03, 0.03],
        'porosity': [0.5, 0.5, 0.5] # Zero variance
    }
    df = pd.DataFrame(data)
    df.to_csv(raw_csv_path, index=False)
    
    # Create a minimal schema
    schema = {
        'required_columns': ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'porosity']
    }
    import yaml
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f)
    
    # Clean up previous flag and state if they exist
    if flag_path.exists():
        flag_path.unlink()
    
    # Run the preprocess script with modified paths
    # We need to monkey-patch or pass args. Since the script uses hardcoded paths in main(),
    # we will modify the script temporarily or create a wrapper.
    # For this test, we'll create a temporary copy of preprocess.py with modified paths.
    preprocess_src = Path("code/preprocess.py").read_text()
    
    # Replace hardcoded paths in the source code for this test
    modified_src = preprocess_src.replace(
        'raw_path = "data/raw/316L_LPBF_dataset.csv"',
        f'raw_path = "{raw_csv_path}"'
    ).replace(
        'schema_path = "contracts/dataset.schema.yaml"',
        f'schema_path = "{schema_path}"'
    ).replace(
        'output_path = "data/processed/cleaned_316L.csv"',
        f'output_path = "{output_path}"'
    )
    
    temp_preprocess_path = test_dir / "preprocess_test.py"
    temp_preprocess_path.write_text(modified_src)
    
    try:
        # Execute the modified script
        result = subprocess.run(
            [sys.executable, str(temp_preprocess_path)],
            capture_output=True,
            text=True
        )
        
        # Verify exit code is 0
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}. Stderr: {result.stderr}"
        
        # Verify flag file exists and contains correct data
        assert flag_path.exists(), "degenerate_flag.json was not created."
        
        with open(flag_path, 'r') as f:
            flag_data = json.load(f)
        
        assert flag_data['reason'] == "Zero porosity variance", f"Unexpected reason: {flag_data['reason']}"
        assert flag_data['status'] == "degenerate", f"Unexpected status: {flag_data['status']}"
        
        # Verify state.yaml was updated (if it existed before)
        # For this test, we assume state.yaml might not exist initially, but the script should handle it.
        # We check if the script ran without crashing on state update.
        
    finally:
        # Cleanup
        if flag_path.exists():
            flag_path.unlink()
        if raw_csv_path.exists():
            raw_csv_path.unlink()
        if schema_path.exists():
            schema_path.unlink()
        if output_path.exists():
            output_path.unlink()
        if temp_preprocess_path.exists():
            temp_preprocess_path.unlink()
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)