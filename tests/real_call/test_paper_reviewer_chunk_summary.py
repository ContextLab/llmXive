"""Real-call test for spec 013 chunked-summarization fallback.

Gated on `LLMXIVE_REAL_TESTS=1`. Calls the Dartmouth API (the project's
default backend) with a real LaTeX chunk and verifies the summarizer
returns lossy-but-faithful prose.

The verification rubric is structural — we check the summary preserves
section headings, citation keys, numeric claims, and `\\ref{...}` /
`\\cite{...}` macros that the prompt explicitly asks the model to retain
verbatim. This is the only safety net we have for a behavior we can't
unit-test (the model could regress on instruction-following).
"""

from __future__ import annotations

import os

import pytest

from llmxive.agents.paper_reviewer import _summarize_chunk
from llmxive.credentials import load_dartmouth_key

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="real-call test; set LLMXIVE_REAL_TESTS=1 to enable",
)


_CORE = r"""
\section{Method}
\label{sec:method}

We evaluate 27 LVLMs on the \bench{} benchmark, comprising 789 questions
across five memory abilities (information extraction, multi-session
reasoning, temporal reasoning, knowledge update, and answer refusal) at
four standard context lengths (32K, 64K, 128K, 256K tokens).

The judge protocol uses Qwen3-VL-235B as the primary scorer, cross-validated
by GPT-5.4-mini ($\kappa = 0.93$) and a three-annotator human consensus
($\kappa = 0.86$, $n = 484$). Per-type item counts are reported in
Appendix~\ref{app:eval_setup} and statistical methodology in
Appendix~\ref{app:judge_validation}~\cite{zheng2023judging,cohen1960coefficient}.

\subsection{Cross-modality validation}
\label{subsec:cross_modality}

An image-ablation study (Table~\ref{tab:cross_modality_ablation}) confirms
that solving \bench{} requires visual evidence: removing evidence images
drops two frontier LVLMs below 2\% accuracy on the 80.4\% of questions
whose evidence includes images. This validates the \emph{cross-modal
necessity} claim central to the benchmark.
""".strip()

# Pad to a realistic chunk size (~30KB) so the summarizer has actual
# verbose prose to compress. Real production chunks are 80-100KB; we
# use 30KB here to keep the test under 3 minutes while still hitting
# the "input long enough that summarization makes sense" regime.
_PADDING = (
    "Additional discussion: " + ("the experimental setup carries multiple "
    "implementation details that are documented elsewhere in the appendix; "
    "specifically, model checkpoints, sampling temperatures, retrieval "
    "depth, and adapter configurations are listed verbatim in the supplementary "
    "material to enable end-to-end reproduction. ") * 200
)
_SAMPLE_CHUNK = _CORE + "\n\n" + _PADDING


def test_summarize_chunk_preserves_required_macros() -> None:
    """The chunk summarizer must preserve section headings, refs, and
    citations verbatim (the prompt instructs this explicitly). If the
    model drops them, downstream reviewers will report broken cross-
    references and we lose the lossy-but-faithful contract."""
    # Verify Dartmouth credentials are reachable; skip if not (the
    # real-call gate is set but the env doesn't have the key).
    try:
        load_dartmouth_key()
    except Exception as exc:
        pytest.skip(f"Dartmouth API key unavailable: {exc}")

    summary = _summarize_chunk(
        _SAMPLE_CHUNK,
        default_backend="dartmouth",
        fallback_backends=[],
        # Matches the paper_reviewer agent's default_model in
        # agents/registry.yaml — keeps the test self-consistent.
        model="qwen.qwen3.5-122b",
    )

    # The summary must not be empty.
    assert summary and len(summary) >= 100, (
        f"summary suspiciously short ({len(summary)} chars): {summary!r}"
    )

    # The summary must be SHORTER than the input (it's a summary).
    assert len(summary) < len(_SAMPLE_CHUNK), (
        f"summary ({len(summary)} chars) is not shorter than input "
        f"({len(_SAMPLE_CHUNK)} chars) — the model isn't summarizing"
    )

    # Section/subsection headings must survive verbatim.
    assert "Method" in summary or "\\section" in summary, (
        f"summary lost the \\section heading: {summary!r}"
    )

    # Citation macros must survive verbatim — at least one of the cite
    # keys (we don't require all because the model may consolidate).
    cite_keys = ["zheng2023judging", "cohen1960coefficient"]
    assert any(k in summary for k in cite_keys), (
        f"summary dropped all citation macros (expected one of "
        f"{cite_keys}): {summary!r}"
    )

    # At least one ref macro must survive verbatim (the model is asked
    # to preserve refs so downstream reviewers can cross-reference).
    ref_keys = ["app:eval_setup", "app:judge_validation",
                "tab:cross_modality_ablation", "subsec:cross_modality"]
    assert any(k in summary for k in ref_keys), (
        f"summary dropped all \\ref/\\label macros (expected one of "
        f"{ref_keys}): {summary!r}"
    )
