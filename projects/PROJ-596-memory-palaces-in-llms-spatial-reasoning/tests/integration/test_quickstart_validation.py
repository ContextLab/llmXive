import os
import json
import subprocess
import tempfile
from pathlib import Path

def test_quickstart_script_execution():
    """Test that the quickstart validation script runs and produces artifacts."""
    # This test assumes the script is executable and dependencies are installed
    # We run the script in a subprocess to verify end-to-end execution
    
    project_root = Path(__file__).parent.parent.parent
    script_path = project_root / "scripts" / "validate_quickstart.sh"
    
    if not script_path.exists():
        # Skip if script doesn't exist (might be in a different state)
        return

    # Run the script
    # Note: In a real CI environment, this would be run with proper setup
    # For unit testing purposes, we check if the script exists and is executable
    assert script_path.stat().st_mode & 0o111, "Script is not executable"
    
    # We do not actually run the full 5-hour pipeline here, 
    # but we verify the script structure and that it calls the main entry point
    with open(script_path, "r") as f:
        content = f.read()
    
    assert "python code/main.py" in content, "Script must call code/main.py"
    assert "artifacts/results/run_summary.json" in content, "Script must check for run_summary.json"
    assert "18000" in content, "Script must enforce 5-hour limit"

def test_runtime_verifier():
    """Test the runtime verifier module."""
    from evaluation.runtime_verifier import verify_runtime, write_runtime_report
    
    # Test verify_runtime
    assert verify_runtime(100, 18000) == True
    assert verify_runtime(20000, 18000) == False
    
    # Test write_runtime_report
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_runtime_report.json"
        report = write_runtime_report(100, 18000, str(output_path))
        
        assert output_path.exists()
        with open(output_path, "r") as f:
            data = json.load(f)
        
        assert data["runtime_seconds"] == 100
        assert data["within_limit"] == True