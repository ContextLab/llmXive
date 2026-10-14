"""Create the canonical project directory layout for the EVA-Bench latency study.

Run as: python code/setup_project.py
Creates every directory required by the tasks in tasks.md (Phase 1, T001)
and verifies that the dependency manifests exist.
"""

from pathlib import Path

from llmxive_toolkit import paths


DIRECTORIES = [
    "code",
    "code/data",
    "code/processing",
    "code/analysis",
    "code/visualization",
    "code/contracts",
    "code/utils",
    "code/injectors",
    "code/synthetic",
    "code/tests",
    "code/tests/unit",
    "code/tests/integration",
    "code/scripts",
    "data",
    "data/raw",
    "data/processed",
    "data/results",
    "data/analysis",
    "data/report",
    "data/baseline",
    "data/perturbation_profiles",
    "tests",
    "tests/unit",
    "tests/integration",
    "logs",
    "figures",
    "results",
    "specs/001-llmxive-follow-up-extending-eva-bench-a/contracts",
    "state/projects",
]

REQUIRED_MANIFESTS = ["pyproject.toml", "requirements.txt"]


def create_project_structure() -> None:
    """Create all required directories if they don't exist."""
    for rel in DIRECTORIES:
        (paths.root / rel).mkdir(parents=True, exist_ok=True)


def main() -> None:
    create_project_structure()
    missing = [m for m in REQUIRED_MANIFESTS if not (paths.root / m).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing dependency manifests: {missing}")
    created = sum(1 for rel in DIRECTORIES if (paths.root / rel).is_dir())
    print(f"Project layout verified: {created}/{len(DIRECTORIES)} directories present.")
    print("Dependency manifests present: pyproject.toml, requirements.txt")


if __name__ == "__main__":
    main()