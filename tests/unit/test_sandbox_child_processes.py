"""What a project script starts is in the project's environment too.

Canary 7 (2026-10-11): ``code/verify_reproducibility.py`` ran in the project
venv and started ``bash code/run_all.sh``, whose ``python`` was the SYSTEM
interpreter -- ``ModuleNotFoundError: No module named 'llmxive_toolkit'``. Only
the shell runner put the venv on PATH. The task failed in execution three times
and the project was kicked back to ``clarified``.
"""
from pathlib import Path

import pytest

from llmxive import sandbox

CHILD = (
    "import subprocess\n"
    "out = subprocess.run(\n"
    "    ['python', '-c', 'import sys, llmxive_toolkit; print(sys.prefix)'],\n"
    "    capture_output=True, text=True)\n"
    "print(out.stdout.strip() or out.stderr.strip())\n"
    "raise SystemExit(out.returncode)\n"
)
SHELL = "#!/usr/bin/env bash\nset -e\npython -c 'import sys, llmxive_toolkit; print(sys.prefix)'\n"


@pytest.fixture
def project(tmp_path: Path) -> Path:
    project = tmp_path / "projects/PROJ-905-children"
    (project / "code").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "code/run_all.sh").write_text(SHELL, encoding="utf-8")
    return project


def _venv(project: Path) -> str:
    return str(sandbox.venv_dir(project).resolve())


def test_a_python_script_starts_python_in_the_project_venv(project: Path) -> None:
    (project / "code/spawn.py").write_text(CHILD, encoding="utf-8")
    result = sandbox.run_python_script(project_dir=project, script_relpath="code/spawn.py")
    assert result.ok, result.stdout + result.stderr
    assert Path(result.stdout.strip()).resolve() == Path(_venv(project))


def test_a_python_script_starts_a_shell_script_in_the_project_venv(project: Path) -> None:
    """The canary's exact shape: python -> bash -> python."""
    (project / "code/verify.py").write_text(
        "import subprocess\n"
        "out = subprocess.run(['bash', 'code/run_all.sh'], capture_output=True, text=True)\n"
        "print(out.stdout.strip() or out.stderr.strip())\n"
        "raise SystemExit(out.returncode)\n", encoding="utf-8")
    result = sandbox.run_python_script(project_dir=project, script_relpath="code/verify.py")
    assert result.ok, result.stdout + result.stderr
    assert Path(result.stdout.strip()).resolve() == Path(_venv(project))


def test_a_test_starts_python_in_the_project_venv(project: Path) -> None:
    (project / "tests/test_spawn.py").write_text(
        "import subprocess, sys\n\n\n"
        "def test_child_python_is_this_python():\n"
        "    out = subprocess.run(['python', '-c', 'import sys; print(sys.prefix)'],\n"
        "                         capture_output=True, text=True, check=True)\n"
        "    assert out.stdout.strip() == sys.prefix\n", encoding="utf-8")
    result = sandbox.run_pytest_file(project_dir=project, test_relpath="tests/test_spawn.py")
    assert result.ok, result.stdout + result.stderr


def test_the_shell_runner_still_uses_the_project_venv(project: Path) -> None:
    result = sandbox.run_shell_script(project_dir=project, script_relpath="code/run_all.sh")
    assert result.ok, result.stdout + result.stderr
    assert Path(result.stdout.strip()).resolve() == Path(_venv(project))
