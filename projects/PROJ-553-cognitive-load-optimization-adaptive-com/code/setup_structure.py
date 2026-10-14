"""
Setup script for initializing the project skeleton.

This script creates the required top-level directories and core files
for the cognitive load optimization project. It is idempotent and can be
run multiple times without error.
"""
import sys
from pathlib import Path
import logging

def main() -> None:
    """
    Create the required directory structure and core files.
    """
    # Determine the project root (parent of the `code` directory)
    project_root = Path(__file__).resolve().parent.parent

    # List of directories to create
    dirs_to_create = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "explanation_tiers",
        project_root / "data" / "simulation_results",
        project_root / "code",
        project_root / "tests",
        project_root / "docs",
        project_root / "logs",
    ]

    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)

    # Core files that must exist
    core_files = {
        project_root / "README.md": "Adaptive complexity scaling for personalized learning research.\n",
        project_root / "requirements.txt": (
            "scikit-learn\n"
            "lightgbm\n"
            "pandas\n"
            "numpy\n"
            "textstat\n"
            "datasets\n"
            "statsmodels\n"
            "pytest\n"
            "requests\n"
            "transformers>=4.30.0\n"
            "torch>=2.0.0\n"
            "sentencepiece\n"
        ),
        project_root / "code" / "__init__.py": "# Code package\n",
        project_root / "tests" / "__init__.py": "\"\"\"Tests package for cognitive-load-optimization project.\"\"\"\n",
        project_root / "docs" / "README.md": (
            "# Cognitive Load Optimization: Adaptive Complexity Scaling for Personalized Learning\n\n"
            "## Overview\n\n"
            "This repository implements an adaptive learning system that adjusts the complexity "
            "of instructional content based on real‑time estimates of a student's cognitive load.\n"
        ),
    }

    for file_path, content in core_files.items():
        if not file_path.exists():
            file_path.write_text(content, encoding="utf-8")

    # Log success
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)
    logger.info("Project skeleton initialized successfully.")

if __name__ == "__main__":
    main()