"""Tests for the generation pipeline (Task T006).

The test suite checks that:
* the three model directories exist under ``data/generated/``,
* every successful generation file records a ``generation_time_s`` ≤ 60 s,
* the per‑model success‑rate in ``generation_success_rates.csv`` is ≥ 0.90,
* a SHA‑256 checksum entry exists in ``data/metadata.yaml`` for each generated
  text and JSON file.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from code.generation import MODEL_IDS, load_commit_pairs, main

@pytest.fixture(scope="module")
def run_pipeline(tmp_path_factory):
    """Execute the generation stage via the module's ``main`` function."""
    # Ensure a fresh temporary data root for isolation.
    tmp_root = tmp_path_factory.mktemp("proj")
    # Monkey‑patch the llmxive_toolkit paths to point inside the temp dir.
    from llmxive_toolkit import paths as toolkit_paths

    original_root = toolkit_paths.root
    try:
        toolkit_paths.root = tmp_root
        # Re‑run the generation pipeline.
        exit_code = main()
        assert exit_code == 0, "Generation pipeline exited with non‑zero status"
        yield tmp_root
    finally:
        toolkit_paths.root = original_root

def test_model_directories_exist(run_pipeline):
    root = run_pipeline
    for model_id in MODEL_IDS:
        dir_path = Path(root, "data", "generated", model_id)
        assert dir_path.is_dir(), f"Missing directory for model {model_id}"

def test_generation_times_and_success_rates(run_pipeline):
    root = run_pipeline
    # Load the success‑rate CSV.
    csv_path = Path(root, "data", "generated", "generation_success_rates.csv")
    assert csv_path.is_file(), "generation_success_rates.csv missing"
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    # Verify each model's success rate.
    for row in rows:
        model_id = row["model_id"]
        rate = float(row["success_rate"])
        assert rate >= 0.90, f"Success rate for {model_id} below 0.90 ({rate})"

    # Check each generated JSON for a generation_time_s ≤ 60 s.
    for model_id in MODEL_IDS:
        json_files = Path(root, "data", "generated", model_id).glob("*.json")
        for jf in json_files:
            with jf.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("status") == "success":
                gen_time = data.get("generation_time_s")
                assert (
                    gen_time is not None and gen_time <= 60
                ), f"Generation time too large in {jf}"

def test_checksums_present(run_pipeline):
    root = run_pipeline
    meta_path = Path(root, "data", "metadata.yaml")
    assert meta_path.is_file(), "metadata.yaml missing"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    # Every generated .txt and .json file must have a checksum entry.
    for model_id in MODEL_IDS:
        gen_dir = Path(root, "data", "generated", model_id)
        for file_path in gen_dir.glob("*"):
            rel = str(file_path.relative_to(root))
            assert rel in meta, f"Missing checksum entry for {rel}"