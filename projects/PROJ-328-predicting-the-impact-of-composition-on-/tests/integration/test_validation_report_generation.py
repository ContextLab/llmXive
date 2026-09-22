"""
Task T016c: Verify Validation Report Generation.

Runs `code/ingestion/generate_validation_report.py` with mock input files
to ensure it executes without errors and produces valid YAML.

This is a verification step (T016c) for the script created in T016b.
It creates temporary mock data, runs the script, and validates the output.
"""
import os
import sys
import json
import yaml
import tempfile
import shutil
import subprocess
from pathlib import Path

# Ensure code/ is in path for imports if running as a module, 
# but for this integration test we invoke the script via subprocess.
code_root = Path(__file__).resolve().parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

def test_validation_report_generation_with_mock_data():
    """
    Test that generate_validation_report.py runs successfully with mock inputs
    and produces a valid YAML file.
    """
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Setup paths relative to the temp directory
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        status_file = processed_dir / ".ingestion_status.json"
        output_file = processed_dir / "validation_report.yaml"
        
        # Create mock .ingestion_status.json
        mock_status = {
            "threshold_status": "50<=N<100",
            "exact_N": 75,
            "excluded_count": 12,
            "power_limitation_warning": "Statistical power may be limited due to N < 100"
        }
        
        with open(status_file, 'w') as f:
            json.dump(mock_status, f, indent=2)
        
        # Construct the command to run the script
        # We need to pass the paths or modify the script to accept arguments.
        # Since the script currently hardcodes paths relative to code_root,
        # we will run it from the project root but temporarily move our mock files
        # to the actual expected location in the project structure, OR
        # we can modify the test to inject the paths if the script supported it.
        #
        # However, the task T016c description says: "Run ... with a mock ... file".
        # The script `generate_validation_report.py` currently hardcodes paths relative to `code_root`.
        # To test it without modifying the production script's path logic (which might be needed for real runs),
        # we will create the mock files in the ACTUAL project's data/processed directory
        # temporarily, run the script, and then verify/clean up.
        #
        # Wait, modifying the live project state in a test is risky if the real data is missing.
        # Better approach: The script `generate_validation_report.py` should ideally accept CLI args.
        # But T016b (the script) was already implemented. T016c is to verify IT.
        # If T016b doesn't accept args, we must either:
        # 1. Modify T016b to accept args (but T016c is the verification task, usually not the implementation).
        # 2. Run the script in an environment where the paths exist.
        #
        # Let's look at the script again. It uses `code_root` (parent of ingestion dir).
        # If we run this test from the project root, `code_root` resolves to the project root.
        # So the script looks for `project_root/data/processed/.ingestion_status.json`.
        #
        # Strategy:
        # 1. Backup real files if they exist.
        # 2. Write mock files to `data/processed/`.
        # 3. Run the script.
        # 4. Verify output.
        # 5. Restore or cleanup.
        
        real_status_file = code_root / "data" / "processed" / ".ingestion_status.json"
        real_output_file = code_root / "data" / "processed" / "validation_report.yaml"
        
        backup_status = None
        backup_output = None
        
        if real_status_file.exists():
            backup_status = real_status_file.read_text()
        if real_output_file.exists():
            backup_output = real_output_file.read_text()
        
        try:
            # Write mock data to the real location
            with open(real_status_file, 'w') as f:
                json.dump(mock_status, f, indent=2)
            
            # Remove old output if exists to ensure fresh generation
            if real_output_file.exists():
                real_output_file.unlink()
            
            # Run the script
            script_path = code_root / "code" / "ingestion" / "generate_validation_report.py"
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(code_root),
                capture_output=True,
                text=True
            )
            
            # Check exit code
            assert result.returncode == 0, f"Script failed with code {result.returncode}. Stderr: {result.stderr}"
            
            # Verify output file exists
            assert real_output_file.exists(), "Output file was not created."
            
            # Verify content is valid YAML and matches expected structure
            with open(real_output_file, 'r') as f:
                report_data = yaml.safe_load(f)
            
            assert report_data is not None, "Loaded YAML is None."
            assert report_data.get("status") == "50<=N<100", "Status mismatch."
            assert report_data.get("count") == 75, "Count mismatch."
            assert report_data.get("excluded_count") == 12, "Excluded count mismatch."
            assert "power_limitation_warning" in report_data, "Warning missing."
            
        finally:
            # Restore original files or cleanup
            if backup_status is not None:
                with open(real_status_file, 'w') as f:
                    f.write(backup_status)
            elif real_status_file.exists():
                real_status_file.unlink()
                
            if backup_output is not None:
                with open(real_output_file, 'w') as f:
                    f.write(backup_output)
            elif real_output_file.exists():
                real_output_file.unlink()

if __name__ == "__main__":
    test_validation_report_generation_with_mock_data()
    print("T016c Verification: PASSED")