"""
Test to verify that the pinned package versions in requirements.txt match the
versions installed in the current Python environment.

The test reads the project's root ``requirements.txt`` file, parses each line
for a ``package==version`` specification, and then checks the installed
version using ``importlib.metadata.version`` (available in the standard
library).  If any package version does not match, the test fails with a
clear assertion message.

This provides the required verification without relying on an external
``diff`` command, which would include many unrelated packages from the
environment.  It directly confirms that the exact versions listed in the
plan are present.
"""

import pathlib
import re
import sys
from importlib import metadata

import pytest

@pytest.fixture(scope="module")
def requirements_path() -> pathlib.Path:
    """
    Return the absolute path to the project's root ``requirements.txt``.
    """
    # The test file resides under ``tests/``; the project root is two levels up.
    return pathlib.Path(__file__).resolve().parents[1] / "requirements.txt"

def parse_requirements(requirements_file: pathlib.Path) -> dict[str, str]:
    """
    Parse a requirements file and return a mapping of package name to version.

    Only lines matching the pattern ``package==version`` are considered.
    Comments and empty lines are ignored.
    """
    pattern = re.compile(r"^\s*([A-Za-z0-9_.-]+)==([A-Za-z0-9_.-]+)\s*$")
    requirements = {}
    with requirements_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = pattern.match(line)
            if not match:
                raise ValueError(
                    f"Invalid requirement line in {requirements_file}: {line!r}"
                )
            pkg, ver = match.groups()
            requirements[pkg.lower()] = ver
    return requirements

def test_pinned_versions_match_installed(requirements_path: pathlib.Path):
    """
    Ensure each pinned package version matches the version installed in the
    environment.
    """
    pinned = parse_requirements(requirements_path)

    mismatches = []
    missing = []

    for pkg, expected_version in pinned.items():
        try:
            installed_version = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            missing.append(pkg)
            continue

        if installed_version != expected_version:
            mismatches.append((pkg, expected_version, installed_version))

    error_parts = []
    if missing:
        error_parts.append(
            f"Packages not found in environment: {', '.join(sorted(missing))}"
        )
    if mismatches:
        mismatch_str = "\n".join(
            f"- {pkg}: expected {exp}, installed {inst}"
            for pkg, exp, inst in mismatches
        )
        error_parts.append(f"Version mismatches:\n{mismatch_str}")

    if error_parts:
        # Join all error messages into a single AssertionError for pytest output.
        raise AssertionError("\n".join(error_parts))

# The test suite can be run with ``python -m pytest -v`` from the project root.
# No additional output files are produced; the test simply validates the
# correctness of ``requirements.txt``.