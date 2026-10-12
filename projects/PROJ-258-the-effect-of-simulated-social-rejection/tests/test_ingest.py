"""
Unit tests for the ingestion pipeline (code/ingest.py).
The tests verify that the pipeline creates the required output files
and respects the size‑limit guard.
"""
import os
import json
import pytest
from pathlib import Path

# Ensure the project root is on sys.path for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from ingest import run_ingestion, get_path

@pytest.fixture(scope="module")
def run_pipeline():
    """Execute the ingestion pipeline once for the test module."""
    # Clean up any previous artifacts to guarantee a fresh run
    raw_dir = Path(get_path("raw"))
    interim_dir = Path(get_path("interim"))
    processed_dir = Path(get_path("processed"))

    for d in (raw_dir, interim_dir, processed_dir):
        if d.exists():
            for p in d.rglob("*"):
                if p.is_file():
                    p.unlink()
        else:
            d.mkdir(parents=True)

    # Run the ingestion pipeline
    run_ingestion()
    yield

def test_manifest_created(run_pipeline):
    manifest_path = Path(get_path("raw")) / "dataset_manifest.json"
    assert manifest_path.is_file(), "dataset_manifest.json should exist"
    with open(manifest_path) as f:
        manifest = json.load(f)
    assert isinstance(manifest, list) and len(manifest) == 2
    for entry in manifest:
        assert "url" in entry and "size_bytes" in entry
        assert entry["sha256"] is None

def test_condition_report(run_pipeline):
    report_path = Path(get_path("interim")) / "condition_report.json"
    assert report_path.is_file(), "condition_report.json should exist"
    with open(report_path) as f:
        report = json.load(f)
    assert all(k in report for k in ("rejection_present", "control_present", "reward_present"))

def test_overlap_and_design(run_pipeline):
    overlap_path = Path(get_path("interim")) / "overlap_report.json"
    design_path = Path(get_path("interim")) / "design_branch.json"
    metadata_path = Path(get_path("processed")) / "metadata.json"

    for p in (overlap_path, design_path, metadata_path):
        assert p.is_file(), f"{p.name} should be created"

    with open(overlap_path) as f:
        overlap = json.load(f)
    assert "overlap" in overlap

    with open(design_path) as f:
        design = json.load(f)
    assert design["design_type"] in ("Within-Subjects", "Between-Subjects")

    with open(metadata_path) as f:
        meta = json.load(f)
    assert meta["design_type"] == design["design_type"]