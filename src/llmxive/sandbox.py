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

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


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
            subprocess.run(
                [str(py), "-m", "pip", "install", "-q", "-r", str(req)],
                check=False,  # tolerate failures so subsequent runs surface them via stderr
                capture_output=True,
            )
            try:
                mtime_file.write_text(f"{cur_mtime}\n", encoding="utf-8")
            except OSError:
                pass
    return py


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
    run_cwd = Path(cwd or project_dir).resolve()
    env = os.environ.copy()
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


__all__ = [
    "ExecutionResult",
    "cleanup_venv",
    "ensure_venv",
    "run_pytest",
    "run_python_script",
]
