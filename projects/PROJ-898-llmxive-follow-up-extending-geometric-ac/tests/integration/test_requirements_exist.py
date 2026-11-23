"""Integration test to verify that the project's requirements.txt file
exists and contains all required dependencies for task T001a-reqs.

The requirements file uses pinned versions (e.g. ``pybullet==3.2.6``),
so package names are compared after stripping any version specifier.
The torch line additionally carries an ``--index-url`` option, which is
also stripped before comparison.
"""

import pathlib


def _package_name(line: str) -> str:
    """Return the bare package name of a requirements line.

    Strips inline options (``--index-url ...``) and version specifiers
    (``==``, ``>=``, etc.) so that ``pybullet==3.2.6`` -> ``pybullet``.
    """
    # Remove pip inline options and everything after them.
    for opt in ("--index-url", "--extra-index-url", "--hash"):
        idx = line.find(opt)
        if idx != -1:
            line = line[:idx]
    line = line.strip()
    # Strip version specifiers.
    for sep in ("==", ">=", "<=", "~=", "!=", ">", "<", "["):
        idx = line.find(sep)
        if idx != -1:
            line = line[:idx]
    return line.strip()


def test_requirements_file_exists_and_contains_all_packages():
    """Assert that requirements.txt exists and lists each required package."""
    req_path = pathlib.Path(__file__).resolve().parents[2] / "requirements.txt"

    # Ensure the file exists
    assert req_path.is_file(), f"requirements.txt not found at {req_path}"

    # Read the file contents
    content = req_path.read_text(encoding="utf-8")

    # Required package names (version pins are allowed and expected)
    required_packages = [
        "pybullet",
        "torch",
        "cvxpy",
        "diff-taichi",
        "scipy",
        "pandas",
        "numpy",
        "pytest",
    ]

    listed = {
        _package_name(line)
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    }

    for pkg in required_packages:
        assert pkg in listed, (
            f"Package not found in requirements.txt: {pkg} "
            f"(listed packages: {sorted(listed)})"
        )

    # The torch line must pin the CPU build with the CPU index URL.
    assert any(
        "torch==2.0.0+cpu" in line
        and "--index-url https://download.pytorch.org/whl/cpu" in line
        for line in content.splitlines()
    ), "torch must be pinned to 2.0.0+cpu with the CPU index URL"

    # Every non-option line must be pinned (task requires pinned deps).
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("--"):
            continue
        if line.startswith("-r") or line.startswith("-e"):
            continue
        assert "==" in line, f"Dependency is not pinned: {line}"

# Running the test directly (useful when executed as a script)
if __name__ == "__main__":
    test_requirements_file_exists_and_contains_all_packages()
    print("All required packages are present in requirements.txt.")