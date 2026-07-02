"""
Unit test for the manifest generation logic in ``code.utils``.
The test does **not** perform a real download (that would be too large for CI);
instead it exercises the verification helper on artificial file lists.
"""

import pathlib
import tempfile

from code.utils import _verify_dataset, DatasetManifest, write_manifest

def test_verify_dataset_ready():
    # Simulate presence of at least one EEG and one questionnaire file
    eeg = [pathlib.Path("/tmp/sub-01/eeg.edf")]
    quest = [pathlib.Path("/tmp/sub-01/questionnaire.tsv")]
    assert _verify_dataset(eeg, quest) == "ready"

def test_verify_dataset_skipped():
    # No questionnaire files
    eeg = [pathlib.Path("/tmp/sub-01/eeg.edf")]
    quest = []
    assert _verify_dataset(eeg, quest) == "skipped"

def test_write_manifest_creates_file():
    manifest = DatasetManifest(
        dataset_id="ds_test",
        verification_status="ready",
        eeg_files=["data/raw/ds_test/sub-01/eeg.edf"],
        questionnaire_files=["data/raw/ds_test/sub-01/questionnaire.tsv"],
    )
    with tempfile.TemporaryDirectory() as td:
        out_path = pathlib.Path(td) / "manifest.json"
        write_manifest(manifest, out_path)
        assert out_path.is_file()
        # Verify JSON content can be loaded
        import json
        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["dataset_id"] == "ds_test"
        assert data["verification_status"] == "ready"
        assert isinstance(data["eeg_files"], list)
        assert isinstance(data["questionnaire_files"], list)