"""
Contract test for the data validation script (T012).
The test creates a minimal BIDS‑like directory structure in a temporary
location, runs the validation script, and checks that the manifest file is
created and contains the expected entries.
"""
import json
import os
from pathlib import Path

import pytest

# Import the module under test
from code.preprocessing.data_validation import main as validation_main, build_manifest


@pytest.fixture
def temp_dataset(tmp_path):
    """
    Create a tiny ds003694‑style dataset with one participant and one session.
    """
    # Set up configuration environment so that utils.config picks up this root
    os.environ["PROJ_ROOT"] = str(tmp_path)

    data_root = tmp_path / "data" / "raw"
    participant = "sub-01"
    session = "ses-01"

    func_dir = data_root / participant / session / "func"
    beh_dir = data_root / participant / session / "beh"
    func_dir.mkdir(parents=True)
    beh_dir.mkdir(parents=True)

    # Create dummy NIfTI file (empty is sufficient for existence check)
    func_path = func_dir / f"{participant}_{session}_task-social_bold.nii.gz"
    func_path.touch()

    # Create behavioral TSV with required columns
    beh_path = beh_dir / f"{participant}_{session}_task-social_beh.tsv"
    with beh_path.open("w") as f:
        f.write("private_belief\tsocial_feedback\tchoice\n")
        f.write("0.5\t0.7\t1\n")

    # Minimal dataset_description.json
    (data_root / "dataset_description.json").write_text("{}")

    return tmp_path


def test_validation_success(temp_dataset):
    """
    The validation should succeed and produce a manifest containing the participant.
    """
    # Run the validation script
    validation_main()

    manifest_path = Path(os.getenv("PROJ_ROOT")) / "state" / "dataset_manifest.json"
    assert manifest_path.is_file(), "Manifest file was not created"

    manifest = json.loads(manifest_path.read_text())
    assert "participants" in manifest
    participants = manifest["participants"]
    assert any(p["id"] == "sub-01" for p in participants)

    # Verify that the session entry contains both func and beh paths
    sub_entry = next(p for p in participants if p["id"] == "sub-01")
    sess_entry = sub_entry["sessions"][0]
    assert sess_entry["func"].endswith("sub-01_ses-01_task-social_bold.nii.gz")
    assert sess_entry["beh"].endswith("sub-01_ses-01_task-social_beh.tsv")


def test_validation_missing_file(tmp_path):
    """
    If a required file is missing, the script should raise FileNotFoundError.
    """
    os.environ["PROJ_ROOT"] = str(tmp_path)
    data_root = tmp_path / "data" / "raw"
    participant = "sub-01"
    session = "ses-01"
    func_dir = data_root / participant / session / "func"
    func_dir.mkdir(parents=True)
    # Intentionally omit the functional image

    # Create behavioral TSV (still valid)
    beh_dir = data_root / participant / session / "beh"
    beh_dir.mkdir(parents=True)
    beh_path = beh_dir / f"{participant}_{session}_task-social_beh.tsv"
    with beh_path.open("w") as f:
        f.write("private_belief\tsocial_feedback\tchoice\n")
        f.write("0.5\t0.7\t1\n")

    (data_root / "dataset_description.json").write_text("{}")

    # The validation should raise because the functional NIfTI is missing
    with pytest.raises(FileNotFoundError) as excinfo:
        # Directly call the helper that builds the manifest to get the error
        build_manifest(data_root)
    assert "Missing functional image" in str(excinfo.value)