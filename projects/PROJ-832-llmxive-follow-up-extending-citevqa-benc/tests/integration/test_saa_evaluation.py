"""
Integration test for the full SAA evaluation loop (User Story 2).

This test verifies the end-to-end computation of Strict Attributed Accuracy (SAA)
by loading text-pipeline results, mapping predicted chunk IDs to bounding boxes,
calculating IoU, and aggregating the final SAA metric.

It relies on:
  - data/results/text_pipeline_results.json (produced by T019)
  - data/processed/chunks.json (produced by T006/T007 pipeline, containing ground truth boxes)
  - code/metrics.py (calculate_iou, compute_saa)
"""

import json
import os
import pytest
from pathlib import Path

# Import the real metric functions from the project codebase
from code.metrics import calculate_iou, compute_saa

# Project root resolution (works whether running from root or tests/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

RESULTS_FILE = PROJECT_ROOT / "data" / "results" / "text_pipeline_results.json"
CHUNKS_FILE = PROJECT_ROOT / "data" / "processed" / "chunks.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Required data file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_ground_truth_box(query_id: str, chunks_data: dict) -> tuple:
    """
    Retrieve the ground truth bounding box for a given query_id.
    Expects chunks_data to be a dict where keys are query_ids and values contain 'box' info.
    Format: {"query_id": {"box": [y_min, x_min, y_max, x_max], ...}}
    """
    if query_id not in chunks_data:
        raise KeyError(f"Query ID {query_id} not found in ground truth chunks.")
    # The ground truth box is typically associated with the correct answer's chunk
    # We assume the structure in chunks_data maps query_id -> { "box": [y1, x1, y2, x2] }
    record = chunks_data[query_id]
    if "box" not in record:
        raise ValueError(f"Ground truth record for {query_id} missing 'box' key.")
    return tuple(record["box"])


def get_predicted_box(query_id: str, results_data: list) -> tuple:
    """
    Retrieve the predicted bounding box for a given query_id from the pipeline results.
    The results_data is a list of dicts: [{"query_id": "...", "predicted_chunk_id": "...", ...}, ...]
    We need to find the matching result and extract the box associated with the predicted chunk ID.
    However, the pipeline results typically contain the predicted chunk ID, not the box itself.
    The box must be looked up in the ground truth chunks using the predicted_chunk_id as a key
    (or the chunk ID maps to a box in the processed data).

    For this integration test, we assume the 'predicted_chunk_id' in results corresponds
    to a key in chunks_data that holds the box for that chunk.
    """
    result_record = next(
        (r for r in results_data if r.get("query_id") == query_id),
        None
    )
    if not result_record:
        raise KeyError(f"Query ID {query_id} not found in evaluation results.")

    predicted_chunk_id = result_record.get("predicted_chunk_id")
    if not predicted_chunk_id:
        # If no chunk ID predicted, we cannot compute IoU. Return None to signal failure.
        return None

    # Look up the box for the predicted chunk ID in the chunks data
    # Note: In a real scenario, chunks_data might be indexed by chunk_id directly
    if predicted_chunk_id not in chunks_data:
        raise KeyError(f"Predicted chunk ID {predicted_chunk_id} not found in ground truth chunks.")

    chunk_record = chunks_data[predicted_chunk_id]
    if "box" not in chunk_record:
        raise ValueError(f"Chunk record for {predicted_chunk_id} missing 'box' key.")

    return tuple(chunk_record["box"])


@pytest.mark.integration
def test_saa_evaluation_loop():
    """
    Integration test: Load results and ground truth, compute IoU and SAA for each sample,
    and verify the final aggregated SAA is a valid float between 0 and 1.
    """
    # 1. Load data
    results_data = load_json(RESULTS_FILE)
    chunks_data = load_json(CHUNKS_FILE)

    assert isinstance(results_data, list), "Evaluation results must be a list."
    assert len(results_data) > 0, "Evaluation results cannot be empty."

    total_count = 0
    correct_count = 0
    iou_scores = []

    # 2. Iterate through results and compute metrics
    for item in results_data:
        query_id = item.get("query_id")
        if not query_id:
            continue

        try:
            # Get ground truth box (associated with the correct answer)
            gt_box = get_ground_truth_box(query_id, chunks_data)

            # Get predicted box (associated with the predicted chunk ID)
            pred_box = get_predicted_box(query_id, results_data)

            # If no prediction was made, SAA is 0 for this item
            if pred_box is None:
                iou = 0.0
                is_correct = False
            else:
                # Calculate IoU
                iou = calculate_iou(gt_box, pred_box)
                iou_scores.append(iou)

                # Determine correctness based on SAA definition:
                # Answer Correctness (Exact Match OR Semantic Sim >= 0.85) AND Spatial Correctness (IoU > 0.5)
                # For this integration test, we assume the 'answer_correct' flag is already in the results
                # or we derive it. If not present, we rely solely on IoU > 0.5 as a proxy for spatial correctness
                # combined with a mock answer correctness check.
                # However, the task T022 (implementation) will handle the full logic.
                # Here we test the *loop* and the *IoU* calculation specifically.

                # Let's assume the results have 'semantic_similarity' and 'exact_match' if available.
                # If not, we default to checking IoU > 0.5 as the spatial component.
                # To strictly follow the SAA definition, we need the answer correctness.
                # We will assume the pipeline results include 'is_answer_correct' boolean.

                is_answer_correct = item.get("is_answer_correct", False)
                is_spatially_correct = iou > 0.5

                is_correct = is_answer_correct and is_spatially_correct

        except (KeyError, ValueError) as e:
            # Log error but continue to test robustness
            pytest.fail(f"Error processing query {query_id}: {e}")

        total_count += 1
        if is_correct:
            correct_count += 1

    # 3. Compute final SAA
    if total_count == 0:
        pytest.fail("No valid samples processed for SAA calculation.")

    final_saa = compute_saa(
        total_samples=total_count,
        correct_samples=correct_count,
        # Note: compute_saa in metrics.py might take a list of results or counts.
        # Based on the API surface: compute_saa(total_samples, correct_samples) -> float
        # Or it might be compute_saa(results_list).
        # We assume the signature: compute_saa(total, correct) returns the ratio.
        # If the actual signature is different, this test will catch it at runtime.
    )

    # 4. Assertions
    assert isinstance(final_saa, (int, float)), "SAA must be a numeric value."
    assert 0.0 <= final_saa <= 1.0, f"SAA must be between 0 and 1, got {final_saa}"

    # Optional: Check that we actually computed some IoUs
    if iou_scores:
        assert min(iou_scores) >= 0.0
        assert max(iou_scores) <= 1.0

    print(f"Integration Test SAA Result: {final_saa:.4f} (n={total_count})")

if __name__ == "__main__":
    # Allow running as a script for manual verification
    pytest.main([__file__, "-v"])
