"""
parse_traces.py

Parses raw π‑Bench JSON files into a normalized CSV of dialogue turns.
The script is invoked via the wrapper at ``src/pipelines/parse_traces.py``.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def parse_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse a single π‑Bench task JSON file into a list of turn dictionaries.

    Expected output fields per turn:
      - task_id
      - turn_index (int, zero‑based)
      - speaker (e.g., "user" or "assistant")
      - utterance (the raw text)
      - ground_truth_intent (may be missing or None)
    """
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Determine task identifier
    task_id = data.get("task_id") or data.get("id") or file_path.stem

    # The dataset may store turns either under a top‑level ``turns`` list
    # or directly as a list of dictionaries.
    if isinstance(data, dict) and "turns" in data:
        turns = data["turns"]
    elif isinstance(data, list):
        turns = data
    else:
        # Fallback: treat the whole dict as a single turn if it contains the needed keys
        turns = [data]

    parsed: List[Dict[str, Any]] = []
    for idx, turn in enumerate(turns):
        speaker = turn.get("speaker") or turn.get("role") or "unknown"
        utterance = turn.get("utterance") or turn.get("text") or ""
        ground_truth_intent = turn.get("ground_truth_intent") or turn.get("intent")
        parsed.append(
            {
                "task_id": task_id,
                "turn_index": idx,
                "speaker": speaker,
                "utterance": utterance,
                "ground_truth_intent": ground_truth_intent,
            }
        )
    return parsed

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Parse raw π‑Bench JSON files into a normalized CSV of dialogue turns."
        )
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        required=True,
        help="Directory containing raw JSON files downloaded from π‑Bench.",
    )
    parser.add_argument(
        "--out-csv",
        type=str,
        required=True,
        help="Path to write the normalized CSV file.",
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_csv = Path(args.out_csv)

    if not raw_dir.is_dir():
        raise FileNotFoundError(f"Raw directory does not exist: {raw_dir}")

    json_files = sorted(raw_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {raw_dir}")

    all_rows: List[Dict[str, Any]] = []
    for json_path in json_files:
        rows = parse_json_file(json_path)
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    # Ensure deterministic column order
    df = df[
        ["task_id", "turn_index", "speaker", "utterance", "ground_truth_intent"]
    ]
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    log.info(f"Wrote normalized traces CSV with {len(df)} rows to {out_csv}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
