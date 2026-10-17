"""
Vector match utility for the cognitive‑load comparison study.

This module provides a function to compare a ground‑truth layout vector
(stored as JSON) with a predicted vector (also JSON) and reports a
boolean indicating an exact match.  It also offers a small CLI that can be
used to batch‑process a directory of ground‑truth and prediction files,
writing a ``SemanticValidation`` record for each trial.

The ``SemanticValidation`` record contains two fields required by the
downstream pipeline:

- ``vector_match``: result of the exact vector comparison.
- ``semantic_pass``: placeholder ``false`` – the semantic similarity check
  is performed by ``semantic_similarity.py`` and will set this field
  appropriately when the combined validation script runs.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def _load_json(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its content."""
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def compare_vectors(gt_path: Path, pred_path: Path) -> bool:
    """
    Compare two layout vectors for exact equality.

    Parameters
    ----------
    gt_path: Path
        Path to the ground‑truth JSON file.  Expected format::
            {"vector": [int, int, ...]}

    pred_path: Path
        Path to the predicted JSON file with the same structure.

    Returns
    -------
    bool
        ``True`` if the ``vector`` entries are identical (order and values);
        ``False`` otherwise.
    """
    gt_data = _load_json(gt_path)
    pred_data = _load_json(pred_path)

    gt_vec = gt_data.get("vector")
    pred_vec = pred_data.get("vector")

    if not isinstance(gt_vec, list) or not isinstance(pred_vec, list):
        raise ValueError("Both JSON files must contain a ``vector`` list.")

    match = gt_vec == pred_vec
    log.debug(
        "Vector compare %s vs %s – result: %s",
        gt_path.name,
        pred_path.name,
        match,
    )
    return match

def _write_validation_record(
    output_path: Path,
    figure_id: str,
    vector_match: bool,
    semantic_pass: bool = False,
) -> None:
    """
    Append a single ``SemanticValidation`` JSON line.

    The schema (contracts/semantic_validation.schema.yaml) expects at least
    the fields ``figure_id``, ``vector_match`` and ``semantic_pass``.
    """
    record = {
        "figure_id": figure_id,
        "vector_match": vector_match,
        "semantic_pass": semantic_pass,
    }
    with output_path.open("a", encoding="utf-8") as f:
        json.dump(record, f)
        f.write("\n")
    log.debug("Wrote validation record for %s to %s", figure_id, output_path)

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Exact vector‑match validation for figure editing trials."
    )
    parser.add_argument(
        "--ground-truth-dir",
        type=str,
        required=True,
        help="Directory containing ground‑truth JSON vector files.",
    )
    parser.add_argument(
        "--prediction-dir",
        type=str,
        required=True,
        help="Directory containing predicted JSON vector files.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/validation",
        help="Directory where the ``semantic_validation.jsonl`` file will be written.",
    )
    return parser

def main() -> None:
    args = _build_arg_parser().parse_args()

    gt_dir = Path(args.ground_truth_dir)
    pred_dir = Path(args.prediction_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    output_file = out_dir / "semantic_validation.jsonl"

    # Process each ground‑truth file that has a matching prediction.
    for gt_file in gt_dir.glob("*.json"):
        figure_id = gt_file.stem
        pred_file = pred_dir / f"{figure_id}.json"
        if not pred_file.is_file():
            log.warning("No prediction found for %s – skipping.", figure_id)
            continue

        try:
            vm = compare_vectors(gt_file, pred_file)
        except Exception as exc:
            log.error("Failed to compare vectors for %s: %s", figure_id, exc)
            vm = False

        # ``semantic_pass`` is set to ``False`` here; the semantic similarity
        # utility will produce its own record and the combined runner will
        # merge the two fields.
        _write_validation_record(output_file, figure_id, vm, semantic_pass=False)

    log.info("Vector‑match validation completed. Records written to %s", output_file)

if __name__ == "__main__":
    main()
