"""Real-call test split: a ``slow`` marker so the PR gate finishes in budget.

The full real-call suite (real arXiv/DOI/OEIS/Wikidata/Wikipedia fetch + grounding,
plus multi-step LLM+LaTeX+Zenodo e2e loops) grew past the 60-min per-PR CI budget
and got cancelled mid-run (passing) once Dartmouth was reachable. Rather than make
every PR a multi-hour run, the heavy modules below are marked ``slow`` and excluded
from the per-PR gate (``pytest tests/real_call -m "not slow"``); the FULL suite runs
in a scheduled nightly job (``llmxive-real-call-nightly.yml``).

Defaults to FAST (PR gate) — a real-call module runs on every PR unless its name is
listed here. So a new heavy module should be added to ``_SLOW_MODULES`` when it
lands. The PR gate keeps a representative smoke layer: connectivity + backend
fallback + the reference/citation gates + personality liveness + Spec Kit scripts.
"""

from __future__ import annotations

import pytest

# Module names (basename, no .py) whose real-call tests do heavy network fetch +
# grounding or multi-step e2e loops — minutes each — so they run nightly, not per-PR.
_SLOW_MODULES = frozenset({
    # multi-step e2e: real LLM loops + LaTeX compile + Zenodo deposit
    "test_full_pipeline_e2e",
    "test_paper_pipeline_e2e",
    "test_implementer_e2e",
    "test_paper_review_convergence_e2e",
    "test_publisher_zenodo_sandbox",
    "test_resume_progression",
    "test_paper_reviewer_chunk_summary",
    # real fetch + grounding (arXiv / DOI / OEIS / Wikidata / Wikipedia)
    "test_grounding_end_to_end",
    "test_grounding_retrieval",
    "test_grounding_guard_flags_fabrication",
    "test_grounding_entailment",
    "test_semantic_substantiation",
    "test_fill_e2e_real",
    "test_fill_oeis_real",
    "test_fill_wikidata_real",
    "test_fill_wikipedia_real",
    "test_fill_relational_real",
    "test_fill_superlative_real",
    "test_fill_provenance_real",
    "test_fill_no_source_blocks_real",
    # heavy compute / verify / resolve / receipts
    "test_compute_real",
    "test_verify_pi_e_real",
    "test_triple_real",
    "test_claim_resolve_real",
    "test_receipt_real",
    "test_calibration_heldout",
    "test_summarize_fidelity",
    # issue #112: 3 repeated judge calls + cache-freeze round trip
    "test_relevance_judge_real",
})


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "slow: heavy real-call test (network fetch + grounding / e2e) — excluded "
        "from the per-PR gate, run in the nightly full suite.",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    for item in items:
        module = item.module.__name__.rsplit(".", 1)[-1]
        if module in _SLOW_MODULES:
            item.add_marker(pytest.mark.slow)
