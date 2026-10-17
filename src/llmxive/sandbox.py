"""Code-execution sandbox for the Implementer + Paper-Implementer.

Without a way to actually *run* the code an LLM writes, every project
ends up as scaffolding that never produces real data, real figures,
or real results — which is exactly what the research reviewers were
flagging. This module gives the agents a deterministic, restricted
sandbox in which to execute scripts and verify their output.

Design constraints:
  - Run inside a per-project venv so requirements.txt is honored without
    polluting the global env. The venv lives OUTSIDE the project, at
    ``<repo>/.llmxive-venvs/<id>`` (see :func:`venv_dir`): it is the
    platform's, and generated code must not be able to see it in its own
    source tree, scan it, or delete it.
  - Cap wall-clock time per script (default 600 s).
  - Cap memory via shell ulimit on POSIX (best-effort; not a
    security boundary — the agents are trusted code we wrote, this
    is a quality / correctness boundary).
  - Capture stdout + stderr + exit code; surface them back to the
    caller.
  - No network restrictions: GHA runners need to download datasets
    from public URLs. The constitution forbids generating new
    secrets or contacting non-listed services.

Usage:
    result = run_python_script(
        project_dir=Path("projects/PROJ-002-..."),
        script_relpath="code/scripts/figure_1.py",
        timeout_s=600,
    )
    if result.ok:
        print(result.stdout)
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    ok: bool
    returncode: int
    stdout: str
    stderr: str
    duration_s: float
    timed_out: bool = False


#: Directory, beside ``projects/``, that holds every per-project venv.
VENV_ROOT_NAME = ".llmxive-venvs"


def venv_root(project_dir: Path) -> Path:
    """The directory that holds this project's venv.

    ``<repo>/.llmxive-venvs`` for a ``projects/<id>`` directory, shared with the
    other projects so one sweep can bound disk. Any other layout (a bare
    workspace) gets a root of its own beside it, ``.<name>.llmxive-venvs``, so
    unrelated workspaces that merely share a parent never evict each other.
    Absolute, and never inside ``project_dir``.
    """
    here = Path(os.path.abspath(project_dir))
    if here.parent.name == "projects":
        return here.parent.parent / VENV_ROOT_NAME
    return here.parent / f".{here.name}{VENV_ROOT_NAME}"


def venv_dir(project_dir: Path) -> Path:
    """Where this project's venv lives: OUTSIDE the project, by design.

    It used to be ``projects/<id>/code/.venv`` — inside the source tree the
    generated analysis owns. Every scan of ``code/`` then had to remember to
    skip it (the fabrication guard once reported 143 false positives from a
    single venv), and generated code met it too. Observed, PROJ-9999 totient
    canary, 2026-10-10: the project's own prohibited-import test walked
    ``code/**/*.py``, found ``scipy`` in site-packages, and the implementer
    "fixed" the false failure by writing a ``conftest.py`` whose
    ``pytest_configure`` runs ``shutil.rmtree("code/.venv")``. Pytest was
    running FROM that venv, so every later import died ``ModuleNotFoundError:
    No module named 'numpy'``; the run-book could never pass, the round cap
    was exhausted and the project was kicked back to ``clarified``.

    The interpreter that runs a project's code is the platform's, not the
    project's. Keeping it out of the project removes the whole class: nothing
    the project scans, cleans or rewrites under its own directory can reach it.
    """
    return venv_root(project_dir) / Path(os.path.abspath(project_dir)).name


def _legacy_venv(project_dir: Path) -> Path:
    """The pre-move location, removed on sight (a venv is a rebuildable cache)."""
    return Path(project_dir) / "code" / ".venv"


#: Pinned packages every project venv can import without declaring them.
BASE_REQUIREMENTS = Path(__file__).resolve().parent / "execution" / "base_requirements.txt"
#: Name of the file, in a project venv's site-packages, that links the base
#: environment and the project toolkit onto its import path.
_LINK_PTH = "llmxive_platform.pth"


def base_env_dir() -> Path:
    """Where the shared base environment for THIS interpreter and pin set lives.

    One directory per (Python minor version, content of the pin file), under
    ``$LLMXIVE_BASE_ENV_DIR`` or ``~/.cache/llmxive/base-env``. It is outside
    every repository, so one build serves every project and every checkout on
    the machine, and a changed pin file simply gets a new directory.
    """
    import hashlib

    home = os.environ.get("LLMXIVE_BASE_ENV_DIR") or str(Path.home() / ".cache" / "llmxive" / "base-env")
    digest = hashlib.sha256(BASE_REQUIREMENTS.read_bytes()).hexdigest()[:12]
    return Path(home) / f"py{sys.version_info.major}{sys.version_info.minor}-{digest}"


def ensure_base_env() -> Path | None:
    """Build the shared base environment once; return it, or ``None``.

    Measured, 2026-10-11: a third-party module missing from the venv was 16.7%
    of all failing run-book commands (261 of 1,566, in 111 projects), and the
    modules were the ordinary ones -- pytest 31, pandas 26, numpy 16. Each cost
    a fix round: fail, have the import auto-declared, reinstall, run again. The
    base environment makes those importable from the first run.

    It is a plain ``pip install --target`` directory, not a venv: project venvs
    reach it through a ``.pth`` line, so it is installed once per machine
    instead of once per project (a project venv was up to 1.2 GB). Built in a
    temporary sibling and renamed into place, so a half-built directory is
    never used and two builders cannot corrupt each other.

    ``None`` means it could not be built (no network, a pin that no longer
    resolves). That is logged and survivable: a project that DECLARES its
    dependencies still gets them from its own requirements.
    """
    import tempfile

    target = base_env_dir()
    if (target / ".complete").is_file():
        return target
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=target.name + ".building-", dir=target.parent))
    except OSError as exc:
        logger.warning("base environment: cannot create %s: %s", target.parent, exc)
        return None
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "--disable-pip-version-check",
             "--target", str(staging), "-r", str(BASE_REQUIREMENTS)],
            check=False, capture_output=True, text=True,
        )
        if proc.returncode != 0:
            logger.warning(
                "base environment: pip failed (rc=%s); projects run with their own "
                "requirements only. tail: %s", proc.returncode, (proc.stderr or "")[-400:])
            return None
        (staging / ".complete").write_text(BASE_REQUIREMENTS.read_text(encoding="utf-8"), encoding="utf-8")
        try:
            staging.rename(target)
        except OSError:
            # Another builder finished first; theirs is as good as ours.
            if not (target / ".complete").is_file():
                raise
        return target
    except OSError as exc:
        logger.warning("base environment: build failed: %s", exc)
        return None
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _link_platform_paths(venv: Path) -> None:
    """Put the project toolkit and the base environment on the venv's path.

    Written as a ``.pth`` file in the venv's own site-packages, so it holds for
    every way the venv's python is started. ``.pth`` entries come AFTER
    site-packages on ``sys.path``: a package the project installed itself
    always wins over the base copy.
    """
    from llmxive.project_toolkit import TOOLKIT_NAME, TOOLKIT_PATH

    lines = [str(TOOLKIT_PATH)]
    base = ensure_base_env()
    if base is not None:
        lines.append(str(base))
    # A ``.pth`` line that starts with ``import`` is executed at interpreter
    # start. Loading the toolkit there BY FILE puts the PLATFORM's module in
    # ``sys.modules``, so a copy a project left on its own path is never the
    # one imported. No path order can do this: the script's directory, and the
    # package root run_in_venv puts first, both outrank PYTHONPATH's tail.
    package = TOOLKIT_PATH / TOOLKIT_NAME
    lines.append(
        "import importlib.util as _u, sys as _s; "
        f"_p = _u.spec_from_file_location({TOOLKIT_NAME!r}, {str(package / '__init__.py')!r}, "
        f"submodule_search_locations=[{str(package)!r}]); "
        f"_m = _u.module_from_spec(_p); _s.modules[{TOOLKIT_NAME!r}] = _m; _p.loader.exec_module(_m)"
    )
    body = "\n".join(lines) + "\n"
    for site in venv.glob("lib/python*/site-packages"):
        pth = site / _LINK_PTH
        try:
            if not pth.is_file() or pth.read_text(encoding="utf-8") != body:
                pth.write_text(body, encoding="utf-8")
        except OSError as exc:
            logger.warning("could not link platform paths into %s: %s", site, exc)


def ensure_venv(project_dir: Path) -> Path:
    """Create or reuse the project's venv (:func:`venv_dir`). Returns the python path.

    Re-runs `pip install -r requirements.txt` whenever requirements.txt
    has been modified since the last sync (tracked via a side-car
    .venv/.requirements_mtime file). This handles the common ordering
    problem where the venv is created before requirements.txt exists
    (lazy creation by the first execute:true script), so pip install
    becomes a no-op and every later script hits ModuleNotFoundError.
    """
    venv = venv_dir(project_dir)
    py = venv / "bin" / "python"
    needs_create = not py.exists()
    legacy = _legacy_venv(project_dir)
    if legacy.is_dir() and not legacy.is_symlink():
        shutil.rmtree(legacy, ignore_errors=True)
    if needs_create:
        # Bound runner disk BEFORE building another 1.2 GB venv: one advance worker
        # runs up to 10 projects per job and the venvs used to accumulate until the
        # disk died ([Errno 28] No space left on device). Only OTHER projects' venvs
        # are evicted — this project's is preserved and reused across ticks.
        evict_other_project_venvs(project_dir)
        venv.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv)],
            check=True,
            capture_output=True,
        )
    _link_platform_paths(venv)
    from llmxive.project_files import requirements_paths

    # EVERY manifest the project has. Only one of code/requirements.txt and
    # requirements.txt used to be read; 31 failing run-book commands in the
    # corpus imported a module the project had declared in the other one.
    manifests = requirements_paths(project_dir)
    if manifests:
        mtime_file = venv / ".requirements_mtime"
        try:
            last_synced = float(mtime_file.read_text().strip()) if mtime_file.exists() else 0.0
        except ValueError:
            last_synced = 0.0
        cur_mtime = max(req.stat().st_mtime for req in manifests)
        if cur_mtime > last_synced or needs_create:
            for req in manifests:
                _resilient_pip_install(py, req)
            try:
                mtime_file.write_text(f"{cur_mtime}\n", encoding="utf-8")
            except OSError:
                pass
    return py


def _resilient_pip_install(py: Path, req: Path) -> None:
    """Install ``requirements.txt`` tolerant of individual un-installable lines.

    A SINGLE bad requirement makes a batch ``pip install -r`` abort the WHOLE
    set, leaving even ``numpy`` uninstalled — every analysis script then dies
    ``ModuleNotFoundError: No module named 'numpy'`` and ``execute_and_gate``
    can NEVER pass (the live PROJ-262 stall: a run-book that imports a local
    package ``models`` or matplotlib's ``mpl_toolkits`` namespace submodule had
    those names auto-added to requirements.txt as if they were PyPI packages,
    so `pip install -r` failed and the real deps never landed).

    Try the fast batch install first; on failure, DIAGNOSE which individual
    requirement lines are un-installable, then RE-RUN the batch on the survivors
    so the resolver picks a MUTUALLY-CONSISTENT set. The old fallback left each
    package installed by a SEPARATE ``pip install`` invocation, so pip could land
    ABI-incompatible binaries (an unpinned ``numpy`` 2.x next to a ``pandas`` /
    ``scipy`` wheel built for numpy 1.x) → ``cannot import name '__version__' from
    numpy`` / ``pandas.compat.numpy`` import breaks that no fix-round can repair
    (the live PROJ-262/300 ABI stall). A single batch install of the survivors
    keeps the whole scientific stack version-consistent (issue #1139 RC-C).
    """
    if _pip_install(py, ["-r", str(req)]).returncode == 0:
        return
    lines = [
        raw.split("#", 1)[0].strip()
        for raw in req.read_text(encoding="utf-8", errors="replace").splitlines()
    ]
    lines = [ln for ln in lines if ln]
    # Diagnose the genuinely un-installable line(s) individually (a local module
    # or a namespace submodule wrongly auto-added — the PROJ-262 bad-line case).
    failed = [pkg for pkg in lines if _pip_install(py, [pkg]).returncode != 0]
    survivors = [ln for ln in lines if ln not in failed]
    if failed:
        logger.warning(
            "batch `pip install -r %s` failed; skipped %d un-installable line(s): "
            "%s", req, len(failed), failed,
        )
    # RECONCILE: one final BATCH install of the survivors so pip's resolver
    # selects a single ABI-consistent version set (never the per-package mix that
    # broke the numpy/pandas/scipy ABI). Best-effort — each survivor already
    # installed individually above, so this only reconciles versions.
    if survivors:
        recon = _pip_install(py, survivors)
        if recon.returncode != 0:
            logger.warning(
                "pip: survivor reconcile install returned rc=%s (deps landed "
                "per-package; a residual version skew may remain). tail: %s",
                recon.returncode, (recon.stderr or "")[-300:],
            )


def _pip_install(py: Path, args: list[str]) -> subprocess.CompletedProcess:
    """Run ``<py> -m pip install -q <args>`` (never raises; caller checks rc)."""
    return subprocess.run(
        [str(py), "-m", "pip", "install", "-q", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _ensure_code_package(project_dir: Path) -> None:
    """Make ``code/`` an importable package so ``from code.X import Y`` works.

    ``code`` is also a STDLIB module, so without a real ``code/__init__.py`` the
    import resolves to the stdlib and dies "'code' is not a package" (PROJ-341). An
    empty ``__init__.py`` turns the project's ``code/`` into a regular package which,
    with the project root on PYTHONPATH (ahead of the stdlib), shadows it. Harmless
    to the 334 projects using bare ``from <subpkg>`` imports. Best-effort; never
    raises — a create failure just leaves the pre-existing behaviour."""
    code = project_dir / "code"
    if not code.is_dir():
        return
    init = code / "__init__.py"
    if not init.exists():
        try:
            init.write_text("", encoding="utf-8")
        except OSError as exc:
            logger.warning("could not create %s: %s", init, exc)


def _analysis_env(project_dir: Path, base_env: dict[str, str]) -> dict[str, str]:
    """``base_env`` plus the project root AND ``code/`` on PYTHONPATH.

    Analysis code imports its own modules two ways and BOTH must resolve: the
    project root enables ``from code.X import Y`` (with :func:`_ensure_code_package`),
    and ``code/`` enables bare ``from <subpkg> import Y``. Prepended so they win over
    any inherited PYTHONPATH. Fixes the ModuleNotFoundError class that dominated the
    execution failures (25 of them) — the analysis crashing on its OWN package."""
    env = dict(base_env)
    # Where llmxive_toolkit.paths anchors: the project, whatever the cwd is.
    env["LLMXIVE_PROJECT_ROOT"] = str(project_dir.resolve())
    from llmxive.project_files import SOURCE_DIRS

    # Prefer the code workspace over same-named project-root scaffolding. With
    # root first, an empty root/src package hides implemented code/src modules.
    # Python still searches the entry script's own directory before PYTHONPATH.
    from llmxive.project_toolkit import TOOLKIT_PATH

    # The platform's toolkit comes FIRST. Canary 8 wrote its own
    # ``llmxive_toolkit/`` "shim" at the project root; from PYTHONPATH it beat
    # the real one (which was only on the venv's .pth) and resolved every path
    # against the working directory instead of the project.
    parts = [str(TOOLKIT_PATH),
             *(str((project_dir / root).resolve()) for root in SOURCE_DIRS), str(project_dir.resolve())]
    if env.get("PYTHONPATH"):
        parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def _venv_environment(project_dir: Path, py: Path) -> dict[str, str]:
    """The environment EVERY project process runs in: analysis paths plus the venv.

    The venv's ``bin`` is first on PATH and ``VIRTUAL_ENV`` is set, so a child
    the project starts (``python``, ``pytest``, ``bash run_all.sh``) is in the
    same environment as its parent. Only the shell runner used to do this; a
    Python script that started ``bash code/run_all.sh`` got the system
    interpreter for everything below it.
    """
    env = _analysis_env(project_dir, analysis_environment(project_dir))
    env["PATH"] = str(py.parent) + os.pathsep + env.get("PATH", "")
    env["VIRTUAL_ENV"] = str(py.parent.parent)
    return env


def _explicit_script_package_root(
    project_dir: Path, args: list[str], run_cwd: Path,
) -> Path | None:
    """Honor the package/workspace of an explicitly selected Python entry file.

    Generic/module invocations retain the normal source-root order. A file such
    as ``src/cli.py`` must import its own regular ``src`` package rather than a
    same-named stale package under ``code/src``. Stop at the code workspace even
    when its compatibility ``__init__.py`` exists. Non-package entry files
    (for example ``tests/check.py`` without ``tests/__init__.py``) use their
    root/code workspace, matching artifact import validation.
    """
    if not args or args[0].startswith("-") or not args[0].endswith(".py"):
        return None
    root = project_dir.resolve()
    script = (run_cwd / args[0]).resolve()
    if not script.is_relative_to(root) or not script.is_file():
        return None
    relative = script.relative_to(root)
    boundary = root / "code" if relative.parts[0] == "code" else root
    package_root = script.parent
    while package_root != boundary and (package_root / "__init__.py").is_file():
        package_root = package_root.parent
    return package_root if package_root != script.parent else boundary


def analysis_environment(workspace: Path) -> dict[str, str]:
    """Environment for generated research code, without the orchestrator's credentials."""
    allowed = ("PATH", "LANG", "LC_ALL", "SYSTEMROOT", "WINDIR", "SSL_CERT_FILE", "SSL_CERT_DIR")
    env = {key: os.environ[key] for key in allowed if key in os.environ}
    home = workspace / ".runtime-home"
    home.mkdir(parents=True, exist_ok=True)
    env.update(HOME=str(home.resolve()), PYTHONNOUSERSITE="1", PYTHONUNBUFFERED="1")
    return env


def run_in_venv(
    *,
    project_dir: Path,
    args: list[str],
    timeout_s: int = 600,
    cwd: Path | None = None,
    extra_env: dict[str, str] | None = None,
) -> ExecutionResult:
    """Run ``python <args...>`` inside the project's venv. Returns capture.

    General form of :func:`run_python_script` (which guards a single-file
    run): ``args`` is whatever follows ``python`` — e.g. ``["code/x.py"]``
    or ``["-c", "import code.foo"]``. Used by the analysis-execution stage
    to run the project's quickstart run-book (mix of script + ``-c`` lines)
    in the per-project venv. cwd defaults to ``project_dir`` so scripts
    write to ``data/`` / ``figures/`` with project-root-relative paths.
    """
    import time

    # ABSOLUTE but SYMLINK-PRESERVING. The subprocess runs with cwd=project_dir,
    # so a relative venv-python path would resolve against the changed cwd and
    # vanish (FileNotFoundError) — hence make it absolute. But NEVER ``.resolve()``
    # it: a venv's ``bin/python`` is a SYMLINK to the base interpreter, and
    # resolving it follows the symlink to e.g. ``/opt/homebrew/.../python3.11`` —
    # the SYSTEM python, which lacks the per-project venv's site-packages. That
    # silently ran every project's analysis against the base interpreter (niche
    # deps like ``database_knotinfo`` → ModuleNotFoundError; common ones happened
    # to be globally present, masking the bug). ``os.path.abspath`` makes it
    # cwd-independent WITHOUT dereferencing the venv symlink.
    run_cwd = Path(cwd or project_dir).resolve()
    if not run_cwd.is_relative_to(project_dir.resolve()):
        return ExecutionResult(False, -1, "", "working directory escapes the project directory", 0.0)
    py = Path(os.path.abspath(ensure_venv(project_dir)))
    _ensure_code_package(project_dir)
    env = _venv_environment(project_dir, py)
    package_root = _explicit_script_package_root(project_dir, args, run_cwd)
    if package_root is not None:
        paths = env["PYTHONPATH"].split(os.pathsep)
        env["PYTHONPATH"] = os.pathsep.join(
            [str(package_root), *(path for path in paths if path != str(package_root))]
        )
    env["PYTHONUNBUFFERED"] = "1"
    if extra_env:
        env.update(extra_env)
    started = time.time()
    timed_out = False
    try:
        proc = subprocess.run(
            [str(py), *args],
            cwd=str(run_cwd),
            timeout=timeout_s,
            capture_output=True,
            text=True,
            env=env,
        )
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        rc = -1
        out = (exc.stdout or b"").decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = (
            (exc.stderr or b"").decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        ) + f"\n[TIMEOUT after {timeout_s}s]"
    elapsed = time.time() - started
    return ExecutionResult(
        ok=rc == 0, returncode=rc, stdout=out, stderr=err,
        duration_s=elapsed, timed_out=timed_out,
    )


def run_python_script(
    *,
    project_dir: Path,
    script_relpath: str,
    script_args: list[str] | None = None,
    timeout_s: int = 600,
    cwd: Path | None = None,
    extra_env: dict[str, str] | None = None,
) -> ExecutionResult:
    """Run a script with literal argv inside the project's venv. Returns capture."""
    if script_args is None:
        script_args = []
    if (not isinstance(script_args, list)
            or any(not isinstance(arg, str) or "\0" in arg for arg in script_args)):
        return ExecutionResult(ok=False, returncode=-1, stdout="",
            stderr="script args must be a list of strings without null bytes", duration_s=0.0)
    script = (project_dir / script_relpath).resolve()
    if not script.is_relative_to(project_dir.resolve()):
        return ExecutionResult(ok=False, returncode=-1, stdout="",
                               stderr="script escapes the project directory", duration_s=0.0)
    if not script.exists():
        return ExecutionResult(
            ok=False,
            returncode=-1,
            stdout="",
            stderr=f"script not found: {script}",
            duration_s=0.0,
        )
    # Pre-execution sanity check: refuse to run anything whose first
    # non-blank line looks like a unified-diff hunk header. The
    # implementer occasionally returns `--- a/foo.py\n+++ b/foo.py\n
    # @@ ...` as the file contents, which produces a SyntaxError that
    # wastes a sandbox run. Catching it here gives the caller a
    # clearer failure message.
    try:
        head = script.read_text(encoding="utf-8", errors="replace")[:200]
    except OSError:
        head = ""
    if head.lstrip().startswith(("--- a/", "+++ b/", "@@ ")):
        return ExecutionResult(
            ok=False,
            returncode=-1,
            stdout="",
            stderr=(
                f"script appears to be a unified diff fragment, not "
                f"valid source. First 200 chars: {head!r}"
            ),
            duration_s=0.0,
        )
    # Run with cwd=project_dir so scripts write to data/raw/, figures/ etc.
    # with project-root-relative paths (delegated to run_in_venv, the SSoT
    # for the venv subprocess invocation).
    return run_in_venv(
        project_dir=project_dir,
        args=[str(script), *script_args],
        timeout_s=timeout_s,
        cwd=cwd,
        extra_env=extra_env,
    )


def run_shell_script(
    *, project_dir: Path, script_relpath: str,
    script_args: list[str] | None = None, timeout_s: int = 600,
    interpreter: str = "bash",
) -> ExecutionResult:
    """Run a project-local shell script with literal argv and the project venv.

    This has the same credential-stripped environment as Python research code.
    It is an execution/correctness boundary, not an OS filesystem sandbox.
    """
    import signal
    import time

    script_args = [] if script_args is None else script_args
    if (not isinstance(script_args, list)
            or any(not isinstance(arg, str) or "\0" in arg for arg in script_args)):
        return ExecutionResult(False, -1, "", "script args must be a list of strings without null bytes", 0.0)
    script = (project_dir / script_relpath).resolve()
    if (not script.is_relative_to(project_dir.resolve())
            or script.suffix != ".sh" or not script.is_file()):
        return ExecutionResult(False, -1, "", "shell script must be an existing project-local .sh file", 0.0)
    executable = shutil.which(interpreter) if interpreter in {"bash", "sh"} else None
    if executable is None:
        return ExecutionResult(False, -1, "", "supported shell interpreter unavailable", 0.0)
    py = Path(os.path.abspath(ensure_venv(project_dir)))
    _ensure_code_package(project_dir)
    env = _venv_environment(project_dir, py)
    started = time.monotonic()
    proc = subprocess.Popen(
        [executable, str(script), *script_args], cwd=project_dir.resolve(),
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        start_new_session=True,
    )
    timed_out = False
    try:
        out, err = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        # Shell wrappers spawn Python children. Stop the process group, so a
        # timeout cannot leave an analysis writing artifacts in the background.
        if os.name == "posix":
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:  # pragma: no cover - CI and production are POSIX
            proc.kill()
        out, err = proc.communicate()
        err += f"\n[TIMEOUT after {timeout_s}s]"
    return ExecutionResult(
        not timed_out and proc.returncode == 0,
        -1 if timed_out else proc.returncode, out, err,
        time.monotonic() - started, timed_out,
    )


def _pytest(project_dir: Path, argv: list[str], *, cwd: Path, timeout_s: int) -> ExecutionResult:
    import time
    # ABSOLUTE but SYMLINK-PRESERVING (same rationale as run_in_venv): the
    # subprocess below runs with a changed cwd, so a RELATIVE venv-python path
    # (e.g. '.llmxive-venvs/PROJ-x/bin/python' when project_dir itself is
    # relative) would resolve against that cwd and vanish — FileNotFoundError.
    # ``os.path.abspath`` anchors it to the ORIGINAL cwd without dereferencing
    # the venv's bin/python symlink.
    py = Path(os.path.abspath(ensure_venv(project_dir)))
    _ensure_code_package(project_dir)
    started = time.time()
    timed_out = False
    try:
        proc = subprocess.run(
            [str(py), "-m", "pytest", *argv],
            cwd=str(cwd),
            timeout=timeout_s,
            capture_output=True,
            text=True,
            env=_venv_environment(project_dir, py),
        )
        rc = proc.returncode
        out = proc.stdout
        err = proc.stderr
    except subprocess.TimeoutExpired:
        timed_out = True
        rc = -1
        out = ""
        err = f"[TIMEOUT after {timeout_s}s]"
    return ExecutionResult(
        ok=rc == 0,
        returncode=rc,
        stdout=out,
        stderr=err,
        duration_s=time.time() - started,
        timed_out=timed_out,
    )


def run_pytest(
    *,
    project_dir: Path,
    test_path: str = "tests/",
    timeout_s: int = 600,
) -> ExecutionResult:
    """Run pytest inside the project's venv, from the project's ``code/``."""
    return _pytest(project_dir, [test_path, "-x", "--tb=short", "-q"],
                   cwd=project_dir / "code", timeout_s=timeout_s)


def run_pytest_file(
    *,
    project_dir: Path,
    test_relpath: str,
    script_args: list[str] | None = None,
    timeout_s: int = 600,
) -> ExecutionResult:
    """Run ONE test module with pytest, from the project root, and name each test.

    ``python tests/test_x.py`` exits 0 having run nothing: a test module has no
    entry point. This is how a test file is actually executed, so its log holds
    a pytest session (``-v``: one PASSED/FAILED line per test) and its exit
    code means what the tests found. The project is the rootdir and no cache
    directory is written, so the run leaves nothing behind in the project.
    """
    if script_args is None:
        script_args = []
    if (not isinstance(script_args, list)
            or any(not isinstance(arg, str) or "\0" in arg for arg in script_args)):
        return ExecutionResult(ok=False, returncode=-1, stdout="",
            stderr="script args must be a list of strings without null bytes", duration_s=0.0)
    root = project_dir.resolve()
    test = (project_dir / test_relpath).resolve()
    if not test.is_relative_to(root):
        return ExecutionResult(ok=False, returncode=-1, stdout="",
                               stderr="test file escapes the project directory", duration_s=0.0)
    if not test.is_file():
        return ExecutionResult(ok=False, returncode=-1, stdout="",
                               stderr=f"test file not found: {test}", duration_s=0.0)
    return _pytest(
        project_dir,
        [str(test.relative_to(root)), "-v", "--tb=short", "-p", "no:cacheprovider",
         f"--rootdir={root}", *script_args],
        cwd=root, timeout_s=timeout_s,
    )


def run_pytest_modules(
    *, project_dir: Path, test_relpaths: list[str], timeout_s: int = 300,
) -> ExecutionResult:
    """Run several of the project's test modules in one pytest session.

    Same invocation as :func:`run_pytest_file` (``-v``, project as rootdir, no
    cache directory), for a harness that needs the outcome of every test at
    one moment: before and after an implementer attempt.
    """
    root = project_dir.resolve()
    tests = [(project_dir / rel).resolve() for rel in test_relpaths]
    if not tests or any(not t.is_relative_to(root) or not t.is_file() for t in tests):
        return ExecutionResult(ok=False, returncode=-1, stdout="",
                               stderr="test modules must be existing files inside the project", duration_s=0.0)
    return _pytest(
        project_dir,
        [*(str(t.relative_to(root)) for t in tests), "-v", "--tb=short", "-p", "no:cacheprovider",
         f"--rootdir={root}"],
        cwd=root, timeout_s=timeout_s,
    )


def cleanup_venv(project_dir: Path) -> None:
    """Remove the project's venv (used by tests)."""
    for venv in (venv_dir(project_dir), _legacy_venv(project_dir)):
        if venv.exists():
            shutil.rmtree(venv, ignore_errors=True)


def evict_other_project_venvs(project_dir: Path) -> int:
    """Delete every OTHER project's venv, keeping this project's.

    A project venv is up to 1.2 GB (torch et al.) and ONE advance worker runs up to
    ``--max-tasks 10`` projects in a single job, so they piled up until the runner
    ran out of disk — `Submission Intake` died with ``[Errno 28] No space left on
    device``. (``cleanup_venv`` existed but was never called from anywhere.)

    Bounding disk to a single venv costs nothing real: a CI job starts on a fresh
    runner, and the CURRENT project's venv is deliberately preserved so it is still
    reused across ticks within the job. Returns the number of venvs removed.
    """
    mine = venv_dir(project_dir)
    removed = 0
    root = venv_root(project_dir)
    if root.is_dir():
        for other in root.iterdir():
            if other.is_dir() and not other.is_symlink() and other != mine:
                shutil.rmtree(other, ignore_errors=True)
                removed += 1
    # Venvs left where they used to live, inside sibling projects.
    projects_root = Path(os.path.abspath(project_dir)).parent
    if projects_root.is_dir():
        for sibling in projects_root.iterdir():
            legacy = _legacy_venv(sibling)
            if sibling.is_dir() and legacy.is_dir() and not legacy.is_symlink():
                shutil.rmtree(legacy, ignore_errors=True)
                removed += 1
    if removed:
        logger.info(
            "evicted %d other project venv(s) to bound runner disk (keeping %s)",
            removed, project_dir.name,
        )
    return removed


__all__ = [
    "BASE_REQUIREMENTS",
    "VENV_ROOT_NAME",
    "ExecutionResult",
    "base_env_dir",
    "cleanup_venv",
    "ensure_base_env",
    "ensure_venv",
    "evict_other_project_venvs",
    "run_pytest",
    "run_python_script",
    "run_shell_script",
    "venv_dir",
    "venv_root",
]
