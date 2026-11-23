import os
import sys
import shutil
import subprocess
from pathlib import Path

# Import the module under test
from ingestion.fetch_real import main as fetch_real_main

def test_missing_url_exits_nonzero(tmp_path, monkeypatch):
    """
    Ensure that when plan.md does not contain a URL, the script aborts
    with a non‑zero exit status and logs an appropriate error.
    """
    # Set up a temporary project structure mirroring the real one
    project_root = tmp_path / "proj"
    project_root.mkdir()
    # Create required directories
    (project_root / "data" / "raw").mkdir(parents=True)
    (project_root / "data" / "logs").mkdir(parents=True)

    # Write a minimal plan.md without a URL
    plan_path = project_root / "plan.md"
    plan_path.write_text("# Test Plan\\n\\nNo URL here.\\n")

    # Monkeypatch get_project_root to point to our temporary root
    from utils import config as config_mod
    monkeypatch.setattr(config_mod, "get_project_root", lambda: project_root)

    # Run the script via subprocess to capture exit code
    script_path = Path(__file__).parent.parent / "code" / "ingestion" / "fetch_real.py"
    result = subprocess.run([sys.executable, str(script_path)],
                            cwd=project_root,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True)

    assert result.returncode != 0, "Script should exit with non‑zero status when URL is missing"
    assert "No real dataset URL – FR-001 cannot be satisfied" in result.stderr

def test_successful_download(tmp_path, monkeypatch):
    """
    Verify that a valid URL results in a CSV file written to data/raw/dataset.csv.
    Uses a small public CSV file to keep the test fast.
    """
    project_root = tmp_path / "proj"
    project_root.mkdir()
    raw_dir = project_root / "data" / "raw"
    raw_dir.mkdir(parents=True)

    # Use a tiny CSV hosted on GitHub (public domain)
    csv_url = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv"

    # Write plan.md with the URL
    plan_path = project_root / "plan.md"
    plan_path.write_text(f"# Plan\\n\\nDataset URL: {csv_url}\\n")

    # Monkeypatch get_project_root
    from utils import config as config_mod
    monkeypatch.setattr(config_mod, "get_project_root", lambda: project_root)

    # Execute the fetch_real script
    script_path = Path(__file__).parent.parent / "code" / "ingestion" / "fetch_real.py"
    result = subprocess.run([sys.executable, str(script_path)],
                            cwd=project_root,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True)

    # The script should succeed (exit code 0)
    assert result.returncode == 0, f"Script failed with stderr: {result.stderr}"

    # Verify that the CSV file exists and is non‑empty
    downloaded_csv = raw_dir / "dataset.csv"
    assert downloaded_csv.exists(), "Downloaded CSV file not found"
    assert downloaded_csv.stat().st_size > 0, "Downloaded CSV file is empty"

    # Ensure the URL line was not duplicated in plan.md
    plan_contents = plan_path.read_text()
    assert plan_contents.count(csv_url) == 1, "Dataset URL should appear exactly once in plan.md"