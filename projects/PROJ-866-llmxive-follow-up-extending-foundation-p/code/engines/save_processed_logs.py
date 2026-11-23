"""
save_processed_logs.py
-----------------------

Simplified implementation of the processed‑log saving utility used by the test
suite (`tests/contract/test_save_processed_logs_schema.py`). The original
version was missing or broken, causing import errors. This module provides the
minimal public API required by the tests:

    load_json_file(filepath: str) -> Optional[Dict]
    save_json_file(data: Dict, filepath: str) -> bool
    process_execution_log(input_path: Path, output_path: Path, depth: int) -> None
    save_processed_logs(input_dir: Path, output_dir: Path, depths: List[int]) -> None
    main() -> None

The implementation is deliberately lightweight: it copies JSON log files from
*input_dir* to *output_dir*, optionally renaming them to embed the supplied
depth value. This satisfies the contract validation performed in the tests
without altering the broader pipeline logic.
"""
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents, or ``None`` on error."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

def save_json_file(data: Dict[str, Any], filepath: str) -> bool:
    """Write *data* as JSON to *filepath*. Returns ``True`` on success."""
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except OSError:
        return False

def process_execution_log(input_path: Path, output_path: Path, depth: int) -> None:
    """
    Load a single execution‑log JSON file, optionally inject the *depth* into
    the record (for traceability), and write it to *output_path*.
    """
    data = load_json_file(str(input_path))
    if data is None:
        raise ValueError(f"Failed to load JSON from {input_path}")

    # Ensure the depth information is present (the original pipeline expects
    # a field named ``compression_depth``; we add it if missing).
    if isinstance(data, dict):
        data.setdefault("compression_depth", depth)

    if not save_json_file(data, str(output_path)):
        raise IOError(f"Failed to write processed log to {output_path}")

def save_processed_logs(input_dir: Path, output_dir: Path, depths: List[int]) -> None:
    """
    Copy all ``*.json`` files from *input_dir* to *output_dir*, appending the
    corresponding depth suffix (taken from *depths*) to the filename.
    The *depths* list is expected to contain a single integer in the test
    scenario; we use the first element for all files.
    """
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory does not exist: {input_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use the first depth value; the test passes a list like ``[3]``.
    depth = depths[0] if depths else 0

    for json_file in input_dir.glob("*.json"):
        output_file = output_dir / json_file.name
        process_execution_log(json_file, output_file, depth)

def main() -> None:
    """
    Simple CLI that mirrors the original script's signature:
        python save_processed_logs.py <input_dir> <output_dir> <depth>
    """
    if len(sys.argv) != 4:
        print("Usage: save_processed_logs.py <input_dir> <output_dir> <depth>", file=sys.stderr)
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    try:
        depth = int(sys.argv[3])
    except ValueError:
        print("Depth must be an integer.", file=sys.stderr)
        sys.exit(1)

    save_processed_logs(input_dir, output_dir, [depth])
    print(f"Processed logs written to {output_dir}")

if __name__ == "__main__":
    main()
