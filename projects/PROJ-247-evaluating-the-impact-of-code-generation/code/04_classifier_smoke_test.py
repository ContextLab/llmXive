"""
Smoke‑test for the CodeBERT classifier (Task T004).

The script loads the first three code blocks from
``data/raw/code_blocks.csv`` (produced by T003), runs the classifier,
and prints the predicted label together with the confidence score.
It exits with status 0 on success.
"""

import csv
import sys
from pathlib import Path

from utils.models import CodeBERTClassifier
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _load_first_n_blocks(csv_path: Path, n: int = 3):
    """Yield the first ``n`` rows from the CSV as dictionaries."""
    if not csv_path.exists():
        log.error(f"Missing input file: {csv_path}")
        sys.exit(1)

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= n:
                break
            yield row

def main():
    classifier = CodeBERTClassifier()
    raw_csv = paths.raw("code_blocks.csv")
    for block in _load_first_n_blocks(raw_csv):
        block_id = block.get("block_id", "<unknown>")
        code = block.get("content", "")
        pred = classifier.predict(code)
        label = pred["label"]
        confidence = pred["confidence"]
        print(f"{block_id}: {label} (confidence={confidence:.4f})")

if __name__ == "__main__":
    main()
