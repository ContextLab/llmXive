"""Spec 020 T029 / US3 — planning docs express measurable outcomes by reference (real-call).

Real-call (LLMXIVE_REAL_TESTS=1 + free Dartmouth model). The updated templates/prompts
(FR-006) steer producers to state the research question, method, and references and to
express success criteria as *what is measured + the source/reference*, not pre-asserted
specific empirical values. This runs the real claim-layer low-level detector over a
reference-anchored planning doc and asserts it carries no non-citation (low-level)
claim in its measurable-outcome section, while a value-asserting variant DOES trip the
detector (so the test is meaningful, not vacuous).
"""

from __future__ import annotations

import os

import pytest

from llmxive.claims.models import ClaimKind

REAL = os.environ.get("LLMXIVE_REAL_TESTS") == "1"


def _has_key() -> bool:
    try:
        from llmxive.credentials import load_dartmouth_key

        return bool(load_dartmouth_key())
    except Exception:
        return False


pytestmark = [
    pytest.mark.skipif(not REAL, reason="LLMXIVE_REAL_TESTS!=1"),
    pytest.mark.skipif(not _has_key(), reason="no Dartmouth key"),
]

_FREE_MODEL = "qwen.qwen3.5-122b"

# Reference-anchored success criteria — what is measured + the source, no specific value.
GOOD = (
    "# Spec\n\n## Success Criteria\n\n"
    "- SC-001: The enumerated prime-knot counts match the standard tables "
    "(Hoste, Thistlethwaite & Weeks 1998) for every crossing number in range.\n"
    "- SC-002: The regression's reported fit is compared against the published "
    "baseline (cited).\n"
)
# Value-asserting variant — pre-asserts specific empirical numbers (the anti-pattern).
BAD = (
    "# Spec\n\n## Success Criteria\n\n"
    "- SC-001: There are exactly 9,988 prime knots at 13 crossings and 1,701,936 "
    "knots up to 16 crossings.\n"
)


def _lowlevel_count(text: str) -> int:
    from llmxive.backends.router import make_backend
    from llmxive.claims.extract import extract_claims

    claims = extract_claims(
        text, artifact_path="projects/PROJ-x/specs/spec.md",
        backend=make_backend("dartmouth"), model=_FREE_MODEL, repo_root=None,
    )
    return sum(1 for c in claims if c.kind != ClaimKind.CITATION)


def test_reference_anchored_doc_has_no_lowlevel_claims() -> None:
    assert _lowlevel_count(GOOD) == 0, "a reference-anchored planning doc tripped the low-level detector"


def test_detector_is_not_vacuous() -> None:
    # The value-asserting variant MUST trip the detector (else the GOOD assertion is meaningless).
    assert _lowlevel_count(BAD) >= 1
