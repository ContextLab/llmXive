"""The toolkit every project can import, and the environment that carries it.

Real venvs, real pip, real subprocesses. The base environment is built once
per machine (``sandbox.base_env_dir``), so only the first run pays for it.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

import pytest

from llmxive import sandbox
from llmxive.project_files import requirements_paths
from llmxive.project_toolkit import TOOLKIT_PATH


def _toolkit(monkeypatch: pytest.MonkeyPatch, root: Path):
    monkeypatch.syspath_prepend(str(TOOLKIT_PATH))
    monkeypatch.setenv("LLMXIVE_PROJECT_ROOT", str(root))
    import llmxive_toolkit

    return llmxive_toolkit


def test_the_toolkit_imports_nothing_outside_the_standard_library() -> None:
    import ast

    source = (TOOLKIT_PATH / "llmxive_toolkit" / "__init__.py").read_text(encoding="utf-8")
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported <= set(sys.stdlib_module_names), imported - set(sys.stdlib_module_names)


def test_asking_for_a_path_creates_its_directory_and_nothing_else(tmp_path, monkeypatch) -> None:
    tk = _toolkit(monkeypatch, tmp_path)
    out = tk.paths.data("results", "census.csv")
    assert out == tmp_path.resolve() / "data" / "results" / "census.csv"
    assert out.parent.is_dir() and not out.exists(), "a path is not a file"
    assert tk.paths.figures() == tmp_path.resolve() / "figures" and tk.paths.figures().is_dir()
    assert tk.paths.results("a.json") == tmp_path.resolve() / "data" / "results" / "a.json"
    assert tk.paths.root == tmp_path.resolve()


@pytest.mark.parametrize("parts", [("..", "outside.txt"), ("data", "..", "..", "x.csv")])
def test_a_path_cannot_leave_the_project(tmp_path, monkeypatch, parts) -> None:
    tk = _toolkit(monkeypatch, tmp_path / "project")
    (tmp_path / "project").mkdir()
    with pytest.raises(ValueError, match="outside the project"):
        tk.paths.path(*parts)
    assert not (tmp_path / "outside.txt").exists()


def test_the_root_is_found_from_a_subdirectory_without_the_variable(tmp_path, monkeypatch) -> None:
    (tmp_path / "code" / "analysis").mkdir(parents=True)
    monkeypatch.syspath_prepend(str(TOOLKIT_PATH))
    monkeypatch.delenv("LLMXIVE_PROJECT_ROOT", raising=False)
    monkeypatch.chdir(tmp_path / "code" / "analysis")
    import llmxive_toolkit

    # code/analysis has no code/ of its own; neither does code/. The project does.
    assert llmxive_toolkit.project_root() == tmp_path.resolve()


@pytest.fixture
def clean_logging():
    root = logging.getLogger()
    before, level = list(root.handlers), root.level
    yield
    for handler in list(root.handlers):
        if handler not in before:
            root.removeHandler(handler)
            handler.close()
    root.setLevel(level)


# Every one of these is a call shape found in the corpus's own logging helpers.
@pytest.mark.parametrize("call", [
    lambda tk: tk.get_logger(__name__),
    lambda tk: tk.get_logger(),
    lambda tk: tk.get_logger("run", "DEBUG"),
    lambda tk: tk.get_logger("run", level=logging.DEBUG),
    lambda tk: tk.get_logger(name="run", log_file="logs/run.log"),
    lambda tk: tk.setup_logging("DEBUG"),
    lambda tk: tk.setup_logging(logging.INFO),
    lambda tk: tk.setup_logging(log_dir="logs", level="info"),
    lambda tk: tk.setup_logging(name="run", log_dir="logs", filename="a.log", verbose=True),
    lambda tk: tk.setup_logging(log_level="DEBUG", config=None),
])
def test_the_logger_accepts_the_ways_it_is_actually_called(tmp_path, monkeypatch, clean_logging, call) -> None:
    tk = _toolkit(monkeypatch, tmp_path)
    logger = call(tk)
    assert isinstance(logger, logging.Logger)
    logger.info("hello")


def test_the_logger_writes_the_file_once_however_often_it_is_set_up(tmp_path, monkeypatch, clean_logging) -> None:
    tk = _toolkit(monkeypatch, tmp_path)
    for _ in range(3):
        log = tk.get_logger("run", log_file="logs/run.log")
    log.info("one line")
    for handler in logging.getLogger().handlers:
        handler.flush()
    text = (tmp_path / "logs" / "run.log").read_text(encoding="utf-8")
    assert text.count("one line") == 1, text
    assert "INFO run: one line" in text


def test_both_requirements_files_are_installed_from(tmp_path) -> None:
    proj = tmp_path / "projects" / "PROJ-X"
    (proj / "code").mkdir(parents=True)
    assert requirements_paths(proj) == []
    (proj / "requirements.txt").write_text("\n", encoding="utf-8")
    assert requirements_paths(proj) == [proj / "requirements.txt"]
    (proj / "code" / "requirements.txt").write_text("\n", encoding="utf-8")
    assert requirements_paths(proj) == [proj / "code" / "requirements.txt", proj / "requirements.txt"]


# --- in a real project venv ----------------------------------------------------


@pytest.fixture(scope="module")
def project(tmp_path_factory) -> Path:
    proj = tmp_path_factory.mktemp("repo") / "projects" / "PROJ-toolkit"
    (proj / "code").mkdir(parents=True)
    return proj


def test_a_project_script_uses_the_toolkit_and_undeclared_base_packages(project: Path) -> None:
    """No requirements file at all: numpy, pandas and the toolkit still import."""
    base = sandbox.ensure_base_env()
    assert base is not None, "the base environment could not be built (network?)"
    (project / "code" / "run.py").write_text(
        "import numpy as np\n"
        "import pandas as pd\n"
        "from llmxive_toolkit import paths, get_logger\n"
        "log = get_logger(__name__, log_file='logs/run.log')\n"
        "out = paths.results('totals.csv')\n"
        "pd.DataFrame({'n': np.arange(4)}).to_csv(out, index=False)\n"
        "log.info('wrote %s', out.relative_to(paths.root))\n",
        encoding="utf-8",
    )
    res = sandbox.run_in_venv(project_dir=project, args=["code/run.py"], timeout_s=300)
    assert res.ok, res.stdout + res.stderr
    assert (project / "data" / "results" / "totals.csv").read_text(encoding="utf-8").split() == ["n", "0", "1", "2", "3"]
    assert "wrote data/results/totals.csv" in (project / "logs" / "run.log").read_text(encoding="utf-8")


def test_pytest_runs_from_the_base_environment(project: Path) -> None:
    (project / "tests").mkdir(exist_ok=True)
    (project / "tests" / "test_ok.py").write_text(
        "import numpy\n\ndef test_ok():\n    assert numpy.arange(3).sum() == 3\n", encoding="utf-8")
    res = sandbox.run_in_venv(project_dir=project, args=["-m", "pytest", "-q", "tests/"], timeout_s=300)
    assert res.ok, res.stdout + res.stderr


def test_a_projects_own_version_wins_and_the_base_is_left_alone(project: Path) -> None:
    """The base pins jsonschema 4.22.0; this project asks for 4.21.1 in the ROOT
    manifest, the one that used to be ignored when code/requirements.txt exists."""
    base = sandbox.ensure_base_env()
    assert base is not None
    (project / "code" / "requirements.txt").write_text("# nothing here\n", encoding="utf-8")
    (project / "requirements.txt").write_text("jsonschema==4.21.1\n", encoding="utf-8")
    probe = ["-c", "import jsonschema, importlib.metadata as m; print(m.version('jsonschema'), jsonschema.__file__)"]
    res = sandbox.run_in_venv(project_dir=project, args=probe, timeout_s=600)
    assert res.ok, res.stdout + res.stderr
    version, where = res.stdout.split()
    assert version == "4.21.1"
    assert Path(where).is_relative_to(sandbox.venv_dir(project)), where
    # The shared copy is untouched: another project still gets the pinned one.
    assert (base / "jsonschema-4.22.0.dist-info").is_dir()
    shared = subprocess.run(
        [sys.executable, "-c", "import sys; sys.path.insert(0, sys.argv[1]); "
         "import importlib.metadata as m; print(m.version('jsonschema'))", str(base)],
        capture_output=True, text=True, check=True, env={"PYTHONNOUSERSITE": "1", "PATH": ""})
    assert shared.stdout.strip() == "4.22.0"


def test_the_base_environment_is_keyed_by_python_and_pins(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LLMXIVE_BASE_ENV_DIR", str(tmp_path))
    first = sandbox.base_env_dir()
    assert first.parent == tmp_path and first.name.startswith(f"py{sys.version_info.major}{sys.version_info.minor}-")
    changed = tmp_path / "pins.txt"
    changed.write_text(sandbox.BASE_REQUIREMENTS.read_text(encoding="utf-8") + "tqdm==4.66.4\n", encoding="utf-8")
    monkeypatch.setattr(sandbox, "BASE_REQUIREMENTS", changed)
    assert sandbox.base_env_dir() != first


def test_an_unbuildable_base_environment_does_not_stop_a_project(tmp_path, monkeypatch) -> None:
    """A pin that cannot resolve: no base, a warning, and the project still runs."""
    broken = tmp_path / "pins.txt"
    broken.write_text("this-package-does-not-exist-llmxive==0.0.0\n", encoding="utf-8")
    monkeypatch.setattr(sandbox, "BASE_REQUIREMENTS", broken)
    monkeypatch.setenv("LLMXIVE_BASE_ENV_DIR", str(tmp_path / "base"))
    assert sandbox.ensure_base_env() is None
    assert not any(p.name.endswith(".complete") for p in (tmp_path / "base").rglob("*"))
    assert list((tmp_path / "base").iterdir()) == [], "no half-built directory is left behind"
    proj = tmp_path / "projects" / "PROJ-Y"
    (proj / "code").mkdir(parents=True)
    res = sandbox.run_in_venv(
        project_dir=proj, args=["-c", "from llmxive_toolkit import paths; print(paths.root.name)"], timeout_s=120)
    assert res.ok and res.stdout.strip() == "PROJ-Y", res.stdout + res.stderr
