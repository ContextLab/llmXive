"""
Script to generate the project state YAML file with SHA-256 hashes of
`requirements.txt` and `pyproject.toml`. This satisfies Constitution
Principle V by recording cryptographic hashes of the project's dependency
configuration files.

The script is intended to be run after the repository has been
initialized (T005c) and the configuration files are present.
"""
import hashlib
import json
from pathlib import Path

import yaml


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hash of a file's full contents."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_state_file(state_path: Path, req_path: Path, pyproj_path: Path) -> None:
    """
    Generate a YAML file at ``state_path`` containing a map ``artifact_hashes``
    with the SHA‑256 hashes of ``requirements.txt`` and ``pyproject.toml``.

    The resulting YAML has the following structure:

    .. code-block:: yaml
    
        artifact_hashes:
          requirements.txt: <hash>
          pyproject.toml: <hash>
        generated_at: <ISO‑8601 timestamp>
    """
    # Ensure the parent directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    hashes = {
        "requirements.txt": compute_sha256(req_path),
        "pyproject.toml": compute_sha256(pyproj_path),
    }

    state_content = {
        "artifact_hashes": hashes,
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    }

    with state_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(state_content, f, sort_keys=False)


def main() -> None:
    """
    Entry point for the script.

    It assumes the repository root is two levels above this file
    (i.e. ``code/scripts`` → repository root). Adjust the relative paths
    if the project layout changes.
    """
    repo_root = Path(__file__).resolve().parents[2]
    requirements_path = repo_root / "requirements.txt"
    pyproject_path = repo_root / "pyproject.toml"
    state_file_path = repo_root / "state" / "projects" / "PROJ-500-neural-correlates-of-predictive-error-si.yaml"

    # Verify required files exist; fail loudly if they do not.
    if not requirements_path.is_file():
        raise FileNotFoundError(f"Missing requirements file: {requirements_path}")
    if not pyproject_path.is_file():
        raise FileNotFoundError(f"Missing pyproject file: {pyproject_path}")

    generate_state_file(state_file_path, requirements_path, pyproject_path)
    print(f"Project state written to {state_file_path}")


if __name__ == "__main__":
    main()