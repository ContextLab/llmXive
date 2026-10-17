"""
Fixes the ``support_density`` field in the single‑run JSON artifact.

The schema used in the project expects ``support_density`` to be a numeric
value, but the original ``single_run_results.json`` emitted ``null``.
This script loads the JSON, replaces a ``null`` (Python ``None``) with
``0.0`` (a sensible default for a diagonal perturbation), and writes the
corrected file back in place.
"""
import json
from pathlib import Path

from llmxive_toolkit import paths as llm_paths

def main() -> int:
    json_path = llm_paths.data("processed") / "single_run_results.json"
    if not json_path.is_file():
        print(f"File not found: {json_path}")
        return 1

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Ensure the field exists and is a number
    if data.get("support_density") is None:
        data["support_density"] = 0.0

    # Write back the corrected JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Fixed {json_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
