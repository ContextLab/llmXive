"""Helpers every llmXive research project can import. Standard library only.

    from llmxive_toolkit import paths, get_logger

    log = get_logger(__name__)
    out = paths.data("results", "census.csv")   # <project>/data/results/census.csv
    log.info("writing %s", out)                 # the parent directory already exists

Why this exists (measured on 713 projects, 2026-10-11): 654 wrote their own
directory scaffold and 545 their own logging setup -- ``setup_logging`` alone
had 78 different signatures across 290 projects -- and code calling one
project-local variant with another's arguments was the largest group of
helper failures at run time. Tasks that only create directories were rejected
by the verifier 345 times. Neither is research; both are here once.

The functions are deliberately forgiving about how they are called. They are
used by models that have seen many logging helpers and remember none exactly.
"""

from __future__ import annotations

import importlib as _importlib
import logging as _logging
import os as _os
import sys as _sys
from pathlib import Path as _Path

__all__ = ["ProjectPaths", "get_logger", "paths", "project_root", "save_figure", "setup_logging"]

_ROOT_ENV = "LLMXIVE_PROJECT_ROOT"
_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def project_root() -> _Path:
    """The project directory: ``$LLMXIVE_PROJECT_ROOT``, else the nearest
    directory at or above the working directory that has a ``code/`` folder,
    else the working directory."""
    given = _os.environ.get(_ROOT_ENV)
    if given:
        return _Path(given).resolve()
    here = _Path.cwd().resolve()
    for candidate in (here, *here.parents):
        if (candidate / "code").is_dir():
            return candidate
    return here


class ProjectPaths:
    """Paths inside the project. Asking for a path creates its parent directory.

    ``paths.data("raw", "x.csv")`` is ``<project>/data/raw/x.csv`` and
    ``<project>/data/raw/`` exists when it returns. ``paths.data()`` is the
    ``data`` directory itself, created. Nothing here writes a file, and no
    path can leave the project.
    """

    @property
    def root(self) -> _Path:
        return project_root()

    def path(self, *parts: str | _os.PathLike[str]) -> _Path:
        """``<project>/<parts...>``, with the parent directory created."""
        root = self.root
        target = root.joinpath(*(str(p) for p in parts)).resolve()
        if target != root and root not in target.parents:
            raise ValueError(f"{target} is outside the project directory {root}")
        # A name with a suffix is a file: make its folder. Otherwise it is a folder.
        (target.parent if target.suffix else target).mkdir(parents=True, exist_ok=True)
        return target

    def data(self, *parts: str | _os.PathLike[str]) -> _Path:
        return self.path("data", *parts)

    def figures(self, *parts: str | _os.PathLike[str]) -> _Path:
        return self.path("figures", *parts)

    def results(self, *parts: str | _os.PathLike[str]) -> _Path:
        # ``paths.<folder>(x)`` is ``<project>/<folder>/x`` for EVERY folder.
        # This was ``data/results`` until canary 8 (2026-10-11): its task said
        # "write results/paper.md", its test read ``paths.results("paper.md")``,
        # and the two were different files.
        return self.path("results", *parts)

    def code(self, *parts: str | _os.PathLike[str]) -> _Path:
        return self.path("code", *parts)

    def docs(self, *parts: str | _os.PathLike[str]) -> _Path:
        return self.path("docs", *parts)

    def __getattr__(self, name: str):
        """``paths.<folder>(...)`` for any other top-level folder of the project.

        ``paths.outputs("tv_plot.png")``, ``paths.models(...)``, ``paths.logs(...)``:
        the first run that used this module reached for ``paths.outputs``, which
        did not exist, and the stage died on AttributeError. A folder name is
        not worth a failed run.
        """
        if name.startswith("_") or not name.isidentifier():
            raise AttributeError(name)

        def folder(*parts: str | _os.PathLike[str]) -> _Path:
            return self.path(name, *parts)

        folder.__name__ = name
        return folder

    def __repr__(self) -> str:
        return f"ProjectPaths(root={str(self.root)!r})"


paths = ProjectPaths()


def _level(level: object) -> int:
    if isinstance(level, int) and not isinstance(level, bool):
        return level
    named = _logging.getLevelName(str(level).strip().upper())
    return named if isinstance(named, int) else _logging.INFO


def get_logger(name: object = None, level: object = "INFO", log_file: object = None,
               **options: object) -> _logging.Logger:
    """A logger that writes to stderr, and to ``log_file`` when one is given.

    Safe to call any number of times and from every module: handlers are added
    once. ``level`` is a name (``"DEBUG"``) or a number. ``log_file`` is taken
    relative to the project directory. Arguments other helpers of this kind
    take -- ``log_dir``, ``log_path``, ``filename``, ``verbose`` -- are
    understood; anything else is ignored rather than raised on.
    """
    if log_file is None:
        log_file = options.get("log_path") or options.get("filename") or options.get("file")
    log_dir = options.get("log_dir") or options.get("output_dir")
    if log_file is None and log_dir is not None:
        log_file = _Path(str(log_dir)) / "run.log"
    elif log_file is not None and log_dir is not None and not _Path(str(log_file)).is_absolute():
        log_file = _Path(str(log_dir)) / str(log_file)
    if options.get("verbose") is True or options.get("debug") is True:
        level = "DEBUG"

    # setup_logging("DEBUG") / setup_logging(logging.DEBUG): the first argument
    # is a level, not a name.
    if (isinstance(name, int) and not isinstance(name, bool)) or (
            isinstance(name, str) and isinstance(_logging.getLevelName(name.upper()), int)
            and name.upper() in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}):
        level, name = name, None

    number = _level(level)
    root = _logging.getLogger()
    if not any(getattr(h, "_llmxive", False) for h in root.handlers):
        stream = _logging.StreamHandler(_sys.stderr)
        stream.setFormatter(_logging.Formatter(_FORMAT))
        stream._llmxive = True  # type: ignore[attr-defined]
        root.addHandler(stream)
    if root.level == _logging.NOTSET or number < root.level or root.level == _logging.WARNING:
        root.setLevel(number)
    if log_file is not None:
        target = _Path(str(log_file))
        if not target.is_absolute():
            target = project_root() / target
        target.parent.mkdir(parents=True, exist_ok=True)
        wanted = str(target.resolve())
        if not any(getattr(h, "_llmxive_file", None) == wanted for h in root.handlers):
            handler = _logging.FileHandler(target, encoding="utf-8")
            handler.setFormatter(_logging.Formatter(_FORMAT))
            handler._llmxive_file = wanted  # type: ignore[attr-defined]
            root.addHandler(handler)
    logger = _logging.getLogger(str(name) if name else "project")
    logger.setLevel(number)
    return logger


#: The other name this helper is most often written under (290 of 545 projects).
setup_logging = get_logger


def save_figure(*args: object, **options: object) -> _Path:
    """Save a matplotlib figure AND a record of what it shows.

    ``save_figure(fig, paths.figures("tv.png"))`` writes ``figures/tv.png`` and
    ``figures/tv.figure.json`` (titles, axis labels and scales, legend entries,
    and every plotted series with its number of points and its ranges). The
    record is how anyone who cannot open the image can confirm what is in it.
    """
    return _importlib.import_module("llmxive_toolkit.figures").save_figure(*args, **options)
