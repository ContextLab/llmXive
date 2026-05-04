"""
Project Structure Creation Script for PROJ-024

Creates the complete directory structure for the Bayesian Nonparametrics
for Anomaly Detection project as specified in the implementation plan.

Usage:
    python create_project_structure.py

This script creates all required directories and initializes Python packages
with __init__.py files for proper module structure.
"""
import os
import sys
from pathlib import Path
import logging
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_directory_structure(base_path: Path) -> List[Tuple[Path, bool]]:
    """
    Create all required directories for the project structure.

    Args:
        base_path: The root path for the project (projects/PROJ-024-...)

    Returns:
        List of (path, created) tuples indicating which directories were created
    """
    directories = [
        # Core code structure
        base_path / "code" / "src",
        base_path / "code" / "src" / "models",
        base_path / "code" / "src" / "utils",
        base_path / "code" / "src" / "data",
        base_path / "code" / "src" / "baselines",
        base_path / "code" / "src" / "evaluation",
        base_path / "code" / "src" / "services",
        base_path / "code" / "tests",
        base_path / "code" / "tests" / "contract",
        base_path / "code" / "tests" / "unit",
        base_path / "code" / "tests" / "integration",
        base_path / "code" / "scripts",
        base_path / "code" / "code",  # Legacy compatibility

        # Data directories
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "processed" / "results",

        # Specification and state directories
        base_path / "specs" / "001-bayesian-nonparametrics-anomaly-detection",
        base_path / "specs" / "contracts",
        base_path / "state" / "projects",

        # Logging directory
        base_path / "logs" / "elbo",

        # Documentation
        base_path / "paper",
        base_path / "paper" / "figures",
    ]

    created = []
    for directory in directories:
        created_before = not directory.exists()
        directory.mkdir(parents=True, exist_ok=True)
        created.append((directory, created_before))
        if created_before:
            logger.info(f"Created directory: {directory}")

    return created


def create_init_files(base_path: Path) -> List[Tuple[Path, bool]]:
    """
    Create __init__.py files for all Python packages.

    Args:
        base_path: The root path for the project

    Returns:
        List of (path, created) tuples
    """
    init_paths = [
        base_path / "code" / "src" / "__init__.py",
        base_path / "code" / "src" / "models" / "__init__.py",
        base_path / "code" / "src" / "utils" / "__init__.py",
        base_path / "code" / "src" / "data" / "__init__.py",
        base_path / "code" / "src" / "baselines" / "__init__.py",
        base_path / "code" / "src" / "evaluation" / "__init__.py",
        base_path / "code" / "src" / "services" / "__init__.py",
        base_path / "code" / "tests" / "__init__.py",
        base_path / "code" / "tests" / "contract" / "__init__.py",
        base_path / "code" / "tests" / "unit" / "__init__.py",
        base_path / "code" / "tests" / "integration" / "__init__.py",
        base_path / "code" / "scripts" / "__init__.py",
    ]

    created = []
    for init_path in init_paths:
        created_before = not init_path.exists()
        if created_before:
            init_path.write_text(
                f'"""Package for {init_path.parent.relative_to(base_path / "code")}."""\n'
            )
            created.append((init_path, True))
            logger.info(f"Created __init__.py: {init_path}")
        else:
            created.append((init_path, False))

    return created


def create_readme_files(base_path: Path) -> List[Tuple[Path, bool]]:
    """
    Create basic README files for documentation.

    Args:
        base_path: The root path for the project

    Returns:
        List of (path, created) tuples
    """
    # Code tests README
    tests_readme = base_path / "code" / "tests" / "README.md"
    tests_readme_created = not tests_readme.exists()
    if tests_readme_created:
        tests_readme.write_text(
            "# Test Suite\n\n"
            "This directory contains all tests for the project.\n\n"
            "## Structure\n\n"
            "- `contract/` - Schema and API contract tests\n"
            "- `unit/` - Unit tests for individual components\n"
            "- `integration/` - Integration tests for end-to-end workflows\n\n"
            "## Running Tests\n\n"
            "```bash\n"
            "cd code\n"
            "pytest tests/ -v --cov=src --cov-report=html\n"
            "```\n\n"
            "## Coverage Requirements\n\n"
            "Per spec.md, all public APIs must have ≥80% line coverage.\n"
        )

    # Data README
    data_readme = base_path / "data" / "README.md"
    data_readme_created = not data_readme.exists()
    if data_readme_created:
        data_readme.write_text(
            "# Data Directory\n\n"
            "This directory contains all data files for the project.\n\n"
            "## Structure\n\n"
            "- `raw/` - Original downloaded datasets (do not modify)\n"
            "- `processed/` - Processed and cleaned data\n"
            "- `processed/results/` - Model outputs and evaluation metrics\n\n"
            "## Data Provenance\n\n"
            "All datasets must have their source URLs and checksums recorded\n"
            "in the state file for reproducibility (Constitution Principle III).\n"
        )

    # Logs README
    logs_readme = base_path / "logs" / "README.md"
    logs_readme_created = not logs_readme.exists()
    if logs_readme_created:
        logs_readme.write_text(
            "# Logs Directory\n\n"
            "This directory contains runtime logs.\n\n"
            "## Structure\n\n"
            "- `elbo/` - ELBO convergence logs for ADVI variational inference\n\n"
            "## Note\n\n"
            "ELBO logs are tracked by git per Constitution Principle VI.\n"
        )

    created = []
    if tests_readme_created:
        created.append((tests_readme, True))
        logger.info(f"Created README: {tests_readme}")
    if data_readme_created:
        created.append((data_readme, True))
        logger.info(f"Created README: {data_readme}")
    if logs_readme_created:
        created.append((logs_readme, True))
        logger.info(f"Created README: {logs_readme}")

    return created


def verify_structure(base_path: Path) -> bool:
    """
    Verify that all required directories and files exist.

    Args:
        base_path: The root path for the project

    Returns:
        True if all required structure exists
    """
    required_dirs = [
        "code/src",
        "code/src/models",
        "code/src/utils",
        "code/src/data",
        "code/src/baselines",
        "code/src/evaluation",
        "code/src/services",
        "code/tests",
        "code/tests/contract",
        "code/tests/unit",
        "code/tests/integration",
        "code/scripts",
        "data/raw",
        "data/processed",
        "data/processed/results",
        "specs/001-bayesian-nonparametrics-anomaly-detection",
        "specs/contracts",
        "state/projects",
        "logs/elbo",
    ]

    all_exist = True
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if not full_path.exists():
            logger.error(f"Missing directory: {full_path}")
            all_exist = False

    required_files = [
        "code/src/__init__.py",
        "code/src/models/__init__.py",
        "code/src/utils/__init__.py",
        "code/src/data/__init__.py",
        "code/src/baselines/__init__.py",
        "code/src/evaluation/__init__.py",
        "code/src/services/__init__.py",
        "code/tests/__init__.py",
    ]

    for file_path in required_files:
        full_path = base_path / file_path
        if not full_path.exists():
            logger.error(f"Missing file: {full_path}")
            all_exist = False

    return all_exist


def main():
    """Main entry point for project structure creation."""
    # Determine base path
    script_path = Path(__file__).resolve()
    base_path = script_path.parent.parent.parent

    logger.info(f"Project base path: {base_path}")

    # Create directory structure
    logger.info("Creating directory structure...")
    dir_results = create_directory_structure(base_path)
    new_dirs = sum(1 for _, created in dir_results if created)
    logger.info(f"Created {new_dirs} new directories")

    # Create __init__.py files
    logger.info("Creating __init__.py files...")
    init_results = create_init_files(base_path)
    new_inits = sum(1 for _, created in init_results if created)
    logger.info(f"Created {new_inits} new __init__.py files")

    # Create README files
    logger.info("Creating README files...")
    readme_results = create_readme_files(base_path)
    new_readmes = sum(1 for _, created in readme_results if created)
    logger.info(f"Created {new_readmes} new README files")

    # Verify structure
    logger.info("Verifying project structure...")
    if verify_structure(base_path):
        logger.info("✓ All required directories and files exist")
        return 0
    else:
        logger.error("✗ Project structure verification failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
