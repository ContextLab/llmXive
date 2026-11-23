"""
Integration test for the download‑and‑preprocess pipeline (US1).

The test verifies that the pipeline can:
1. Download the OpenNeuro dataset ``ds000248`` (real download).
2. Produce a pre‑processed epochs file.
3. Generate the behavioural measures CSV.
4. Exit with a non‑zero status when required variables are missing
   (simulated by temporarily removing a required channel file).

The test is deliberately lightweight: it runs the pipeline with the
``--output`` argument pointing to a temporary directory under ``/tmp``.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

@pytest.mark.integration
def test_full_pipeline_success():
    """Run the pipeline on the real dataset and check for expected outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir)
        # Execute the script; it will download the data into data/raw/
        result = subprocess.run(
            [
                sys.executable,
                "code/01_download_preprocess.py",
                "--dataset",
                "ds000248",
                "--output",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )
        # The script should exit with code 0
        assert result.returncode == 0, f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

        # Expected artefacts
        epochs_file = output_path / "epochs.fif"
        behavioural_file = output_path / "behavioral_measures.csv"

        assert epochs_file.is_file(), "Epochs file not created"
        assert behavioural_file.is_file(), "Behavioural measures CSV not created"

@pytest.mark.integration
def test_missing_behavioural_measures_triggers_error():
    """
    Run the pipeline but deliberately remove the behavioural CSV after
    epoching to provoke the validation error added in T016.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir)

        # First run to generate all files
        subprocess.run(
            [
                sys.executable,
                "code/01_download_preprocess.py",
                "--dataset",
                "ds000248",
                "--output",
                str(output_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        # Remove the behavioural measures file to simulate missing data
        behavioural_file = output_path / "behavioral_measures.csv"
        if behavioural_file.is_file():
            behavioural_file.unlink()

        # Re‑run the validation step only – we invoke the script with a
        # flag that skips download/pre‑processing.  The script does not
        # expose such a flag, so we call the Python module directly:
        from importlib import reload
        import code._01_download_preprocess as dp_mod  # type: ignore

        # Reload to ensure a fresh logger
        reload(dp_mod)

        # The validation function should now cause sys.exit(1)
        with pytest.raises(SystemExit) as excinfo:
            dp_mod._validate_requirements(
                output_dir=output_path,
                cfg=dp_mod.load_config(),
                dataset_id="ds000248",
                logger=dp_mod.setup_logger(),
            )
        assert excinfo.value.code == 1