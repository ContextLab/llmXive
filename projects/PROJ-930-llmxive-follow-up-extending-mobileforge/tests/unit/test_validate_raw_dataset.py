import subprocess
import sys
from pathlib import Path

def test_validate_raw_dataset():
    """Run the validation script and ensure it exits cleanly.

    The script should create a JSON summary file in `outputs/`.
    """
    script_path = Path("code/data/raw/validate_extraction_dataset.py")
    assert script_path.is_file(), "Validation script missing"

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )
    # The script must exit with code 0.
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # The output JSON must exist and contain a PASS status.
    out_path = Path("outputs/validation_raw_dataset.json")
    assert out_path.is_file(), "Output summary not created"

    import json

    data = json.loads(out_path.read_text())
    assert data.get("status") == "PASS", "Validation did not pass"
    assert isinstance(data.get("validated_records"), int), "Record count missing"