"""Kaggle GPU-offload execution lane (issue #367).

GPU-bound research projects (transformers + 8-bit quantization, CUDA kernels,
large-RAM jobs) fail on the FREE, CPU-only CI runner. ``_compute_infra_failures``
(``execution.stage``) already DETECTS those failures; this module RUNS the same
quickstart run-book on Kaggle's free GPU instead of grinding the auto-fix loop or
parking the project. The flow is async (Kaggle kernels run minutes-to-hours):
``dispatch`` → ``poll`` → ``retrieve``, mirrored by the offload tri-state in
:mod:`llmxive.state.execution_status`.

GATED-ON-SECRETS: when ``KAGGLE_USERNAME`` / ``KAGGLE_KEY`` are absent or the
``kaggle`` CLI is not importable, :func:`is_available` returns False and the
whole lane is INERT — the normal local execute-and-gate path runs unchanged.
Every external call is wrapped so a Kaggle/network/quota error NEVER crashes the
pipeline: it logs and returns a sentinel so the caller falls back to the local
path. The same quickstart commands the local runner uses
(``analysis_runner.extract_run_commands``) are run on Kaggle — Single Source of
Truth, no duplicated command extraction.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from llmxive.execution.analysis_runner import (
    _find_quickstart,
    extract_run_commands,
)

logger = logging.getLogger(__name__)

#: PUBLIC GitHub repo the kernel clones at the current commit SHA. The kernel
#: runs on Kaggle's machines (no access to the runner's working tree), so it
#: re-materialises the project from the public mirror.
_PUBLIC_REPO_URL = "https://github.com/ContextLab/llmXive.git"

#: Artifact sub-dirs the kernel copies back into /kaggle/working/ and that
#: :func:`retrieve` pulls back into the project (matches analysis_runner's
#: artifact dirs + results/, the harness-receipt dir).
_ARTIFACT_DIRS = ("data", "figures", "results")
_ARTIFACT_SUFFIXES = (
    ".csv", ".json", ".parquet", ".npy", ".npz", ".tsv", ".h5", ".feather",
    ".png", ".pdf", ".jpg", ".jpeg", ".svg",
)

#: Kaggle status tokens we normalise ``poll`` onto.
_STATUS_RUNNING = "running"
_STATUS_COMPLETE = "complete"
_STATUS_ERROR = "error"
_STATUS_CANCELLED = "cancelAcknowledged"


def _slug(project_id: str) -> str:
    """Kaggle-safe kernel slug: lowercase, alnum + dashes, length-bounded.

    Kaggle kernel slugs must be 5-50 chars, ``[a-z0-9-]``. The project id
    (e.g. ``PROJ-261-evaluating-the-impact-of-code-duplicatio``) is lowered,
    non-conforming chars collapse to single dashes, and the result is prefixed
    ``llmxive-`` and capped at 50 chars.
    """
    base = re.sub(r"[^a-z0-9]+", "-", project_id.lower()).strip("-")
    ref = f"llmxive-{base}"
    return ref[:50].rstrip("-")


def _ensure_kaggle_auth() -> tuple[str, str] | None:
    """Resolve Kaggle credentials AND make the ``kaggle`` CLI able to authenticate.

    Accepts THREE forms (priority order) so a SINGLE repo secret suffices in CI:

      1. ``KAGGLE_USERNAME`` + ``KAGGLE_KEY`` env vars (the kaggle-native pair);
      2. ``KAGGLE_API_TOKEN`` — the verbatim contents of the ``kaggle.json`` the
         Kaggle site issues from "Create New API Token"
         (``{"username": ..., "key": ...}``). We parse it, export the pair into
         the environment (``dispatch`` reads ``KAGGLE_USERNAME`` for the kernel
         ref) AND write ``~/.kaggle/kaggle.json`` (chmod 600) so the CLI
         authenticates;
      3. an existing on-disk ``~/.kaggle/kaggle.json``;
      4. the llmXive credentials file (``~/.config/llmxive/credentials.toml``) —
         ``kaggle_username``/``kaggle_key``, a ``[kaggle]`` table, or a verbatim
         ``kaggle_api_token`` — so the Kaggle creds live in the SAME place as the
         Dartmouth key (resolution is centralized in ``credentials.load_kaggle_creds``).

    Returns ``(username, key)`` or ``None``. Idempotent; never raises.
    """
    from llmxive.credentials import load_kaggle_creds

    pair = load_kaggle_creds()
    if pair is None:
        return None
    user, key = pair
    # NEW Kaggle personal-access tokens (``kgat_`` prefix — the current default
    # "Create New API Token" issues these, NOT the legacy 32-hex key) are BEARER
    # tokens consumed via ``KAGGLE_API_TOKEN`` by the kaggle>=1.7 client; the old
    # Basic username:key path 401s with them. Export it so the CLI authenticates.
    # The username is still needed for the kernel ref (``<username>/<slug>``), so we
    # keep resolving + exporting it too. (Pin kaggle==2.2.3 + kagglesdk==0.1.31 in
    # pyproject — the latest kagglesdk 0.1.32 wheel is missing
    # ``competitions.legacy`` and breaks ``import kaggle`` outright.)
    if key.lower().startswith("kgat_"):
        os.environ["KAGGLE_API_TOKEN"] = key
    # Export the env pair (``dispatch`` reads KAGGLE_USERNAME for the kernel ref)
    # AND ensure ~/.kaggle/kaggle.json exists (chmod 600) so the kaggle CLI itself
    # authenticates (legacy key path).
    os.environ.setdefault("KAGGLE_USERNAME", user)
    os.environ.setdefault("KAGGLE_KEY", key)
    try:
        kdir = Path.home() / ".kaggle"
        kdir.mkdir(parents=True, exist_ok=True)
        kj = kdir / "kaggle.json"
        if not kj.is_file():
            kj.write_text(json.dumps({"username": user, "key": key}), encoding="utf-8")
            kj.chmod(0o600)
    except OSError as exc:
        logger.warning("could not write ~/.kaggle/kaggle.json: %s", exc)
    return (user, key)


def is_available() -> bool:
    """True iff offload can run: Kaggle creds resolve AND the CLI is importable.

    When False the offload lane is a no-op and the normal local execute-and-gate
    path runs unchanged (the gated-on-secrets contract). Accepts creds as the
    ``KAGGLE_USERNAME``/``KAGGLE_KEY`` pair, a single ``KAGGLE_API_TOKEN``
    (kaggle.json contents), or an on-disk ``~/.kaggle/kaggle.json`` (see
    :func:`_ensure_kaggle_auth`), and confirms the ``kaggle`` package imports
    (the CLI ships with it) so a half-configured runner never attempts a doomed
    dispatch.
    """
    if _ensure_kaggle_auth() is None:
        return False
    import importlib.util

    if importlib.util.find_spec("kaggle") is not None:
        return True
    return shutil.which("kaggle") is not None


def _run_kaggle(args: list[str], *, timeout_s: int = 300) -> subprocess.CompletedProcess | None:
    """Run a ``kaggle`` CLI command, capturing output. Returns None on any
    failure (missing CLI, non-zero exit, timeout, OSError) — never raises, so a
    Kaggle/network/quota error always degrades to the local fallback.
    """
    try:
        proc = subprocess.run(
            ["kaggle", *args],
            capture_output=True, text=True, timeout=timeout_s,
            env={**os.environ},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning("kaggle %s failed to launch: %s", " ".join(args[:2]), exc)
        return None
    if proc.returncode != 0:
        tail = ((proc.stdout or "") + (proc.stderr or "")).strip()[-500:]
        logger.warning("kaggle %s rc=%d: %s", " ".join(args[:2]), proc.returncode, tail)
        return proc  # caller inspects output (e.g. quota messages) then falls back
    return proc


def _kernel_script(project_id: str, commit_sha: str, commands: list[str]) -> str:
    """Generate the kernel script (kernel_type=script) run on Kaggle.

    It git-clones the PUBLIC repo at ``commit_sha``, cds to the project, installs
    ``code/requirements.txt``, runs the SAME quickstart run-book commands the
    local runner would, then copies produced data/figures/results into
    ``/kaggle/working/`` so ``kaggle kernels output`` can retrieve them.
    """
    proj_rel = f"projects/{project_id}"
    runbook = "\n".join(
        f"    {json.dumps(cmd)},"
        for cmd in commands
    )
    art_dirs = ", ".join(json.dumps(d) for d in _ARTIFACT_DIRS)
    return f'''# llmXive GPU-offload kernel (issue #367) — auto-generated, do not edit.
# Runs the SAME quickstart run-book as the local runner, on Kaggle's free GPU.
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

REPO_URL = {json.dumps(_PUBLIC_REPO_URL)}
COMMIT_SHA = {json.dumps(commit_sha)}
PROJECT_REL = {json.dumps(proj_rel)}
RUNBOOK = [
{runbook}
]
ARTIFACT_DIRS = [{art_dirs}]
WORKDIR = Path("/kaggle/working")
CLONE = WORKDIR / "llmXive"


def _sh(args, cwd=None, env=None):
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=cwd, env=env, check=True)


# 1. Clone the public repo at the exact commit the pipeline ran from.
if CLONE.exists():
    shutil.rmtree(CLONE)
_sh(["git", "clone", "--no-single-branch", REPO_URL, str(CLONE)])
_sh(["git", "checkout", COMMIT_SHA], cwd=str(CLONE))

proj = CLONE / PROJECT_REL
code = proj / "code"

# 2. Install the project's requirements into the kernel environment.
req = code / "requirements.txt"
if req.is_file():
    _sh([sys.executable, "-m", "pip", "install", "-q", "-r", str(req)])

# 3. Run the quickstart run-book commands (code/ on PYTHONPATH, run from proj).
env = {{**os.environ, "PYTHONPATH": str(code.resolve())}}
failed = []
for command in RUNBOOK:
    args = shlex.split(command)
    print("=== run:", command, flush=True)
    rc = subprocess.run(args, cwd=str(proj), env=env).returncode
    if rc != 0:
        print(f"!!! command rc={{rc}}: {{command}}", flush=True)
        failed.append(command)

# 4. Copy produced artifacts into /kaggle/working/ for retrieval (best-effort).
for sub in ARTIFACT_DIRS:
    src = proj / sub
    if not src.is_dir():
        continue
    dst = WORKDIR / sub
    for p in src.rglob("*"):
        if not p.is_file() or p.name == ".gitkeep":
            continue
        rel = p.relative_to(src)
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, out)
        print("artifact:", (Path(sub) / rel).as_posix(), flush=True)

if failed:
    print(f"{{len(failed)}} run-book command(s) failed on GPU", flush=True)
'''


def _current_commit_sha(repo_root: Path) -> str | None:
    """The git HEAD SHA the kernel must check out. None if it can't be read
    (e.g. a non-git checkout) — caller treats that as a soft dispatch failure."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root), capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning("could not read HEAD sha for offload: %s", exc)
        return None
    if proc.returncode != 0:
        return None
    sha = proc.stdout.strip()
    return sha or None


def dispatch(project_dir: Path, repo_root: Path) -> str | None:
    """Build + push a Kaggle GPU kernel for the project's analysis run-book.

    Returns the kernel ref ``<username>/<slug>`` on a successful push, or None on
    ANY soft failure (no quickstart, no commands, no commit SHA, quota, network,
    CLI error) so the caller falls back to the normal local path. Never raises.
    """
    project_dir = Path(project_dir)
    project_id = project_dir.name
    creds = _ensure_kaggle_auth()
    if creds is None:
        return None
    username = creds[0]

    quickstart = _find_quickstart(project_dir)
    if quickstart is None or not quickstart.is_file():
        logger.warning("offload skipped for %s: no quickstart run-book", project_id)
        return None
    commands = extract_run_commands(
        quickstart.read_text(encoding="utf-8", errors="replace")
    )
    if not commands:
        logger.warning("offload skipped for %s: quickstart has no python commands", project_id)
        return None

    commit_sha = _current_commit_sha(Path(repo_root))
    if not commit_sha:
        logger.warning("offload skipped for %s: no resolvable commit SHA", project_id)
        return None

    slug = _slug(project_id)
    kernel_ref = f"{username}/{slug}"
    try:
        kdir = Path(tempfile.mkdtemp(prefix=f"kaggle-offload-{slug}-"))
        code_file = "kernel.py"
        (kdir / code_file).write_text(
            _kernel_script(project_id, commit_sha, commands), encoding="utf-8"
        )
        metadata = {
            "id": kernel_ref,
            "title": f"llmXive {project_id}",
            "code_file": code_file,
            "language": "python",
            "kernel_type": "script",
            "enable_gpu": True,
            "enable_internet": True,
            "is_private": True,
        }
        (kdir / "kernel-metadata.json").write_text(
            json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
        )
    except OSError as exc:
        logger.warning("offload kernel build failed for %s: %s", project_id, exc)
        return None

    proc = _run_kaggle(["kernels", "push", "-p", str(kdir)])
    if proc is None or proc.returncode != 0:
        out = (proc.stdout + proc.stderr) if proc is not None else ""
        if re.search(r"quota|rate limit|too many", out, re.IGNORECASE):
            logger.warning("offload push hit Kaggle quota for %s; falling back", project_id)
        else:
            logger.warning("offload push failed for %s; falling back to local path", project_id)
        return None
    logger.info("offload dispatched %s -> kernel %s @ %s", project_id, kernel_ref, commit_sha[:8])
    return kernel_ref


def poll(kernel_ref: str) -> str:
    """Return the kernel's status: ``running|complete|error|cancelAcknowledged``.

    Parses ``kaggle kernels status <ref>``. On any CLI/parse failure returns
    ``running`` (the safe non-terminal default) so the caller keeps polling
    rather than wrongly treating a transient hiccup as terminal — the offload
    stays pending and never triggers a human-input escalation.
    """
    proc = _run_kaggle(["kernels", "status", kernel_ref])
    if proc is None:
        return _STATUS_RUNNING
    low = ((proc.stdout or "") + " " + (proc.stderr or "")).lower()
    # `kaggle kernels status` reports e.g. `<ref> has status "complete"`. Match
    # the reported token in priority order; an unrecognised line stays RUNNING
    # (the safe non-terminal default → keep polling, never escalate).
    if "cancelacknowledged" in low or "cancelrequested" in low:
        return _STATUS_CANCELLED
    if "complete" in low:
        return _STATUS_COMPLETE
    if "error" in low:
        return _STATUS_ERROR
    return _STATUS_RUNNING


def retrieve(kernel_ref: str, project_dir: Path) -> list[str]:
    """Pull the completed kernel's output artifacts back into the project.

    Runs ``kaggle kernels output <ref> -p <tmp>``, copies any real
    data/figures/results files into ``project_dir`` (preserving sub-paths), and
    returns the list of project-relative artifact paths pulled. Returns ``[]`` on
    any failure or when the kernel produced nothing real — the caller treats an
    empty list as "retrieve yielded nothing" and falls back. Never raises.
    """
    project_dir = Path(project_dir)
    tmp = Path(tempfile.mkdtemp(prefix="kaggle-output-"))
    proc = _run_kaggle(["kernels", "output", kernel_ref, "-p", str(tmp)])
    if proc is None or proc.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        return []

    pulled: list[str] = []
    try:
        for p in sorted(tmp.rglob("*")):
            if not p.is_file():
                continue
            if p.suffix.lower() not in _ARTIFACT_SUFFIXES:
                continue
            try:
                if p.stat().st_size == 0:
                    continue
            except OSError:
                continue
            # The kernel mirrored proj/<dir>/... under /kaggle/working/<dir>/...,
            # so the output tarball carries the same <dir>/<rel> layout. Keep
            # only files that land under a known artifact dir.
            rel = p.relative_to(tmp)
            parts = rel.parts
            if not parts or parts[0] not in _ARTIFACT_DIRS:
                continue
            dst = project_dir / rel
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dst)
            except OSError as exc:
                logger.warning("offload retrieve copy failed for %s: %s", rel, exc)
                continue
            pulled.append(rel.as_posix())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return pulled


__all__ = ["dispatch", "is_available", "poll", "retrieve"]
