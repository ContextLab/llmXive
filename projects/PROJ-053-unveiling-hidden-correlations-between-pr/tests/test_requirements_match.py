"""
Test that the versions installed in the current environment satisfy the
constraints declared in ``requirements.txt``.

The test parses each requirement line, extracts the package name and the
version specifier (e.g. ``>=``), and then checks the version reported by
``pip freeze``.  If any requirement is not satisfied, the test fails with
a clear error message.
"""

import subprocess
import re
from pathlib import Path

import pkg_resources
from packaging.version import Version, InvalidVersion

# Helper to parse a requirement line like "numpy>=1.21.0"
_REQ_RE = re.compile(r"""^\s*
    (?P<name>[\w\-\_]+)          # package name
    \s*
    (?P<specifier>([<>=!]=?|~=)\s*[\d\.\*]+)?   # optional version specifier
    \s*$
""", re.VERBOSE)

def _parse_requirement(line: str):
    """Return (name, operator, version) or raise ValueError."""
    match = _REQ_RE.match(line)
    if not match:
        raise ValueError(f"Unable to parse requirement line: {line!r}")
    name = match.group("name")
    spec = match.group("specifier")
    if spec:
        # split operator and version, allowing spaces
        op_match = re.match(r"([<>=!~]=?)\s*([\d\.]+)", spec.strip())
        if not op_match:
            raise ValueError(f"Invalid version specifier in line: {line!r}")
        operator, version = op_match.groups()
    else:
        operator, version = None, None
    return name.lower(), operator, version

def test_requirements_match():
    """Assert that all requirements are satisfied by the installed packages."""
    # Load the raw requirements.txt file from the repository root.
    req_path = Path(__file__).resolve().parents[1] / "code" / "requirements.txt"
    assert req_path.is_file(), f"requirements.txt not found at {req_path}"
    req_lines = [l.strip() for l in req_path.read_text().splitlines() if l.strip() and not l.startswith("#")]

    # Get ``pip freeze`` output once.
    result = subprocess.run(
        ["pip", "freeze"],
        check=True,
        capture_output=True,
        text=True,
    )
    freeze_map = {}
    for line in result.stdout.splitlines():
        if "==" in line:
            pkg, ver = line.strip().split("==", 1)
            freeze_map[pkg.lower()] = ver

    for line in req_lines:
        name, operator, required_version = _parse_requirement(line)
        assert name in freeze_map, f"Package {name} not installed (required by {line})"
        installed_version = freeze_map[name]

        if operator is None:
            # No version constraint – presence is enough.
            continue

        try:
            installed_v = Version(installed_version)
            required_v = Version(required_version)
        except InvalidVersion as exc:
            raise AssertionError(f"Invalid version format for {name}: {exc}")

        if operator in (">=", "=>"):
            assert installed_v >= required_v, (
                f"{name} version {installed_version} does not satisfy "
                f"required >= {required_version}"
            )
        elif operator in ("==", "="):
            assert installed_v == required_v, (
                f"{name} version {installed_version} does not match required {required_version}"
            )
        elif operator in ("<", "<="):
            if operator == "<":
                assert installed_v < required_v, (
                    f"{name} version {installed_version} not < {required_version}"
                )
            else:
                assert installed_v <= required_v, (
                    f"{name} version {installed_version} not <= {required_version}"
                )
        elif operator.startswith("~"):
            # PEP 440 compatible compatible release operator.
            # For simplicity we treat it as >= required_version.
            assert installed_v >= required_v, (
                f"{name} version {installed_version} does not satisfy compatible release {required_version}"
            )
        else:
            raise AssertionError(f"Unsupported operator {operator} in requirement {line}")

# The test will be discovered and run by pytest automatically.