"""Analysis code must be able to import its OWN modules — both conventions.

`run_in_venv` set only PYTHONUNBUFFERED, never the project root / code dir on
PYTHONPATH. So a run-book script died `ModuleNotFoundError` on its own package —
`from code.simulation.X import Y` (PROJ-341: `code` even collides with the stdlib
`code` module, giving "'code' is not a package") and `from models import Y`
(PROJ-024). 104 in_progress projects use `from code.X`, 334 use bare `from <subpkg>`.
Both must work: code dir on the path for bare imports, project root + a `code`
package for the `code.` prefix.
"""

from __future__ import annotations

import os
from pathlib import Path

from llmxive import sandbox


def test_analysis_env_puts_code_and_root_on_pythonpath(tmp_path: Path) -> None:
    proj = tmp_path / "PROJ-1-x"
    (proj / "code").mkdir(parents=True)
    env = sandbox._analysis_env(proj, {"PATH": "/usr/bin"})
    parts = env["PYTHONPATH"].split(os.pathsep)
    assert str(proj) in parts, "project root not on PYTHONPATH (breaks `from code.X`)"
    assert str(proj / "code") in parts, "code dir not on PYTHONPATH (breaks bare imports)"
    assert env["PATH"] == "/usr/bin", "base env dropped"


def test_analysis_env_prepends_to_existing_pythonpath(tmp_path: Path) -> None:
    proj = tmp_path / "PROJ-2-x"
    (proj / "code").mkdir(parents=True)
    env = sandbox._analysis_env(proj, {"PYTHONPATH": "/pre/existing"})
    assert env["PYTHONPATH"].endswith("/pre/existing"), "existing PYTHONPATH lost"
    assert str(proj / "code") in env["PYTHONPATH"]


def test_ensure_code_package_creates_init(tmp_path: Path) -> None:
    proj = tmp_path / "PROJ-3-x"
    (proj / "code").mkdir(parents=True)
    sandbox._ensure_code_package(proj)
    assert (proj / "code" / "__init__.py").exists(), (
        "code/__init__.py needed so `from code.X` finds a real package, not stdlib `code`"
    )


def test_ensure_code_package_is_noop_without_code_dir(tmp_path: Path) -> None:
    sandbox._ensure_code_package(tmp_path / "PROJ-4-x")  # must not raise


def test_both_import_styles_run_end_to_end(tmp_path: Path) -> None:
    """REAL run through run_in_venv (no requirements → fast venv): a script using
    `from code.pkg.mod` AND one using bare `from pkg.mod` both import successfully."""
    proj = tmp_path / "PROJ-5-x"
    (proj / "code" / "pkg").mkdir(parents=True)
    (proj / "code" / "pkg" / "mod.py").write_text("VALUE = 42\n", encoding="utf-8")
    (proj / "code" / "run_prefix.py").write_text(
        "from code.pkg.mod import VALUE\nprint('prefix', VALUE)\n", encoding="utf-8"
    )
    (proj / "code" / "run_bare.py").write_text(
        "from pkg.mod import VALUE\nprint('bare', VALUE)\n", encoding="utf-8"
    )
    r1 = sandbox.run_in_venv(project_dir=proj, args=["code/run_prefix.py"], timeout_s=120)
    assert r1.ok and "prefix 42" in r1.stdout, (r1.returncode, r1.stderr[-400:])
    r2 = sandbox.run_in_venv(project_dir=proj, args=["code/run_bare.py"], timeout_s=120)
    assert r2.ok and "bare 42" in r2.stdout, (r2.returncode, r2.stderr[-400:])
