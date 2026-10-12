"""
Classification script for T004.

This script reads the raw code‑block CSV produced by T003,
runs the CodeBERT ONNX classifier on each block, filters out
low‑confidence predictions (threshold 0.8), computes static
complexity metrics with radon, and writes the final
``tagged_blocks.csv`` together with a log of excluded blocks.

The script is deliberately self‑contained: it does **not** fall back
to synthetic data.  If any required resource (e.g. the ONNX model)
cannot be obtained, an exception is raised and the pipeline aborts,
satisfying the “fail loudly” requirement.
"""

import csv
import pathlib
import sys
import logging

from radon.complexity import cc_visit
from radon.visitors import ComplexityVisitor
from llmxive_toolkit import paths, get_logger

# Import the classifier we defined in ``code/utils/models.py``
from utils.models import CodeBERTClassifier

LOG_PATH = paths.logs("classifier_exclusions.log")
OUTPUT_PATH = paths.processed("tagged_blocks.csv")

# Ensure output directories exist
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)

CONFIDENCE_THRESHOLD = 0.8


def _load_code_blocks(csv_path: pathlib.Path) -> list[dict]:
    """
    Load the raw ``code_blocks.csv`` produced by T003.

    The CSV is expected to contain at least the following columns:
        block_id, repo_name, file_path, start_line, end_line,
        language, content, introduction_commit, introduction_timestamp
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Required file not found: {csv_path}")

    rows = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _compute_complexity_metrics(code: str) -> tuple[int, int]:
    """
    Compute cyclomatic complexity and a very simple nesting depth.

    *Cyclomatic complexity* is obtained from radon’s ``cc_visit``.
    *Nesting depth* is approximated by the maximum indentation level
    (number of leading spaces divided by 4) across all lines.
    """
    try:
        blocks = cc_visit(code)
        # Sum complexities of all functions/classes in the snippet
        complexity = sum(b.complexity for b in blocks)
    except Exception:
        complexity = 0

    # Simple nesting depth: count leading spaces
    nesting = 0
    for line in code.splitlines():
        stripped = line.lstrip()
        if stripped:
            indent = (len(line) - len(stripped)) // 4
            nesting = max(nesting, indent)
    return complexity, nesting


def _write_exclusions(exclusions: list[dict], path: pathlib.Path) -> None:
    """
    Write the exclusion log.  The format follows the specification:
    ``block_id,reason,confidence`` (CSV with a header).
    """
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["block_id", "reason", "confidence"])
        for exc in exclusions:
            writer.writerow([exc["block_id"], exc["reason"], f'{exc["confidence"]:.4f}'])


def _write_tagged_blocks(tagged: list[dict], path: pathlib.Path) -> None:
    """
    Write the final ``tagged_blocks.csv`` conforming to the contract.
    """
    fieldnames = [
        "block_id",
        "repo_id",
        "file_path",
        "start_line",
        "end_line",
        "origin_label",
        "confidence",
        "complexity",
        "nesting_depth",
        "loc",
        "introduction_commit",
        "introduction_timestamp",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in tagged:
            writer.writerow(row)


def main() -> None:
    """
    Entry point executed by the quick‑start command.
    """
    logger.info("Starting CodeBERT classification pipeline")

    # Initialise the classifier – this will download the ONNX model if needed.
    classifier = CodeBERTClassifier()

    raw_csv = paths.raw("code_blocks.csv")
    blocks = _load_code_blocks(raw_csv)

    if not blocks:
        logger.error("No code blocks found in the input CSV")
        sys.exit(1)

    tagged_rows = []
    exclusions = []

    for block in blocks:
        block_id = block.get("block_id")
        code = block.get("content", "")

        # Run the classifier
        pred = classifier.predict(code)
        label = pred["label"]
        confidence = pred["confidence"]

        if confidence < CONFIDENCE_THRESHOLD:
            exclusions.append(
                {
                    "block_id": block_id,
                    "reason": "low_confidence",
                    "confidence": confidence,
                }
            )
            continue

        # Compute static metrics
        complexity, nesting = _compute_complexity_metrics(code)
        loc = len(code.splitlines())

        # Build the output row respecting the contract
        out_row = {
            "block_id": block_id,
            "repo_id": block.get("repo_name", ""),
            "file_path": block.get("file_path", ""),
            "start_line": int(block.get("start_line", 0)),
            "end_line": int(block.get("end_line", 0)),
            "origin_label": label,
            "confidence": f"{confidence:.4f}",
            "complexity": complexity,
            "nesting_depth": nesting,
            "loc": loc,
            "introduction_commit": block.get("introduction_commit", ""),
            "introduction_timestamp": block.get("introduction_timestamp", ""),
        }
        tagged_rows.append(out_row)

    # Write results
    _write_tagged_blocks(tagged_rows, OUTPUT_PATH)
    _write_exclusions(exclusions, LOG_PATH)

    logger.info(
        f"Classification completed – {len(tagged_rows)} blocks kept, {len(exclusions)} excluded"
    )


if __name__ == "__main__":
    main()
