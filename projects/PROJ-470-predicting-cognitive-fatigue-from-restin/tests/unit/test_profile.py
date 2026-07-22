import os
import sys
import json
import pytest
from pathlib import Path
import time

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

def test_profile_report_generation():
    """
    Tests that the profile script runs and generates a valid JSON report.
    """
    # Import the main function from the profile module
    from profile_memory import main, profile_function

    # Run the profile main
    # Note: This might fail if data is missing, but it should still generate a report
    # with status "skipped" or "failed" and valid keys.
    try:
        main()
    except SystemExit:
        # Expected if critical errors occur, but we check the file anyway
        pass

    report_path = Path("data/analysis/profile_report.json")
    assert report_path.exists(), "Profile report file was not created."

    with open(report_path, "r") as f:
        report = json.load(f)

    # Verify structure
    assert "steps" in report, "Report missing 'steps' key."
    assert "summary" in report, "Report missing 'summary' key."
    
    summary = report["summary"]
    assert "peak_memory_mb" in summary, "Summary missing 'peak_memory_mb'."
    assert "wall_time_s" in summary, "Summary missing 'wall_time_s'."
    
    # Verify types
    assert isinstance(summary["peak_memory_mb"], (int, float)), "peak_memory_mb must be a number."
    assert isinstance(summary["wall_time_s"], (int, float)), "wall_time_s must be a number."

    # Verify step structure
    for step in report["steps"]:
        assert "step" in step, "Step missing 'step' name."
        # Even if skipped/failed, it should have memory/time keys (possibly 0)
        assert "peak_memory_mb" in step, f"Step {step.get('step')} missing 'peak_memory_mb'."
        assert "wall_time_s" in step, f"Step {step.get('step')} missing 'wall_time_s'."

def test_profile_function_accuracy():
    """
    Tests the profile_function helper with a known heavy operation.
    """
    from profile_memory import profile_function
    import numpy as np

    def heavy_calc():
        x = np.random.rand(1000, 1000)
        return np.dot(x, x.T)

    stats = profile_function(heavy_calc)
    
    assert "peak_memory_mb" in stats
    assert "wall_time_s" in stats
    assert stats["peak_memory_mb"] > 0, "Memory usage should be positive for heavy calculation."
    assert stats["wall_time_s"] > 0, "Wall time should be positive for heavy calculation."
