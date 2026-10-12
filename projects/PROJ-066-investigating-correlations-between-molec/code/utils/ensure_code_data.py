"""Ensure the code/data/ directory exists for PROJ-066 (task T008c).

Creates the directory if missing and prints a manifest of its contents
as evidence that the directory exists on disk.
"""

from pathlib import Path

from llmxive_toolkit import paths


def main() -> None:
    data_code_dir = paths.code("data")
    data_code_dir.mkdir(parents=True, exist_ok=True)

    entries = sorted(data_code_dir.iterdir())
    print(f"Directory exists: {data_code_dir}")
    print(f"Entry count: {len(entries)}")
    for entry in entries:
        kind = "dir" if entry.is_dir() else "file"
        print(f"  [{kind}] {entry.name}")

    if not entries:
        raise RuntimeError(
          "code/data/ directory exists but is empty; expected at least "
          "the .gitkeep placeholder file."
      )


if __name__ == "__main__":
    main()