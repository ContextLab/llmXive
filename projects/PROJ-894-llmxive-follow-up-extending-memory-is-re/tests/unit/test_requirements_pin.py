"""T000 verification: the pinned requirements file is complete and conflict-free.

Checks (static, no network required):
1. Every non-comment line in code/requirements.txt is pinned with `==`
   (exact versions only — no loose `>=`/`~=` or unpinned entries).
2. All dependencies explicitly required by task T000 are present:
   datasets, pandas, networkx, sentence-transformers, transformers,
   bitsandbytes, llama-cpp-python, scipy, numpy, pytest, timeout-decorator.
3. No package appears twice with conflicting pins.
4. Known cross-package constraints hold:
   - numpy major version >= 2 (required by pyarrow wheels pulled in by
     `datasets`; the previous numpy==1.24.3 pin broke `import datasets`).
   - pandas version is compatible with the pinned numpy (pandas>=2.2.2
     supports numpy 2.x).
5. `pip check` reports no broken requirements in the active environment
   (skipped if pip is unavailable).
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIREMENTS = PROJECT_ROOT / "code" / "requirements.txt"

# Packages whose distribution name differs from the import/pip name.
CANONICAL = {
    "pyyaml": "pyyaml",
    "llama-cpp-python": "llama-cpp-python",
    "huggingface-hub": "huggingface-hub",
    "sentence-transformers": "sentence-transformers",
    "timeout-decorator": "timeout-decorator",
}

REQUIRED_PACKAGES = {
    "datasets",
    "pandas",
    "networkx",
    "sentence-transformers",
    "transformers",
    "bitsandbytes",
    "llama-cpp-python",
    "scipy",
    "numpy",
    "pytest",
    "timeout-decorator",
}

LINE_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)\s*==\s*([0-9][A-Za-z0-9_.*\-]*)\s*$")


def parse_requirements():
    """Return {canonical_package_name: pinned_version} from requirements.txt."""
    assert REQUIREMENTS.exists(), f"missing requirements file: {REQUIREMENTS}"
    pins = {}
    for lineno, raw in enumerate(
        REQUIREMENTS.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = LINE_RE.match(line)
        assert m, (
            f"line {lineno} of {REQUIREMENTS} is not exactly pinned "
            f"with '==': {line!r}"
        )
        name = m.group(1).lower()
        version = m.group(2)
        if name in pins:
            assert pins[name] == version, (
                f"conflicting duplicate pin for {name}: "
                f"{pins[name]} vs {version}"
            )
        pins[name] = version
    assert pins, "requirements.txt contains no pinned dependencies"
    return pins


def test_all_entries_exactly_pinned():
    pins = parse_requirements()
    # parse_requirements already asserts the `==` format for every line;
    # here we additionally confirm there are no loose specifiers.
    for raw in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        assert ">=" not in line and "<=" not in line and "~=" not in line, (
            f"loose version specifier found: {line!r}"
        )
        assert not line.endswith("\\"), f"unexpected continuation: {line!r}"
    assert all(re.match(r"^[0-9]", v) for v in pins.values())


def test_required_packages_present():
    pins = parse_requirements()
    missing = REQUIRED_PACKAGES - set(pins)
    assert not missing, f"required packages missing from requirements.txt: {missing}"


def test_no_conflicting_duplicate_pins():
    pins = parse_requirements()  # raises on conflicting duplicates
    assert len(pins) >= len(REQUIRED_PACKAGES)


def test_numpy_pyarrow_compatibility():
    """numpy must be >= 2.0 because pyarrow (via datasets) requires it."""
    pins = parse_requirements()
    assert "pyarrow" in pins, "pyarrow pin missing (needed by datasets)"
    major = int(pins["numpy"].split(".")[0])
    assert major >= 2, (
        "numpy pinned below 2.0 breaks `import datasets` "
        "(pyarrow requires NumPy 2.0+); found "
        f"numpy=={pins['numpy']}"
    )
    # pandas must support numpy 2.x
    pandas_parts = pins["pandas"].split(".")
    assert (int(pandas_parts[0]), int(pandas_parts[1])) >= (2, 2), (
        "pandas < 2.2.2 does not support numpy 2.x"
    )


def test_pip_check_clean():
    """The active environment must report no broken requirements."""
    pip = shutil.which("pip")
    if pip is None:
        pytest.skip("pip not available on PATH")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    # Only fail on genuinely broken dependency resolution; a non-zero
    # exit with 'No broken requirements found' text is a success.
    combined = result.stdout + result.stderr
    if "No broken requirements found" in combined:
        return
    assert result.returncode == 0, (
        f"pip check reported conflicts:\n{combined}"
    )