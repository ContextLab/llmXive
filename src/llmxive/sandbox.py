"""Code-execution sandbox for the Implementer + Paper-Implementer.

Without a way to actually *run* the code an LLM writes, every project
ends up as scaffolding that never produces real data, real figures,
or real results — which is exactly what the research reviewers were
flagging. This module gives the agents a deterministic, restricted
sandbox in which to execute scripts and verify their output.

Design constraints:
  - Run inside a per-project venv at projects/<id>/code/.venv so
    requirements.txt is honored without polluting the global env.
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


def ensure_venv(project_dir: Path) -> Path:
    """Create or reuse the project's code/.venv. Returns the python path.

    Re-runs `pip install -r requirements.txt` whenever requirements.txt
    has been modified since the last sync (tracked via a side-car
    .venv/.requirements_mtime file). This handles the common ordering
    problem where the venv is created before requirements.txt exists
    (lazy creation by the first execute:true script), so pip install
    becomes a no-op and every later script hits ModuleNotFoundError.
    """
    venv = project_dir / "code" / ".venv"
    py = venv / "bin" / "python"
    needs_create = not py.exists()
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
    req = project_dir / "code" / "requirements.txt"
    if req.exists():
        mtime_file = venv / ".requirements_mtime"
        last_synced = (
            float(mtime_file.read_text().strip()) if mtime_file.exists() else 0.0
        )
        cur_mtime = req.stat().st_mtime
        if cur_mtime > last_synced or needs_create:
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
    parts = [str(project_dir), str(project_dir / "code")]
    if env.get("PYTHONPATH"):
        parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(parts)
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
    py = Path(os.path.abspath(ensure_venv(project_dir)))
    _ensure_code_package(project_dir)
    run_cwd = Path(cwd or project_dir).resolve()
    env = _analysis_env(project_dir, os.environ.copy())
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
    timeout_s: int = 600,
    cwd: Path | None = None,
    extra_env: dict[str, str] | None = None,
) -> ExecutionResult:
    """Run `python <script>` inside the project's venv. Returns capture."""
    script = project_dir / script_relpath
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
        args=[str(script)],
        timeout_s=timeout_s,
        cwd=cwd,
        extra_env=extra_env,
    )


def run_pytest(
    *,
    project_dir: Path,
    test_path: str = "tests/",
    timeout_s: int = 600,
) -> ExecutionResult:
    """Run pytest inside the project's venv."""
    import time
    py = ensure_venv(project_dir)
    _ensure_code_package(project_dir)
    code_dir = project_dir / "code"
    started = time.time()
    timed_out = False
    try:
        proc = subprocess.run(
            [str(py), "-m", "pytest", test_path, "-x", "--tb=short", "-q"],
            cwd=str(code_dir),
            timeout=timeout_s,
            capture_output=True,
            text=True,
            env=_analysis_env(project_dir, os.environ.copy()),
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


def cleanup_venv(project_dir: Path) -> None:
    """Remove the project's venv (used by tests)."""
    venv = project_dir / "code" / ".venv"
    if venv.exists():
        shutil.rmtree(venv, ignore_errors=True)


def evict_other_project_venvs(project_dir: Path) -> int:
    """Delete every OTHER project's ``code/.venv``, keeping this project's.

    A project venv is up to 1.2 GB (torch et al.) and ONE advance worker runs up to
    ``--max-tasks 10`` projects in a single job, so they piled up until the runner
    ran out of disk — `Submission Intake` died with ``[Errno 28] No space left on
    device``. (``cleanup_venv`` existed but was never called from anywhere.)

    Bounding disk to a single venv costs nothing real: a CI job starts on a fresh
    runner, and the CURRENT project's venv is deliberately preserved so it is still
    reused across ticks within the job. Returns the number of venvs removed.
    """
    project_dir = Path(project_dir)
    projects_root = project_dir.parent
    if not projects_root.is_dir():
        return 0
    removed = 0
    for sibling in projects_root.iterdir():
        if not sibling.is_dir() or sibling.resolve() == project_dir.resolve():
            continue
        venv = sibling / "code" / ".venv"
        if venv.is_dir():
            shutil.rmtree(venv, ignore_errors=True)
            removed += 1
    if removed:
        logger.info(
            "evicted %d other project venv(s) to bound runner disk (keeping %s)",
            removed, project_dir.name,
        )
    return removed


__all__ = [
    "ExecutionResult",
    "cleanup_venv",
    "ensure_venv",
    "evict_other_project_venvs",
    "run_pytest",
    "run_python_script",
]
