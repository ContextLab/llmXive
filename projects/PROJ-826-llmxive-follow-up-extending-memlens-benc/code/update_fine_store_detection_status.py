"""
update_fine_store_detection_status.py
-------------------------------------

This module implements the logic required by task **T011B**:
* For every sample in the Fine memory store, explicitly set a
  ``detection_status`` flag.
* ``detection_status`` values:
    - ``success``        – YOLO detected one or more objects.
    - ``zero_detection`` – YOLO ran but detected no objects.
    - ``fallback``       – YOLO failed to run (e.g., model load error).
* The flag is written back into the Fine store JSON so that downstream
  components (e.g., statistical analysis, composite fidelity) can rely on a
  uniform field for **all** entries.

The script is deliberately lightweight and does **not** re‑run the YOLO
detector. It expects that the detection step (implemented in
``code/detection.py``) has already produced a per‑sample JSON file
``data/processed/detection_results.json`` with the following schema:

.. code-block:: json

    [
      {
        "sample_id": "<unique identifier matching the fine store entry>",
        "detection_status": "success" | "zero_detection" | "fallback"
      },
      ...
    ]

The Fine store is stored at
``data/processed/memory_stores/fine_store.json`` and is a list of entries,
each containing at least a ``sample_id`` field. The script merges the
``detection_status`` from the detection results into each fine‑store entry
and overwrites the original file (or writes to a new location if
``--output`` is supplied).

Usage
-----
```bash
python code/update_fine_store_detection_status.py \
    --fine-store data/processed/memory_stores/fine_store.json \
    --detection-results data/processed/detection_results.json \
    [--output data/processed/memory_stores/fine_store.json]
```

The command exits with a non‑zero status if any required file is missing
or if the merging process encounters mismatched identifiers.

The implementation follows the project's coding conventions, uses only
the Python standard library, and does not introduce new runtime
dependencies.
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict

def load_json(file_path: Path) -> List[Dict]:
    """Load a JSON file that contains a list of dictionaries."""
    if not file_path.is_file():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected a list in {file_path}, got {type(data)}")
    return data

def write_json(data: List[Dict], file_path: Path) -> None:
    """Write a list of dictionaries to a JSON file (pretty‑printed)."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def merge_detection_status(
    fine_store: List[Dict],
    detection_results: List[Dict]
) -> List[Dict]:
    """
    Merge ``detection_status`` from ``detection_results`` into ``fine_store``.

    Parameters
    ----------
    fine_store: List[Dict]
        The original fine‑store entries. Each entry must contain a unique
        ``sample_id`` key.
    detection_results: List[Dict]
        List of detection result entries with ``sample_id`` and
        ``detection_status``.

    Returns
    -------
    List[Dict]
        Updated fine‑store entries with a ``detection_status`` field for
        every entry. If a ``sample_id`` is missing from the detection
        results, the status is set to ``fallback`` (conservative default).
    """
    # Build a lookup dict for fast access
    status_lookup = {
        entry["sample_id"]: entry["detection_status"]
        for entry in detection_results
        if "sample_id" in entry and "detection_status" in entry
    }

    updated_store = []
    for entry in fine_store:
        sample_id = entry.get("sample_id")
        if not sample_id:
            raise KeyError("Each fine‑store entry must contain a 'sample_id' key.")
        # Default to 'fallback' if we have no explicit result
        detection_status = status_lookup.get(sample_id, "fallback")
        entry["detection_status"] = detection_status
        updated_store.append(entry)

    return updated_store

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge YOLO detection status into the Fine memory store."
    )
    parser.add_argument(
        "--fine-store",
        type=Path,
        required=True,
        help="Path to the Fine store JSON file (e.g., data/processed/memory_stores/fine_store.json).",
    )
    parser.add_argument(
        "--detection-results",
        type=Path,
        required=True,
        help="Path to the detection results JSON file produced by code/detection.py.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Path to write the updated Fine store. If omitted, the original file is overwritten."
        ),
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()

    fine_store_path: Path = args.fine_store
    detection_results_path: Path = args.detection_results
    output_path: Path = args.output or fine_store_path

    # Load data
    fine_store = load_json(fine_store_path)
    detection_results = load_json(detection_results_path)

    # Merge status flags
    updated_fine_store = merge_detection_status(fine_store, detection_results)

    # Write back
    write_json(updated_fine_store, output_path)
    print(f"Updated Fine store written to {output_path}")

if __name__ == "__main__":
    main()
