"""Unit tests for the BIDS structure setup (T006)."""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from importlib import import_module

bids = import_module("00_setup_bids")


def test_generate_dataset_description():
    desc = bids.generate_dataset_description("ds000248")
    assert desc["BIDSVersion"].startswith("1.")
    assert "ds000248" in desc["Name"]
    assert desc["SourceDatasets"][0]["URL"].endswith("ds000248")


def test_create_bids_structure(tmp_path):
    root = tmp_path / "ds000248"
    # pre-register two subjects
    (root).mkdir(parents=True)
    (root / "participants.tsv").write_text(
        "participant_id\nsub-01\nsub-02\n"
    )
    manifest = bids.create_bids_structure(str(root))
    assert (root / "code").is_dir()
    assert (root / "derivatives").is_dir()
    assert (root / ".bidsignore").exists()
    assert (root / "sub-01" / "eeg").is_dir()
    assert (root / "sub-02" / "eeg").is_dir()
    assert manifest["n_subjects"] == 2


def test_generate_participants_and_subjects_explicit(tmp_path):
    root = tmp_path / "dsX"
    bids.generate_participants_and_subjects(
        str(root), subject_ids=["sub-01", "sub-02"]
    )
    text = (root / "participants.tsv").read_text()
    assert text == "participant_id\nsub-01\nsub-02\n"
    assert (root / "participants.json").exists()