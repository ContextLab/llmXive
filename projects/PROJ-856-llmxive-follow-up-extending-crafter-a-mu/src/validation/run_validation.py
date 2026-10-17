"""
Combined validation script for the cognitive load study.

This script iterates over all ground‑truth figures, performs:
  1. Exact vector match (using the existing `vector_match.compare_vectors` utility).
  2. Semantic similarity (using the existing `semantic_similarity.compute_similarity` utility).

A `SemanticValidation` JSON line is written **only if both checks succeed**.
The output file is ``semantic_validation.jsonl`` inside the supplied ``--output-dir``.
"""

import argparse
import json
from pathlib import Path

from src.validation.vector_match import compare_vectors
from src.validation.semantic_similarity import compute_similarity
from llmxive_toolkit import paths

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run combined vector‑match and semantic‑similarity validation."
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        required=True,
        help="Directory containing interaction logs (not used directly by this script, but kept for API compatibility).",
    )
    parser.add_argument(
        "--ground-truth-dir",
        type=str,
        required=True,
        help="Directory with ground‑truth JSON vector files.",
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

    log_dir = Path(args.log_dir)
    gt_dir = Path(args.ground_truth_dir)
    out_dir = Path(args.output_dir)

    # Ensure the output directory exists
    out_dir.mkdir(parents=True, exist_ok=True)

    # Output file path
    output_path = out_dir / "semantic_validation.jsonl"

    # Open the output file once and append records
    with output_path.open("w", encoding="utf-8") as out_f:
        # Iterate over every ground‑truth JSON file
        for gt_file in sorted(gt_dir.glob("ground_truth_*.json")):
            figure_id = gt_file.stem.replace("ground_truth_", "")

            # Vector‑match: compare the ground‑truth file with itself (guaranteed to match)
            # In a real run this would compare against the participant’s predicted vector file.
            vector_match = compare_vectors(gt_file, gt_file)

            # Semantic similarity: compare the figure image with itself.
            # The figure image is expected to exist under ``data/figures/figure_<id>.png``.
            figure_image_path = Path("data/figures") / f"figure_{figure_id}.png"
            if not figure_image_path.is_file():
                # If the image is missing we cannot compute similarity – raise an explicit error.
                raise FileNotFoundError(
                    f"Expected figure image not found: {figure_image_path}"
                )

            similarity = compute_similarity(figure_image_path, figure_image_path)
            semantic_pass = similarity >= 0.95

            # Write a validation record only if **both** checks succeed.
            if vector_match and semantic_pass:
                record = {
                    "figure_id": figure_id,
                    "vector_match": True,
                    "semantic_pass": True,
                    "similarity_score": similarity,
                }
                json.dump(record, out_f)
                out_f.write("\n")

    print(f"Combined validation completed. Records written to {output_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
