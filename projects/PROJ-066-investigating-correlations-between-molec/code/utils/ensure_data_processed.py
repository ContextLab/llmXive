"""Create the data/processed/ directory for PROJ-066 (Task T008b).

Ensures the directory exists and contains a .gitkeep placeholder so it
is tracked by version control. Fails loudly if creation fails.
"""

from llmxive_toolkit import paths


def main() -> None:
    processed_dir = paths.data("processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    gitkeep = processed_dir / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")
    if not processed_dir.is_dir():
        raise RuntimeError(f"Failed to create directory: {processed_dir}")
    print(f"OK: {processed_dir} exists")


if __name__ == "__main__":
    main()