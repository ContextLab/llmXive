import json
from pathlib import Path

from code.data import load_gsm8k, load_bigbench_lite, download_all

def test_load_gsm8k_counts():
    train = load_gsm8k(split="train")
    test = load_gsm8k(split="test")
    assert len(train) == 2000, f"expected 2000 train examples, got {len(train)}"
    assert len(test) == 500, f"expected 500 test examples, got {len(test)}"

def test_load_bigbench_lite_count():
    bb = load_bigbench_lite()
    assert len(bb) == 500, f"expected 500 bigbench examples, got {len(bb)}"

def test_download_all_creates_manifest(tmp_path, monkeypatch):
    # Use a temporary raw directory to avoid polluting the project data folder
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    monkeypatch.setattr("llmxive_toolkit.paths.data", lambda *parts: raw_dir)
    manifest_path = download_all()
    assert manifest_path.is_file()
    lines = manifest_path.read_text().strip().splitlines()
    # Expect three entries (train, test, bigbench)
    assert len(lines) == 3
    # Verify each line contains the expected filename
    expected_files = {"gsm8k_train.jsonl", "gsm8k_test.jsonl", "bigbench_logical_deduction.jsonl"}
    for line in lines:
        filename = line.split("\t")[0]
        assert filename in expected_files