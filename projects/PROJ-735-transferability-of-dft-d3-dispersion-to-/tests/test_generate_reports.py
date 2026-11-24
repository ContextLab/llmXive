import os
from pathlib import Path

import pytest

# Import the main function from the module we just modified
from generate_reports import main as generate_reports_main

@pytest.fixture(autouse=True)
def clean_environment(tmp_path, monkeypatch):
    """
    Ensure that each test runs in a fresh temporary directory that mimics the
    project layout. The fixture copies the minimal required data files
    (the synthetic benchmark zip) into the temporary directory and adjusts
    the working directory accordingly.
    """
    # Switch to the temporary directory for the duration of the test
    old_cwd = Path.cwd()
    os.chdir(tmp_path)

    # Recreate the expected directory structure
    (tmp_path / "data" / "derived").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)

    # Copy the synthetic dataset zip from the real project into the temp location
    real_zip = Path(__file__).resolve().parents[2] / "data" / "IL-Benchmark-local.zip"
    assert real_zip.is_file(), "Synthetic benchmark zip not found in the repository"
    (tmp_path / "data" / "IL-Benchmark-local.zip").write_bytes(real_zip.read_bytes())

    # Ensure there is no pre‑existing scaling factor file so the code will generate a default one
    scaling_path = tmp_path / "data" / "derived" / "scaling_factor.txt"
    if scaling_path.exists():
        scaling_path.unlink()

    yield  # run the test

    # Return to original cwd after test
    os.chdir(old_cwd)


def test_generate_reports_creates_benchmark_and_scaling(tmp_path):
    """
    Run generate_reports.main() in an isolated temporary project layout.
    Verify that:
    1. `data/derived/scaling_factor.txt` is created with a numeric value.
    2. `docs/benchmark_report.md` is created.
    3. The benchmark report contains the "Calibration Procedure" section
       and the scaling factor line matches the value written to the file.
    """
    # Run the report generation
    generate_reports_main()

    # Paths we expect to exist
    scaling_file = Path("data/derived/scaling_factor.txt")
    benchmark_md = Path("docs/benchmark_report.md")

    assert scaling_file.is_file(), "Scaling factor file was not created"
    assert benchmark_md.is_file(), "Benchmark report markdown was not created"

    # Parse the scaling factor from the file
    content = scaling_file.read_text()
    # Expected format: "optimal_s: <float>"
    try:
        scaling_value = float(content.split(":")[1].strip())
    except Exception as e:
        pytest.fail(f"Failed to parse scaling factor from file: {e}")

    # Verify that the benchmark report includes the calibration section
    md_text = benchmark_md.read_text()
    assert "## 4. Calibration Procedure" in md_text, "Calibration Procedure section missing"

    # Verify that the scaling factor shown in the markdown matches the file value
    expected_line = f"- **Scaling factor (s)**: `{scaling_value:.4f}`"
    assert expected_line in md_text, f"Scaling factor line not found or does not match: expected {expected_line}"