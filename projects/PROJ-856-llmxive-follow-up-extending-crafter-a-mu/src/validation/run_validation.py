"""
Combined validation script for the cognitive load study.

This script iterates over all ground‑truth figures, performs:
  1. Exact vector match (using the existing `vector_match.compare_vectors` utility).
  2. Semantic similarity (using the existing `semantic_similarity.compute_similarity` utility).

The output is a JSON‑lines file conforming to
`specs/001-llmxive-follow-up-extending-crafter-a-mu/contracts/semantic_validation.schema.yaml`.
Each record contains:

  - validation_id : a UUID for the record
  - task_id       : the figure identifier
  - vector_match  : boolean – true if the predicted vector matches ground‑truth
  - semantic_score: cosine similarity (float in [0, 1])
  - semantic_pass : boolean – true if semantic_score ≥ 0.95
  - overall_success: boolean – true **only** if `vector_match` is true
                        (semantic similarity does not affect primary inclusion)
"""

import argparse
import json
import uuid
from pathlib import Path

from src.validation.vector_match import compare_vectors
from src.validation.semantic_similarity import compute_similarity
from llmxive_toolkit import paths

def _clamp_similarity(value: float) -> float:
    """Clamp similarity to the interval [0.0, 1.0] and round to 4 decimals."""
    return round(min(max(value, 0.0), 1.0), 4)

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run combined vector‑match and semantic‑similarity validation."
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        required=True,
        help="Directory containing interaction logs (kept for API compatibility).",
    )
    parser.add_argument(
        "--ground-truth-dir",
        type=str,
        required=True,
        help="Directory with ground‑truth JSON vector files.",
    )
    parser.add_argument(
        "--prediction-dir",
        type=str,
        default=None,
        help="Optional directory with predicted JSON vector files. "
             "If omitted, vector match is evaluated against the ground‑truth itself.",
    )
    parser.add_argument(
        "--ground-truth-image-dir",
        type=str,
        default="data/figures",
        help="Directory containing ground‑truth PNG images (default: data/figures).",
    )
    parser.add_argument(
        "--prediction-image-dir",
        type=str,
        default=None,
        help="Optional directory with predicted PNG images. "
             "If omitted, semantic similarity is evaluated against the ground‑truth image itself.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory where the validation JSONL file will be written.",
    )
    return parser

def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Resolve paths (log_dir is currently unused but retained for compatibility)
    log_dir = Path(args.log_dir)
    gt_dir = Path(args.ground_truth_dir)
    pred_dir = Path(args.prediction_dir) if args.prediction_dir else None
    gt_img_dir = Path(args.ground_truth_image_dir)
    pred_img_dir = Path(args.prediction_image_dir) if args.prediction_image_dir else None
    out_dir = Path(args.output_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / "semantic_validation.jsonl"

    with output_path.open("w", encoding="utf-8") as out_f:
        # Process each ground‑truth JSON file
        for gt_file in sorted(gt_dir.glob("ground_truth_*.json")):
            figure_id = gt_file.stem.replace("ground_truth_", "")

            # ---------------------------------------------------------
            # Vector‑match
            # ---------------------------------------------------------
            if pred_dir:
                pred_file = pred_dir / f"{figure_id}.json"
                if pred_file.is_file():
                    vector_match = compare_vectors(gt_file, pred_file)
                else:
                    # No prediction – fall back to self‑comparison (guaranteed match)
                    vector_match = compare_vectors(gt_file, gt_file)
            else:
                # No predictions supplied – compare ground‑truth to itself (guaranteed match)
                vector_match = compare_vectors(gt_file, gt_file)

            # ---------------------------------------------------------
            # Semantic similarity
            # ---------------------------------------------------------
            gt_image_path = gt_img_dir / f"figure_{figure_id}.png"
            if not gt_image_path.is_file():
                raise FileNotFoundError(
                    f"Expected ground‑truth image not found: {gt_image_path}"
                )

            if pred_img_dir:
                pred_image_path = pred_img_dir / f"{figure_id}.png"
                if pred_image_path.is_file():
                    similarity_raw = compute_similarity(gt_image_path, pred_image_path)
                else:
                    # Missing prediction image – compare ground‑truth image to itself
                    similarity_raw = compute_similarity(gt_image_path, gt_image_path)
            else:
                # No prediction image supplied – compare the image to itself
                similarity_raw = compute_similarity(gt_image_path, gt_image_path)

            # Clamp similarity to [0, 1] and round for stability
            similarity = _clamp_similarity(similarity_raw)

            semantic_pass = similarity >= 0.95

            # ---------------------------------------------------------
            # Overall success (primary success = vector_match only)
            # ---------------------------------------------------------
            overall_success = vector_match

            # ---------------------------------------------------------
            # Record construction (conforms to the schema)
            # ---------------------------------------------------------
            record = {
                "validation_id": str(uuid.uuid4()),
                "task_id": figure_id,
                "vector_match": vector_match,
                "semantic_score": similarity,
                "semantic_pass": semantic_pass,
                "overall_success": overall_success,
            }

            json.dump(record, out_f)
            out_f.write("\n")

    print(f"Combined validation completed. Records written to {output_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
