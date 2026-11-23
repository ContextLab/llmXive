"""Deterministic dataset downloader for the MMLU-STEM benchmark.

Task T011 (US1): Download the STEM subset of the HuggingFaceH4/mmlu
dataset (a verified, deterministic benchmark with ground-truth answers)
and parse it into `code/data/processed/mmlu_stem.jsonl`.

The loader fetches REAL data from the Hugging Face Hub. It has no
synthetic fallback: if the download fails, it raises so the failure is
visible (fail loudly, never silently).
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterator, List, Optional

# Ensure sibling modules (utils.checksum, etc.) are importable when this
# script is executed directly as `python code/data/download.py`.
_CODE_DIR = Path(__file__).resolve().parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from datasets import load_dataset  # real HF datasets library

from llmxive_toolkit import paths, get_logger

from utils.checksum import save_checksum_for_file

log = get_logger(__name__)

DATASET_ID = "HuggingFaceH4/mmlu"
SPLIT = "test"

# Standard MMLU STEM subject categories (deterministic, verifiable
# ground-truth answers). These cover mathematics, physics, chemistry,
# biology, computer science, and engineering.
STEM_SUBJECTS = frozenset(
    {
        "abstract_algebra",
        "anatomy",
        "astronomy",
        "college_biology",
        "college_chemistry",
        "college_computer_science",
        "college_mathematics",
        "college_physics",
        "computer_security",
        "conceptual_physics",
        "electrical_engineering",
        "elementary_mathematics",
        "formal_logic",
        "high_school_biology",
        "high_school_chemistry",
        "high_school_computer_science",
        "high_school_mathematics",
        "high_school_physics",
        "high_school_statistics",
        "machine_learning",
    }
)

DEFAULT_OUTPUT = paths.code("data", "processed", "mmlu_stem.jsonl")


def _format_prompt(question: str, choices: List[str]) -> str:
    """Render an MMLU item as a multiple-choice prompt string."""
    letters = ["A", "B", "C", "D", "E"]
    lines = [question.strip(), ""]
    for letter, choice in zip(letters, choices):
        lines.append(f"{letter}. {choice}")
    lines.append("")
    lines.append("Answer with the letter of the correct option.")
    return "\n".join(lines)


def _to_record(item: Dict, index: int) -> Dict:
    """Convert a raw MMLU dataset row into the project's prompt schema."""
    choices = list(item["choices"])
    answer_idx = int(item["answer"])
    answer_letter = chr(ord("A") + answer_idx)
    return {
        "prompt_id": f"mmlu-stem-{item.get('subject', 'unknown')}-{index:06d}",
        "prompt": _format_prompt(item["question"], choices),
        "choices": choices,
        "answer_index": answer_idx,
        "answer": answer_letter,
        "answer_text": choices[answer_idx],
        "subject": item.get("subject", "unknown"),
        "domain": "deterministic",
        "source": DATASET_ID,
    }


def iter_mmlu_stem(max_items: Optional[int] = None) -> Iterator[Dict]:
    """Stream real MMLU test rows restricted to STEM subjects.

    Raises on any download error (no synthetic fallback).
    """
    dataset = load_dataset(DATASET_ID, "all", split=SPLIT)
    count = 0
    for index, item in enumerate(dataset):
        if item.get("subject") not in STEM_SUBJECTS:
            continue
        yield _to_record(item, index)
        count += 1
        if max_items is not None and count >= max_items:
            return


def download_mmlu_stem(
    output_path: Path = DEFAULT_OUTPUT, max_items: Optional[int] = None
) -> Path:
    """Download the MMLU STEM subset and write it as JSONL.

    Args:
        output_path: Destination JSONL file.
        max_items: Optional cap on the number of STEM items written.

    Returns:
        Path to the written JSONL file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    n_written = 0
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as fh:
        for record in iter_mmlu_stem(max_items=max_items):
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            n_written += 1
    tmp_path.replace(output_path)

    if n_written == 0:
        raise RuntimeError(
            f"No STEM items found in {DATASET_ID} ({SPLIT} split); "
            "refusing to write an empty dataset."
        )

    checksum_path = save_checksum_for_file(output_path)
    log.info(
        "Wrote %d MMLU-STEM items to %s (checksum: %s)",
        n_written,
        output_path,
        checksum_path,
    )
    return output_path


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download the MMLU STEM subset into JSONL."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output JSONL path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=None,
        help="Optional cap on number of STEM items (default: all)",
    )
    args = parser.parse_args(argv)

    download_mmlu_stem(output_path=args.output, max_items=args.max_items)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())