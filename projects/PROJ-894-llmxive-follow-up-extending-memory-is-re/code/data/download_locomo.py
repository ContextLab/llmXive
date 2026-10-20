"""
Strict LoCoMo benchmark downloader (Task T001).

Downloads the real LoCoMo benchmark from the verified HuggingFace source
(``snap-research/locomo``) via ``datasets.load_dataset(..., streaming=True)``
and writes ``data/raw/locomo.csv`` with columns:
``task_id, question, context, ground_truth``.

This loader is STRICT: there is no synthetic/mock fallback. If the real
fetch or schema validation fails, it raises and the run fails loudly.
It does NOT write to ``state/`` (platform-owned); the SHA-256 checksum is
written to ``data/raw/locomo.sha256`` instead.
"""
import csv
import hashlib
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List

# Make sibling modules importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from llmxive_toolkit import paths

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DATASET_ID = "snap-research/locomo"
REQUIRED_COLUMNS = ["task_id", "question", "context", "ground_truth"]
# Candidate splits, tried in order (the published LoCoMo card exposes a
# small number of splits; trying each is a split-name resolution, NOT a
# data fallback — all splits contain the same real benchmark data).
CANDIDATE_SPLITS = ("test", "validation", "train")
# Cap on QA rows materialized from the stream (RAM / runtime budget).
# The full stream is iterated; rows are capped at MAX_ROWS.
MAX_ROWS = 500

OUTPUT_CSV = paths.data("raw", "locomo.csv")
OUTPUT_SHA = paths.data("raw", "locomo.sha256")


def _find_qa_list(sample: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Locate the list of QA dicts inside a LoCoMo sample."""
    for key in ("qa", "question_answer", "questions", "qas"):
        value = sample.get(key)
        if (
            isinstance(value, list)
            and value
            and isinstance(value[0], dict)
            and "question" in value[0]
        ):
            return value
    return []


def _find_conversation(sample: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Locate the conversation turn list inside a LoCoMo sample."""
    for key in ("conversation", "dialogue", "dialog", "history"):
        value = sample.get(key)
        if (
            isinstance(value, list)
            and value
            and isinstance(value[0], dict)
        ):
            return value
    return []


def _context_from_turns(turns: List[Dict[str, Any]]) -> str:
    """Render the conversation turns as a single context string."""
    lines = []
    for turn in turns:
        speaker = turn.get("speaker", turn.get("speaker_id", ""))
        text = turn.get("text", turn.get("utterance", ""))
        if not text:
            continue
        lines.append(f"{speaker}: {text}" if speaker else str(text))
    return "\n".join(lines)


def _ground_truth(qa: Dict[str, Any]) -> str:
    """Extract the ground-truth answer from a QA dict."""
    for key in ("answer", "gt", "gold", "correct_answer"):
        value = qa.get(key)
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, list) and value:
            return str(value[0])
    return ""


def _extract_rows(stream: Iterator[Dict[str, Any]], max_rows: int) -> List[Dict[str, str]]:
    """Stream the real dataset and materialize up to ``max_rows`` task rows."""
    rows: List[Dict[str, str]] = []
    for sample_idx, sample in enumerate(stream):
        if len(rows) >= max_rows:
            break
        qa_list = _find_qa_list(sample)
        turns = _find_conversation(sample)
        if not qa_list:
            # Real sample without a recognizable QA block: fail loudly
            # rather than fabricating rows.
            raise ValueError(
                "Dataset schema mismatch: sample "
                f"{sample_idx} has no QA list (keys: {sorted(sample.keys())})"
            )
        context = _context_from_turns(turns)
        sample_id = sample.get("id", sample.get("sample_id", sample_idx))
        for qa_idx, qa in enumerate(qa_list):
            if len(rows) >= max_rows:
                break
            question = qa.get("question", "")
            if not isinstance(question, str) or not question.strip():
                continue
            rows.append(
                {
                    "task_id": f"{sample_id}_{qa_idx}",
                    "question": question,
                    "context": context,
                    "ground_truth": _ground_truth(qa),
                }
            )
    if not rows:
        raise ValueError("Dataset schema mismatch: no task rows extracted")
    return rows


def load_locomo_strict(max_rows: int = MAX_ROWS) -> List[Dict[str, str]]:
    """
    Load the REAL LoCoMo benchmark via streaming HF datasets.

    Raises on any failure (network, missing dataset, schema mismatch).
    Never falls back to synthetic or mock data.
    """
    from datasets import load_dataset  # imported lazily; failure propagates

    last_error: Exception | None = None
    for split in CANDIDATE_SPLITS:
        try:
            stream = load_dataset(DATASET_ID, split=split, streaming=True)
            logger.info("Streaming real dataset %s (split=%s)", DATASET_ID, split)
            return _extract_rows(iter(stream), max_rows)
        except ValueError as exc:
            # Unknown split name — try the next candidate split.
            logger.warning("Split %r unavailable for %s: %s", split, DATASET_ID, exc)
            last_error = exc
    raise RuntimeError(
        f"Failed to load real dataset {DATASET_ID} "
        f"(tried splits {CANDIDATE_SPLITS}): {last_error}"
    )


def validate_schema(rows: List[Dict[str, str]]) -> None:
    """Verify that every expected column is present and non-trivial."""
    if not rows:
        raise ValueError("Dataset schema mismatch: no rows")
    actual = set(rows[0].keys())
    missing = set(REQUIRED_COLUMNS) - actual
    if missing:
        raise ValueError(
            f"Dataset schema mismatch: missing columns {sorted(missing)}"
        )
    for row in rows:
        if not row.get("question"):
            raise ValueError("Dataset schema mismatch: empty question field")
    logger.info("Schema validation passed: columns %s", sorted(actual))


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(rows: List[Dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Wrote %d rows to %s", len(rows), output_path)


def main() -> Path:
    logger.info("Downloading LoCoMo benchmark (strict, streaming, no fallback)")
    rows = load_locomo_strict()
    validate_schema(rows)
    write_csv(rows, OUTPUT_CSV)

    digest = sha256_of(OUTPUT_CSV)
    OUTPUT_SHA.write_text(digest + "\n", encoding="utf-8")
    logger.info("SHA-256 of %s: %s", OUTPUT_CSV, digest)
    logger.info(
        "Wrote %d real task rows (cap=%d). Checksum: %s",
        len(rows), MAX_ROWS, OUTPUT_SHA,
    )
    return OUTPUT_CSV


if __name__ == "__main__":
    main()
