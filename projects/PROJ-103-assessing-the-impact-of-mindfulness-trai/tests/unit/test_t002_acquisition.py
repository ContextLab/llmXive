import pytest
from pathlib import Path
from code.src.datasets.download_datasets import download_dataset, compute_file_checksum
from code.datasets.verify_design import verify_dataset_design
from llmxive_toolkit import paths

def test_checksum_logic(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello world")
    cs = compute_file_checksum(f)
    assert len(cs) == 64

def test_download_sample(tmp_path):
    # Mock paths for the test
    with pytest.MonkeyPatch.context() as mp:
        # Redirect paths.data to tmp_path
        mp.setattr("llmxive_toolkit.paths.data", lambda *args: tmp_path / "/".join(args))
        # We use a known valid OpenNeuro ID
        res = download_dataset("ds000226", sample_only=True)
        assert "dataset_id" in res
        assert (tmp_path / "raw/ds000226/dataset_description.json").exists()

def test_verify_design_failure(tmp_path):
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("llmxive_toolkit.paths.data", lambda *args: tmp_path / "/".join(args))
        
        # Create a fake dataset description without 'mindfulness'
        ds_id = "ds_fake"
        raw_dir = tmp_path / f"raw/{ds_id}"
        raw_dir.mkdir(parents=True)
        with open(raw_dir / "dataset_description.json", "w") as f:
            f.write(json.dumps({"Name": "Random Brain Study"}))
        
        import json
        valid, reason = verify_dataset_design(ds_id)
        assert valid is False
        assert reason == "design_missing"
