"""Regression: publication is idempotent and resumable (spec 023 / FR-020
edge case: "DOI minting succeeds but the final state write fails — or vice
versa — re-running the publisher must not mint a second DOI and must
converge to a consistent posted state").

Real project/publication state in a hermetic repo (``LLMXIVE_REPO_ROOT``);
the Zenodo HTTP client and the LaTeX compile subprocess are faked at their
external boundaries (recording fakes; the real client is exercised by the
sandbox real-call suite).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
import yaml

from llmxive.agents import publisher as publisher_mod
from llmxive.agents.base import AgentContext
from llmxive.agents.publisher import PaperPublisher
from llmxive.speckit._publication_signoff import write_signoff
from llmxive.state import project as project_store
from llmxive.state import publication as pub_state
from llmxive.types import (
    AgentRegistryEntry,
    Project,
    Publication,
    Stage,
)

PROJ_ID = "PROJ-921-idem"


class _FakeZenodo:
    """External-boundary fake with the ZenodoClient surface."""

    instances: list[_FakeZenodo] = []

    def __init__(self, *, sandbox: bool = False, timeout: float = 60.0):
        self.sandbox = sandbox
        self.created: list[dict] = []
        self.published_ids: list[int] = []
        self.uploads: list[str] = []
        self._depositions: dict[int, dict] = dict(_FakeZenodo.seed_depositions)
        _FakeZenodo.instances.append(self)

    seed_depositions: dict[int, dict] = {}

    def create_deposition(self, metadata):
        from llmxive.pipeline.zenodo import Deposition

        dep_id = 5000 + len(self.created)
        self.created.append(metadata)
        self._depositions[dep_id] = {"id": dep_id, "submitted": False}
        return Deposition(
            deposition_id=dep_id,
            doi=f"10.5281/zenodo.{dep_id}",
            bucket_url="https://bucket.example/b1",
            publish_url="https://publish.example/p1",
            raw={},
        )

    def upload_file(self, bucket_url, name, content):
        self.uploads.append(name)

    def publish(self, deposition_id):
        from llmxive.pipeline.zenodo import PublishedDeposition

        self.published_ids.append(deposition_id)
        self._depositions[deposition_id] = {
            "id": deposition_id, "submitted": True,
            "doi": f"10.5281/zenodo.{deposition_id}",
        }
        return PublishedDeposition(
            deposition_id=deposition_id,
            doi=f"10.5281/zenodo.{deposition_id}",
            doi_url=f"https://doi.org/10.5281/zenodo.{deposition_id}",
            concept_doi=None,
            raw={},
        )

    def get_deposition(self, deposition_id):
        from llmxive.pipeline.zenodo import ZenodoAPIError

        if deposition_id not in self._depositions:
            raise ZenodoAPIError(404, "not found")
        d = self._depositions[deposition_id]
        return {
            "id": d["id"],
            "submitted": d.get("submitted", False),
            "doi": d.get("doi", ""),
            "doi_url": f"https://doi.org/{d.get('doi', '')}",
            "links": {"bucket": "https://bucket.example/b1"},
            "metadata": {"prereserve_doi": {"doi": d.get("doi", "")}},
        }

    def new_version(self, deposition_id):  # pragma: no cover — not used here
        raise AssertionError("new_version must not be called in these tests")


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    for sub in ("projects", "run-log", "locks"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    monkeypatch.setenv("LLMXIVE_ZENODO_ENV", "sandbox")
    _FakeZenodo.instances = []
    _FakeZenodo.seed_depositions = {}
    monkeypatch.setattr(publisher_mod.zenodo_module, "ZenodoClient", _FakeZenodo)
    monkeypatch.setattr(
        publisher_mod, "_compile_full", lambda source_dir: (True, b"%PDF-1.5 ok")
    )
    return tmp_path


def _bootstrap(repo: Path) -> Project:
    paper_dir = repo / "projects" / PROJ_ID / "paper"
    (paper_dir / "source").mkdir(parents=True, exist_ok=True)
    (paper_dir / "source" / "main.tex").write_text(
        "\\documentclass{article}\\begin{document}x\\end{document}\n",
        encoding="utf-8",
    )
    (paper_dir / "metadata.json").write_text(
        '{"title": "Idempotence test paper", "abstract": "a"}', encoding="utf-8"
    )
    now = datetime.now(UTC)
    project = Project(
        id=PROJ_ID,
        title="Idempotence test paper",
        field="test",
        current_stage=Stage.AWAITING_PUBLICATION_SIGNOFF,
        created_at=now,
        updated_at=now,
        artifact_hashes={},
        speckit_research_dir=f"projects/{PROJ_ID}/specs/001-t",
        speckit_paper_dir=f"projects/{PROJ_ID}/paper/specs/001-p",
    )
    project_store.save(project, repo_root=repo)
    write_signoff(
        repo / "projects" / PROJ_ID / ".specify" / "memory",
        who="maintainer", what="test sign-off",
    )
    return project


REAL_REPO = Path(__file__).resolve().parents[2]


def _entry() -> AgentRegistryEntry:
    from llmxive.agents.registry import load

    reg = load(repo_root=REAL_REPO)
    return next(e for e in reg.agents if e.name == "paper_publisher")


def _run(repo: Path):
    agent = PaperPublisher(_entry())
    entry = agent.run(
        AgentContext(
            project_id=PROJ_ID, run_id=str(uuid4()), task_id=str(uuid4()),
            inputs=[], metadata={},
        )
    )
    assert entry.failure_reason is None or "already published" in (
        entry.failure_reason or ""
    ), f"publisher run failed: {entry.failure_reason}"
    return entry


def test_happy_path_mints_once_and_posts(repo: Path) -> None:
    _bootstrap(repo)
    _run(repo)
    saved = project_store.load(PROJ_ID, repo_root=repo)
    assert saved.current_stage == Stage.POSTED
    pub = pub_state.load(PROJ_ID, repo_root=repo)
    assert pub and pub.doi.startswith("10.5281/zenodo.")
    client = _FakeZenodo.instances[-1]
    assert len(client.created) == 1
    assert len(client.published_ids) == 1
    # The recovery ledger is cleaned up after the state write.
    assert not (repo / "projects" / PROJ_ID / "paper" / ".zenodo_draft.yaml").exists()


def test_rerun_after_state_write_failure_converges_without_second_mint(
    repo: Path,
) -> None:
    """Mint succeeded; state write 'failed' (simulated by resetting the
    stage while keeping publication.yaml). Re-run converges to POSTED
    without ANY Zenodo call."""
    project = _bootstrap(repo)
    pub = Publication(
        project_id=PROJ_ID, title=project.title, volume="01", issue="01",
        display_volume_issue="01.01", doi="10.5281/zenodo.4242",
        doi_url="https://doi.org/10.5281/zenodo.4242", concept_doi=None,
        doi_versions=[], zenodo_id=4242, zenodo_environment="sandbox",
        citation_string="x", authors_at_publication=[],
        accepted_at=project.updated_at, published_at=datetime.now(UTC),
        review_summary={},
    )
    pub_state.save(PROJ_ID, pub, repo_root=repo)

    _run(repo)

    saved = project_store.load(PROJ_ID, repo_root=repo)
    assert saved.current_stage == Stage.POSTED
    # Convergence happens BEFORE the Zenodo client is even constructed —
    # no client instance, no remote call, no second DOI.
    assert _FakeZenodo.instances == []
    assert pub_state.load(PROJ_ID, repo_root=repo).doi == "10.5281/zenodo.4242"


def test_rerun_after_publish_crash_resumes_same_deposition(repo: Path) -> None:
    """The draft ledger records the deposition; the remote publish
    SUCCEEDED but the run crashed before publication.yaml. The re-run
    fetches the deposition, sees submitted=true, adopts its DOI — no
    create, no second publish."""
    _bootstrap(repo)
    paper_dir = repo / "projects" / PROJ_ID / "paper"
    (paper_dir / ".zenodo_draft.yaml").write_text(
        yaml.safe_dump(
            {
                "deposition_id": 7777,
                "doi": "10.5281/zenodo.7777",
                "environment": "sandbox",
                "created_at": datetime.now(UTC).isoformat(),
            }
        ),
        encoding="utf-8",
    )
    _FakeZenodo.seed_depositions = {
        7777: {"id": 7777, "submitted": True, "doi": "10.5281/zenodo.7777"}
    }

    _run(repo)

    saved = project_store.load(PROJ_ID, repo_root=repo)
    assert saved.current_stage == Stage.POSTED
    pub = pub_state.load(PROJ_ID, repo_root=repo)
    assert pub and pub.doi == "10.5281/zenodo.7777", "the ORIGINAL DOI was adopted"
    client = _FakeZenodo.instances[-1]
    assert client.created == [], "no new deposition"
    assert client.published_ids == [], "no second publish"
    assert not (paper_dir / ".zenodo_draft.yaml").exists()


def test_rerun_with_unpublished_draft_reuses_it(repo: Path) -> None:
    """Crash AFTER draft creation but BEFORE publish: the re-run reuses
    the drafted deposition (same pre-reserved DOI), uploading + publishing
    it instead of creating a duplicate."""
    _bootstrap(repo)
    paper_dir = repo / "projects" / PROJ_ID / "paper"
    (paper_dir / ".zenodo_draft.yaml").write_text(
        yaml.safe_dump(
            {
                "deposition_id": 8888,
                "doi": "10.5281/zenodo.8888",
                "environment": "sandbox",
                "created_at": datetime.now(UTC).isoformat(),
            }
        ),
        encoding="utf-8",
    )
    _FakeZenodo.seed_depositions = {8888: {"id": 8888, "submitted": False,
                                           "doi": "10.5281/zenodo.8888"}}

    _run(repo)

    client = _FakeZenodo.instances[-1]
    assert client.created == [], "draft reused, not recreated"
    assert client.published_ids == [8888]
    pub = pub_state.load(PROJ_ID, repo_root=repo)
    assert pub and pub.doi == "10.5281/zenodo.8888"
