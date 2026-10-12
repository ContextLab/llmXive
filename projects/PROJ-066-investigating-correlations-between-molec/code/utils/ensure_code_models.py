"""Ensure the code/models/ directory exists for PROJ-066 (T008d).

Creates <project>/code/models/ and an empty __init__.py inside it so the
directory is a proper Python package for the upcoming train.py / evaluate.py
modules (T017-T027).
"""

from pathlib import Path

from llmxive_toolkit import paths


def main() -> None:
    models_dir = paths.code("models")
    models_dir.mkdir(parents=True, exist_ok=True)

    init_file = models_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text(
            "# Package marker for PROJ-066 model training/evaluation modules.\n",
            encoding="utf-8",
        )

    print(f"OK: directory exists at {models_dir}")
    assert models_dir.is_dir()
    assert init_file.is_file()


if __name__ == "__main__":
    main()