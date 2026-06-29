"""Classifier + migration for the paper-reprocessor (spec 024).

Deterministic (no LLM, no network): the branch transforms are tested in
test_branch_nocode / test_branch_code; here we pin the code-vs-no-code
classification and the self-guarding migration predicate.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from llmxive.paper_reprocess.classify import (
    classify_paper,
    code_repos,
    normalize_repo_url,
)
from llmxive.paper_reprocess.migrate import (
    is_unprocessed_external_paper,
    migrate_unprocessed_external_papers,
)
from llmxive.state import project as project_store
from llmxive.types import Project, Stage


# ── classifier ──────────────────────────────────────────────────────────────
@pytest.mark.parametrize("url,expected", [
    ("https://github.com/foo/bar", "https://github.com/foo/bar"),
    ("https://github.com/foo/bar/blob/main/x.py", "https://github.com/foo/bar"),
    ("https://github.com/foo/bar/tree/dev/sub", "https://github.com/foo/bar"),
    ("https://github.com/foo/bar.git", "https://github.com/foo/bar"),
    ("https://gitlab.com/a/b", "https://gitlab.com/a/b"),
    ("https://github.com/orgs/SomeOrg", None),          # org page, not a repo
    ("https://huggingface.co/datasets/foo/bar", None),  # data, not code
    ("https://example.com/foo/bar", None),              # not a code host
    ("not a url", None),
])
def test_normalize_repo_url(url, expected) -> None:
    assert normalize_repo_url(url) == expected


def test_code_repos_dedups_and_normalizes() -> None:
    meta = {"code": [
        "https://github.com/foo/bar",
        "https://github.com/foo/bar/blob/main/run.py",  # same repo, different path
        "https://github.com/baz/qux.git",
        "https://example.com/not/code",
    ]}
    assert code_repos(meta) == [
        "https://github.com/foo/bar",
        "https://github.com/baz/qux",
    ]


def _make_paper_project(repo, pid, *, stage=Stage.PAPER_REVIEW, code=None,
                        arxiv_id="2605.00001", speckit_research_dir=None) -> Project:
    pdir = repo / "projects" / pid / "paper"
    pdir.mkdir(parents=True)
    (repo / "state" / "projects").mkdir(parents=True, exist_ok=True)
    meta = {"title": "T", "authors": ["A. Author"], "code": code or []}
    if arxiv_id is not None:
        meta["arxiv_id"] = arxiv_id
    (pdir / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
    now = datetime.now(UTC)
    p = Project(id=pid, title="T", field="cs", current_stage=stage,
                created_at=now, updated_at=now,
                speckit_research_dir=speckit_research_dir)
    project_store.save(p, repo_root=repo)
    return p


def test_classify_paper_code_vs_nocode(tmp_path) -> None:
    _make_paper_project(tmp_path, "PROJ-810-x", code=["https://github.com/o/r"])
    _make_paper_project(tmp_path, "PROJ-811-y", code=[])
    assert classify_paper(tmp_path / "projects" / "PROJ-810-x") == "code"
    assert classify_paper(tmp_path / "projects" / "PROJ-811-y") == "nocode"


# ── migration (self-guarding predicate) ─────────────────────────────────────
def test_predicate_matches_only_bare_external_at_paper_review(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    # bare external intake at paper_review -> YES
    ext = _make_paper_project(tmp_path, "PROJ-820-ext")
    assert is_unprocessed_external_paper(ext, tmp_path / "projects" / "PROJ-820-ext")
    # an AUTHORED paper at paper_review (speckit_research_dir set) -> NO
    authored = _make_paper_project(tmp_path, "PROJ-821-auth",
                                   speckit_research_dir="projects/PROJ-821-auth/specs/001-x")
    assert not is_unprocessed_external_paper(authored, tmp_path / "projects" / "PROJ-821-auth")
    # not at paper_review -> NO
    elsewhere = _make_paper_project(tmp_path, "PROJ-822-bs", stage=Stage.BRAINSTORMED)
    assert not is_unprocessed_external_paper(elsewhere, tmp_path / "projects" / "PROJ-822-bs")
    # no external arxiv_id -> NO
    noext = _make_paper_project(tmp_path, "PROJ-823-noid", arxiv_id=None)
    assert not is_unprocessed_external_paper(noext, tmp_path / "projects" / "PROJ-823-noid")


def test_migrate_moves_matches_and_is_idempotent(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    _make_paper_project(tmp_path, "PROJ-830-a")
    _make_paper_project(tmp_path, "PROJ-831-b")
    _make_paper_project(tmp_path, "PROJ-832-auth",
                        speckit_research_dir="projects/PROJ-832-auth/specs/001-x")
    # dry-run reports the two, mutates nothing
    assert sorted(migrate_unprocessed_external_papers(repo_root=tmp_path, dry_run=True)) == \
        ["PROJ-830-a", "PROJ-831-b"]
    assert project_store.load("PROJ-830-a", repo_root=tmp_path).current_stage == Stage.PAPER_REVIEW
    # real run migrates them
    assert sorted(migrate_unprocessed_external_papers(repo_root=tmp_path)) == \
        ["PROJ-830-a", "PROJ-831-b"]
    assert project_store.load("PROJ-830-a", repo_root=tmp_path).current_stage == Stage.PAPER_INGESTED
    assert project_store.load("PROJ-832-auth", repo_root=tmp_path).current_stage == Stage.PAPER_REVIEW
    # idempotent: nothing left to migrate
    assert migrate_unprocessed_external_papers(repo_root=tmp_path) == []
