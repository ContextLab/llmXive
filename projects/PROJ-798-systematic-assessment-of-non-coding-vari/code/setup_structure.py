#!/usr/bin/env python3
"""
create_structure.py

Creates the required project directory layout and records a manifest file.
The manifest is written to ``data/results/structure_manifest.txt`` and contains a
sorted list of all directories under ``code``, ``data`` and ``tests``.
This satisfies the verification step:

    find code data tests -type d | sort > data/results/structure_manifest.txt

The script exits with a non‑zero status if any step fails, ensuring loud failure
on missing system utilities.
"""

import subprocess
from pathlib import Path

def main() -> None:
    # Required directory paths (relative to the repository root)
    required_dirs = [
        Path("code"),
        Path("code/data_ingestion"),
        Path("code/scoring"),
        Path("code/analysis"),
        Path("code/utils"),
        Path("data/raw"),
        Path("data/derived"),
        Path("data/results"),
        Path("tests/unit"),
        Path("tests/integration"),
        Path("tests/contract"),
    ]

    # Create each directory (parents=True allows nested creation)
    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Path for the manifest file
    manifest_path = Path("data/results/structure_manifest.txt")

    # Use the system ``find`` command to generate the full directory list.
    # ``check=True`` ensures the script fails loudly if ``find`` is unavailable
    # or returns a non‑zero exit status.
    result = subprocess.run(
        ["find", "code", "data", "tests", "-type", "d"],
        check=True,
        capture_output=True,
        text=True,
    )

    # Sort the output to guarantee deterministic ordering
    dirs = sorted(line.strip() for line in result.stdout.splitlines() if line.strip())

    # Write the sorted list to the manifest file, ending with a newline.
    manifest_path.write_text("\n".join(dirs) + "\n")

if __name__ == "__main__":
    main()
