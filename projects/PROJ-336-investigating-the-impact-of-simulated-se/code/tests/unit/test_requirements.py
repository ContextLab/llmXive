"""
Unit test for verifying that the project's ``requirements.txt`` contains all
required packages with the exact pinned versions.
"""

import pathlib

# Expected packages and their exact versions
EXPECTED_REQUIREMENTS = {
    "nibabel": "5.1.0",
    "numpy": "1.26.2",
    "pandas": "2.2.0",
    "networkx": "3.2",
    "scikit-learn": "1.4.0",
    "scipy": "1.12.0",
    "matplotlib": "3.8.2",
    "seaborn": "0.13.2",
    "bids-validator": "1.14.0",
    "requests": "2.31.0",
}


def _load_requirements():
    """
    Load ``requirements.txt`` from the project root and return a mapping of
    package name → version (both as strings). Blank lines and comments are
    ignored.
    """
    # ``test_requirements.py`` lives in ``code/tests/unit``.
    # The project root is three levels up from this file.
    project_root = pathlib.Path(__file__).resolve().parents[3]
    req_path = project_root / "requirements.txt"

    if not req_path.is_file():
        raise FileNotFoundError(f"requirements.txt not found at expected location: {req_path}")

    requirements = {}
    for line in req_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line:
            raise ValueError(f"Invalid requirement line (expected 'package==version'): {line}")
        pkg, ver = line.split("==", 1)
        requirements[pkg.strip().lower()] = ver.strip()
    return requirements


def test_requirements_contain_all_expected_packages():
    """
    Ensure that every package listed in ``EXPECTED_REQUIREMENTS`` is present
    in ``requirements.txt`` with the exact pinned version.
    """
    reqs = _load_requirements()
    missing = []
    mismatched = []
    for pkg, expected_ver in EXPECTED_REQUIREMENTS.items():
        actual_ver = reqs.get(pkg.lower())
        if actual_ver is None:
            missing.append(pkg)
        elif actual_ver != expected_ver:
            mismatched.append(f"{pkg}: expected {expected_ver}, found {actual_ver}")

    assert not missing, f"Missing required packages in requirements.txt: {', '.join(missing)}"
    assert not mismatched, f"Version mismatches in requirements.txt: {', '.join(mismatched)}"