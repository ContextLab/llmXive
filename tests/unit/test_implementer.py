"""Spec 013 / US1+US2 — unit tests for the llmXive-implementer agent.

Covers:
  - T012: edit-application helpers (search_and_replace, unified_diff,
    FR-017 deletion guard)
  - T013: per-task snapshot + rollback
  - T024 / FR-019 / US2: path validation for writing vs science severity
"""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

import pytest

from llmxive.agents.implementer import (
    apply_search_and_replace,
    apply_unified_diff,
    _is_forbidden_deletion,
    _parse_llm_edit,
    _restore,
    _snapshot,
    _validate_edit_path,
)


# ---- search_and_replace --------------------------------------------------

class TestSearchAndReplace:
    def test_single_match_applies_and_records_hashes(self, tmp_path: Path) -> None:
        f = tmp_path / "main.tex"
        f.write_text("intro\nbody\noutro\n")
        before_hash = hashlib.sha256(f.read_bytes()).hexdigest()
        r = apply_search_and_replace(f, "body", "BODY")
        assert r.applied
        assert f.read_text() == "intro\nBODY\noutro\n"
        assert r.before_hashes[str(f)] == before_hash
        assert r.after_hashes[str(f)] == hashlib.sha256(f.read_bytes()).hexdigest()

    def test_multi_match_rejected_as_ambiguous(self, tmp_path: Path) -> None:
        f = tmp_path / "main.tex"
        f.write_text("foo\nfoo\nfoo\n")
        r = apply_search_and_replace(f, "foo", "bar")
        assert not r.applied
        assert r.reject_reason is not None
        assert "ambiguous" in r.reject_reason
        assert f.read_text() == "foo\nfoo\nfoo\n"  # untouched

    def test_no_match_rejected(self, tmp_path: Path) -> None:
        f = tmp_path / "main.tex"
        f.write_text("hello\n")
        r = apply_search_and_replace(f, "missing", "x")
        assert not r.applied
        assert "no-match" in (r.reject_reason or "")

    def test_file_not_found(self, tmp_path: Path) -> None:
        r = apply_search_and_replace(tmp_path / "ghost.tex", "x", "y")
        assert not r.applied
        assert "file-not-found" in (r.reject_reason or "")

    def test_fr017_abstract_deletion_rejected(self, tmp_path: Path) -> None:
        """FR-017 (closes finding F4): forbid whole-section / abstract /
        bibliography deletions even via search_and_replace."""
        f = tmp_path / "main.tex"
        body = r"\begin{abstract}" + "\nthe abstract\n" + r"\end{abstract}"
        f.write_text(body)
        r = apply_search_and_replace(f, body, "")
        assert not r.applied
        assert "FR-017" in (r.reject_reason or "")
        assert f.read_text() == body  # untouched

    def test_fr017_bibliography_deletion_rejected(self, tmp_path: Path) -> None:
        f = tmp_path / "main.tex"
        f.write_text(r"prose \bibliography{ref} more prose")
        r = apply_search_and_replace(f, r"\bibliography{ref}", "")
        assert not r.applied
        assert "FR-017" in (r.reject_reason or "")

    def test_fr017_thebibliography_env_deletion_rejected(self, tmp_path: Path) -> None:
        f = tmp_path / "main.tex"
        env = (r"\begin{thebibliography}{99}" + "\n\\bibitem{a} A.\n" +
               r"\end{thebibliography}")
        f.write_text(env)
        r = apply_search_and_replace(f, env, "")
        assert not r.applied
        assert "FR-017" in (r.reject_reason or "")

    def test_fr017_allows_replace_with_content(self, tmp_path: Path) -> None:
        """Replacing the abstract with NEW content is allowed; only
        delete-to-empty is forbidden."""
        f = tmp_path / "main.tex"
        body = r"\begin{abstract}" + "old\n" + r"\end{abstract}"
        f.write_text(body)
        r = apply_search_and_replace(f, body, body.replace("old", "new"))
        assert r.applied


# ---- unified_diff --------------------------------------------------------

class TestUnifiedDiff:
    def test_clean_diff_applies(self, tmp_path: Path) -> None:
        f = tmp_path / "doc.tex"
        f.write_text("line1\nline2\nline3\n")
        diff = (
            "--- a/doc.tex\n+++ b/doc.tex\n"
            "@@ -1,3 +1,3 @@\n line1\n-line2\n+LINE2\n line3\n"
        )
        r = apply_unified_diff(f, diff)
        assert r.applied, r.reject_reason
        assert "LINE2" in f.read_text()

    def test_check_failure_rejected(self, tmp_path: Path) -> None:
        f = tmp_path / "doc.tex"
        f.write_text("alpha\n")
        # Diff references content not in the file.
        diff = (
            "--- a/doc.tex\n+++ b/doc.tex\n"
            "@@ -1,1 +1,1 @@\n-something else\n+new\n"
        )
        r = apply_unified_diff(f, diff)
        assert not r.applied
        assert "git apply --check" in (r.reject_reason or "") or "check failed" in (r.reject_reason or "")

    def test_diff_with_unexpected_file_rejected(self, tmp_path: Path) -> None:
        """Defensive: a diff that names paths outside our target file is
        rejected so the LLM can't accidentally rewrite other files."""
        f = tmp_path / "doc.tex"
        f.write_text("x\n")
        diff = "--- a/other.tex\n+++ b/other.tex\n@@ -1,1 +1,1 @@\n-x\n+y\n"
        r = apply_unified_diff(f, diff)
        assert not r.applied
        assert "unexpected files" in (r.reject_reason or "")


# ---- snapshot + rollback (T013) ------------------------------------------

class TestSnapshotRollback:
    def test_snapshot_captures_bytes(self, tmp_path: Path) -> None:
        f = tmp_path / "x.tex"
        f.write_bytes(b"original\n")
        snap = _snapshot([f])
        assert snap[f] == b"original\n"

    def test_restore_returns_file_to_exact_prior_bytes(self, tmp_path: Path) -> None:
        f = tmp_path / "x.tex"
        f.write_bytes(b"v1\n")
        snap = _snapshot([f])
        f.write_bytes(b"v2 (modified)\n")
        _restore(snap)
        assert f.read_bytes() == b"v1\n"

    def test_restore_removes_file_that_didnt_exist(self, tmp_path: Path) -> None:
        """If snapshot was taken when file didn't exist (snapshot stores
        empty bytes), restore removes it."""
        f = tmp_path / "new.tex"
        snap = _snapshot([f])  # f doesn't exist; snap[f] == b""
        f.write_bytes(b"created later\n")
        _restore(snap)
        assert not f.is_file()

    def test_round_trip_via_apply_then_snapshot_restore(self, tmp_path: Path) -> None:
        """Integration: apply_search_and_replace → snapshot was taken
        BEFORE → restore returns to that pre-edit state."""
        f = tmp_path / "x.tex"
        f.write_bytes(b"hello world\n")
        snap = _snapshot([f])
        r = apply_search_and_replace(f, "hello", "HELLO")
        assert r.applied
        assert f.read_text() == "HELLO world\n"
        _restore(snap)
        assert f.read_bytes() == b"hello world\n"


# ---- LLM edit parsing ----------------------------------------------------

class TestLLMEditParsing:
    def test_plain_json(self) -> None:
        e = _parse_llm_edit('{"kind":"search_and_replace","file":"a","search":"b","replace":"c"}')
        assert e is not None
        assert e["kind"] == "search_and_replace"

    def test_markdown_fenced(self) -> None:
        text = '```json\n{"kind":"unified_diff","file":"a","diff":"..."}\n```'
        e = _parse_llm_edit(text)
        assert e is not None
        assert e["kind"] == "unified_diff"

    def test_prose_around_json(self) -> None:
        text = 'Sure! Here is my edit:\n{"kind":"search_and_replace","file":"a","search":"b","replace":"c"}\nLet me know.'
        e = _parse_llm_edit(text)
        assert e is not None

    def test_missing_kind_returns_none(self) -> None:
        e = _parse_llm_edit('{"file":"a","search":"b"}')
        assert e is None

    def test_garbage_returns_none(self) -> None:
        assert _parse_llm_edit("this is not JSON at all") is None
        assert _parse_llm_edit("") is None


# ---- Path validation (FR-019, US2) ---------------------------------------

class TestPathValidation:
    def test_writing_allows_paper_source(self, tmp_path: Path) -> None:
        (tmp_path / "projects" / "PROJ-X" / "paper" / "source").mkdir(parents=True)
        p = _validate_edit_path(
            "projects/PROJ-X/paper/source/main.tex",
            project_id="PROJ-X", severity="writing", repo_root=tmp_path,
        )
        assert p is not None

    def test_writing_rejects_code_dir(self, tmp_path: Path) -> None:
        (tmp_path / "projects" / "PROJ-X" / "code").mkdir(parents=True)
        p = _validate_edit_path(
            "projects/PROJ-X/code/analysis.py",
            project_id="PROJ-X", severity="writing", repo_root=tmp_path,
        )
        assert p is None  # writing severity cannot touch code/

    def test_science_allows_code_dir(self, tmp_path: Path) -> None:
        (tmp_path / "projects" / "PROJ-X" / "code").mkdir(parents=True)
        p = _validate_edit_path(
            "projects/PROJ-X/code/analysis.py",
            project_id="PROJ-X", severity="science", repo_root=tmp_path,
        )
        assert p is not None

    def test_science_allows_data_dir(self, tmp_path: Path) -> None:
        (tmp_path / "projects" / "PROJ-X" / "data").mkdir(parents=True)
        p = _validate_edit_path(
            "projects/PROJ-X/data/labels.csv",
            project_id="PROJ-X", severity="science", repo_root=tmp_path,
        )
        assert p is not None

    def test_path_escape_rejected(self, tmp_path: Path) -> None:
        """An LLM's `../../etc/passwd` shenanigans must be refused."""
        p = _validate_edit_path(
            "../../etc/passwd",
            project_id="PROJ-X", severity="science", repo_root=tmp_path,
        )
        assert p is None

    def test_random_dir_rejected(self, tmp_path: Path) -> None:
        (tmp_path / "projects" / "PROJ-X" / "notes").mkdir(parents=True)
        p = _validate_edit_path(
            "projects/PROJ-X/notes/scratch.txt",
            project_id="PROJ-X", severity="science", repo_root=tmp_path,
        )
        assert p is None  # notes/ isn't in the whitelist
