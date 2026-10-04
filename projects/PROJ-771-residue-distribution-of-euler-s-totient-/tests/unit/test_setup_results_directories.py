import os
import pytest
from pathlib import Path
from code.setup_results_directories import setup_results_directories

def test_setup_results_directories_creates_folders():
    """
    Verify that setup_results_directories creates results/plots and results/reports.
    """
    # Clean up if they exist from previous runs
    results_dir = Path("results")
    if results_dir.exists():
        import shutil
        shutil.rmtree(results_dir)

    result = setup_results_directories()

    assert "plots" in result
    assert "reports" in result

    assert Path(result["plots"]).exists()
    assert Path(result["reports"]).exists()

    # Verify .gitkeep files exist to ensure directory tracking
    assert (Path(result["plots"]) / ".gitkeep").exists()
    assert (Path(result["reports"]) / ".gitkeep").exists()

def test_setup_results_directories_idempotent():
    """
    Verify that running setup_results_directories multiple times doesn't fail.
    """
    # Run twice
    result1 = setup_results_directories()
    result2 = setup_results_directories()

    assert result1["plots"] == result2["plots"]
    assert result1["reports"] == result2["reports"]
    assert Path(result1["plots"]).exists()
    assert Path(result1["reports"]).exists()