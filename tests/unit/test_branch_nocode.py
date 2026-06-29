"""Tests for the no-code branch of the ingested-paper reprocessor (spec 024).

The deterministic helpers are exercised with a known summary/extension string
(no LLM); the one live test makes a real free-model call to prove the wiring.
Both run against a TMP copy of a real no-code project (seeded into a tmp repo via
``LLMXIVE_REPO_ROOT``) so the live project is never mutated.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.paper_reprocess import branch_nocode
from llmxive.types import Project, Stage

# A real no-code (code: []) ingested project to copy the paper/ from.
_SRC_PROJECT = (
    Path(__file__).resolve().parents[2]
    / "projects"
    / "PROJ-563-many-shot-cot-icl-making-in-context-lear"
)
_PROJ_ID = "PROJ-901-nocode-followup-test"


# --------------------------------------------------------------------------- #
# A real (no third-party dependency) BibTeX parseability check.
# --------------------------------------------------------------------------- #
def _parse_bibtex(text: str) -> list[dict[str, str]]:
    """Parse ``@type{key, field = {value}, ...}`` entries by brace-matching.

    Returns one dict per entry: ``{"_type", "_key", <field>: <value>, ...}``.
    Raises ValueError on unbalanced braces (i.e. an unparseable entry) so the
    test fails loudly rather than silently accepting garbage.
    """
    entries: list[dict[str, str]] = []
    for m in re.finditer(r"@(\w+)\s*\{", text):
        entry_type = m.group(1)
        # Walk braces from the opening '{' to find the matching close.
        depth = 0
        start = m.end() - 1  # at the '{'
        j = start
        while j < len(text):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if depth != 0:
            raise ValueError(f"unbalanced braces in {entry_type} entry near offset {start}")
        inner = text[start + 1 : j]
        # First comma-separated token is the cite key; rest are fields.
        key, _, rest = inner.partition(",")
        entry: dict[str, str] = {"_type": entry_type.lower(), "_key": key.strip()}
        # Field = {value} pairs (brace-delimited values, may contain commas).
        for fm in re.finditer(r"(\w+)\s*=\s*\{([^{}]*)\}", rest):
            entry[fm.group(1).lower()] = fm.group(2).strip()
        entries.append(entry)
    if not entries:
        raise ValueError("no @-entries found")
    return entries


# --------------------------------------------------------------------------- #
# Fixtures: a tmp repo containing a COPY of the real project's paper/.
# --------------------------------------------------------------------------- #
@pytest.fixture
def tmp_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Seed a hermetic repo: copy the real project's ``paper/`` into a tmp repo,
    point ``LLMXIVE_REPO_ROOT`` at it, and seed the project-state YAML so
    ``state.project.save``'s history diff has a prior to load."""
    repo = tmp_path / "repo"
    pdir = repo / "projects" / _PROJ_ID
    pdir.mkdir(parents=True)
    shutil.copytree(_SRC_PROJECT / "paper", pdir / "paper")

    # The agent registry is PLATFORM config; the hermetic repo needs it so the
    # registry resolves under $LLMXIVE_REPO_ROOT. Symlink the real agents/ tree
    # (read-only; the test never mutates it).
    real_repo = Path(__file__).resolve().parents[2]
    (repo / "agents").symlink_to(real_repo / "agents")
    # An intake-stub idea file the follow-up must replace.
    (pdir / "idea").mkdir()
    (pdir / "idea" / "stub.md").write_text("---\nfield: other\n---\n\n# Stub\n", encoding="utf-8")

    # Seed the canonical project-state file at paper_ingested (the pre-transform
    # stage). The agents/ + state/ dirs are read from the *real* repo via the
    # package; only projects/ + state/projects/ live in the tmp repo.
    state_dir = repo / "state" / "projects"
    state_dir.mkdir(parents=True)
    now = datetime.now(UTC)
    proj = Project(
        id=_PROJ_ID,
        title="Many-Shot CoT-ICL: Making In-Context Learning Truly Learn",
        field="computer science",
        current_stage=Stage.PAPER_INGESTED,
        created_at=now,
        updated_at=now,
    )
    from llmxive.state import project as project_store

    # registry/contracts resolve from the real repo root, but project-state and
    # projects/ resolve from repo_root we pass explicitly.
    project_store.save(proj, repo_root=repo)

    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(repo))
    return repo


def _load_project(repo: Path) -> Project:
    from llmxive.state import project as project_store

    return project_store.load(_PROJ_ID, repo_root=repo)


def _metadata(repo: Path) -> dict:
    return json.loads(
        (repo / "projects" / _PROJ_ID / "paper" / "metadata.json").read_text(encoding="utf-8")
    )


_EXTENSION = (
    "## Summary of the prior work\n"
    "The paper studies many-shot chain-of-thought in-context learning.\n\n"
    "## Proposed extension\n"
    "Does interleaving self-generated rationales improve few-shot accuracy on a "
    "CPU-tractable text-classification benchmark?\n\n"
    "## Methodology sketch\n"
    "Use a small open model on AG-News; compare interleaved vs. block prompts.\n"
)


# --------------------------------------------------------------------------- #
# Deterministic (no-LLM) tests
# --------------------------------------------------------------------------- #
def test_bibtex_entry_parseable_and_cites_arxiv(tmp_repo: Path):
    meta = _metadata(tmp_repo)
    entry_text = branch_nocode.build_bibtex_entry(meta)
    parsed = _parse_bibtex(entry_text)
    assert len(parsed) == 1
    e = parsed[0]
    assert e["_type"] == "article"
    assert meta["arxiv_id"] in e.get("eprint", "") or meta["arxiv_id"] in e.get("journal", "")
    assert e.get("title", "").startswith("Many-Shot CoT-ICL")
    # Original authors are still in the citation even though we drop the byline.
    assert "Tsz Ting Chung" in e.get("author", "")


def test_transform_drops_authors_cites_and_writes_brainstormed(tmp_repo: Path):
    project = _load_project(tmp_repo)
    pdir = tmp_repo / "projects" / _PROJ_ID
    meta = _metadata(tmp_repo)
    assert meta["authors"], "precondition: original project has authors"

    updated = branch_nocode.transform_to_followup(
        project,
        repo_root=tmp_repo,
        extension_body=_EXTENSION,
        metadata=meta,
        pdir=pdir,
    )

    # 1. Returned + persisted stage is brainstormed.
    assert updated.current_stage == Stage.BRAINSTORMED
    assert _load_project(tmp_repo).current_stage == Stage.BRAINSTORMED
    assert updated.updated_at >= project.updated_at

    # 2. metadata.json::authors dropped to [].
    assert _metadata(tmp_repo)["authors"] == []

    # 3. reference.bib has a parseable @article for the arxiv_id.
    bib = (pdir / "paper" / "source" / "reference.bib").read_text(encoding="utf-8")
    parsed = _parse_bibtex(bib)
    assert any(meta["arxiv_id"] in (e.get("eprint", "") + e.get("journal", "")) for e in parsed)

    # 4. The idea file matches the brainstormed format + Builds-on lineage.
    idea_files = list((pdir / "idea").glob("*.md"))
    assert len(idea_files) == 1, "stub replaced by exactly one follow-up idea"
    idea = idea_files[0].read_text(encoding="utf-8")
    assert idea.startswith("---\n")
    assert "field: computer science" in idea
    assert "paper_authors:" not in idea  # byline cleared
    assert idea.split("---", 2)[2].lstrip().startswith("# ")  # title heading after FM
    assert "**Builds on**" in idea
    assert meta["arxiv_url"] in idea
    assert "Proposed extension" in idea  # the extension body is embedded


def test_assemble_paper_text_caps_and_includes_abstract(tmp_repo: Path):
    pdir = tmp_repo / "projects" / _PROJ_ID
    meta = _metadata(tmp_repo)
    text = branch_nocode.assemble_paper_text(pdir, meta, max_chars=2000)
    assert len(text) <= 2000 + 40  # cap + truncation marker
    assert "Abstract" in text
    assert meta["title"] in text


def test_bibtex_idempotent_on_rerun(tmp_repo: Path):
    project = _load_project(tmp_repo)
    pdir = tmp_repo / "projects" / _PROJ_ID
    meta = _metadata(tmp_repo)
    branch_nocode.transform_to_followup(
        project, repo_root=tmp_repo, extension_body=_EXTENSION, metadata=meta, pdir=pdir
    )
    # Re-run with the (now author-less) metadata: bib must keep the original
    # citation and not duplicate the entry.
    meta2 = _metadata(tmp_repo)
    branch_nocode.transform_to_followup(
        project, repo_root=tmp_repo, extension_body=_EXTENSION, metadata=meta2, pdir=pdir
    )
    bib = (pdir / "paper" / "source" / "reference.bib").read_text(encoding="utf-8")
    assert bib.count("@article{") == 1


# --------------------------------------------------------------------------- #
# Live real-call test (one real free-model call). Gated behind LLMXIVE_REAL_TESTS.
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(
    not os.environ.get("LLMXIVE_REAL_TESTS"),
    reason="set LLMXIVE_REAL_TESTS=1 for the real free-model end-to-end run",
)
def test_to_followup_idea_live(tmp_repo: Path):
    project = _load_project(tmp_repo)
    updated = branch_nocode.to_followup_idea(project, repo_root=tmp_repo)

    assert updated.current_stage == Stage.BRAINSTORMED
    pdir = tmp_repo / "projects" / _PROJ_ID

    # Authors dropped + original cited.
    assert _metadata(tmp_repo)["authors"] == []
    bib = (pdir / "paper" / "source" / "reference.bib").read_text(encoding="utf-8")
    parsed = _parse_bibtex(bib)
    arxiv = "2605.13511"
    assert any(arxiv in (e.get("eprint", "") + e.get("journal", "")) for e in parsed)

    # The idea exists, is non-trivial, and cites the original.
    idea = next((pdir / "idea").glob("*.md")).read_text(encoding="utf-8")
    assert "**Builds on**" in idea
    assert arxiv in idea
    # The model body is present (some real content beyond the lineage boilerplate).
    body = idea.split("agents; the original authors are credited only via the citation in", 1)[-1]
    assert len(body.strip()) > 80, "LLM extension body should be non-trivial"

    # Surface the produced idea title for the report.
    title = next(line for line in idea.splitlines() if line.startswith("# "))
    print(f"\n[live] produced idea title: {title}")
    print(f"[live] cites original arXiv {arxiv}: True")
