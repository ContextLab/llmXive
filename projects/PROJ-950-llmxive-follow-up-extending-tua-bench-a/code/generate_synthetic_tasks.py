"""Generate a balanced subset of TUA‑Bench tasks.

This script streams the official ``tua_bench`` dataset, selects a user‑specified
number of complex and routine tasks, and writes the selected entries to a JSON
file.  Each output entry contains the fields required by the verification step:
``task_id``, ``description``, ``validation_script`` and ``task_type``.
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict

from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download TUA‑Bench and create a balanced synthetic task set."
    )
    parser.add_argument(
        "--num_complex",
        type=int,
        required=True,
        help="Number of complex (multi‑step) tasks to include.",
    )
    parser.add_argument(
        "--num_routine",
        type=int,
        required=True,
        help="Number of routine (single‑command) tasks to include.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path (relative to project root) where the JSON subset will be saved.",
    )
    return parser.parse_args()

def stream_tasks() -> List[Dict]:
    """Stream the entire TUA‑Bench dataset and return a list of raw task dicts."""
    log.info("Streaming the official TUA‑Bench dataset...")
    # The dataset name is ``tua_bench``; streaming ensures we never load the whole
    # collection into memory.
    ds = load_dataset("tua_bench", streaming=True)
    # The dataset contains a single split named ``train`` (the official benchmark).
    # We iterate over it and collect the raw dictionaries.
    tasks = []
    for item in ds["train"]:
        tasks.append(dict(item))
    log.info(f"Total tasks streamed: {len(tasks)}")
    return tasks

def select_balanced_subset(
    tasks: List[Dict],
    num_complex: int,
    num_routine: int,
) -> List[Dict]:
    """Select the first *num_complex* complex and *num_routine* routine tasks.

    The TUA‑Bench schema defines ``task_type`` as either ``complex`` or ``routine``.
    If a task does not contain the expected field, it is ignored.
    """
    complex_tasks = [
        t for t in tasks if t.get("task_type", "").lower() == "complex"
    ]
    routine_tasks = [
        t for t in tasks if t.get("task_type", "").lower() == "routine"
    ]

    if len(complex_tasks) < num_complex:
        raise ValueError(
            f"Requested {num_complex} complex tasks but only {len(complex_tasks)} are available."
        )
    if len(routine_tasks) < num_routine:
        raise ValueError(
            f"Requested {num_routine} routine tasks but only {len(routine_tasks)} are available."
        )

    selected = complex_tasks[:num_complex] + routine_tasks[:num_routine]
    log.info(
        f"Selected {len(complex_tasks[:num_complex])} complex and "
        f"{len(routine_tasks[:num_routine])} routine tasks (total {len(selected)})."
    )
    # Ensure each entry has the required keys; otherwise raise an informative error.
    required_keys = {"task_id", "description", "validation_script", "task_type"}
    for idx, entry in enumerate(selected):
        missing = required_keys - entry.keys()
        if missing:
            raise KeyError(
                f"Task at index {idx} is missing required fields: {missing}"
            )
    return selected

def write_json(data: List[Dict], output_path: str) -> None:
    """Write *data* to *output_path* as pretty‑printed JSON."""
    # Resolve the path via the toolkit helper to guarantee the directory exists.
    out_path: Path = paths.path(*output_path.split("/"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    log.info(f"Writing {len(data)} tasks to {out_path}")
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info("Write complete.")

def main() -> None:
    args = parse_args()
    all_tasks = stream_tasks()
    subset = select_balanced_subset(
        all_tasks,
        num_complex=args.num_complex,
        num_routine=args.num_routine,
    )
    write_json(subset, args.output)

if __name__ == "__main__":
    main()
