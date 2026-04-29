"""Code-execution sandbox tool (T088).

Runs short Python scripts in a subprocess inside the GitHub Actions
runner with a strict per-execution wall-clock timeout (default
SANDBOX_BUDGET_SECONDS, configured via web/about.html and exposed
through llmxive.config). Used by Figure-Generation, Statistics, and
any code-running agent task.

Per the spec's R7 (Code-execution sandbox): the runner is itself the
sandbox — a fresh ephemeral VM per scheduled run. SIGKILL on timeout;
partial stdout/stderr captured before the kill. Per-project working
directory; per-run virtualenv populated from the project's pinned
requirements.txt.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from llmxive.config import SANDBOX_BUDGET_SECONDS


@dataclass
class SandboxResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    output_files: list[str]


class SandboxError(RuntimeError):
    """Raised when the sandbox cannot start (not when it times out)."""


def _ensure_venv(working_dir: Path, requirements_path: Path | None) -> Path:
    """Create a per-run virtualenv at `working_dir/.sandbox-venv` if missing.

    The venv is ephemeral on a fresh Actions runner. Locally, it persists
    across runs which speeds up repeated invocations.
    """
    venv_dir = working_dir / ".sandbox-venv"
    if not venv_dir.is_dir():
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            check=True,
            capture_output=True,
        )
        # Always upgrade pip first; we want the latest resolver.
        py = venv_dir / "bin" / "python"
        subprocess.run(
            [str(py), "-m", "pip", "install", "--quiet", "--upgrade", "pip"],
            check=True,
            capture_output=True,
        )
    if requirements_path and requirements_path.exists():
        py = venv_dir / "bin" / "python"
        subprocess.run(
            [str(py), "-m", "pip", "install", "--quiet", "-r", str(requirements_path)],
            check=True,
            capture_output=True,
            timeout=300,
        )
    return venv_dir


def run_python(
    script: str,
    *,
    working_dir: Path,
    requirements_path: Path | None = None,
    timeout_seconds: int | None = None,
    env_extra: dict[str, str] | None = None,
    capture_output_dir: Path | None = None,
) -> SandboxResult:
    """Run `script` (Python source) inside a sandboxed venv at `working_dir`.

    `capture_output_dir` is enumerated before and after execution; any
    new files appearing there are reported in `output_files` (used by
    the Figure-Generation Agent to detect generated PDFs/PNGs).
    """
    working_dir.mkdir(parents=True, exist_ok=True)
    timeout = timeout_seconds if timeout_seconds is not None else SANDBOX_BUDGET_SECONDS

    venv_dir = _ensure_venv(working_dir, requirements_path)
    py = venv_dir / "bin" / "python"
    if not py.exists():
        raise SandboxError(f"venv python missing: {py}")

    pre_files: set[str] = set()
    if capture_output_dir is not None and capture_output_dir.is_dir():
        pre_files = {str(p) for p in capture_output_dir.rglob("*") if p.is_file()}

    with tempfile.NamedTemporaryFile(
        "w",
        suffix=".py",
        dir=str(working_dir),
        delete=False,
        encoding="utf-8",
    ) as fh:
        fh.write(script)
        script_path = Path(fh.name)

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    if env_extra:
        env.update(env_extra)

    try:
        proc = subprocess.Popen(
            [str(py), str(script_path)],
            cwd=str(working_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            start_new_session=True,  # so we can SIGKILL the process group
        )
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = proc.communicate()
            timed_out = True

        post_files: set[str] = set()
        if capture_output_dir is not None and capture_output_dir.is_dir():
            post_files = {str(p) for p in capture_output_dir.rglob("*") if p.is_file()}
        new_files = sorted(post_files - pre_files)

        return SandboxResult(
            returncode=proc.returncode,
            stdout=stdout or "",
            stderr=stderr or "",
            timed_out=timed_out,
            output_files=new_files,
        )
    finally:
        try:
            script_path.unlink()
        except OSError:
            pass


__all__ = ["SandboxResult", "SandboxError", "run_python"]
