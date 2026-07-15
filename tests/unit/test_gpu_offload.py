"""Tests for the Kaggle GPU-offload execution lane (issue #367).

These exercise the REAL code paths — ``execute_and_gate``, the
``execution_status`` offload tri-state, and ``offload``'s metadata/script
generation. The ONLY thing faked is the external Kaggle boundary (the
``subprocess`` call to the ``kaggle`` CLI, and ``offload.dispatch``/``poll``/
``retrieve`` at the network edge) — never the pipeline logic under test.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from llmxive.execution import offload
from llmxive.execution.analysis_runner import AnalysisRunResult, RunCommandResult
from llmxive.execution.stage import execute_and_gate
from llmxive.state import execution_status


def _bootstrap_project(tmp_path: Path, project_id: str, tasks_md: str,
                       quickstart: str | None = None) -> Path:
    proj = tmp_path / "projects" / project_id
    (proj / "specs" / "001-x").mkdir(parents=True)
    (proj / ".specify" / "memory").mkdir(parents=True)
    (proj / "specs" / "001-x" / "tasks.md").write_text(tasks_md, encoding="utf-8")
    if quickstart is not None:
        (proj / "specs" / "001-x" / "quickstart.md").write_text(quickstart, encoding="utf-8")
    (tmp_path / "state" / "execution_status").mkdir(parents=True)
    return proj


# --- is_available() gating --------------------------------------------------


def test_is_available_false_without_creds(monkeypatch, tmp_path) -> None:
    # Hermetic: clear env AND redirect HOME + neutralize the credentials file, so a
    # host with a real ~/.kaggle/kaggle.json or ~/.config/llmxive/credentials.toml
    # (e.g. a dev who configured the offload) can't flip this result.
    for var in ("KAGGLE_USERNAME", "KAGGLE_KEY", "KAGGLE_API_TOKEN"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))          # Path.home() -> empty tmp
    from llmxive import credentials as _c
    monkeypatch.setattr(
        _c, "check_permissions",
        lambda: _c.CredentialsCheck(ok=True, reason=None, path=tmp_path / "none.toml", exists=False),
    )
    assert offload.is_available() is False


def test_is_available_false_with_creds_but_no_cli(monkeypatch) -> None:
    monkeypatch.setenv("KAGGLE_USERNAME", "u")
    monkeypatch.setenv("KAGGLE_KEY", "k")
    # No `kaggle` package and not on PATH → still unavailable.
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert offload.is_available() is False


def test_is_available_true_with_creds_and_cli(monkeypatch) -> None:
    monkeypatch.setenv("KAGGLE_USERNAME", "u")
    monkeypatch.setenv("KAGGLE_KEY", "k")
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/kaggle")
    # Importable kaggle OR a kaggle on PATH both satisfy availability.
    assert offload.is_available() is True


def test_auth_from_single_api_token_secret(tmp_path, monkeypatch) -> None:
    """A single KAGGLE_API_TOKEN secret (the verbatim kaggle.json the Kaggle site
    issues) resolves creds: it exports KAGGLE_USERNAME/KAGGLE_KEY and writes
    ~/.kaggle/kaggle.json so the CLI authenticates — and is_available() is True."""
    # delenv at start so monkeypatch restores absence even though the function
    # sets these (no leak to other tests).
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))  # Path.home() → tmp_path on POSIX
    monkeypatch.setenv(
        "KAGGLE_API_TOKEN",
        json.dumps({"username": "tok-user", "key": "tok-key"}),
    )
    creds = offload._ensure_kaggle_auth()
    assert creds == ("tok-user", "tok-key")
    assert os.environ["KAGGLE_USERNAME"] == "tok-user"
    assert os.environ["KAGGLE_KEY"] == "tok-key"
    kj = tmp_path / ".kaggle" / "kaggle.json"
    assert kj.is_file(), "kaggle.json must be written for the CLI to authenticate"
    assert json.loads(kj.read_text())["key"] == "tok-key"
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/kaggle")
    assert offload.is_available() is True


def test_auth_none_with_malformed_api_token(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("KAGGLE_API_TOKEN", "not-json")
    assert offload._ensure_kaggle_auth() is None
    assert offload.is_available() is False


# --- kernel-metadata.json generation ----------------------------------------


def test_dispatch_generates_kernel_metadata_with_gpu_and_internet(tmp_path, monkeypatch) -> None:
    """A real dispatch writes kernel-metadata.json with enable_gpu +
    enable_internet (+ private + script). Only the `kaggle kernels push`
    subprocess and the HEAD-sha read are faked; everything else is REAL."""
    monkeypatch.setenv("KAGGLE_USERNAME", "tester")
    monkeypatch.setenv("KAGGLE_KEY", "k")
    proj = _bootstrap_project(
        tmp_path, "PROJ-261-gpu",
        "- [x] T001 produce data/out.csv\n",
        quickstart="```bash\npython main.py --sample-size 10\n```\n",
    )
    captured: dict[str, Path] = {}

    class _Proc:
        returncode = 0
        stdout = "Kernel pushed"
        stderr = ""

    def _fake_run_kaggle(args, *, timeout_s=300):
        # Capture the kernel dir handed to `kernels push -p <dir>` and inspect it.
        if args[:2] == ["kernels", "push"]:
            captured["dir"] = Path(args[args.index("-p") + 1])
        return _Proc()

    monkeypatch.setattr(offload, "_run_kaggle", _fake_run_kaggle)
    monkeypatch.setattr(offload, "_current_commit_sha", lambda root: "abc123def456")

    ref = offload.dispatch(proj, tmp_path)
    assert ref == "tester/llmxive-proj-261-gpu"

    meta_path = captured["dir"] / "kernel-metadata.json"
    meta = json.loads(meta_path.read_text())
    assert meta["enable_gpu"] is True
    assert meta["enable_internet"] is True
    assert meta["is_private"] is True
    assert meta["kernel_type"] == "script"
    assert meta["language"] == "python"
    assert meta["id"] == "tester/llmxive-proj-261-gpu"

    # The kernel script runs the SAME quickstart command + clones at the SHA.
    script = (captured["dir"] / meta["code_file"]).read_text()
    assert "abc123def456" in script
    assert "python main.py --sample-size 10" in script
    assert "ContextLab/llmXive" in script
    # The repo is cloned OUTSIDE /kaggle/working so `kaggle kernels output` retrieves
    # ONLY the copied artifacts, not the entire repo (which times the retrieve out).
    assert "/tmp/llmxive-clone" in script
    assert 'CLONE = WORKDIR' not in script


def test_dispatch_long_name_title_resolves_to_truncated_slug(tmp_path, monkeypatch) -> None:
    """For a project whose name exceeds Kaggle's 50-char slug cap, the kernel TITLE
    must still slugify to the (truncated) id — else the kaggle>=2 CLI rejects the
    push with 400 'title does not resolve to the specified id', silently breaking
    offload for every long-named (e.g. arXiv) project."""
    import re

    monkeypatch.setenv("KAGGLE_USERNAME", "tester")
    monkeypatch.setenv("KAGGLE_KEY", "k")
    long_id = "PROJ-488-evaluating-the-impact-of-code-generation-on-software-quality"
    proj = _bootstrap_project(tmp_path, long_id, "- [x] T001 produce data/out.csv\n",
                              quickstart="```bash\npython main.py\n```\n")
    captured: dict[str, Path] = {}

    class _Proc:
        returncode = 0
        stdout = "Kernel pushed"
        stderr = ""

    def _fake_run_kaggle(args, *, timeout_s=300):
        if args[:2] == ["kernels", "push"]:
            captured["dir"] = Path(args[args.index("-p") + 1])
        return _Proc()

    monkeypatch.setattr(offload, "_run_kaggle", _fake_run_kaggle)
    monkeypatch.setattr(offload, "_current_commit_sha", lambda root: "abc123")

    offload.dispatch(proj, tmp_path)
    meta = json.loads((captured["dir"] / "kernel-metadata.json").read_text())
    slug = meta["id"].split("/", 1)[1]
    assert len(slug) <= 50
    # Kaggle derives the slug from the title by lowercasing + collapsing any run of
    # non-alphanumerics to a single dash; the title MUST round-trip to the id.
    def _kaggle_slugify(t: str) -> str:
        return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", t.lower())).strip("-")
    assert _kaggle_slugify(meta["title"]) == slug


def test_dispatch_returns_none_without_quickstart_commands(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("KAGGLE_USERNAME", "tester")
    monkeypatch.setenv("KAGGLE_KEY", "k")
    proj = _bootstrap_project(tmp_path, "PROJ-Z-nocmd", "- [x] T001\n",
                              quickstart="```bash\nls -la\n```\n")
    monkeypatch.setattr(offload, "_current_commit_sha", lambda root: "sha")
    assert offload.dispatch(proj, tmp_path) is None


# --- record_offload does NOT bump fix_rounds (the no-escalation invariant) ---


def test_record_offload_does_not_bump_fix_rounds_and_pending_transitions(tmp_path) -> None:
    (tmp_path / "state" / "execution_status").mkdir(parents=True)
    pid = "PROJ-700-off"
    # A prior failure left fix_rounds=1.
    execution_status.record(pid, ok=False, reason="gpu boom", artifacts=[],
                            failures=["python m.py -> rc=1 CUDA"], repo_root=tmp_path)
    assert execution_status.fix_rounds(pid, repo_root=tmp_path) == 1

    # Submitting an offload MUST NOT bump fix_rounds.
    execution_status.record_offload(pid, status="submitted",
                                    kernel_ref="u/llmxive-proj-700-off", repo_root=tmp_path)
    assert execution_status.fix_rounds(pid, repo_root=tmp_path) == 1
    assert execution_status.is_offload_pending(pid, repo_root=tmp_path) is True
    off = execution_status.offload_state(pid, repo_root=tmp_path)
    assert off["status"] == "submitted" and off["kernel_ref"].endswith("proj-700-off")
    submitted_at = off["submitted_at"]

    # running → still pending, still no bump, submitted_at preserved.
    execution_status.record_offload(pid, status="running",
                                    kernel_ref="u/llmxive-proj-700-off", repo_root=tmp_path)
    assert execution_status.fix_rounds(pid, repo_root=tmp_path) == 1
    assert execution_status.is_offload_pending(pid, repo_root=tmp_path) is True
    assert execution_status.offload_state(pid, repo_root=tmp_path)["submitted_at"] == submitted_at

    # failed → NOT pending, still no bump (the bump comes from the local fallback).
    execution_status.record_offload(pid, status="failed",
                                    kernel_ref="u/llmxive-proj-700-off", repo_root=tmp_path)
    assert execution_status.fix_rounds(pid, repo_root=tmp_path) == 1
    assert execution_status.is_offload_pending(pid, repo_root=tmp_path) is False

    # clear drops the sub-record but preserves the rest.
    execution_status.clear_offload(pid, repo_root=tmp_path)
    assert execution_status.offload_state(pid, repo_root=tmp_path) is None
    assert execution_status.fix_rounds(pid, repo_root=tmp_path) == 1


# --- execute_and_gate dispatches on a compute-infra failure when available ---


def test_execute_and_gate_dispatches_offload_on_compute_infra_failure(tmp_path, monkeypatch) -> None:
    """A compute-infra (CUDA) failure WITH offload available dispatches to Kaggle
    and records a pending offload WITHOUT bumping fix_rounds. Exercises the REAL
    execute_and_gate + execution_status; only offload.is_available/dispatch (the
    Kaggle edge) are faked, by a real in-process fake that records a kernel_ref."""
    pid = "PROJ-261-cuda"
    proj = _bootstrap_project(tmp_path, pid,
                              "- [x] T001 run code/model_metrics.py\n")

    def _cuda_fail(project_dir, **kw):
        return AnalysisRunResult(
            ok=False,
            commands=[RunCommandResult(
                "python code/model_metrics.py", False, 1, 0.5, False,
                "RuntimeError: bitsandbytes load_in_8bit requires CUDA",
            )],
            artifacts_produced=[],
            reason="1 command failed (CUDA)",
        )
    monkeypatch.setattr("llmxive.execution.stage.run_analysis", _cuda_fail)
    monkeypatch.setattr(offload, "is_available", lambda: True)

    dispatched: dict[str, str] = {}

    def _fake_dispatch(project_dir, repo_root):
        dispatched["ref"] = "tester/llmxive-proj-261-cuda"
        return dispatched["ref"]
    monkeypatch.setattr(offload, "dispatch", _fake_dispatch)

    assert execute_and_gate(proj, repo_root=tmp_path) is False
    assert dispatched["ref"] == "tester/llmxive-proj-261-cuda"
    # Pending offload recorded, fix_rounds NOT bumped (the invariant).
    assert execution_status.is_offload_pending(pid, repo_root=tmp_path) is True
    assert execution_status.fix_rounds(pid, repo_root=tmp_path) == 0
    assert execution_status.is_ok(pid, repo_root=tmp_path) is False


# --- pending offload polls → complete → retrieve → ok=True ------------------


def test_execute_and_gate_polls_pending_offload_to_completion(tmp_path, monkeypatch) -> None:
    """A pending offload that polls complete + retrieves real artifacts records
    ok=True (research_complete-eligible) and clears the offload sub-record."""
    pid = "PROJ-261-done"
    proj = _bootstrap_project(tmp_path, pid, "- [x] T001 produce data/out.csv\n")
    execution_status.record_offload(pid, status="running",
                                    kernel_ref="tester/llmxive-proj-261-done", repo_root=tmp_path)

    monkeypatch.setattr(offload, "poll", lambda ref: "complete")

    def _fake_retrieve(ref, project_dir):
        out = Path(project_dir) / "data" / "out.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("a,b\n1,2\n", encoding="utf-8")
        return ["data/out.csv"]
    monkeypatch.setattr(offload, "retrieve", _fake_retrieve)
    # run_analysis must NOT be called while polling — guard it.
    monkeypatch.setattr("llmxive.execution.stage.run_analysis",
                        lambda *a, **k: pytest.fail("run_analysis must not run while polling"))

    assert execute_and_gate(proj, repo_root=tmp_path) is True
    assert execution_status.is_ok(pid, repo_root=tmp_path) is True
    assert execution_status.offload_state(pid, repo_root=tmp_path) is None
    assert (proj / "data" / "out.csv").is_file()


def test_pending_offload_running_keeps_polling_no_bump(tmp_path, monkeypatch) -> None:
    pid = "PROJ-261-running"
    proj = _bootstrap_project(tmp_path, pid, "- [x] T001 produce data/out.csv\n")
    execution_status.record_offload(pid, status="submitted",
                                    kernel_ref="tester/llmxive-proj-261-running", repo_root=tmp_path)
    monkeypatch.setattr(offload, "poll", lambda ref: "running")
    monkeypatch.setattr("llmxive.execution.stage.run_analysis",
                        lambda *a, **k: pytest.fail("run_analysis must not run while polling"))

    assert execute_and_gate(proj, repo_root=tmp_path) is False
    assert execution_status.is_offload_pending(pid, repo_root=tmp_path) is True
    assert execution_status.fix_rounds(pid, repo_root=tmp_path) == 0


def test_pending_offload_error_falls_back_to_local_failure(tmp_path, monkeypatch) -> None:
    """An errored kernel marks the offload failed and falls through to ONE normal
    local-failure pass (which bumps fix_rounds) — NOT another dispatch."""
    pid = "PROJ-261-err"
    proj = _bootstrap_project(tmp_path, pid, "- [x] T001 run code/model_metrics.py\n")
    execution_status.record_offload(pid, status="running",
                                    kernel_ref="tester/llmxive-proj-261-err", repo_root=tmp_path)
    monkeypatch.setattr(offload, "poll", lambda ref: "error")
    monkeypatch.setattr(offload, "is_available", lambda: True)
    # If the fallback wrongly re-dispatched, this would be hit:
    monkeypatch.setattr(offload, "dispatch",
                        lambda *a, **k: pytest.fail("must not re-dispatch after a failed offload"))

    def _cuda_fail(project_dir, **kw):
        return AnalysisRunResult(
            ok=False,
            commands=[RunCommandResult(
                "python code/model_metrics.py", False, 1, 0.5, False,
                "RuntimeError: CUDA out of memory",
            )],
            artifacts_produced=[], reason="CUDA OOM",
        )
    monkeypatch.setattr("llmxive.execution.stage.run_analysis", _cuda_fail)

    assert execute_and_gate(proj, repo_root=tmp_path) is False
    # local failure path ran: fix_rounds bumped, not pending anymore.
    assert execution_status.fix_rounds(pid, repo_root=tmp_path) == 1
    assert execution_status.is_offload_pending(pid, repo_root=tmp_path) is False


# --- offload UNAVAILABLE → existing bump-fix_rounds path unchanged ----------


def test_compute_infra_failure_without_offload_uses_existing_path(tmp_path, monkeypatch) -> None:
    """When offload is NOT available, a compute-infra failure follows the
    EXISTING path: record ok=False (bump fix_rounds), write feedback, re-open
    tasks — exactly as before this feature."""
    pid = "PROJ-261-noff"
    proj = _bootstrap_project(tmp_path, pid, "- [x] T001 run code/model_metrics.py\n")
    monkeypatch.setattr(offload, "is_available", lambda: False)

    def _cuda_fail(project_dir, **kw):
        return AnalysisRunResult(
            ok=False,
            commands=[RunCommandResult(
                "python code/model_metrics.py", False, 1, 0.5, False,
                "RuntimeError: bitsandbytes load_in_8bit requires CUDA",
            )],
            artifacts_produced=[], reason="CUDA",
        )
    monkeypatch.setattr("llmxive.execution.stage.run_analysis", _cuda_fail)

    assert execute_and_gate(proj, repo_root=tmp_path) is False
    assert execution_status.fix_rounds(pid, repo_root=tmp_path) == 1
    assert execution_status.is_offload_pending(pid, repo_root=tmp_path) is False
    fb = (proj / ".specify" / "memory" / "execution_feedback.md").read_text()
    assert "COMPUTE-ENVIRONMENT" in fb and "RE-SCOPE" in fb
    new_tasks = (proj / "specs" / "001-x" / "tasks.md").read_text()
    assert "- [ ] T001 run code/model_metrics.py" in new_tasks


def test_poll_transient_http_error_stays_running(monkeypatch) -> None:
    """A TRANSIENT status-query failure (404/permission/5xx — the kaggle>=2 client
    emits 'NNN Client Error: ...') must NOT be read as the kernel's terminal ERROR
    state; poll() returns RUNNING so the offload keeps polling instead of wrongly
    failing a still-running kernel."""
    class _Proc:
        returncode = 1
        stdout = ""
        stderr = "404 Client Error: Not Found for url: .../GetKernelSessionStatus"
    monkeypatch.setattr(offload, "_run_kaggle", lambda *a, **k: _Proc())
    assert offload.poll("u/k") == "running"


def test_poll_reports_real_kernel_error_and_complete(monkeypatch) -> None:
    """A SUCCESSFUL status query that reports the kernel's own ERROR/COMPLETE state
    (incl. the kaggle>=2 'KernelWorkerStatus.X' enum form) is parsed correctly."""
    def _mk(status_text):
        class _P:
            returncode = 0
            stdout = f'u/k has status "{status_text}"'
            stderr = ""
        return _P()
    monkeypatch.setattr(offload, "_run_kaggle", lambda *a, **k: _mk("KernelWorkerStatus.ERROR"))
    assert offload.poll("u/k") == "error"
    monkeypatch.setattr(offload, "_run_kaggle", lambda *a, **k: _mk("KernelWorkerStatus.COMPLETE"))
    assert offload.poll("u/k") == "complete"
    monkeypatch.setattr(offload, "_run_kaggle", lambda *a, **k: _mk("complete"))
    assert offload.poll("u/k") == "complete"


def test_derive_username_parses_owner_from_kernels_list(monkeypatch) -> None:
    """_derive_kaggle_username parses <owner> from the caller's own kernels list, so
    a bare kgat_ Bearer token (which carries no username) still yields the kernel-ref
    owner without a second secret."""
    offload._DERIVED_USERNAME = None

    class _P:
        returncode = 0
        stdout = "ref,title,author\njeremy9/llmxive-proj-657,llmxive proj 657,Jeremy\n"
        stderr = ""
    monkeypatch.setattr(offload, "_run_kaggle", lambda *a, **k: _P())
    assert offload._derive_kaggle_username() == "jeremy9"
    offload._DERIVED_USERNAME = None


def test_bare_kgat_token_derives_username_needs_no_second_secret(monkeypatch, tmp_path) -> None:
    """With ONLY a bare kgat_ KAGGLE_API_TOKEN (the single CI secret) and no username
    anywhere on disk/env, _ensure_kaggle_auth derives the username via the API and
    returns creds — so the offload works with just that one secret."""
    for v in ("KAGGLE_USERNAME", "KAGGLE_KEY"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))          # no ~/.kaggle/kaggle.json
    monkeypatch.setenv("KAGGLE_API_TOKEN", "KGAT_abc123def456")
    from llmxive import credentials as C
    monkeypatch.setattr(
        C, "check_permissions",
        lambda: C.CredentialsCheck(ok=True, reason=None, path=tmp_path / "none.toml", exists=False),
    )
    offload._DERIVED_USERNAME = None

    class _P:
        returncode = 0
        stdout = "ref\njeremy9/k1\n"
        stderr = ""
    monkeypatch.setattr(offload, "_run_kaggle", lambda *a, **k: _P())
    creds = offload._ensure_kaggle_auth()
    assert creds == ("jeremy9", "KGAT_abc123def456")
    assert os.environ["KAGGLE_API_TOKEN"] == "KGAT_abc123def456"
    offload._DERIVED_USERNAME = None


def test_compute_infra_regex_catches_common_real_gpu_absence_errors() -> None:
    """Offload's reachability depends on this: when the implementer FINALLY writes
    real `device="cuda"` code (per the updated planner/tasker prompts), the CPU-CI
    run must be recognised as a compute-infra failure so it offloads. Pin the exact
    error strings a GPU-less box raises for real GPU code."""
    from llmxive.execution.stage import _compute_infra_failures

    real_errors = [
        "RuntimeError: Found no NVIDIA driver on your system.",
        "RuntimeError: No CUDA GPUs are available",
        "AssertionError: Torch not compiled with CUDA enabled",
        "RuntimeError: No CUDA-capable device is detected",
        "The installed version of bitsandbytes was compiled without GPU support.",
        "RuntimeError: CUDA error: no kernel image is available",
    ]
    for err in real_errors:
        assert _compute_infra_failures([f"python code/train.py -> rc=1\n{err}"]), (
            f"real GPU-absence error not recognised as compute-infra: {err!r}"
        )


def test_compute_infra_regex_does_not_match_ordinary_bugs() -> None:
    """Must NOT fire on a plain code bug (that would wrongly offload instead of
    letting the implementer fix it)."""
    from llmxive.execution.stage import _compute_infra_failures

    for benign in [
        "KeyError: 'accuracy'",
        "FileNotFoundError: data/raw/x.csv",
        "ValueError: could not convert string to float",
    ]:
        assert not _compute_infra_failures([f"python code/x.py -> rc=1\n{benign}"]), benign
