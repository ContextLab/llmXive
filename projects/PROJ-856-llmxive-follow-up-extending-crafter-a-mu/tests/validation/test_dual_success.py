"""
Test suite for dual-success validation (vector match + semantic similarity).

This test creates three scenarios:
1. Exact vector match only (semantic similarity may also pass).
2. Semantic similarity pass only (vector mismatch).
3. Total failure (both vector mismatch and semantic similarity below threshold).

For each scenario it runs the combined validation script
`src.validation.run_validation` and validates the resulting JSON‑Lines
records against the official schema
`specs/001-llmxive-follow-up-extending-crafter-a-mu/contracts/semantic_validation.schema.yaml`.

The test uses temporary directories and synthetic images that are
deterministic and small, ensuring the run completes quickly on CI.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import jsonschema
import pytest

# Path to the schema file relative to the project root
SCHEMA_PATH = Path(
    "specs/001-llmxive-follow-up-extending-crafter-a-mu/contracts/semantic_validation.schema.yaml"
)

@pytest.fixture(scope="module")
def schema():
    """Load the JSON‑Schema for semantic validation records."""
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def _create_image(path: Path, color: tuple[int, int, int] = (0, 0, 0)):
    """Create a 64×64 PNG image of a solid color."""
    from PIL import Image

    img = Image.new("RGB", (64, 64), color)
    img.save(path, format="PNG")

def _run_validation(
    log_dir: Path,
    gt_json_dir: Path,
    pred_json_dir: Path,
    gt_img_dir: Path,
    pred_img_dir: Path,
    output_dir: Path,
) -> Path:
    """
    Execute the validation script as a subprocess and return the path
    to the generated ``semantic_validation.jsonl`` file.
    """
    cmd = [
        sys.executable,
        "-m",
        "src.validation.run_validation",
        "--log-dir",
        str(log_dir),
        "--ground-truth-dir",
        str(gt_json_dir),
        "--prediction-dir",
        str(pred_json_dir),
        "--ground-truth-image-dir",
        str(gt_img_dir),
        "--prediction-image-dir",
        str(pred_img_dir),
        "--output-dir",
        str(output_dir),
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Validation script failed: {result.stderr}"
    output_file = output_dir / "semantic_validation.jsonl"
    assert output_file.is_file(), "Expected output file not created"
    return output_file

def test_dual_success_validation(schema):
    """
    End‑to‑end test covering the three required scenarios.
    """
    with tempfile.TemporaryDirectory() as tmp_root:
        root = Path(tmp_root)

        # Directories required by the validation script
        log_dir = root / "logs"
        gt_json_dir = root / "gt_json"
        pred_json_dir = root / "pred_json"
        gt_img_dir = root / "gt_img"
        pred_img_dir = root / "pred_img"
        output_dir = root / "out"

        for d in (
            log_dir,
            gt_json_dir,
            pred_json_dir,
            gt_img_dir,
            pred_img_dir,
            output_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)

        # -----------------------------------------------------------------
        # Common ground‑truth data (vector and image)
        # -----------------------------------------------------------------
        gt_vector = {"vector": [0, 32, 32]}
        gt_vector_path = gt_json_dir / "ground_truth_0.json"
        gt_vector_path.write_text(json.dumps(gt_vector, indent=2), encoding="utf-8")

        gt_image_path = gt_img_dir / "figure_0.png"
        _create_image(gt_image_path, color=(255, 0, 0))  # solid red

        # -----------------------------------------------------------------
        # Scenario 1: Exact vector match (primary success)
        # -----------------------------------------------------------------
        pred_vector_match = {"vector": [0, 32, 32]}
        pred_vector_match_path = pred_json_dir / "0.json"
        pred_vector_match_path.write_text(
            json.dumps(pred_vector_match, indent=2), encoding="utf-8"
        )
        # Use the same image to guarantee semantic similarity = 1.0
        pred_image_match_path = pred_img_dir / "0.png"
        _create_image(pred_image_match_path, color=(255, 0, 0))

        # -----------------------------------------------------------------
        # Scenario 2: Semantic similarity pass only (vector mismatch)
        # -----------------------------------------------------------------
        pred_vector_semantic = {"vector": [99, 99, 99]}
        pred_vector_semantic_path = pred_json_dir / "1.json"
        pred_vector_semantic_path.write_text(
            json.dumps(pred_vector_semantic, indent=2), encoding="utf-8"
        )
        # Identical image ensures similarity = 1.0 → semantic_pass = true
        pred_image_semantic_path = pred_img_dir / "1.png"
        _create_image(pred_image_semantic_path, color=(255, 0, 0))

        # Ground‑truth files for scenario 2 (reuse same GT vector/image but with different IDs)
        gt_vector_path_2 = gt_json_dir / "ground_truth_1.json"
        gt_vector_path_2.write_text(json.dumps(gt_vector, indent=2), encoding="utf-8")
        gt_image_path_2 = gt_img_dir / "figure_1.png"
        _create_image(gt_image_path_2, color=(255, 0, 0))

        # -----------------------------------------------------------------
        # Scenario 3: Total failure (both checks fail)
        # -----------------------------------------------------------------
        pred_vector_fail = {"vector": [42, 42, 42]}
        pred_vector_fail_path = pred_json_dir / "2.json"
        pred_vector_fail_path.write_text(
            json.dumps(pred_vector_fail, indent=2), encoding="utf-8"
        )
        # Create a markedly different image (blue) → low similarity
        pred_image_fail_path = pred_img_dir / "2.png"
        _create_image(pred_image_fail_path, color=(0, 0, 255))

        gt_vector_path_3 = gt_json_dir / "ground_truth_2.json"
        gt_vector_path_3.write_text(json.dumps(gt_vector, indent=2), encoding="utf-8")
        gt_image_path_3 = gt_img_dir / "figure_2.png"
        _create_image(gt_image_path_3, color=(255, 0, 0))

        # -----------------------------------------------------------------
        # Run validation across all three scenarios
        # -----------------------------------------------------------------
        output_file = _run_validation(
            log_dir=log_dir,
            gt_json_dir=gt_json_dir,
            pred_json_dir=pred_json_dir,
            gt_img_dir=gt_img_dir,
            pred_img_dir=pred_img_dir,
            output_dir=output_dir,
        )

        # -----------------------------------------------------------------
        # Load and validate each record
        # -----------------------------------------------------------------
        records = []
        with output_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))

        assert len(records) == 3, "Expected three validation records"

        # Helper to find a record by its task_id (derived from ground‑truth filename)
        def find_by_task_id(task_id: str):
            for rec in records:
                if rec["task_id"] == task_id:
                    return rec
            raise AssertionError(f"Record with task_id {task_id} not found")

        # Scenario 1 expectations
        rec1 = find_by_task_id("0")
        jsonschema.validate(instance=rec1, schema=schema)
        assert rec1["vector_match"] is True
        assert rec1["semantic_pass"] is True  # identical images → pass
        assert rec1["overall_success"] is True

        # Scenario 2 expectations
        rec2 = find_by_task_id("1")
        jsonschema.validate(instance=rec2, schema=schema)
        assert rec2["vector_match"] is False
        assert rec2["semantic_pass"] is True
        assert rec2["overall_success"] is False  # overall depends only on vector_match

        # Scenario 3 expectations
        rec3 = find_by_task_id("2")
        jsonschema.validate(instance=rec3, schema=schema)
        assert rec3["vector_match"] is False
        assert rec3["semantic_pass"] is False
        assert rec3["overall_success"] is False

# The test can be executed with `pytest -q tests/validation/test_dual_success.py`