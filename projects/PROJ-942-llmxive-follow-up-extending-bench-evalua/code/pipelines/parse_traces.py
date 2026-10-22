import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

# Optional: download real dataset if raw directory is empty
try:
    from datasets import load_dataset
except Exception as e:
    load_dataset = None  # type: ignore

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _download_and_save_raw(raw_dir: Path) -> List[Path]:
    """
    Downloads the official ``pi_bench`` dataset via ``datasets`` (streaming)
    and writes each example as a JSON file into ``raw_dir``.
    Returns the list of written file paths.
    """
    if load_dataset is None:
        raise ImportError(
            "The `datasets` library is required to download the pi_bench dataset. "
            "Ensure it is installed (add `datasets` to requirements.txt)."
        )

    log.info("Raw directory empty – downloading pi_bench dataset via `datasets`...")
    ds = load_dataset("pi_bench", streaming=True)

    written_files: List[Path] = []
    for idx, example in enumerate(ds):
        # Attempt to obtain a stable identifier for the task
        task_id = (
            str(example.get("task_id"))
            or str(example.get("id"))
            or f"task_{idx:05d}"
        )
        # Clean task_id for filesystem safety
        safe_task_id = "".join(c if c.isalnum() or c in "._-" else "_" for c in task_id)
        out_path = raw_dir / f"{safe_task_id}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(example, f, ensure_ascii=False)
        written_files.append(out_path)
        if (idx + 1) % 100 == 0:
            log.info(f"Downloaded and saved {idx + 1} tasks...")
    log.info(f"Finished downloading pi_bench: {len(written_files)} JSON files written.")
    return written_files

def parse_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Parses a single pi-Bench task JSON file into a list of turns."""
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # pi-Bench tasks can be structured as a list of turns or a dict containing turns
    turns_data = []
    if isinstance(data, list):
        turns_data = data
    elif isinstance(data, dict):
        # Try common keys for the dialogue sequence
        for key in ["dialogue", "turns", "interaction", "traces"]:
            if key in data and isinstance(data[key], list):
                turns_data = data[key]
                break
        if not turns_data:
            # Fallback: if it's a dict but no known list key, it might be a single-turn task
            # or a different format. We treat it as a single turn if it looks like one.
            if "speaker" in data and ("utterance" in data or "text" in data):
                turns_data = [data]
            else:
                log.warning(f"Could not find dialogue sequence in {file_path}")

    if not turns_data:
        return []

    task_id = file_path.stem
    normalized_turns: List[Dict[str, Any]] = []

    for idx, turn in enumerate(turns_data):
        # Extract fields with fallbacks for common naming variations
        speaker = turn.get("speaker", "unknown")
        utterance = (
            turn.get("utterance")
            or turn.get("text")
            or turn.get("content")
            or ""
        )
        # Ground truth intent is optional
        gt_intent = (
            turn.get("ground_truth_intent")
            or turn.get("intent")
            or turn.get("hidden_intent")
        )

        normalized_turns.append(
            {
                "task_id": task_id,
                "turn_index": idx,
                "speaker": speaker,
                "utterance": utterance,
                "ground_truth_intent": gt_intent,
            }
        )

    return normalized_turns

def main():
    parser = argparse.ArgumentParser(
        description="Parse raw pi-Bench traces into a normalized CSV."
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        required=True,
        help="Directory containing raw JSON files.",
    )
    parser.add_argument(
        "--out-csv",
        type=str,
        required=True,
        help="Path to the output CSV file.",
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_path = Path(args.out_csv)

    # Ensure the raw directory exists
    if not raw_dir.exists():
        log.info(f"Raw directory {raw_dir} does not exist – creating it.")
        raw_dir.mkdir(parents=True, exist_ok=True)

    # Gather JSON files; if none exist, attempt to download the dataset
    json_files = list(raw_dir.glob("*.json"))
    if not json_files:
        try:
            json_files = _download_and_save_raw(raw_dir)
        except Exception as e:
            log.error(f"Failed to download pi_bench dataset: {e}")
            raise

    if not json_files:
        log.error(f"No JSON files found in {raw_dir}")
        raise FileNotFoundError(f"No JSON files found in {raw_dir}")

    all_turns: List[Dict[str, Any]] = []
    for json_file in json_files:
        try:
            turns = parse_json_file(json_file)
            all_turns.extend(turns)
        except Exception as e:
            log.error(f"Failed to parse {json_file}: {e}")
            continue

    if not all_turns:
        log.error("No valid turns extracted from any JSON files.")
        raise RuntimeError("No data extracted. Check raw file formats.")

    df = pd.DataFrame(all_turns)

    # Ensure schema: cast types and handle NaNs
    df["task_id"] = df["task_id"].astype(str)
    df["turn_index"] = df["turn_index"].astype(int)
    df["speaker"] = df["speaker"].astype(str)
    df["utterance"] = df["utterance"].astype(str)
    df["ground_truth_intent"] = (
        df["ground_truth_intent"]
        .astype(str)
        .replace("nan", pd.NA)
    )

    # Create output directory if it doesn't exist
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(out_path, index=False)
    log.info(f"Successfully wrote {len(df)} turns to {out_path}")

if __name__ == "__main__":
    # Configure basic logging if the toolkit logger hasn't been set up
    logging.basicConfig(level=logging.INFO)
    main()
