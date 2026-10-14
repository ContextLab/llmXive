import subprocess
import json
from pathlib import Path

def test_download_and_validate():
    """
    End‑to‑end test for T002:
    1. Run the download script (creates the Moral Machine CSV).
    2. Run the validation script.
    3. Assert that the validation report exists and reports PASS.
    """
    # Step 1 – download the dataset
    download_rc = subprocess.run(
        ["python", "code/download_moral_machine.py"],
        capture_output=True,
        text=True,
    )
    assert download_rc.returncode == 0, f"Download failed: {download_rc.stderr}"

    # Step 2 – validate sources
    validate_rc = subprocess.run(
        ["python", "code/validate_sources.py"],
        capture_output=True,
        text=True,
    )
    assert validate_rc.returncode == 0, f"Validation failed: {validate_rc.stderr}"

    # Step 3 – check the JSON report
    report_path = Path("results/logs/validation_report.json")
    assert report_path.is_file(), "validation_report.json was not created"

    report = json.loads(report_path.read_text())
    assert report.get("overall_status") == "PASS", "Validation report did not indicate PASS"