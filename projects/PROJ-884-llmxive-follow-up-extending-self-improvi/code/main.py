"""
Minimal entry point used by the quickstart for the pilot run.
Generates a tiny dataset (4x4 Sudoku + 4x4 pathfinding) and
runs the deterministic verifier on it.  Results are written to
`data/processed/pilot_result.jsonl` as JSON‑lines (one line per puzzle).
"""

import sys
import json
from pathlib import Path
from llmxive_toolkit import paths, get_logger

# Local imports
from code.dataset.generator import PuzzleGenerator, PuzzleType
from code.dataset.verifier import PuzzleVerifier

log = get_logger(__name__)

def _run_pilot():
    # Use deterministic seed and minimal complexity
    generator = PuzzleGenerator(seed=42, source_id="pilot_run")
    output_path = generator.generate_puzzles(
        n_values=[4],               # 4x4 Sudoku / 4x4 grid for pathfinding
        count=1,
        puzzle_types=[PuzzleType.SUDOKU, PuzzleType.PATHFINDING],
        output_dir="data/raw"
    )

    # Verify the generated puzzles
    verifier = PuzzleVerifier(timeout_ms=100)

    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    puzzles = data.get("puzzles", [])
    result_lines = []

    for puzzle in puzzles:
        is_valid, err_code = verifier.verify(puzzle)
        result = {
            "puzzle_type": puzzle.get("puzzle_type"),
            "is_valid": is_valid,
            "error_code": err_code
        }
        result_lines.append(json.dumps(result))

    # Write JSON‑lines output
    out_file = paths.processed("pilot_result.jsonl")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text("\n".join(result_lines) + "\n")
    log.info(f"Pilot verification results written to {out_file}")

def main():
    if "--pilot" not in sys.argv:
        print("Usage: python -m code.main --pilot")
        sys.exit(1)

    try:
        _run_pilot()
        return 0
    except Exception as e:
        log.error(f"Pilot run failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
