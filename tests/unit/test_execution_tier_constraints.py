"""Escalation ladder as REQUIREMENT constraints, not model-id literals (spec 026
slice 6). Drives the REAL ``execution_status`` tier functions + the REAL
``RequirementOverrides`` value — no mocks (Constitution III)."""

from __future__ import annotations

import pytest

from llmxive.state import execution_status as es


@pytest.fixture(autouse=True)
def _free_first(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    monkeypatch.delenv("LLMXIVE_EXECUTION_PAID_ESCALATION", raising=False)


def test_tier0_is_free_only_even_when_opt_in_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    ov = es.tier_constraint(0).to_overrides()
    assert ov.allow_paid is False and ov.require_paid is False
    assert ov.exclude_leader is False
    assert ov.exclude_models == frozenset()


def test_tier1_free_second_opinion_sets_exclude_leader() -> None:
    ov = es.tier_constraint(1).to_overrides()
    assert ov.allow_paid is False
    assert ov.exclude_leader is True
    assert ov.exclude_models == frozenset()


def test_corrupt_tier_resolves_free_only() -> None:
    for bad in (-1, True, 2.5, "1", 10**9):
        c = es.tier_constraint(bad)  # type: ignore[arg-type]
        assert c.allow_paid is False and c.require_paid is False


def test_corrupt_tier_resolves_free_only_even_with_paid_rung(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The corrupt-tier→free-only invariant is only meaningful when a paid rung
    EXISTS at the end of the ladder — otherwise every rung is free anyway and a
    re-introduced last-rung clamp would go undetected. Lock it WITH the paid
    rung present (real env, no mocks)."""
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "1")  # ladder gains a paid rung
    assert len(es.model_tier_ladder()) == 4  # three free rungs + one paid rung
    for bad in (-1, True, 2.5, "1", 10**9):
        c = es.tier_constraint(bad)  # type: ignore[arg-type]
        assert c.is_paid is False and c.allow_paid is False  # never the paid rung
    # A stale in-range paid tier index resolves to free once paid is disabled:
    monkeypatch.delenv("LLMXIVE_EXECUTION_PAID_ESCALATION", raising=False)
    paid_index = 3  # where the paid rung sat while escalation was enabled
    assert paid_index >= len(es.model_tier_ladder())  # now past the free-only ladder
    assert es.tier_constraint(paid_index) == es.model_tier_ladder()[0]  # -> ladder[0]
    assert es.tier_constraint(paid_index).is_paid is False


def test_paid_rung_present_only_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    assert all(not c.is_paid for c in es.model_tier_ladder())  # free-only default
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "1")
    ladder = es.model_tier_ladder()
    assert sum(c.is_paid for c in ladder) == 1  # exactly one paid rung
    paid = next(c for c in ladder if c.is_paid)
    assert paid.allow_paid is True and paid.require_paid is True


def test_paid_rung_to_overrides_is_require_paid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "1")
    ov = es.model_tier_ladder()[-1].to_overrides()
    assert ov.allow_paid is True and ov.require_paid is True


def test_env_unset_defaults_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLMXIVE_EXECUTION_PAID_ESCALATION", raising=False)
    assert all(not c.is_paid for c in es.model_tier_ladder())


def test_env_invalid_new_value_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "banana")
    assert all(not c.is_paid for c in es.model_tier_ladder())  # invalid → off


def test_next_usable_tier_skips_paid_when_opt_in_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "1")  # ladder has paid rung
    # opt-in OFF → paid unusable
    assert es.next_usable_tier(0) == 1               # free second opinion
    assert es.next_usable_tier(1) == 2               # third free family
    assert es.next_usable_tier(2) is None            # paid skipped (opt-in off)


def test_fabrication_free_only_never_reaches_paid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "1")
    monkeypatch.setattr(es, "paid_tier_usable", lambda: True)  # opt-in ON, headroom
    assert es.next_usable_tier(2) == 3                       # paid reachable generally
    assert es.model_tier_ladder()[3].is_paid
    assert es.next_usable_tier(2, free_only=True) is None    # ...but not free_only
    assert es.next_usable_tier(0, free_only=True) == 1
    assert es.next_usable_tier(1, free_only=True) == 2       # every free rung stays reachable


def test_third_free_rung_drops_the_top_two_candidates() -> None:
    """Tier 2 is a THIRD free family: it excludes the two best-ranked candidates
    (no model id), so the policy's third-best free model leads."""
    from llmxive.model_selection.route import resolve_chain

    free = [c for c in es.model_tier_ladder() if not c.is_paid]
    assert len(free) == 3
    leaders = [
        resolve_chain([], profile="deep_code", max_tokens=1, overrides=c.to_overrides())[1]
        .candidates[0].model_ref.model_id
        for c in free
    ]
    # Over the offline snapshot's free chain (tests/conftest.py), in policy order.
    assert leaders == ["zai-org.glm-5.3", "qwen.qwen3.5-122b", "google.gemma-4-31B-it"]
    assert all(c.to_overrides().allow_paid is False for c in free)


def test_workflows_set_the_paid_escalation_variable_the_code_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The deployed workflows must enable the paid rung through the variable this
    module reads. They once kept setting the retired model-id list
    ``LLMXIVE_EXECUTION_PAID_TIERS`` after the reader moved to the boolean, so the
    paid rung could never enable in CI. Reads the REAL workflow files."""
    import re
    from pathlib import Path

    import yaml

    workflows = Path(__file__).resolve().parents[2] / ".github" / "workflows"
    found: dict[str, list[tuple[str, str]]] = {}

    def walk(node: object, name: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(key, str) and key.startswith("LLMXIVE_EXECUTION_PAID"):
                    found.setdefault(name, []).append((key, str(value)))
                walk(value, name)
        elif isinstance(node, list):
            for item in node:
                walk(item, name)

    for path in sorted(workflows.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        walk(yaml.safe_load(text), path.name)
        # Also catch the name outside a mapping key (an inline shell export).
        assert "LLMXIVE_EXECUTION_PAID_TIERS" not in text, path.name
        for name in re.findall(r"LLMXIVE_EXECUTION_PAID\w*", text):
            assert name == es.PAID_ESCALATION_ENV, (path.name, name)

    # The five pipeline lanes that opt in to paid spend also enable the rung.
    assert set(found) >= {
        "advance.yml", "llmxive-pipeline.yml", "maintenance.yml",
        "pipeline-personality.yml", "reprocess.yml",
    }
    for name, pairs in found.items():
        for key, value in pairs:
            assert key == es.PAID_ESCALATION_ENV, (name, key)
            # The value is a boolean the reader accepts, never a model-id list.
            monkeypatch.setenv(es.PAID_ESCALATION_ENV, value)
            assert es._paid_escalation_enabled() is True, (name, value)


# --- Spec 027 section 5.10: each free rung raises the funded strength level ---------


def test_each_free_rung_raises_the_funded_level_by_its_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert [c.to_overrides().level_delta for c in es.model_tier_ladder()] == [0, 1, 2]
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "1")
    ladder = es.model_tier_ladder()
    assert ladder[-1].to_overrides().level_delta == 0 and len(ladder) == 4


def test_rungs_climb_levels_and_end_at_strongest_when_dartmouth_is_down() -> None:
    from llmxive.model_selection.route import resolve_chain
    from tests.helpers.funded import B, E, snapshot

    snap = snapshot(local=False)

    def walk(profile: str) -> tuple[list[str | None], list[str]]:
        out = [
            resolve_chain([], profile=profile, max_tokens=1,
                          overrides=c.to_overrides(), snapshot=snap)
            for c in es.model_tier_ladder()
        ]
        return [r.strength for r, _ in out], [ch.candidates[0].model_ref.model_id for _, ch in out]

    assert walk("cheap_structured") == (["economy", "balanced", "strong"], [B, E, E])
    assert walk("deep_code") == (["strong", "strongest", "strongest"], [B, B, B])


def test_funded_leader_is_never_excluded() -> None:
    from llmxive.model_selection.route import resolve_chain
    from llmxive.model_selection.types import RequirementOverrides
    from tests.helpers.funded import B, snapshot

    req, chain = resolve_chain(
        [], profile="deep_code", max_tokens=1, snapshot=snapshot(local=False),
        overrides=RequirementOverrides(exclude_leaders=2, level_delta=1),
    )
    assert [c.model_ref.model_id for c in chain.candidates] == [B]
    assert req.exclude_models == frozenset()
