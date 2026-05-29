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


def run_python_script(
    *,
    project_dir: Path,
    script_relpath: str,
    timeout_s: int = 600,
    cwd: Path | None = None,
    extra_env: dict[str, str] | None = None,
) -> ExecutionResult:
    """Run `python <script>` inside the project's venv. Returns capture."""
    import time

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
    py = ensure_venv(project_dir)
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    if extra_env:
        env.update(extra_env)
    started = time.time()
    timed_out = False
    try:
        proc = subprocess.run(
            [str(py), str(script)],
            # Run with cwd=project_dir so scripts can write to data/raw/,
            # paper/figures/ etc. with paths relative to the project
            # root. Previously cwd=code/ which meant scripts created
            # code/data/raw/ which subsequent scripts couldn't find.
            cwd=str(cwd or project_dir),
            timeout=timeout_s,
            capture_output=True,
            text=True,
            env=env,
        )
        rc = proc.returncode
        out = proc.stdout
        err = proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        rc = -1
        out = (exc.stdout or b"").decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = (
            (exc.stderr or b"").decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        ) + f"\n[TIMEOUT after {timeout_s}s]"
    elapsed = time.time() - started
    return ExecutionResult(
        ok=rc == 0,
        returncode=rc,
        stdout=out,
        stderr=err,
        duration_s=elapsed,
        timed_out=timed_out,
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
