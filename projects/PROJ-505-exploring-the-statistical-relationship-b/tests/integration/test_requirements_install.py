"""
Integration test for T001.
Verifies that each package listed in requirements.txt was installed
successfully by inspecting the pip install log captured in ci/install_log.txt.
"""
import re
from pathlib import Path

def _parse_requirements(req_file: Path):
    """Yield package names from a requirements.txt file."""
    for line in req_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Expected format: package==major.minor.*
        pkg = line.split("==", 1)[0].strip()
        yield pkg

def test_all_requirements_successfully_installed():
    project_root = Path(__file__).resolve().parents[2]  # tests/integration -> project root
    req_path = project_root / "requirements.txt"
    log_path = project_root / "ci" / "install_log.txt"

    # Ensure the log file exists
    assert log_path.is_file(), f"Install log not found at {log_path}"

    log_content = log_path.read_text(encoding="utf-8")
    # Pip prints a line containing "Successfully installed" followed by a list of packages.
    # We'll search for that phrase and ensure each required package appears somewhere in the log.
    success_phrase = "Successfully installed"
    assert success_phrase in log_content, "pip install did not report successful installation"

    # Build a set of packages reported as installed.
    installed_packages = set()
    for line in log_content.splitlines():
        if success_phrase in line:
            # Extract package names (they appear after the phrase, separated by spaces)
            parts = line.split(success_phrase, 1)[1].strip().split()
            for part in parts:
                # The format may be pkg==ver or just pkg; we keep the name before any '=='
                name = part.split("==", 1)[0]
                installed_packages.add(name)

    # Verify each requirement appears in the installed set
    missing = []
    for pkg in _parse_requirements(req_path):
        if pkg not in installed_packages:
            missing.append(pkg)

    assert not missing, f"The following packages were not reported as installed: {', '.join(missing)}"