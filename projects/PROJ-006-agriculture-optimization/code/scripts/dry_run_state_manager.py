"""
Script to perform a dry-run hash calculation on a dummy file
to confirm the update mechanism works (Verification for T002).
"""

import os
import tempfile
from pathlib import Path
import sys

# Add code directory to path
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.utils import state_manager
import hashlib

def main():
    print("=== T002 Verification: Dry-Run Hash Calculation ===")

    # Create a temporary directory to simulate project structure
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Simulate data directories
        data_raw = tmp_path / "data" / "raw"
        data_raw.mkdir(parents=True)
        
        # Create a dummy file
        dummy_file = data_raw / "dummy_data.csv"
        dummy_content = "id,value\n1,100\n2,200"
        dummy_file.write_text(dummy_content)
        
        # Calculate expected hash manually
        expected_hash = hashlib.sha256(dummy_content.encode()).hexdigest()
        
        # Mock the state_manager module paths to point to our temp directory
        state_manager.PROJECT_ROOT = tmp_path
        state_manager.STATE_DIR = tmp_path / "state" / "projects"
        state_manager.STATE_FILE = state_manager.STATE_DIR / "PROJ-006-agriculture-optimization.yaml"
        state_manager.DATA_RAW_DIR = data_raw
        state_manager.DATA_PROCESSED_DIR = tmp_path / "data" / "processed"
        
        print(f"Created dummy file: {dummy_file}")
        print(f"Expected Hash: {expected_hash}")
        
        # Run the dry-run command logic (scanning only)
        print("\nRunning dry-run scan...")
        state_manager.main() # This will trigger the 'dry-run' command if passed, but we need to simulate it or call logic directly
        
        # Since main() parses args, let's call the logic directly for the dry run
        print("\nDirect logic execution for verification:")
        artifacts = state_manager.scan_directory_for_artifacts(data_raw)
        if artifacts:
            for artifact in artifacts:
                calculated_hash = state_manager.compute_file_hash(artifact)
                print(f"  File: {artifact.name}")
                print(f"  Calculated Hash: {calculated_hash}")
                
                if calculated_hash == expected_hash:
                    print("  [PASS] Hash matches expected value.")
                else:
                    print("  [FAIL] Hash mismatch!")
                    return 1
        else:
            print("  [FAIL] No artifacts found.")
            return 1

        # Test the update mechanism
        print("\nTesting update mechanism...")
        hashes = state_manager.update_artifact_hashes()
        if dummy_file.name in [Path(k).name for k in hashes.keys()]:
            print("  [PASS] Update mechanism successfully recorded the dummy file.")
            return 0
        else:
            print("  [FAIL] Update mechanism failed to record the dummy file.")
            return 1

if __name__ == "__main__":
    sys.exit(main())