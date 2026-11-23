import os
from pathlib import Path

def main():
    """
    Verify that linting and formatting configurations exist.
    This script acts as a bootstrap check for T003.
    """
    project_root = Path(__file__).resolve().parent.parent

    required_files = [
        project_root / ".ruff.toml",
        project_root / ".flake8",
        project_root / "pyproject.toml",
        project_root / ".pre-commit-config.yaml",
    ]

    missing = [f for f in required_files if not f.exists()]

    if missing:
        missing_str = "\n".join([str(f) for f in missing])
        raise FileNotFoundError(
            f"Linting configuration files missing. Please ensure T003 has been run.\nMissing:\n{missing_str}"
        )

    print("Linting configuration verified successfully.")
    print("Tools configured: ruff, black, flake8, pre-commit.")

if __name__ == "__main__":
    main()
