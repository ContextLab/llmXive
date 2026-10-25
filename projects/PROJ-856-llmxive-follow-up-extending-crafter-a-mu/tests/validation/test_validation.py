"""
Unit tests for the dual‑success validation utilities (T005).

The tests cover three scenarios:
  a) Exact vector match & semantic pass → overall_success = True
  b) Vector mismatch but semantic pass → overall_success = False (primary success depends only on vector match)
  c) Both checks fail → overall_success = False

The test creates a minimal temporary dataset (ground‑truth vectors,
optional prediction vectors, and PNG images) and invokes the
`src.validation.run_validation` CLI.  The resulting JSONL file is
inspected to ensure the fields match the contract and that the
`overall_success` logic follows the primary‑only rule.
"""

import json
import sys
from pathlib import Path

import pytest
from PIL import Image

# Import the entry‑point so we can invoke it with a fabricated argv.
from src.validation.run_validation import main as run_validation_main

@pytest.fixture
def setup_dataset(tmp_path):
    """
    Create a tiny synthetic dataset under the project root:

    data/
      figures/
        figure_0.png
        figure_1.png
        figure_2.png
    gt/
      ground_truth_0.json
      ground_truth_1.json
      ground_truth_2.json
    pred/
      1.json   (mismatched vector)
      2.json   (mismatched vector)
    pred_imgs/
      2.png    (different image → low similarity)
    """
    # Directories
    figures_dir = Path("data/figures")
    gt_dir = tmp_path / "gt"
    pred_dir = tmp_path / "pred"
    pred_img_dir = tmp_path / "pred_imgs"
    out_dir = tmp_path / "out"

    for d in (figures_dir, gt_dir, pred_dir, pred_img_dir, out_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Helper to write a JSON vector file
    def write_vector(dir_path: Path, idx: int, vector):
        (dir_path / f"ground_truth_{idx}.json").write_text(
            json.dumps({"vector": vector}, indent=2), encoding="utf-8"
        )

    # Helper to write a PNG image (solid colour)
    def write_image(path: Path, colour):
        img = Image.new("RGB", (32, 32), colour)
        img.save(path, format="PNG")

    # --- Ground‑truth ---
    for i in range(3):
        write_vector(gt_dir, i, [i, 32, 32])
        write_image(figures_dir / f"figure_{i}.png", (255, 0, 0))  # red image for all

    # --- Predictions for vector mismatch (scenario b & c) ---
    # vector mismatch for figure 1 and 2
    (pred_dir / "1.json").write_text(
        json.dumps({"vector": [999, 32, 32]}, indent=2), encoding="utf-8"
    )
    (pred_dir / "2.json").write_text(
        json.dumps({"vector": [999, 32, 32]}, indent=2), encoding="utf-8"
    )

    # --- Prediction image for figure 2 (different colour → low similarity) ---
    write_image(pred_img_dir / "2.png", (0, 0, 255))  # blue image

    return {
        "gt_dir": gt_dir,
        "pred_dir": pred_dir,
        "pred_img_dir": pred_img_dir,
        "out_dir": out_dir,
        "log_dir": tmp_path,  # dummy, not used
    }

def run_validation_cli(args):
    """
    Helper that temporarily replaces sys.argv, runs the CLI, and restores it.
    """
    old_argv = sys.argv
    sys.argv = ["run_validation"] + args
    try:
        exit_code = run_validation_main()
    finally:
        sys.argv = old_argv
    return exit_code

def test_overall_success_logic(setup_dataset):
    ds = setup_dataset

    # Execute the validation script
    exit_code = run_validation_cli([
        "--log-dir", str(ds["log_dir"]),
        "--ground-truth-dir", str(ds["gt_dir"]),
        "--prediction-dir", str(ds["pred_dir"]),
        "--ground-truth-image-dir", "data/figures",
        "--prediction-image-dir", str(ds["pred_img_dir"]),
        "--output-dir", str(ds["out_dir"]),
    ])
    assert exit_code == 0

    # Load the produced JSONL file
    out_file = ds["out_dir"] / "semantic_validation.jsonl"
    assert out_file.is_file()
    records = [json.loads(line) for line in out_file.read_text(encoding="utf-8").splitlines()]

    # Index records by task_id for easy lookup
    rec_by_id = {r["task_id"]: r for r in records}

    # --- Scenario a: exact match (figure 0) ---
    rec0 = rec_by_id["0"]
    assert rec0["vector_match"] is True
    assert rec0["semantic_pass"] is True
    assert rec0["overall_success"] is True
    assert 0.99 <= rec0["semantic_score"] <= 1.0  # identical images → similarity ≈ 1

    # --- Scenario b: vector mismatch, semantic pass (figure 1) ---
    rec1 = rec_by_id["1"]
    assert rec1["vector_match"] is False
    assert rec1["semantic_pass"] is True
    # Primary success depends only on exact vector match
    assert rec1["overall_success"] is False
    assert 0.99 <= rec1["semantic_score"] <= 1.0  # same image compared → high similarity

    # --- Scenario c: both checks fail (figure 2) ---
    rec2 = rec_by_id["2"]
    assert rec2["vector_match"] is False
    # The blue image vs red ground‑truth should give a low similarity (<0.95)
    assert rec2["semantic_pass"] is False
    assert rec2["overall_success"] is False
    assert rec2["semantic_score"] < 0.95

    # Verify required schema fields are present
    for r in records:
        for field in ["validation_id", "task_id", "vector_match",
                      "semantic_score", "semantic_pass", "overall_success"]:
            assert field in r