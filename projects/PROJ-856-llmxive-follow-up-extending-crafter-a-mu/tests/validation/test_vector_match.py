import json
import tempfile
from pathlib import Path

from src.validation.vector_match import compare_vectors, _write_validation_record

def test_compare_vectors_exact_match(tmp_path: Path):
    # Create matching ground‑truth and prediction files.
    gt = {"vector": [1, 2, 3]}
    pred = {"vector": [1, 2, 3]}

    gt_path = tmp_path / "ground_truth_0.json"
    pred_path = tmp_path / "prediction_0.json"

    gt_path.write_text(json.dumps(gt), encoding="utf-8")
    pred_path.write_text(json.dumps(pred), encoding="utf-8")

    assert compare_vectors(gt_path, pred_path) is True

def test_compare_vectors_mismatch(tmp_path: Path):
    gt = {"vector": [1, 2, 3]}
    pred = {"vector": [3, 2, 1]}

    gt_path = tmp_path / "ground_truth_1.json"
    pred_path = tmp_path / "prediction_1.json"

    gt_path.write_text(json.dumps(gt), encoding="utf-8")
    pred_path.write_text(json.dumps(pred), encoding="utf-8")

    assert compare_vectors(gt_path, pred_path) is False

def test_write_validation_record(tmp_path: Path):
    out_file = tmp_path / "semantic_validation.jsonl"
    _write_validation_record(out_file, "fig_1", vector_match=True, semantic_pass=False)

    # Verify that the JSON line was written correctly.
    line = out_file.read_text(encoding="utf-8").strip()
    record = json.loads(line)
    assert record["figure_id"] == "fig_1"
    assert record["vector_match"] is True
    assert record["semantic_pass"] is False
