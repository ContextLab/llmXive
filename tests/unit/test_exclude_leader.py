"""exclude_leader: the tier-1 'free second opinion' rung without a model id."""
from __future__ import annotations

from dataclasses import replace

import pytest

from llmxive.model_selection.profiles import build_requirement
from llmxive.model_selection.select import select
from llmxive.model_selection.types import CallBudget, ModelUnavailable, RequirementOverrides
from llmxive.state import execution_status as es

# Import the established route_chat injection pattern (fake backend factory +
# fixed snapshot) rather than inventing a new one (Task 1 review finding).
from tests.unit.test_model_selection_route import (
    _MSGS,
    _RecordingBackend,
)
from tests.unit.test_model_selection_route import _factory as _route_factory
from tests.unit.test_model_selection_route import _snapshot as _route_snapshot

# Import the existing fixed-snapshot helper rather than rebuilding one.
from tests.unit.test_model_selection_select import _snapshot

_CB = CallBudget(max_input_tokens=1000, max_output_tokens=500)


def _leader(chain):
    return chain.candidates[0].model_ref.model_id


def test_exclude_leader_drops_rank_one_only():
    snap = _snapshot()
    base = build_requirement("standard_generation", _CB)
    full = select(base, snap)
    assert _leader(full) == "qwen.qwen3.5-122b"

    narrowed = replace(base, exclude_models=base.exclude_models | {_leader(full)})
    second = select(narrowed, snap)
    assert _leader(second) == "google.gemma-4-31B-it"
    # every OTHER candidate from the full chain survives, in order
    assert [c.model_ref.model_id for c in second.candidates] == [
        c.model_ref.model_id for c in full.candidates if c.model_ref.model_id != _leader(full)
    ]


def test_tier_constraint_carries_exclude_leader_not_a_model_id():
    rung = es.TierConstraint(allow_paid=False, exclude_leader=True)
    ov = rung.to_overrides()          # NO default_model argument
    assert ov.exclude_leader is True
    assert ov.exclude_models == frozenset()   # no model id smuggled in


def test_tier_overrides_needs_no_default_model(tmp_path):
    pid = "PROJ-001-x"
    ov0 = es.tier_overrides(pid, repo_root=tmp_path)   # tier 0
    assert ov0.exclude_leader is False
    es.bump_model_tier(pid, repo_root=tmp_path)
    ov1 = es.tier_overrides(pid, repo_root=tmp_path)   # tier 1
    assert ov1.exclude_leader is True
    assert ov1.exclude_models == frozenset()


def test_exclude_leader_composes_with_existing_exclusions():
    snap = _snapshot()
    base = build_requirement("standard_generation", _CB,
                             exclude_models=frozenset({"google.gemma-4-31B-it"}))
    full = select(base, snap)
    assert _leader(full) == "qwen.qwen3.5-122b"
    narrowed = replace(base, exclude_models=base.exclude_models | {_leader(full)})
    assert _leader(select(narrowed, snap)) == "openai.gpt-oss-120b"


def test_pass_one_model_unavailable_propagates_immediately():
    """When pass 1 finds nothing eligible, ModelUnavailable propagates and pass 2
    is NEVER invoked (there is no leader to exclude)."""
    snap = _snapshot()
    impossible = build_requirement(
        "standard_generation", _CB,
        exclude_models=frozenset({
            "qwen.qwen3.5-122b", "google.gemma-4-31B-it", "openai.gpt-oss-120b",
            "anthropic.claude-haiku-4-5-20251001", "Qwen/Qwen2.5-3B-Instruct",
        }),
    )
    with pytest.raises(ModelUnavailable):
        select(impossible, snap)


# --------------------------------------------------------------------------- #
# route_chat-level coverage (Task 1 review finding): every test above drives
# select() directly via a manual dataclasses.replace, which never executes
# route_chat's OWN two-pass translation (route.py:217-224). A bug there — e.g.
# resolving the leader from `base` instead of the merged `requirement` — would
# leave every test above green. These drive the REAL production entry point,
# reusing the injected-fake-backend-factory + fixed-snapshot pattern already
# established in test_model_selection_route.py.
# --------------------------------------------------------------------------- #


def test_route_chat_exclude_leader_serves_second_candidate():
    """The production two-pass path: overrides.exclude_leader=True must exclude
    whatever select() ranks first (qwen) and serve the NEXT candidate
    (gemma-4) — proven by which model the injected backend was actually asked
    to serve, not just what select() would compute standalone."""
    from llmxive.model_selection.route import route_chat

    be = _RecordingBackend("dartmouth")
    resp = route_chat(
        _MSGS,
        profile="standard_generation",
        max_tokens=512,
        overrides=RequirementOverrides(exclude_leader=True),
        snapshot=_route_snapshot(),
        backend_factory=_route_factory(be),
    )
    assert resp.model == "google.gemma-4-31B-it"
    assert be.calls[0]["model"] == "google.gemma-4-31B-it"
    assert "qwen.qwen3.5-122b" not in [c["model"] for c in be.calls]


def test_route_chat_exclude_leader_resolves_from_merged_requirement():
    """The leader excluded by pass 1 must be resolved from the MERGED
    requirement (base + overrides.exclude_models), not from `base` alone. With
    qwen already excluded via exclude_models, the merged leader is gemma-4 —
    so exclude_leader must drop gemma-4 too, and the final chain must lead
    with gpt-oss. A `base`-only resolution would instead recompute qwen as the
    leader (already excluded, so a no-op re-exclusion) and wrongly leave
    gemma-4 in front — this test fails under that bug and passes under the
    correct implementation."""
    from llmxive.model_selection.route import route_chat

    be = _RecordingBackend("dartmouth")
    resp = route_chat(
        _MSGS,
        profile="standard_generation",
        max_tokens=512,
        overrides=RequirementOverrides(
            exclude_models=frozenset({"qwen.qwen3.5-122b"}), exclude_leader=True
        ),
        snapshot=_route_snapshot(),
        backend_factory=_route_factory(be),
    )
    assert resp.model == "openai.gpt-oss-120b"
    assert be.calls[0]["model"] == "openai.gpt-oss-120b"
    assert "google.gemma-4-31B-it" not in [c["model"] for c in be.calls]


# --------------------------------------------------------------------------- #
# exclude_leader x max_candidates truncation (minor finding, folded in here).
# --------------------------------------------------------------------------- #


def test_exclude_leader_two_pass_truncation_reveals_next_candidate():
    """The full eligible set is sorted BEFORE truncation, so pass 1's leader is
    always the top-ranked model regardless of the cap — but pass 2's truncated
    window shifts once the leader is excluded, pulling in a candidate the cap
    had cut from the baseline chain."""
    snap = _snapshot()
    base = build_requirement("standard_generation", _CB)
    capped = replace(base, max_candidates=2)

    baseline = select(capped, snap)
    assert [c.model_ref.model_id for c in baseline.candidates] == [
        "qwen.qwen3.5-122b", "google.gemma-4-31B-it",
    ]

    leader = select(capped, snap).candidates[0].model_ref.model_id
    assert leader == "qwen.qwen3.5-122b"  # unaffected by the cap: sort precedes truncation
    narrowed = replace(capped, exclude_models=capped.exclude_models | {leader})
    after = select(narrowed, snap)

    # gpt-oss was cut by the cap in the baseline (rank 2, cap 2) but survives
    # once the leader is excluded and the truncation window shifts.
    assert [c.model_ref.model_id for c in after.candidates] == [
        "google.gemma-4-31B-it", "openai.gpt-oss-120b",
    ]
    assert len(after.candidates) == 2  # cap still enforced post-exclusion
