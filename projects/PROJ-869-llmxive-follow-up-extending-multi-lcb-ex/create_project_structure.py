#!/usr/bin/env python3
"""
Script to create the canonical project layout for the llmXive follow‑up experiment.

This script is idempotent: it can be run multiple times without error.
It creates the required directories and minimal top‑level files
(requirements.txt and README.md) inside the project root
``projects/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex``.
"""

import os
from pathlib import Path

def main() -> None:
    # Resolve the directory containing this script – this is the project root.
    root = Path(__file__).resolve().parent

    # Define the directory structure required by the specification.
    dirs = [
        root / "code" / "src",
        root / "code" / "tests",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "results",
    ]

    # Create each directory (including any missing parents).
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Create a minimal requirements.txt – the same content as the repo’s
    # top‑level requirements.txt so that downstream scripts can install
    # dependencies from this location.
    # ------------------------------------------------------------------
    req_path = root / "requirements.txt"
    req_content = """# Core Dependencies
llama-cpp-python>=0.2.0
datasets>=2.14.0
pandas>=2.0.0
pyyaml>=6.0
scipy>=1.11.0
joblib>=1.3.0

# Testing
pytest>=7.4.0

# Linting & Formatting
ruff>=0.1.0
black>=23.0.0
"""
    req_path.write_text(req_content.strip() + "\n")

    # ------------------------------------------------------------------
    # Create a simple README.md describing the scaffold.
    # ------------------------------------------------------------------
    readme_path = root / "README.md"
    readme_content = """# PROJ‑869 llmxive follow‑up

Project scaffolding for the “Multi‑LCB: Extending LiveCodeBench to Multiple Programming Languages” experiment.

This repository contains the reproducible pipeline required by task **T001**.
"""
    readme_path.write_text(readme_content.strip() + "\n")

if __name__ == "__main__":
    main()