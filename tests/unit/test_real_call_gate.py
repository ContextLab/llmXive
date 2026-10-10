"""The ``LLMXIVE_REAL_TESTS`` gate must classify by test FILE, not by node id.

``tests/conftest.py`` skips the real-call suite when the env flag is absent.
Keying that decision on ``item.nodeid`` leaked parameter values into the
decision: an offline regression parametrized with a ``tests/real_call/...``
path string was skipped as though it were a real-call test, and a silent skip
is indistinguishable from a pass in CI. These tests pin the classifier to the
file path, and exercise the REAL gate through an actual pytest collection.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from tests.conftest import under_real_call

TESTS_ROOT = Path(__file__).resolve().parent.parent


def test_real_call_files_are_gated():
    assert under_real_call(TESTS_ROOT / "real_call" / "test_router_real.py")
    assert under_real_call(TESTS_ROOT / "real_call" / "conftest.py")
    assert under_real_call(TESTS_ROOT / "real_call" / "nested" / "test_x.py")


def test_offline_files_and_parameter_values_are_not_gated():
    assert not under_real_call(TESTS_ROOT / "unit" / "test_real_call_gate.py")
    assert not under_real_call(TESTS_ROOT / "conftest.py")
    # A *parameter* that spells a real-call path is not a real-call test file.
    assert not under_real_call("tests/real_call/test_resolve_reference_registrar_agnostic.py")
    assert not under_real_call("src/llmxive/backends/router.py")
    # Paths outside the tests tree never match, however they are spelled.
    assert not under_real_call("/some/other/real_call/test_x.py")


def test_collection_gates_the_real_call_file_and_runs_the_parametrized_offline_test(tmp_path):
    """Run the REAL conftest gate through an actual pytest collection.

    The temporary tree mirrors the repository layout the gate cares about: a
    ``real_call`` package that must be skipped, and a sibling offline test
    whose parameter is a real-call path and must RUN.
    """
    shutil.copyfile(TESTS_ROOT / "conftest.py", tmp_path / "conftest.py")
    (tmp_path / "real_call").mkdir()
    (tmp_path / "real_call" / "test_gated.py").write_text(
        "def test_gated():\n    pass\n", encoding="utf-8",
    )
    (tmp_path / "test_offline.py").write_text(
        "import pytest\n\n\n"
        "@pytest.mark.parametrize('path', ['tests/real_call/test_gated.py'])\n"
        "def test_offline(path):\n"
        "    assert path\n",
        encoding="utf-8",
    )

    env = dict(os.environ)
    env.pop("LLMXIVE_REAL_TESTS", None)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2] / "src")
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", "-p", "no:cacheprovider", "."],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=300,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "1 passed, 1 skipped" in completed.stdout, completed.stdout
    assert "test_offline[tests/real_call/test_gated.py] PASSED" in completed.stdout
    assert "real_call/test_gated.py::test_gated SKIPPED" in completed.stdout
