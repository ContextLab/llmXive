"""Per-profile composite projections (spec 026 slice 7, US5 AC1 support / §2.1).

Each profile's exact candidate chain is asserted against a COMPOSITE snapshot —
the full free Dartmouth text chain + the vision peer + the local qwen2.5
candidate + the paid claude-haiku tail, opt-in ON with headroom — rather than
the small 3-model offline snapshot (``tests/conftest.py``'s
``_offline_model_selection_snapshot``), which is too narrow to ever reveal a
``max_candidates`` truncation. This is what makes each profile's candidate cap
express INTENT and be VERIFIED, rather than every profile being homogenized to
whatever cap happens not to truncate a 3-model fixture. Each profile gets its
own explicit, separately reviewed assertion — never collapsed into a loop.

See ``model_selection/profiles.py`` for the review finding that raised
``cheap_structured`` / ``deep_review`` / ``deep_code`` / ``vision`` to cap 8 so
this composite projection holds.
"""

from __future__ import annotations

from llmxive.model_selection.profiles import build_requirement
from llmxive.model_selection.select import select
from llmxive.model_selection.types import CallBudget, IndependenceBaseline
from tests.unit.test_model_selection_select import _ids, _snapshot

_CB = CallBudget(max_input_tokens=1000, max_output_tokens=500)


def _composite():
    """The full free text chain + vision peer + local qwen2.5 + paid
    claude-haiku tail, opt-in ON with headroom — large enough that a narrow
    ``max_candidates`` visibly truncates the guarded paid tail instead of
    coincidentally fitting under any cap."""
    return _snapshot(paid_opt_in=True, credit_source="live")


def test_standard_generation_keeps_the_free_chain_plus_the_guarded_paid_tail():
    ids = [c.model_ref.model_id for c in select(
        build_requirement("standard_generation", _CB, allow_paid=True), _composite())
    .candidates]
    assert ids[:3] == ["qwen.qwen3.5-122b", "google.gemma-4-31B-it", "openai.gpt-oss-120b"]
    assert "anthropic.claude-haiku-4-5-20251001" in ids, "paid tail truncated by max_candidates"


def test_deep_review_keeps_the_free_chain_plus_the_guarded_paid_tail():
    ids = _ids(select(build_requirement("deep_review", _CB, allow_paid=True), _composite()))
    assert ids[:3] == ["qwen.qwen3.5-122b", "google.gemma-4-31B-it", "openai.gpt-oss-120b"]
    assert "anthropic.claude-haiku-4-5-20251001" in ids


def test_deep_code_keeps_the_free_chain_plus_the_guarded_paid_tail():
    ids = _ids(select(build_requirement("deep_code", _CB, allow_paid=True), _composite()))
    assert ids[:3] == ["qwen.qwen3.5-122b", "google.gemma-4-31B-it", "openai.gpt-oss-120b"]
    assert "anthropic.claude-haiku-4-5-20251001" in ids


def test_cheap_structured_keeps_the_free_chain_plus_the_guarded_paid_tail():
    ids = _ids(select(build_requirement("cheap_structured", _CB, allow_paid=True), _composite()))
    assert ids[:3] == ["qwen.qwen3.5-122b", "google.gemma-4-31B-it", "openai.gpt-oss-120b"]
    assert "anthropic.claude-haiku-4-5-20251001" in ids


def test_vision_leads_with_qwen35_and_keeps_the_vl_peer():
    ids = _ids(select(build_requirement("vision", _CB), _composite()))
    assert ids[0] == "qwen.qwen3.5-122b"
    assert "qwen.qwen3-vl:32b" in ids
    # gemma-4/gpt-oss have no vision attribution and must NOT appear
    assert "google.gemma-4-31B-it" not in ids and "openai.gpt-oss-120b" not in ids


def test_independent_review_requires_a_different_family():
    ids = _ids(select(build_requirement(
        "independent_review", _CB,
        independence_against=IndependenceBaseline(families=frozenset({"qwen3.5"})),
    ), _composite()))
    assert "qwen.qwen3.5-122b" not in ids, "required family independence not honored"
