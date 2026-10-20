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

# -------------------------------------------------------------------------
# Dataset loading helpers
# -------------------------------------------------------------------------

def _load_with_datasets() -> List[Dict]:
    """
    Attempt to load the TUA‑Bench dataset using the ``datasets`` library.
    This function is isolated so that any ImportError (e.g. missing
    ``pyarrow``) can be caught and a fallback can be used.
    """
    try:
        from datasets import load_dataset  # type: ignore
    except Exception as exc:
        raise ImportError("datasets library could not be imported") from exc

    log.info("Streaming the official TUA‑Bench dataset via ``datasets``...")
    ds = load_dataset("tua_bench", streaming=True)
    tasks: List[Dict] = []
    for item in ds["train"]:
        tasks.append(dict(item))
    log.info(f"Total tasks streamed: {len(tasks)}")
    return tasks

def _load_with_hf_hub() -> List[Dict]:
    """
    Fallback loader that downloads the raw split file from the HuggingFace hub
    and parses it without requiring ``datasets`` or ``pyarrow``.
    """
    from huggingface_hub import hf_hub_download  # type: ignore
    import pandas as pd  # pandas is part of the base environment

    # The repository typically contains a ``train`` split; try common filenames.
    possible_filenames = ["train.jsonl", "train.parquet", "train.csv"]
    file_path = None
    for fname in possible_filenames:
        try:
            file_path = hf_hub_download(repo_id="tua_bench", filename=fname)
            log.info(f"Downloaded '{fname}' from the hub.")
            break
        except Exception:
            continue
    if file_path is None:
        raise FileNotFoundError(
            "Unable to locate a supported train split file in the 'tua_bench' repo."
        )

    tasks: List[Dict] = []
    if file_path.endswith(".jsonl"):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    tasks.append(json.loads(line))
    elif file_path.endswith(".parquet"):
        df = pd.read_parquet(file_path)
        tasks = df.to_dict(orient="records")
    elif file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
        tasks = df.to_dict(orient="records")
    else:
        raise ValueError(f"Unsupported file extension for fallback: {file_path}")

    log.info(f"Loaded {len(tasks)} tasks via fallback method.")
    return tasks

def stream_tasks() -> List[Dict]:
    """
    Stream the entire TUA‑Bench dataset and return a list of raw task dicts.
    Tries the primary ``datasets`` method first; if that fails (e.g. due to
    missing ``pyarrow``), falls back to a lightweight download via
    ``huggingface_hub``.
    """
    try:
        return _load_with_datasets()
    except Exception as e:
        log.warning(
            f"Primary loader failed ({e}); attempting fallback loader..."
        )
        return _load_with_hf_hub()

# -------------------------------------------------------------------------
# Sub‑selection utilities
# -------------------------------------------------------------------------

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

# -------------------------------------------------------------------------
# Output helper
# -------------------------------------------------------------------------

def write_json(data: List[Dict], output_path: str) -> None:
    """Write *data* to *output_path* as pretty‑printed JSON."""
    # Resolve the path via the toolkit helper to guarantee the directory exists.
    out_path: Path = paths.path(*output_path.split("/"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    log.info(f"Writing {len(data)} tasks to {out_path}")
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info("Write complete.")

# -------------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------------

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