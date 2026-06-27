"""Spec 013 / US3 — unit tests for author management (FR-006..FR-008).

Authorship is by MODEL. Covers `collect_contributor_models()` /
`sync_paper_authors()` (reconcile metadata.json::authors to humans + one
entry per distinct paper-content model, reviewers excluded),
`update_latex_author_block()` (preserves originals, appends "Revised by:"
sub-block), and FR-016 immutability of non-`authors` metadata.json fields.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from llmxive.pipeline import authors as authors_module
from llmxive.state import runlog as runlog_store
from llmxive.types import Outcome, RunLogEntry

_NOW = datetime(2026, 5, 19, 10, 14, 0, tzinfo=UTC)
_PROJ = "PROJ-997-author-attribution"


def _write_metadata(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _log(repo: Path, *, agent: str, model: str, outputs: list[str],
         minute: int, outcome: Outcome = Outcome.SUCCESS) -> None:
    """Append one real run-log entry for the author-attribution project."""
    started = datetime(2026, 6, 27, 12, minute, 0, tzinfo=UTC)
    runlog_store.append_entry(
        RunLogEntry(
            run_id=f"run-{minute}",
            entry_id=f"entry-{minute}",
            agent_name=agent,
            project_id=_PROJ,
            task_id="t",
            inputs=[],
            outputs=outputs,
            backend="dartmouth",
            model_name=model,
            prompt_version="1.0.0",
            started_at=started,
            ended_at=started,
            outcome=outcome,
            cost_estimate_usd=0.0,
        ),
        repo_root=repo,
    )


class TestSyncPaperAuthors:
    def _meta(self, repo: Path) -> Path:
        return repo / "projects" / _PROJ / "paper" / "metadata.json"

    def test_collects_distinct_models_excludes_reviewers(self, tmp_path: Path) -> None:
        # Two content models + one reviewer model + a dup + a failure.
        src = f"projects/{_PROJ}/paper/source/main.tex"
        _log(tmp_path, agent="llmxive_implementer", model="model-alpha",
             outputs=[src], minute=10)
        _log(tmp_path, agent="paper_writer", model="model-beta",
             outputs=[f"projects/{_PROJ}/paper/source/sections.tex"], minute=20)
        # Reviewer output goes under paper/reviews/ — NOT authorship.
        _log(tmp_path, agent="paper_reviewer_figure_critic", model="model-gamma",
             outputs=[f"projects/{_PROJ}/paper/reviews/r__2026-06-27__paper.md"],
             minute=30)
        # Same model again, later — must dedupe to ONE entry (earliest date).
        _log(tmp_path, agent="llmxive_implementer", model="model-alpha",
             outputs=[src], minute=40)
        # A failed run must not contribute authorship.
        _log(tmp_path, agent="paper_writer", model="model-delta",
             outputs=[src], minute=50, outcome=Outcome.FAILED)

        models = authors_module.collect_contributor_models(_PROJ, repo_root=tmp_path)
        names = [m.name for m in models]
        assert names == ["model-alpha", "model-beta"]  # sorted by first contribution
        assert all(m.kind == "llm" and m.name == m.model_name for m in models)
        assert "model-gamma" not in names, "reviewers are not authors"
        assert "model-delta" not in names, "failed runs do not confer authorship"

    def test_sync_preserves_humans_and_writes_models(self, tmp_path: Path) -> None:
        meta = self._meta(tmp_path)
        _write_metadata(meta, {
            "title": "P", "arxiv_id": "2605.1",
            "authors": [{"name": "Alice", "kind": "human", "affiliation": "X"},
                        {"name": "Bob", "kind": "human"}],
        })
        _log(tmp_path, agent="llmxive_implementer", model="model-alpha",
             outputs=[f"projects/{_PROJ}/paper/source/main.tex"], minute=10)

        out = authors_module.sync_paper_authors(meta, _PROJ, repo_root=tmp_path)
        data = json.loads(meta.read_text())
        assert [a["name"] for a in data["authors"]] == ["Alice", "Bob", "model-alpha"]
        assert data["authors"][2]["kind"] == "llm"
        assert data["authors"][2]["model_name"] == "model-alpha"
        assert data["arxiv_id"] == "2605.1", "FR-016: other fields untouched"
        assert [a.name for a in out] == ["Alice", "Bob", "model-alpha"]

    def test_sync_is_idempotent_and_self_migrating(self, tmp_path: Path) -> None:
        """A second sync produces the same list; a stale per-AGENT llm entry
        from the older scheme is REPLACED by the per-model entry."""
        meta = self._meta(tmp_path)
        _write_metadata(meta, {"authors": [
            {"name": "Alice", "kind": "human"},
            # legacy agent-named llm entry (old add_implementer scheme):
            {"name": "llmXive-implementer-v1.0", "kind": "llm",
             "agent_version": "1.0.0", "model_name": "model-alpha",
             "backend": "dartmouth"},
        ]})
        _log(tmp_path, agent="llmxive_implementer", model="model-alpha",
             outputs=[f"projects/{_PROJ}/paper/source/main.tex"], minute=10)

        authors_module.sync_paper_authors(meta, _PROJ, repo_root=tmp_path)
        authors_module.sync_paper_authors(meta, _PROJ, repo_root=tmp_path)
        data = json.loads(meta.read_text())
        names = [a["name"] for a in data["authors"]]
        assert names == ["Alice", "model-alpha"], (
            "legacy agent entry replaced by canonical per-model entry; idempotent"
        )

    def test_also_injects_current_unlogged_contribution(self, tmp_path: Path) -> None:
        """The in-flight run's model isn't in the run-log yet — `also` adds it."""
        meta = self._meta(tmp_path)
        _write_metadata(meta, {"authors": [{"name": "Alice", "kind": "human"}]})
        out = authors_module.sync_paper_authors(
            meta, _PROJ, repo_root=tmp_path,
            also=("model-current", "dartmouth", _NOW),
        )
        assert [a.name for a in out] == ["Alice", "model-current"]

    def test_preserves_arxiv_string_authors(self, tmp_path: Path) -> None:
        """Original arXiv authors are stored as bare STRINGS — syncing model
        contributors must NEVER drop them (would wipe the paper's real byline)."""
        meta = self._meta(tmp_path)
        _write_metadata(meta, {"authors": ["Harrison F. Stropkay", "Jiayi Chen"]})
        _log(tmp_path, agent="llmxive_implementer", model="model-alpha",
             outputs=[f"projects/{_PROJ}/paper/source/main.tex"], minute=10)
        out = authors_module.sync_paper_authors(meta, _PROJ, repo_root=tmp_path)
        data = json.loads(meta.read_text())
        # original humans preserved (normalized to dicts) + model appended
        assert [a["name"] for a in data["authors"]] == [
            "Harrison F. Stropkay", "Jiayi Chen", "model-alpha"]
        assert all(a.get("kind") for a in data["authors"]), "homogeneous dicts"
        assert [a.name for a in out] == [
            "Harrison F. Stropkay", "Jiayi Chen", "model-alpha"]

    def test_list_authors_coerces_bare_strings(self, tmp_path: Path) -> None:
        meta = self._meta(tmp_path)
        _write_metadata(meta, {"authors": ["Solo Human", {"name": "D", "kind": "human"}]})
        out = authors_module.list_authors(meta)
        assert [a.name for a in out] == ["Solo Human", "D"]
        assert all(a.kind == "human" for a in out)


class TestListAuthors:
    def test_legacy_untyped_entries_coerced_to_human(self, tmp_path: Path) -> None:
        meta = tmp_path / "metadata.json"
        _write_metadata(meta, {"authors": [{"name": "Old Style"}]})
        out = authors_module.list_authors(meta)
        assert len(out) == 1
        assert out[0].kind == "human"
        assert out[0].name == "Old Style"

    def test_malformed_entries_skipped(self, tmp_path: Path) -> None:
        """Edge Case 5: malformed entries shouldn't crash; they're
        skipped if they can't even round-trip as kind=human."""
        meta = tmp_path / "metadata.json"
        _write_metadata(meta, {"authors": [
            "just a string",                             # not a dict — skipped
            {"name": "Alice"},                           # legacy → human
            {"name": "llm", "kind": "llm", "agent_version": "1.0.0"},
        ]})
        out = authors_module.list_authors(meta)
        names = [a.name for a in out]
        assert "Alice" in names
        assert "llm" in names


class TestUpdateLatexAuthorBlock:
    def _make_tex(self, tmp_path: Path, body: str) -> Path:
        f = tmp_path / "main.tex"
        f.write_text(body, encoding="utf-8")
        return f

    def test_replaces_author_block_with_revised_by(self, tmp_path: Path) -> None:
        from llmxive.types import AuthorEntry
        tex = self._make_tex(
            tmp_path,
            r"\documentclass{article}"
            r"\author{Alice \and Bob}"
            r"\begin{document}body\end{document}"
        )
        authors = [
            AuthorEntry(name="Alice", kind="human"),
            AuthorEntry(name="Bob", kind="human"),
            AuthorEntry(
                name="llmXive-implementer-v1.0", kind="llm",
                agent_version="1.0.0", model_name="qwen.qwen3.5-122b",
                backend="dartmouth", first_contributed_at=_NOW,
            ),
        ]
        changed = authors_module.update_latex_author_block(tex, authors)
        assert changed
        out = tex.read_text()
        assert "Alice" in out
        assert "Bob" in out
        assert "Revised by:" in out
        assert "llmXive-implementer-v1.0" in out

    def test_idempotent_on_rerun(self, tmp_path: Path) -> None:
        from llmxive.types import AuthorEntry
        tex = self._make_tex(
            tmp_path, r"\author{Alice}\begin{document}x\end{document}"
        )
        authors = [
            AuthorEntry(name="Alice", kind="human"),
            AuthorEntry(name="llmXive-implementer-v1.0", kind="llm",
                        agent_version="1.0.0", model_name="m", backend="b",
                        first_contributed_at=_NOW),
        ]
        authors_module.update_latex_author_block(tex, authors)
        # Second call with same inputs should be a no-op.
        changed = authors_module.update_latex_author_block(tex, authors)
        assert not changed

    def test_inserts_author_macro_when_missing(self, tmp_path: Path) -> None:
        from llmxive.types import AuthorEntry
        tex = self._make_tex(
            tmp_path, r"\documentclass{article}\begin{document}x\end{document}"
        )
        authors_module.update_latex_author_block(
            tex, [AuthorEntry(name="Alice", kind="human")],
        )
        assert r"\author{" in tex.read_text()

    def test_empty_authors_returns_false(self, tmp_path: Path) -> None:
        tex = self._make_tex(
            tmp_path, r"\author{Alice}\begin{document}x\end{document}"
        )
        assert authors_module.update_latex_author_block(tex, []) is False

    def test_model_author_byline_lists_model_not_agent(self, tmp_path: Path) -> None:
        """A model-as-author entry (name == model_name) renders the MODEL in
        the byline, without repeating it as a parenthetical agent label."""
        from llmxive.types import AuthorEntry
        tex = self._make_tex(
            tmp_path, r"\author{Alice}\begin{document}x\end{document}"
        )
        authors = [
            AuthorEntry(name="Alice", kind="human"),
            AuthorEntry(name="openai.gpt-oss-120b", kind="llm",
                        model_name="openai.gpt-oss-120b", backend="dartmouth",
                        first_contributed_at=_NOW),
        ]
        authors_module.update_latex_author_block(tex, authors)
        out = tex.read_text()
        assert "Revised by:" in out
        assert "openai.gpt-oss-120b" in out
        assert "via dartmouth" in out
        # the model name appears once in the byline, not duplicated as "X on X"
        assert "openai.gpt-oss-120b on openai.gpt-oss-120b" not in out
