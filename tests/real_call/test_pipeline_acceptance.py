"""Real calls, real execution, real paper: the full-pipeline acceptance gate."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_E2E_FULL") != "1",
    reason="set LLMXIVE_E2E_FULL=1 for the complete research-to-paper canary",
)


def test_complete_research_and_paper(tmp_path: Path, monkeypatch) -> None:
    from llmxive.pipeline.acceptance import run
    from llmxive.repair.runner import copy_platform
    from llmxive.state import project as store
    from llmxive.types import Project, Stage

    source = Path(__file__).resolve().parents[2]
    repo = tmp_path / "canary"
    copy_platform(source, repo)
    shutil.copytree(source / "papers/.style", repo / "papers/.style")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=canary",
            "-c",
            "user.email=canary@localhost",
            "commit",
            "-qm",
            "platform snapshot",
        ],
        cwd=repo,
        check=True,
    )
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(repo))
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "0")
    # No outbound issues/comments or publication credentials in this test.
    monkeypatch.setenv("GH_CONFIG_DIR", str(tmp_path / "empty-gh"))
    for key in ("GH_TOKEN", "GITHUB_TOKEN", "ZENODO_API_TOKEN", "ZENODO_SANDBOX_API_TOKEN"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(repo)
    pid = "PROJ-9999-totient-canary"
    shutil.copytree(source / "tests/real_call/fixtures" / pid, repo / "projects" / pid)
    now = datetime.now(UTC)
    store.save(
        Project(
            id=pid,
            title="Finite-range residue imbalance of Euler's totient",
            field="mathematics",
            current_stage=Stage.FLESH_OUT_COMPLETE,
            points_research={},
            points_paper={},
            created_at=now,
            updated_at=now,
            artifact_hashes={},
        ),
        repo_root=repo,
    )
    # Keep evidence outside pytest temp cleanup when CI requests an artifact directory.
    evidence_dir = os.environ.get("LLMXIVE_ACCEPTANCE_ARTIFACTS")
    try:
        result = run(pid, repo, budget_s=14400)
        assert result["status"] == "accepted", json.dumps(result)
    finally:
        if evidence_dir:
            dest = Path(evidence_dir).resolve()
            dest.mkdir(parents=True, exist_ok=True)
            for name in ("projects", "state", "notes"):
                if (repo / name).exists():
                    shutil.copytree(
                        repo / name,
                        dest / name,
                        dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(".venv", "__pycache__", ".runtime-home"),
                    )
