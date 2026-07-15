import os
import sys
from pathlib import Path
import subprocess

def ensure_config_dir() -> Path:
    """
    Ensure that a ``config`` directory exists at the project root.

    Returns
    -------
    Path
        Path object pointing to the configuration directory.
    """
    config_dir = Path.cwd() / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def create_ruff_config(config_dir: Path) -> None:
    """
    Write a minimal ``.ruff.toml`` configuration file.

    Parameters
    ----------
    config_dir : Path
        Directory where the configuration file should be placed.
    """
    ruff_path = config_dir / ".ruff.toml"
    ruff_content = """[tool.ruff]
line-length = 88
select = ["E", "F", "W", "C90"]
ignore = []
"""
    ruff_path.write_text(ruff_content)
    print(f"Created Ruff config at {ruff_path}")


def create_black_config(_: Path) -> None:
    """
    Write (or extend) a ``pyproject.toml`` file with Black configuration.
    The function writes the file at the repository root.
    """
    pyproject_path = Path.cwd() / "pyproject.toml"
    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
"""
    if pyproject_path.exists():
        existing = pyproject_path.read_text()
        if "[tool.black]" not in existing:
            with pyproject_path.open("a") as f:
                f.write("\n" + black_section.strip() + "\n")
            print(f"Appended Black config to existing {pyproject_path}")
        else:
            print(f"Black config already present in {pyproject_path}")
    else:
        pyproject_path.write_text(black_section.strip() + "\n")
        print(f"Created new {pyproject_path} with Black config")


def update_requirements() -> None:
    """
    Ensure that ``requirements.txt`` exists and contains pinned versions of
    ``ruff`` and ``black`` (alongside any pre‑existing dependencies).
    """
    req_path = Path.cwd() / "requirements.txt"
    # Pin versions – these are known‑good versions at the time of implementation.
    needed = {
        "ruff==0.6.0",
        "black==24.2.0",
    }
    if req_path.exists():
        existing = {
            line.strip()
            for line in req_path.read_text().splitlines()
            if line.strip() and not line.strip().startswith("#")
        }
        combined = existing.union(needed)
    else:
        combined = needed

    # Write sorted for deterministic output
    req_path.write_text("\n".join(sorted(combined)) + "\n")
    print(f"Updated requirements at {req_path}")


def main() -> None:
    """
    Entry point: create configuration files and update requirements.
    """
    try:
        config_dir = ensure_config_dir()
        create_ruff_config(config_dir)
        create_black_config(config_dir)
        update_requirements()
        print("✅ Linting (ruff) and formatting (black) tools configured successfully.")
    except Exception as exc:
        print(f"❌ Failed to configure linting/formatting tools: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()