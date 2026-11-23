"""
Unit test for the pre‑analysis guard (code/99_preanalysis_guard.py).

The test creates a temporary copy of the LMM script with both a correct
implementation and a deliberately incorrect one, then invokes the guard
function to ensure it behaves as expected.
"""

import sys
import types
from pathlib import Path
import importlib.util

import pytest

# Path to the guard module
GUARD_MODULE_PATH = Path(__file__).resolve().parents[2] / "code" / "99_preanalysis_guard.py"

# Helper to load a module from a given file path
def load_module_from_path(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module

@pytest.fixture
def guard_module():
    return load_module_from_path("preanalysis_guard", GUARD_MODULE_PATH)

def test_guard_passes_with_correct_lmm(tmp_path, guard_module):
    """
    Create a minimal LMM script that only references the expected processed
    path and ensure the guard exits with status 0.
    """
    lmm_path = tmp_path / "04_fit_lmm.py"
    lmm_path.write_text(
        "from pathlib import Path\\n"
        "DATA_PATH = Path('data/processed/anonymised_ratings.csv')\\n"
    )
    # Monkey‑patch the path the guard uses
    guard_module.LMM_SCRIPT_RELATIVE = lmm_path

    # Capture sys.exit
    with pytest.raises(SystemExit) as exc:
        guard_module.check_lmm_script()
    assert exc.value.code == 0

def test_guard_fails_on_raw_path(tmp_path, guard_module):
    """
    LMM script that references a raw data file should cause the guard to
    exit with a non‑zero status.
    """
    lmm_path = tmp_path / "04_fit_lmm.py"
    lmm_path.write_text(
        "import csv\\n"
        "RAW_PATH = 'data/raw/real_ratings.csv'\\n"
    )
    guard_module.LMM_SCRIPT_RELATIVE = lmm_path

    with pytest.raises(SystemExit) as exc:
        guard_module.check_lmm_script()
    assert exc.value.code == 1

def test_guard_fails_when_processed_path_missing(tmp_path, guard_module):
    """
    LMM script that does not mention the expected processed file should
    cause the guard to fail.
    """
    lmm_path = tmp_path / "04_fit_lmm.py"
    lmm_path.write_text("print('Hello world')\\n")
    guard_module.LMM_SCRIPT_RELATIVE = lmm_path

    with pytest.raises(SystemExit) as exc:
        guard_module.check_lmm_script()
    assert exc.value.code == 1