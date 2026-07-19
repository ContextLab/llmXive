"""Per-profile composite projections (spec 026 slice 7, US5 AC1 support / §2.1).

Each profile's exact candidate chain is asserted against a COMPOSITE snapshot —
the full free Dartmouth text chain + the vision peer + the local qwen2.5
candidate + the paid claude-haiku tail — rather than the small 3-model offline
snapshot (``tests/conftest.py``'s ``_offline_model_selection_snapshot``), which
is too narrow to ever reveal a ``max_candidates`` truncation. This is what
makes each profile's candidate cap express INTENT and be VERIFIED, rather than
every profile being homogenized to whatever cap happens not to truncate a
3-model fixture. Each profile gets its own explicit, separately reviewed
assertion — never collapsed into a loop.

SC-007 and the design call for EXACT model-ID projections: every test below
asserts the COMPLETE ordered tuple (never a ``ids[:N]`` prefix or bare
membership check), under BOTH an explicit paid-OFF and an explicit paid-ON
composite snapshot — so an extra candidate, a wrong local-tier position, a
duplicate, or a misplaced/absent paid tail all fail the assertion instead of
silently passing.

See ``model_selection/profiles.py`` for the review finding that raised
``cheap_structured`` / ``deep_review`` / ``deep_code`` / ``vision`` to cap 8 so
this composite projection holds.
"""

from __future__ import annotations

from llmxive.model_selection.profiles import build_requirement
from llmxive.model_selection.select import select
from llmxive.model_selection.types import CallBudget, IndependenceBaseline
from tests.unit.test_model_selection_select import (
    CLAUDE,
    GEMMA4,
    GPT_OSS,
    LOCAL,
    QWEN,
    VL,
    _ids,
    _snapshot,
)

_CB = CallBudget(max_input_tokens=1000, max_output_tokens=500)


def _paid_off():
    """The full free text chain + vision peer + local qwen2.5 + paid
    claude-haiku tail, opt-in OFF — the paid candidate is present in the
    snapshot but must never be admitted into any chain."""
    return _snapshot(paid_opt_in=False, credit_source="live")


def _paid_on():
    """Same composite snapshot, opt-in ON with headroom — large enough that a
    narrow ``max_candidates`` visibly truncates the guarded paid tail instead
    of coincidentally fitting under any cap."""
    return _snapshot(paid_opt_in=True, credit_source="live")


# --------------------------------------------------------------------------- #
# standard_generation
# --------------------------------------------------------------------------- #


def test_standard_generation_paid_off_exact_chain():
    ids = _ids(select(build_requirement("standard_generation", _CB, allow_paid=False), _paid_off()))
    assert ids == [QWEN, GEMMA4, GPT_OSS, LOCAL]


def test_standard_generation_paid_on_exact_chain():
    ids = _ids(select(build_requirement("standard_generation", _CB, allow_paid=True), _paid_on()))
    assert ids == [QWEN, GEMMA4, GPT_OSS, LOCAL, CLAUDE]


# --------------------------------------------------------------------------- #
# cheap_structured
# --------------------------------------------------------------------------- #


def test_cheap_structured_paid_off_exact_chain():
    ids = _ids(select(build_requirement("cheap_structured", _CB, allow_paid=False), _paid_off()))
    assert ids == [QWEN, GEMMA4, GPT_OSS, LOCAL]


def test_cheap_structured_paid_on_exact_chain():
    ids = _ids(select(build_requirement("cheap_structured", _CB, allow_paid=True), _paid_on()))
    assert ids == [QWEN, GEMMA4, GPT_OSS, LOCAL, CLAUDE]


# --------------------------------------------------------------------------- #
# deep_review
# --------------------------------------------------------------------------- #


def test_deep_review_paid_off_exact_chain():
    ids = _ids(select(build_requirement("deep_review", _CB, allow_paid=False), _paid_off()))
    assert ids == [QWEN, GEMMA4, GPT_OSS]


def test_deep_review_paid_on_exact_chain():
    ids = _ids(select(build_requirement("deep_review", _CB, allow_paid=True), _paid_on()))
    assert ids == [QWEN, GEMMA4, GPT_OSS, CLAUDE]


# --------------------------------------------------------------------------- #
# deep_code
# --------------------------------------------------------------------------- #


def test_deep_code_paid_off_exact_chain():
    ids = _ids(select(build_requirement("deep_code", _CB, allow_paid=False), _paid_off()))
    assert ids == [QWEN, GEMMA4, GPT_OSS]


def test_deep_code_paid_on_exact_chain():
    ids = _ids(select(build_requirement("deep_code", _CB, allow_paid=True), _paid_on()))
    assert ids == [QWEN, GEMMA4, GPT_OSS, CLAUDE]


# --------------------------------------------------------------------------- #
# independent_review
# --------------------------------------------------------------------------- #


def test_independent_review_paid_off_exact_chain():
    ids = _ids(select(build_requirement("independent_review", _CB, allow_paid=False), _paid_off()))
    assert ids == [QWEN, GEMMA4, GPT_OSS]


def test_independent_review_paid_on_exact_chain():
    ids = _ids(select(build_requirement("independent_review", _CB, allow_paid=True), _paid_on()))
    assert ids == [QWEN, GEMMA4, GPT_OSS, CLAUDE]


def test_independent_review_requires_a_different_family():
    ids = _ids(select(build_requirement(
        "independent_review", _CB,
        independence_against=IndependenceBaseline(families=frozenset({"qwen3.5"})),
    ), _paid_on()))
    assert QWEN not in ids, "required family independence not honored"


# --------------------------------------------------------------------------- #
# vision — no paid tail is attributed today (claude-haiku-4-5 has no vision
# capability), so the paid-OFF and paid-ON chains are IDENTICAL; both are
# asserted explicitly (never collapsed into one) so a future paid-vision
# attribution is caught by whichever assertion it breaks.
# --------------------------------------------------------------------------- #


def test_vision_paid_off_exact_chain():
    ids = _ids(select(build_requirement("vision", _CB, allow_paid=False), _paid_off()))
    assert ids == [QWEN, VL]


def test_vision_paid_on_exact_chain():
    ids = _ids(select(build_requirement("vision", _CB, allow_paid=True), _paid_on()))
    assert ids == [QWEN, VL]
    # gemma-4/gpt-oss/claude have no vision attribution and must NOT appear.
    assert GEMMA4 not in ids and GPT_OSS not in ids and CLAUDE not in ids
