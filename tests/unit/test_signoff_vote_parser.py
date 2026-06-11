"""Regression: publication sign-off vote gate (spec 023 / US5,
FR-019..021 + edge cases).

Real ledger/state files in a hermetic repo; the GitHub boundary is a
recording fake with the ``gh`` tuple protocol; the publisher dispatch is
faked at ``graph.run_one_step`` (its real behavior is covered by
test_publisher_idempotence and the real-call suite).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml

from llmxive.integrations import signoff_gate as sg
from llmxive.speckit._publication_signoff import read_signoff
from llmxive.state import project as project_store
from llmxive.types import Project, Stage

PROJ_ID = "PROJ-920-signoff"
MAINTAINERS = {"jeremymanning", "co-maintainer"}


class _FakeGitHub:
    """Records issue/comment/reaction traffic behind the gh tuple protocol."""

    def __init__(self) -> None:
        self.issues: dict[int, dict] = {}
        self.comments: dict[int, list[dict]] = {}
        self.reactions: dict[int, list[dict]] = {}
        self.posted_comments: list[tuple[int, str]] = []
        self.closed: list[int] = []
        self._next = 200

    def react(self, n: int, user: str, content: str) -> None:
        self.reactions.setdefault(n, []).append(
            {"user": {"login": user}, "content": content}
        )

    def comment_as(self, n: int, user: str, body: str) -> None:
        self.comments.setdefault(n, []).append(
            {"user": {"login": user}, "body": body}
        )

    def __call__(self, *args: str) -> tuple[int, str, str]:
        joined = " ".join(args)
        if "/issues/" in joined and joined.endswith("/reactions?per_page=100"):
            n = int(args[-1].split("/issues/")[1].split("/")[0])
            return 0, json.dumps(self.reactions.get(n, [])), ""
        if "/comments?per_page=100" in joined:
            n = int(args[-1].split("/issues/")[1].split("/")[0])
            return 0, json.dumps(self.comments.get(n, [])), ""
        if "/comments" in joined and "POST" in args:
            n = int(args[1].split("/issues/")[1].split("/")[0])
            body = next(a[5:] for a in args if a.startswith("body="))
            self.posted_comments.append((n, body))
            return 0, "{}", ""
        if joined.endswith("repos/ContextLab/llmXive/issues -X POST") or (
            "issues" in joined and "POST" in args and "title=" in joined
        ):
            self._next += 1
            title = next(a[6:] for a in args if a.startswith("title="))
            self.issues[self._next] = {"title": title}
            return 0, json.dumps({"number": self._next}), ""
        if "PATCH" in args and "state=closed" in joined:
            n = int(args[1].rsplit("/", 1)[1])
            self.closed.append(n)
            return 0, "{}", ""
        if "collaborators" in joined:
            return 0, json.dumps(
                [
                    {"login": m, "permissions": {"push": True}}
                    for m in sorted(MAINTAINERS)
                ]
            ), ""
        return 0, "{}", ""


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    for sub in ("projects", "run-log", "locks"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv(sg.MAINTAINERS_ENV, ",".join(sorted(MAINTAINERS)))
    return tmp_path


@pytest.fixture
def gh() -> _FakeGitHub:
    return _FakeGitHub()


def _bootstrap(repo: Path, *, with_pdf: bool = True) -> Project:
    paper_dir = repo / "projects" / PROJ_ID / "paper"
    (paper_dir / "pdf").mkdir(parents=True, exist_ok=True)
    if with_pdf:
        (paper_dir / "pdf" / "main.pdf").write_bytes(b"%PDF-1.5 fake")
    (paper_dir / "source").mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)
    project = Project(
        id=PROJ_ID,
        title="Sign-off gate test paper",
        field="test",
        current_stage=Stage.AWAITING_PUBLICATION_SIGNOFF,
        created_at=now,
        updated_at=now,
        artifact_hashes={},
        speckit_research_dir=f"projects/{PROJ_ID}/specs/001-t",
        speckit_paper_dir=f"projects/{PROJ_ID}/paper/specs/001-p",
    )
    project_store.save(project, repo_root=repo)
    return project


def test_gate_opens_issue_with_protocol_and_tags(repo: Path, gh: _FakeGitHub) -> None:
    project = _bootstrap(repo)
    action = sg.poll_project(project, repo_root=repo, gh=gh)
    assert action == "opened"
    ledger = sg.read_ledger(PROJ_ID, repo_root=repo)
    n = ledger["issue_number"]
    assert ledger["decision"] == "pending"
    assert n in gh.issues
    assert PROJ_ID in gh.issues[n]["title"]


def test_gate_refuses_without_pdf(repo: Path, gh: _FakeGitHub) -> None:
    project = _bootstrap(repo, with_pdf=False)
    assert sg.poll_project(project, repo_root=repo, gh=gh) == "skipped"
    assert gh.issues == {}, "fail-fast: no compiled PDF → no gate (FR-019)"


def test_approval_by_reaction_publishes_and_closes(
    repo: Path, gh: _FakeGitHub, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _bootstrap(repo)
    sg.poll_project(project, repo_root=repo, gh=gh)
    n = sg.read_ledger(PROJ_ID, repo_root=repo)["issue_number"]
    gh.react(n, "jeremymanning", "+1")

    def fake_publish(p, *, repo_root=None, run_id=None):
        # Simulate the real publisher: writes publication.yaml + POSTED.
        from llmxive.state import publication as pub_state
        from llmxive.types import Publication

        pub = Publication(
            project_id=p.id, title=p.title, volume="01", issue="01",
            display_volume_issue="01.01", doi="10.5281/zenodo.999999",
            doi_url="https://doi.org/10.5281/zenodo.999999",
            concept_doi=None, doi_versions=[], zenodo_id=1,
            zenodo_environment="sandbox", citation_string="x",
            authors_at_publication=[], accepted_at=p.updated_at,
            published_at=datetime.now(UTC), review_summary={},
        )
        pub_state.save(p.id, pub, repo_root=repo_root)
        updated = p.model_copy(update={"current_stage": Stage.POSTED})
        project_store.save(updated, repo_root=repo_root)
        return updated

    import llmxive.pipeline.graph as graph_mod

    monkeypatch.setattr(graph_mod, "run_one_step", fake_publish)

    action = sg.poll_project(project, repo_root=repo, gh=gh)

    assert action == "approved"
    ledger = sg.read_ledger(PROJ_ID, repo_root=repo)
    assert ledger["decision"] == "approved"
    assert ledger["decided_by"] == "jeremymanning"
    assert ledger["doi"] == "10.5281/zenodo.999999"
    assert n in gh.closed, "issue closed with the DOI"
    assert any("10.5281/zenodo.999999" in b for (_n, b) in gh.posted_comments)
    # The FR-054 record the publisher gates on was written by the parser.
    signoff = read_signoff(repo / "projects" / PROJ_ID / ".specify" / "memory")
    assert signoff and signoff["who"] == "jeremymanning"


def test_rejection_with_reason_routes_to_revision_loop(
    repo: Path, gh: _FakeGitHub
) -> None:
    project = _bootstrap(repo)
    sg.poll_project(project, repo_root=repo, gh=gh)
    n = sg.read_ledger(PROJ_ID, repo_root=repo)["issue_number"]
    gh.comment_as(n, "co-maintainer", "reject: figure 3 is mislabeled")

    action = sg.poll_project(project, repo_root=repo, gh=gh)

    assert action == "rejected"
    saved = project_store.load(PROJ_ID, repo_root=repo)
    assert saved.current_stage == Stage.PAPER_REVIEW
    assert saved.revision_spec_path, "the reason became revision work (US1 machinery)"
    spec_tasks = repo / saved.revision_spec_path / "tasks.md"
    assert spec_tasks.is_file()
    assert "figure 3 is mislabeled" in spec_tasks.read_text(encoding="utf-8")
    assert n in gh.closed
    ledger = sg.read_ledger(PROJ_ID, repo_root=repo)
    assert ledger["decision"] == "rejected"
    assert ledger["rejection_reason"] == "figure 3 is mislabeled"


def test_rejection_precedence_over_approval(repo: Path, gh: _FakeGitHub) -> None:
    project = _bootstrap(repo)
    sg.poll_project(project, repo_root=repo, gh=gh)
    n = sg.read_ledger(PROJ_ID, repo_root=repo)["issue_number"]
    gh.react(n, "jeremymanning", "+1")
    gh.comment_as(n, "co-maintainer", "reject: methods section overstates claims")

    action = sg.poll_project(project, repo_root=repo, gh=gh)

    assert action == "rejected", "any maintainer rejection blocks (FR-020)"
    assert any("rejection takes precedence" in b.lower() or "Conflicting" in b
               for (_n, b) in gh.posted_comments), "conflict recorded on the issue"


def test_non_maintainer_votes_ignored(repo: Path, gh: _FakeGitHub) -> None:
    project = _bootstrap(repo)
    sg.poll_project(project, repo_root=repo, gh=gh)
    n = sg.read_ledger(PROJ_ID, repo_root=repo)["issue_number"]
    gh.react(n, "drive-by-account", "+1")
    gh.comment_as(n, "another-rando", "reject: I dislike it")

    action = sg.poll_project(project, repo_root=repo, gh=gh)

    assert action == "waiting"
    assert sg.read_ledger(PROJ_ID, repo_root=repo)["decision"] == "pending"


def test_bare_thumbsdown_prompts_without_deciding(repo: Path, gh: _FakeGitHub) -> None:
    project = _bootstrap(repo)
    sg.poll_project(project, repo_root=repo, gh=gh)
    n = sg.read_ledger(PROJ_ID, repo_root=repo)["issue_number"]
    gh.react(n, "co-maintainer", "-1")

    action = sg.poll_project(project, repo_root=repo, gh=gh)

    assert action == "waiting"
    assert any("reject: <reason>" in b for (_n, b) in gh.posted_comments)
    assert sg.read_ledger(PROJ_ID, repo_root=repo)["decision"] == "pending"
    # The prompt is sent once, not on every poll.
    before = len(gh.posted_comments)
    sg.poll_project(project, repo_root=repo, gh=gh)
    assert len(gh.posted_comments) == before


def test_reminder_after_window_without_blocking(repo: Path, gh: _FakeGitHub) -> None:
    project = _bootstrap(repo)
    sg.poll_project(project, repo_root=repo, gh=gh)
    later = datetime.now(UTC) + timedelta(hours=sg.REMINDER_INTERVAL_HOURS + 1)

    action = sg.poll_project(project, repo_root=repo, gh=gh, now=later)

    assert action == "reminded"
    assert any("Reminder" in b for (_n, b) in gh.posted_comments)
    ledger = sg.read_ledger(PROJ_ID, repo_root=repo)
    assert len(ledger["reminders_sent"]) == 1
    # Within the next window: no spam.
    soon = later + timedelta(hours=1)
    assert sg.poll_project(project, repo_root=repo, gh=gh, now=soon) == "waiting"


def test_decided_ledger_is_idempotent_even_if_issue_vanishes(
    repo: Path, gh: _FakeGitHub
) -> None:
    """Edge case: the issue is edited/deleted after a decision — the local
    ledger is authoritative; no second decision, no double mint."""
    project = _bootstrap(repo)
    ledger = {
        "issue_number": 999,
        "decision": "approved",
        "decided_by": "jeremymanning",
        "doi": "10.5281/zenodo.123",
        "reminders_sent": [],
        "opened_at": datetime.now(UTC).isoformat(),
    }
    p = repo / "projects" / PROJ_ID / "paper" / "signoff.yaml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(ledger), encoding="utf-8")

    assert sg.poll_project(project, repo_root=repo, gh=gh) == "already-decided"
    assert gh.issues == {}, "no new issue, no re-processing"


def test_signoff_stage_never_scheduled(repo: Path) -> None:
    """FR-021: gate-parked projects consume zero scheduler capacity."""
    import random

    from llmxive.pipeline import scheduler

    _bootstrap(repo)
    for seed in range(50):
        assert scheduler.pick_next(repo_root=repo, rng=random.Random(seed)) is None
