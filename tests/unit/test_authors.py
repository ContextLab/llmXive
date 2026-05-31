"""Spec 013 / US3 — unit tests for author management (FR-006..FR-008).

Covers T031: `add_implementer()` (append-only, deduplicated by
`(name, agent_version)`), `update_latex_author_block()` (preserves
originals, appends "Revised by:" sub-block), and FR-016 immutability
of non-`authors` metadata.json fields.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from llmxive.pipeline import authors as authors_module

_NOW = datetime(2026, 5, 19, 10, 14, 0, tzinfo=UTC)


def _write_metadata(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


class TestAddImplementer:
    def test_appends_to_empty_authors(self, tmp_path: Path) -> None:
        meta = tmp_path / "metadata.json"
        _write_metadata(meta, {"authors": [], "title": "T"})
        ok = authors_module.add_implementer(
            meta,
            agent_name="llmXive-implementer-v1.0",
            agent_version="1.0.0",
            model_name="qwen.qwen3.5-122b",
            backend="dartmouth",
            first_contributed_at=_NOW,
        )
        assert ok is True
        data = json.loads(meta.read_text())
        assert len(data["authors"]) == 1
        a = data["authors"][0]
        assert a["name"] == "llmXive-implementer-v1.0"
        assert a["kind"] == "llm"
        assert a["model_name"] == "qwen.qwen3.5-122b"

    def test_dedup_same_name_and_version(self, tmp_path: Path) -> None:
        meta = tmp_path / "metadata.json"
        _write_metadata(meta, {"authors": []})
        kwargs = dict(
            agent_name="llmXive-implementer-v1.0",
            agent_version="1.0.0",
            model_name="qwen.qwen3.5-122b",
            backend="dartmouth",
            first_contributed_at=_NOW,
        )
        assert authors_module.add_implementer(meta, **kwargs) is True
        assert authors_module.add_implementer(meta, **kwargs) is False
        data = json.loads(meta.read_text())
        assert len(data["authors"]) == 1, "FR-008 dedupe (name, agent_version)"

    def test_different_version_creates_new_entry(self, tmp_path: Path) -> None:
        meta = tmp_path / "metadata.json"
        _write_metadata(meta, {"authors": []})
        common = dict(
            agent_name="llmXive-implementer-v1.0",
            model_name="qwen.qwen3.5-122b",
            backend="dartmouth",
            first_contributed_at=_NOW,
        )
        authors_module.add_implementer(meta, agent_version="1.0.0", **common)
        authors_module.add_implementer(meta, agent_version="2.0.0", **common)
        data = json.loads(meta.read_text())
        assert len(data["authors"]) == 2

    def test_preserves_human_authors(self, tmp_path: Path) -> None:
        meta = tmp_path / "metadata.json"
        humans = [
            {"name": "Alice", "kind": "human", "affiliation": "HKUST"},
            {"name": "Bob", "kind": "human"},
        ]
        _write_metadata(meta, {"authors": list(humans), "title": "Paper"})
        authors_module.add_implementer(
            meta,
            agent_name="llmXive-implementer-v1.0",
            agent_version="1.0.0",
            model_name="m", backend="b", first_contributed_at=_NOW,
        )
        data = json.loads(meta.read_text())
        assert data["authors"][0]["name"] == "Alice"
        assert data["authors"][1]["name"] == "Bob"
        assert data["authors"][2]["kind"] == "llm"

    def test_fr016_other_fields_unchanged(self, tmp_path: Path) -> None:
        """FR-016 closes finding F3: add_implementer must NOT modify
        arxiv_id, title, submitter, or any non-`authors` field."""
        meta = tmp_path / "metadata.json"
        original = {
            "title": "MemLens",
            "arxiv_id": "2605.14906",
            "arxiv_url": "https://arxiv.org/abs/2605.14906",
            "submitter": "alice@example.com",
            "authors": [{"name": "Alice", "kind": "human"}],
            "some_other_field": [1, 2, 3],
        }
        _write_metadata(meta, original)
        authors_module.add_implementer(
            meta,
            agent_name="llmXive-implementer-v1.0",
            agent_version="1.0.0",
            model_name="m", backend="b", first_contributed_at=_NOW,
        )
        after = json.loads(meta.read_text())
        for key in ("title", "arxiv_id", "arxiv_url", "submitter", "some_other_field"):
            assert after[key] == original[key], f"FR-016: {key} must not be modified"


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
