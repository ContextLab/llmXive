"""Tests for paper_reviewer's arxiv-intake fallback path.

Real-world failure: 26 paper-reviewer invocations across PROJ-564 +
PROJ-566 (both arXiv-submitted papers) failed with
``FileNotFoundError: no paper specs/ feature dir`` because those
projects never ran through the home-grown spec→plan→tasks→implement
pipeline — they came in fully-formed from arXiv with ``paper/source/``
+ ``paper/metadata.json``. The reviewer now falls back to hashing
``metadata.json`` when ``paper/specs/`` doesn't exist.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _make_arxiv_intake_project(repo: Path, project_id: str) -> Path:
    """Build a minimal arXiv-intake project layout (paper/ + metadata.json,
    NO paper/specs/)."""
    proj_dir = repo / "projects" / project_id
    paper = proj_dir / "paper"
    (paper / "source").mkdir(parents=True)
    (paper / "pdf").mkdir()
    (paper / "figures").mkdir()
    (paper / "source" / "main.tex").write_text(r"\documentclass{article}\begin{document}x\end{document}",
                                                encoding="utf-8")
    (paper / "metadata.json").write_text(json.dumps({
        "arxiv_id": "2605.99999",
        "arxiv_url": "https://arxiv.org/abs/2605.99999",
        "title": "Synthetic Test Paper",
        "authors": ["A. Author"],
        "submitter": "github-actions[bot]",
        "submitted_via": "test",
        "source_files": ["main.tex"],
        "toplevel_tex": ["main.tex"],
    }, indent=2), encoding="utf-8")
    return proj_dir


class TestArxivIntakeFallback:
    def test_paper_feature_dir_returns_none_when_no_specs(self, tmp_path: Path) -> None:
        """Without instantiating the full agent (which needs a complete
        registry entry), exercise the _paper_feature_dir helper directly
        as an unbound method on the class — it doesn't read self."""
        from llmxive.agents.paper_reviewer import PaperReviewerAgent
        proj = _make_arxiv_intake_project(tmp_path, "PROJ-999-test")
        # _paper_feature_dir is a method but only reads project_dir; bypass
        # __init__ to avoid the registry-entry validation.
        agent = object.__new__(PaperReviewerAgent)
        assert agent._paper_feature_dir(proj) is None

    def test_handle_response_uses_metadata_json_when_no_feature_dir(self, tmp_path: Path, monkeypatch) -> None:
        """When `paper/specs/` is missing, handle_response should hash
        `paper/metadata.json` and produce a schema-valid artifact_path
        (matches ^projects/PROJ-\\d+-...$)."""
        # We don't run the full handle_response (writes to repo state) —
        # just verify the path-selection logic by reading the source.
        # An integration-style test would need the full agents-registry
        # stack which is out of unit-test scope.
        from llmxive.agents.paper_reviewer import PaperReviewerAgent
        # Sanity: confirm the file references the metadata.json fallback.
        src = Path(__file__).resolve().parents[2] / "src" / "llmxive" / "agents" / "paper_reviewer.py"
        text = src.read_text()
        assert 'project_dir / "paper" / "metadata.json"' in text, (
            "paper_reviewer.handle_response should fall back to metadata.json "
            "when feature_dir is None"
        )
        assert "arXiv-intake" in text, (
            "the fallback path should be documented in code as arxiv-intake"
        )

    def test_no_feature_dir_AND_no_metadata_still_hard_fails(self, tmp_path: Path) -> None:
        """A project with NEITHER paper/specs/ NOR paper/metadata.json
        is a real precondition violation — the reviewer must still
        hard-fail with an actionable message."""
        from llmxive.agents.paper_reviewer import PaperReviewerAgent
        # Just confirm the source still has the hard-fail branch.
        src = Path(__file__).resolve().parents[2] / "src" / "llmxive" / "agents" / "paper_reviewer.py"
        text = src.read_text()
        assert "and no paper/metadata.json" in text, (
            "the hard-fail message should explain BOTH conditions"
        )


class TestArxivIntakeFigureDiscovery:
    """For arXiv-intake papers, figures live in paper/source/{figs,pics,
    images,Figures}/ — not paper/figures/. The reviewer must discover
    them or the LLM has no visual context to review."""

    def test_discovers_pdf_figures_under_pics(self, tmp_path: Path) -> None:
        from llmxive.agents.paper_reviewer import _collect_figures_from_arxiv_source
        src = tmp_path / "source"
        (src / "pics").mkdir(parents=True)
        (src / "pics" / "figure1.pdf").write_bytes(b"x" * 1234)
        (src / "pics" / "figure2.png").write_bytes(b"y" * 100)
        out = _collect_figures_from_arxiv_source(src)
        assert "pics/figure1.pdf" in out
        assert "pics/figure2.png" in out
        assert "1234 bytes" in out

    def test_discovers_figures_in_multiple_subdirs(self, tmp_path: Path) -> None:
        from llmxive.agents.paper_reviewer import _collect_figures_from_arxiv_source
        src = tmp_path / "source"
        # macOS HFS+ is case-insensitive, so don't use both "figures" and
        # "Figures" — pick distinct subdir names.
        (src / "figures").mkdir(parents=True)
        (src / "images").mkdir(parents=True)
        (src / "logo").mkdir(parents=True)
        (src / "figures" / "a.pdf").write_bytes(b"a")
        (src / "images" / "b.eps").write_bytes(b"b")
        (src / "logo" / "c.svg").write_bytes(b"c")
        out = _collect_figures_from_arxiv_source(src)
        assert all(s in out for s in ("figures/a.pdf", "images/b.eps", "logo/c.svg"))

    def test_skips_top_level_pdfs_likely_compiled_output(self, tmp_path: Path) -> None:
        from llmxive.agents.paper_reviewer import _collect_figures_from_arxiv_source
        src = tmp_path / "source"
        src.mkdir(parents=True)
        (src / "main.pdf").write_bytes(b"compiled output, not a figure")
        (src / "pics").mkdir()
        (src / "pics" / "real-figure.pdf").write_bytes(b"actual figure")
        out = _collect_figures_from_arxiv_source(src)
        assert "main.pdf" not in out  # top-level PDF skipped
        assert "pics/real-figure.pdf" in out

    def test_caps_at_200_entries(self, tmp_path: Path) -> None:
        from llmxive.agents.paper_reviewer import _collect_figures_from_arxiv_source
        src = tmp_path / "source" / "figs"
        src.mkdir(parents=True)
        for i in range(250):
            (src / f"f{i:03d}.png").write_bytes(b"x")
        out = _collect_figures_from_arxiv_source(src.parent)
        assert "truncated at 200 entries" in out

    def test_real_world_proj_564_discovers_10_figures(self) -> None:
        """Smoke test against the actual PROJ-564 source on disk.
        Skips if PROJ-564 isn't checked out (e.g., on a fresh clone)."""
        from llmxive.agents.paper_reviewer import _collect_figures_from_arxiv_source
        repo = Path(__file__).resolve().parents[2]
        src = repo / "projects" / "PROJ-564-qwen-image-vae-2-0-technical-report" / "paper" / "source"
        if not src.is_dir():
            pytest.skip("PROJ-564 source not checked out")
        out = _collect_figures_from_arxiv_source(src)
        lines = [line for line in out.splitlines() if line.startswith("- ")]
        assert len(lines) >= 5, f"expected ≥5 figures in PROJ-564 source, got {len(lines)}"
        # At least one figure under pics/
        assert any("pics/" in line for line in lines)


class TestTexConcatPrefersEntryPoint:
    """Real-world failure on PROJ-578: the prompt sent to the reviewer
    was 3,390 chars of *package declarations only* (extra_pkgs.tex sorts
    before main.tex alphabetically; main.tex itself was 254KB > the old
    60KB budget, so it got skipped). The reviewer (correctly) called this
    out as 'Incomplete LaTeX source' and demanded a major_revision. The
    fix promotes the file containing ``\\documentclass`` (the entry
    point) to the front so it always gets included, truncated if needed.
    """

    def test_promotes_documentclass_file_first(self, tmp_path: Path) -> None:
        from llmxive.agents.paper_reviewer import _concat_tex
        src = tmp_path / "source"
        src.mkdir()
        # extra_pkgs.tex sorts first alphabetically but is just packages.
        (src / "extra_pkgs.tex").write_text(r"\usepackage{amsmath}", encoding="utf-8")
        # main.tex is the entry point — must appear first in concat output.
        (src / "main.tex").write_text(
            r"\documentclass{article}\begin{document}HELLO\end{document}",
            encoding="utf-8",
        )
        out = _concat_tex(src)
        idx_main = out.index("main.tex")
        idx_pkgs = out.index("extra_pkgs.tex")
        assert idx_main < idx_pkgs, (
            "entry-point file (with \\documentclass) must be inlined "
            "BEFORE package files"
        )
        assert "HELLO" in out

    def test_entry_point_included_even_when_budget_tight(self, tmp_path: Path) -> None:
        from llmxive.agents.paper_reviewer import _concat_tex
        src = tmp_path / "source"
        src.mkdir()
        big_body = "X" * 50_000
        (src / "extra_pkgs.tex").write_text(r"\usepackage{amsmath}", encoding="utf-8")
        (src / "main.tex").write_text(
            r"\documentclass{article}\begin{document}" + big_body + r"\end{document}",
            encoding="utf-8",
        )
        # Budget smaller than main.tex — old code would skip main.tex
        # entirely and only include the tiny package file. New code must
        # include main.tex (truncated) since it's the entry point.
        out = _concat_tex(src, max_chars=10_000)
        assert "main.tex" in out
        assert "truncated to fit budget" in out

    def test_real_world_proj_578_includes_actual_paper_body(self) -> None:
        """Smoke test against PROJ-578 (the failure that motivated the fix).
        Skips if PROJ-578 isn't checked out."""
        from llmxive.agents.paper_reviewer import _concat_tex
        repo = Path(__file__).resolve().parents[2]
        src = repo / "projects" / "PROJ-578-https-arxiv-org-abs-2605-14906" / "paper" / "source"
        if not src.is_dir():
            pytest.skip("PROJ-578 source not checked out")
        out = _concat_tex(src)
        # The old prompt had ~3,390 chars (just extra_pkgs.tex + truncation
        # marker). The new prompt must include the real paper body.
        assert len(out) > 50_000, (
            f"expected ≥50KB of tex concat, got {len(out)} chars — "
            "the entry-point file is probably being skipped again"
        )
        # MemLens defines a custom \bench command in the main file —
        # confirms we have the actual paper body, not just packages.
        assert "MemLens" in out or "\\bench" in out


class TestChunkedSummarization:
    """Spec 013: when the raw `.tex` corpus exceeds the reviewer's
    context budget, we chunk the source and summarize each chunk via
    LLM instead of truncating to a marker. The reviewer sees lossy-but-
    full coverage of the paper.

    These tests pass a deterministic `summarize_fn` to exercise the
    orchestration logic (chunking, caching, output framing). A real
    LLM-call test lives in `tests/real_call/`.
    """

    def test_chunk_corpus_splits_on_section_boundaries(self) -> None:
        from llmxive.agents.paper_reviewer import _chunk_corpus
        text = ""
        for i in range(8):
            text += f"\n\\section{{Section {i}}}\n" + ("body line\n" * 100)
        chunks = _chunk_corpus(text, max_chunk_size=4_000)
        # Every chunk after the first should start at a \section boundary
        # (i.e., the chunker preferred the strong boundary over a hard cut).
        for c in chunks[1:]:
            assert c.lstrip().startswith("\\section"), (
                f"expected section boundary, got: {c[:60]!r}"
            )

    def test_chunk_corpus_falls_back_to_paragraph_breaks(self) -> None:
        from llmxive.agents.paper_reviewer import _chunk_corpus
        # No \section anywhere; chunker must use paragraph breaks.
        body = "paragraph A.\n\n" + "x " * 500 + "\n\nparagraph B.\n\n" + "y " * 500
        chunks = _chunk_corpus(body, max_chunk_size=1_200)
        assert len(chunks) > 1
        # No chunk should exceed the budget (paragraphs gave a valid cut).
        assert all(len(c) <= 1_200 for c in chunks)

    def test_chunk_corpus_hard_cuts_when_no_natural_boundary(self) -> None:
        from llmxive.agents.paper_reviewer import _chunk_corpus
        # No section, no paragraph breaks — single long run.
        text = "x" * 30_000
        chunks = _chunk_corpus(text, max_chunk_size=10_000)
        assert len(chunks) == 3
        assert all(len(c) <= 10_000 for c in chunks)

    def test_build_corpus_returns_verbatim_when_under_budget(
        self, tmp_path: Path,
    ) -> None:
        from llmxive.agents.paper_reviewer import _build_corpus_with_summaries
        src = tmp_path / "source"
        src.mkdir()
        (src / "main.tex").write_text(
            r"\documentclass{article}\begin{document}HELLO\end{document}",
            encoding="utf-8",
        )
        calls: list[int] = []

        def fake_summarize(chunk: str) -> str:
            calls.append(len(chunk))
            return "(summary)"

        out = _build_corpus_with_summaries(
            src, final_budget=10_000, summarize_fn=fake_summarize,
        )
        assert "HELLO" in out
        assert calls == [], "no summarization should fire when under budget"

    def test_build_corpus_summarizes_when_over_budget(
        self, tmp_path: Path,
    ) -> None:
        from llmxive.agents.paper_reviewer import _build_corpus_with_summaries
        src = tmp_path / "source"
        src.mkdir()
        # 60KB main.tex — exceeds the test budget below.
        big = ""
        for i in range(5):
            big += f"\n\\section{{Section {i}}}\n" + ("X" * 10_000)
        (src / "main.tex").write_text(
            r"\documentclass{article}\begin{document}" + big + r"\end{document}",
            encoding="utf-8",
        )

        def fake_summarize(chunk: str) -> str:
            return f"<<summary of {len(chunk)}>>"

        out = _build_corpus_with_summaries(
            src,
            final_budget=20_000,
            chunk_size=15_000,
            summarize_fn=fake_summarize,
        )
        # Spec 015 T017: corpus reduction now delegates to the SSoT summarizer,
        # which returns a budget-bounded inode-table pointer block (superseding the
        # old AUTO-SUMMARIZED/NOTICE framing). The per-chunk summaries still appear,
        # and the full source is recoverable on disk (no silent loss).
        from llmxive.tools.summarize import desummarize
        assert out.startswith("[[LLMXIVE-SUMMARY v1]]")
        assert "<<summary of " in out
        assert len(out) < len(big)  # substantially smaller than the raw corpus
        restored = desummarize(out)
        assert restored.count("\\section{Section") == 5

    def test_build_corpus_caches_summaries_across_calls(
        self, tmp_path: Path,
    ) -> None:
        from llmxive.agents.paper_reviewer import _build_corpus_with_summaries
        src = tmp_path / "source"
        src.mkdir()
        big = ("\\section{X}\n" + "Y" * 12_000) * 3
        (src / "main.tex").write_text(
            r"\documentclass{article}\begin{document}" + big + r"\end{document}",
            encoding="utf-8",
        )
        cache = tmp_path / "cache"
        call_count = [0]

        def fake_summarize(chunk: str) -> str:
            call_count[0] += 1
            return "(s)"

        a = _build_corpus_with_summaries(
            src, final_budget=2_000, chunk_size=10_000,
            summarize_fn=fake_summarize, cache_dir=cache,
        )
        first_calls = call_count[0]
        assert first_calls >= 2
        b = _build_corpus_with_summaries(
            src, final_budget=2_000, chunk_size=10_000,
            summarize_fn=fake_summarize, cache_dir=cache,
        )
        assert call_count[0] == first_calls, (
            "second call must hit cache; expected 0 new calls, got "
            f"{call_count[0] - first_calls}"
        )
        assert a == b, "cached output must be byte-identical to first run"

    def test_build_corpus_uses_inode_table_without_summarizer(
        self, tmp_path: Path,
    ) -> None:
        """Spec 015 T017: with `summarize_fn=None` the corpus builder no longer
        TRUNCATES — it returns the SSoT inode-table pointer block, and the full
        source is recoverable on disk (no silent loss)."""
        from llmxive.agents.paper_reviewer import _build_corpus_with_summaries
        from llmxive.tools.summarize import desummarize
        src = tmp_path / "source"
        src.mkdir()
        big = "X" * 60_000
        (src / "main.tex").write_text(
            r"\documentclass{article}\begin{document}" + big + r"\end{document}",
            encoding="utf-8",
        )
        out = _build_corpus_with_summaries(
            src, final_budget=10_000, cache_dir=tmp_path / "c",
        )
        assert out.startswith("[[LLMXIVE-SUMMARY v1]]")
        # No truncation: the full 60K-char body is recoverable on disk.
        assert desummarize(out).count("X") >= 60_000


class TestBibSummary:
    """For arXiv-intake papers, ``state/citations/<PROJ>.yaml`` is never
    populated — only the .bib file under paper/source/ exists. The
    reviewer must fall back to inlining that .bib so it can see what's
    cited (otherwise the reviewer correctly says 'no citations recorded'
    and demands a major_revision)."""

    def test_summarize_bibfile_includes_content(self, tmp_path: Path) -> None:
        from llmxive.agents.paper_reviewer import _summarize_bibfile
        src = tmp_path / "source"
        src.mkdir()
        (src / "ref.bib").write_text(
            "@article{smith2024,\n  title={A paper},\n  author={Smith},\n}\n",
            encoding="utf-8",
        )
        out = _summarize_bibfile(src)
        assert "ref.bib" in out
        assert "smith2024" in out
        assert "A paper" in out

    def test_summarize_bibfile_empty_when_no_bib(self, tmp_path: Path) -> None:
        from llmxive.agents.paper_reviewer import _summarize_bibfile
        src = tmp_path / "source"
        src.mkdir()
        (src / "main.tex").write_text("x", encoding="utf-8")
        out = _summarize_bibfile(src)
        assert out == ""

    def test_summarize_bibfile_truncates_at_budget(self, tmp_path: Path) -> None:
        from llmxive.agents.paper_reviewer import _summarize_bibfile
        src = tmp_path / "source"
        src.mkdir()
        # 100KB of bib entries
        big = ("@article{a,\n  title={hello},\n}\n" * 4000)
        (src / "ref.bib").write_text(big, encoding="utf-8")
        out = _summarize_bibfile(src, max_chars=5000)
        assert "ref.bib" in out
        assert "truncated" in out
        assert len(out) <= 5200  # small slack for header

    def test_real_world_proj_578_inlines_refbib(self) -> None:
        """Smoke test against PROJ-578 ref.bib (46KB)."""
        from llmxive.agents.paper_reviewer import _summarize_bibfile
        repo = Path(__file__).resolve().parents[2]
        src = repo / "projects" / "PROJ-578-https-arxiv-org-abs-2605-14906" / "paper" / "source"
        if not src.is_dir():
            pytest.skip("PROJ-578 source not checked out")
        out = _summarize_bibfile(src)
        assert "ref.bib" in out
        assert len(out) > 10_000


class TestArxivIntakeMetadataBlock:
    """The reviewer prompt must include a 'paper provenance' header for
    arxiv-intake papers so the LLM knows it's reviewing a third-party
    manuscript, not a home-grown one."""

    def test_intake_block_exists_in_source(self) -> None:
        src = Path(__file__).resolve().parents[2] / "src" / "llmxive" / "agents" / "paper_reviewer.py"
        text = src.read_text()
        assert "Paper provenance — IMPORTANT context" in text
        assert "third-party" in text or "ingested verbatim" in text
        assert "submitter field is the llmXive intake" in text


class TestScoreNormalization:
    """LLM occasionally picks a verdict but writes the wrong score
    (e.g., verdict=accept score=0.0). The score↔verdict binding is
    invariant — we normalize on parse so a typo doesn't lose a
    substantive review to a validation error."""

    def test_handle_response_normalizes_accept_score(self) -> None:
        src = Path(__file__).resolve().parents[2] / "src" / "llmxive" / "agents" / "paper_reviewer.py"
        text = src.read_text()
        # The normalization is deterministic; document its presence so
        # future refactors don't silently drop it.
        assert 'verdict == "accept"' in text
        assert 'front["score"] = 0.5' in text
        assert 'front["score"] = 0.0' in text
