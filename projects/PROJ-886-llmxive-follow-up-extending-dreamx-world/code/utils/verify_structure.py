import os
import logging
from pathlib import Path
import subprocess
import sys

def main():
    """
    Verifies the existence of the 15 required directories for the project.
    Returns 0 if all exist, 1 otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    project_dir = project_root / "projects" / "PROJ-886-llmxive-follow-up-extending-dreamx-world"

    required_dirs = [
        "data/raw",
        "data/derived",
        "data/derived/videos",
        "code",
        "code/models",
        "code/pipeline",
        "code/analysis",
        "code/utils",
        "tests/unit",
        "tests/integration",
        "logs",
        "docs",
        "config",
        "projects/PROJ-886-llmxive-follow-up-extending-dreamx-world",
        "projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/data"
    ]

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)

    all_exist = True
    missing_dirs = []

    logger.info(f"Verifying structure in: {project_root}")

    for rel_path in required_dirs:
        full_path = project_root / rel_path
        if full_path.exists() and full_path.is_dir():
            logger.info(f"[OK] {rel_path}")
        else:
            logger.error(f"[MISSING] {rel_path} (Expected at: {full_path})")
            missing_dirs.append(rel_path)
            all_exist = False

    if all_exist:
        logger.info("SUCCESS: All 15 required directories exist.")
        
        # Generate a tree-like listing for verification evidence
        try:
            result = subprocess.run(
                ["find", str(project_dir), "-type", "d", "-maxdepth", "3"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Directory Tree Evidence:\n" + result.stdout)
        except Exception as e:
            logger.warning(f"Could not generate tree listing: {e}")
        
        return 0
    else:
        logger.error(f"FAILURE: Missing {len(missing_dirs)} directories: {missing_dirs}")
        return 1

if __name__ == "__main__":
    sys.exit(main())