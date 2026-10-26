"""Tests for the deterministic gold‑standard annotation (Task T004)."""

import json
from pathlib import Path

import pytest

from code.gold_annotation import (
    OUTPUT_JSON,
    run_annotation_pipeline,
    write_output,
    CSV_PATH,
)
from code.seeds import SEED

@pytest.fixture(scope="module")
def generated_annotations(tmp_path_factory):
    """Run the annotation pipeline once and return the parsed JSON."""
    # Ensure the output path is under the temporary directory to avoid
    # interfering with a real run‑pipeline execution.
    output_path = Path(tmp_path_factory.getbasetemp()) / "annotations.json"
    # Monkey‑patch the constant used by the module
    original_path = OUTPUT_JSON
    try:
        # Replace the module‑level constant temporarily
        import importlib

        mod = importlib.import_module("code.gold_annotation")
        mod.OUTPUT_JSON = output_path

        records = run_annotation_pipeline()
        write_output(records)

        with output_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    finally:
        # Restore original constant to avoid side effects
        mod.OUTPUT_JSON = original_path

def test_annotation_file_structure(generated_annotations):
    """Validate the shape and contents of the JSON file."""
    assert isinstance(generated_annotations, list), "Root element must be a list"
    assert len(generated_annotations) == 50, "Exactly 50 samples must be annotated"

    for rec in generated_annotations:
        # Required top‑level keys
        for key in ("sample_id", "intent_entities", "kappa", "fallback_used"):
            assert key in rec, f"Missing key {key} in record"

        # Types and value ranges
        assert isinstance(rec["sample_id"], str)
        assert isinstance(rec["intent_entities"], list)
        assert isinstance(rec["kappa"], float)
        assert 0.0 <= rec["kappa"] <= 1.0
        assert isinstance(rec["fallback_used"], bool)

    # Consistency of the fallback flag with the κ threshold
    kappas = [rec["kappa"] for rec in generated_annotations]
    # All records share the same κ because it is computed globally
    assert all(k == kappas[0] for k in kappas), "All records must have identical κ"
    kappa_val = kappas[0]
    for rec in generated_annotations:
        if rec["fallback_used"]:
            assert kappa_val < 0.6
            assert rec["intent_entities"] == []
        else:
            assert kappa_val >= 0.6
            # When not falling back the merged list should be non‑empty
            # unless both annotators found nothing (unlikely but allowed)
            assert isinstance(rec["intent_entities"], list)

def test_deterministic_sampling():
    """Ensure that sampling is deterministic given the pinned seed."""
    from code.gold_annotation import _load_commit_pairs, _sample_commit_pairs

    df = _load_commit_pairs(CSV_PATH)
    first_sample = _sample_commit_pairs(df, 5, SEED)
    second_sample = _sample_commit_pairs(df, 5, SEED)

    # The two calls must produce identical DataFrames
    pd.testing.assert_frame_equal(first_sample, second_sample)