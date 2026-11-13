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
    assert tk.paths.results("a.json") == tmp_path.resolve() / "results" / "a.json"
    # Every paths.<folder>(x) is <project>/<folder>/x: a task that says
    # "write results/paper.md" and code that asks for paths.results("paper.md")
    # must mean the same file (canary 8, 2026-10-11).
    for folder in ("data", "figures", "results", "docs", "code", "outputs", "logs"):
        assert getattr(tk.paths, folder)("x.txt") == tmp_path.resolve() / folder / "x.txt"
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
    assert (project / "results" / "totals.csv").read_text(encoding="utf-8").split() == ["n", "0", "1", "2", "3"]
    assert "wrote results/totals.csv" in (project / "logs" / "run.log").read_text(encoding="utf-8")


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


def test_any_top_level_folder_is_a_path_helper(tmp_path, monkeypatch) -> None:
    """Canary, 2026-10-11: `paths.outputs("tv_plot.png")` raised AttributeError."""
    tk = _toolkit(monkeypatch, tmp_path)
    out = tk.paths.outputs("tv_plot.png")
    assert out == tmp_path.resolve() / "outputs" / "tv_plot.png" and out.parent.is_dir()
    assert tk.paths.models() == tmp_path.resolve() / "models" and tk.paths.models().is_dir()
    with pytest.raises(ValueError, match="outside the project"):
        tk.paths.outputs("..", "..", "x.txt")
    with pytest.raises(AttributeError):
        tk.paths._private  # noqa: B018


# --- a project cannot replace the toolkit (canary 8, 2026-10-11) -------------
#
# The implementer wrote `llmxive_toolkit/__init__.py`, "a minimal shim", at the
# project root. From PYTHONPATH it beat the platform's module and resolved
# every path against the working directory.

SHIM = "class _P:\n    def results(self, *parts):\n        raise RuntimeError('the shim was imported')\n\n\npaths = _P()\n"


@pytest.mark.parametrize("rel, copy", [
    ("llmxive_toolkit/__init__.py", True), ("llmxive_toolkit/paths.py", True),
    ("code/llmxive_toolkit/__init__.py", True), ("code/llmxive_toolkit.py", True),
    ("llmxive_toolkit.py", True), ("code/toolkit.py", False),
    ("code/my_llmxive_toolkit_notes.md", False), ("tests/test_llmxive_toolkit_use.py", False),
])
def test_what_counts_as_a_copy_of_the_toolkit(rel: str, copy: bool) -> None:
    from llmxive.project_toolkit import is_toolkit_copy

    assert is_toolkit_copy(rel) is copy


@pytest.mark.parametrize("where", ["llmxive_toolkit/__init__.py", "code/llmxive_toolkit/__init__.py",
                                   "code/llmxive_toolkit.py"])
def test_the_platform_toolkit_wins_over_a_copy_already_in_the_project(project: Path, where: str) -> None:
    shim = project / where
    shim.parent.mkdir(parents=True, exist_ok=True)
    shim.write_text(SHIM, encoding="utf-8")
    (project / "code" / "use.py").write_text(
        "import llmxive_toolkit\nfrom llmxive_toolkit import paths\n"
        "print(paths.results('paper.md').relative_to(paths.root))\n", encoding="utf-8")
    try:
        res = sandbox.run_in_venv(project_dir=project, args=["code/use.py"], timeout_s=300)
    finally:
        shim.unlink()
    assert res.ok, res.stdout + res.stderr
    assert res.stdout.strip() == "results/paper.md"


def test_the_implementer_refuses_to_write_a_copy_of_the_toolkit(tmp_path: Path, capsys) -> None:
    from types import SimpleNamespace

    import yaml

    from llmxive.backends.base import ChatResponse
    from llmxive.speckit.implement_cmd import ImplementerAgent

    proj = tmp_path / "projects/PROJ-908-shim"
    feature = proj / "specs/001-study"
    feature.mkdir(parents=True)
    tasks = feature / "tasks.md"
    tasks.write_text("- [ ] T001 Write code/lib.py\n", encoding="utf-8")
    document = {"task_id": "T001", "verdict": "completed", "artifacts": [
        {"path": "llmxive_toolkit/__init__.py", "contents": SHIM},
        {"path": "code/lib.py", "contents": "X = 1\n"}]}
    ImplementerAgent().write_artifacts(
        SimpleNamespace(project_dir=proj, project_id=proj.name),
        {"tasks_path": str(tasks), "feature_dir": str(feature),
         "next_task_id": "T001", "all_complete": False},
        ChatResponse(text=yaml.safe_dump(document), model="test", backend="dartmouth"))
    assert not (proj / "llmxive_toolkit").exists()
    assert (proj / "code/lib.py").is_file()
    assert "provided by the platform" in capsys.readouterr().out


def test_save_figure_writes_the_image_and_what_it_shows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """2026-10-11: a task requiring "visual verification of the plot" was
    rejected on all nine attempts, because nothing a reviewer could read said
    what the image contained."""
    import json

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    (tmp_path / "code").mkdir()
    toolkit = _toolkit(monkeypatch, tmp_path)
    fig, ax = plt.subplots()
    ax.plot([1000, 10000, 100000], [0.5, 0.25, 0.125], label="Unconditional TV")
    ax.plot([1000, 10000, 100000], [0.4, float("nan"), 0.1], label="Conditional TV")
    ax.scatter([1, 2], [3, 4], label="checks")
    ax.set_xscale("log")
    ax.set_xlabel("N")
    ax.set_ylabel("TV distance")
    ax.set_title("p = 5")
    ax.legend()
    image = toolkit.save_figure(fig, toolkit.paths.figures("tv_p5.png"), dpi=60)
    plt.close(fig)
    assert image == tmp_path / "figures/tv_p5.png" and image.stat().st_size > 1000
    record = json.loads((tmp_path / "figures/tv_p5.figure.json").read_text(encoding="utf-8"))
    assert record["image"] == "tv_p5.png" and record["written_by"] == "llmxive_toolkit.save_figure"
    (axes,) = record["axes"]
    assert (axes["title"], axes["xlabel"], axes["ylabel"], axes["xscale"], axes["yscale"]) == (
        "p = 5", "N", "TV distance", "log", "linear")
    assert axes["legend"] == ["Unconditional TV", "Conditional TV", "checks"]
    first, second, points = axes["series"]
    assert first == {"kind": "line", "label": "Unconditional TV", "points": 3,
                     "x_min": 1000.0, "x_max": 100000.0, "y_min": 0.125, "y_max": 0.5}
    assert second["points"] == 2 and second["y_min"] == 0.1  # the NaN is not a point
    assert points["kind"] == "points" and points["points"] == 2
    # The current figure, and a path relative to the project.
    plt.figure()
    plt.bar(["a", "b"], [2, 5], label="counts")
    toolkit.save_figure("figures/bars.png")
    plt.close("all")
    bars = json.loads((tmp_path / "figures/bars.figure.json").read_text(encoding="utf-8"))["axes"][0]["series"]
    assert bars == [{"kind": "bars", "label": "counts", "points": 2, "x_min": 0.0, "x_max": 1.0, "y_min": 2.0, "y_max": 5.0}]
    with pytest.raises(TypeError, match="needs the path"):
        toolkit.save_figure(fig)
