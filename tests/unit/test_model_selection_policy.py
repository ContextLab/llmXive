"""Capability-policy schema + attribution tests (spec 026, slice 2, FR-006)."""

from __future__ import annotations

import pytest

from llmxive.model_selection.policy import (
    CAPABILITY_POLICY,
    SELECTION_POLICY_VERSION,
    CapabilityPolicy,
    PolicyEntry,
)
from llmxive.model_selection.types import Capability

_VALID_CAPABILITIES = {"cheap", "standard", "deep", "vision"}
_EXPECTED_FAMILIES = {
    "glm-5.3", "qwen3.5", "gemma-4", "gpt-oss", "claude-haiku-4-5", "qwen3-vl", "qwen2.5",
}


def test_policy_version_matches_constant():
    assert CAPABILITY_POLICY.version == SELECTION_POLICY_VERSION == 4


def test_expected_families_present_and_gemma3_absent():
    assert set(CAPABILITY_POLICY.entries) == _EXPECTED_FAMILIES
    # The maintainer-approved gemma-3→gemma-4 correction: gemma-3 is deliberately
    # NOT attributed → ineligible even while it lingers in the live catalog.
    assert "gemma-3" not in CAPABILITY_POLICY.entries


def test_schema_every_entry_well_formed():
    for family, entry in CAPABILITY_POLICY.entries.items():
        assert isinstance(entry, PolicyEntry)
        assert entry.capabilities, f"{family} has no capabilities"
        assert entry.capabilities <= _VALID_CAPABILITIES, f"{family} has an unknown capability"
        assert entry.quality_tier > 0, f"{family} quality_tier must be positive"
        assert entry.max_context_tokens > 0, f"{family} context must be positive"
        assert isinstance(entry.features, frozenset)


def test_entries_are_immutable():
    with pytest.raises(TypeError):
        CAPABILITY_POLICY.entries["injected"] = PolicyEntry(frozenset(), frozenset(), 1, 1)  # type: ignore[index]


def test_attribution_helpers():
    assert CAPABILITY_POLICY.has_capability("qwen3.5", "deep")
    assert not CAPABILITY_POLICY.has_capability("qwen3-vl", "deep")  # vision-only
    assert CAPABILITY_POLICY.has_capability("qwen3-vl", "vision")
    assert CAPABILITY_POLICY.has_features("qwen3.5", frozenset({"reasoning", "structured"}))
    assert not CAPABILITY_POLICY.has_features("gemma-4", frozenset({"reasoning"}))
    assert CAPABILITY_POLICY.quality_tier("qwen3.5") == 3
    assert CAPABILITY_POLICY.quality_tier("qwen2.5") == 1  # local fallback, lowest
    assert CAPABILITY_POLICY.max_context_tokens("qwen3.5") == 256_000


def test_unknown_family_is_ineligible():
    assert CAPABILITY_POLICY.entry("no-such-family") is None
    assert not CAPABILITY_POLICY.has_capability("no-such-family", "cheap")
    assert CAPABILITY_POLICY.quality_tier("no-such-family") == 0
    assert CAPABILITY_POLICY.max_context_tokens("no-such-family") is None


def test_capability_literal_covered():
    # Every capability value the policy attributes is a member of the Capability
    # Literal (guards against a typo silently attributing an unroutable capability).
    valid = set(Capability.__args__)  # type: ignore[attr-defined]
    for entry in CAPABILITY_POLICY.entries.values():
        assert entry.capabilities <= valid


def test_injected_policy_is_frozen_copy():
    src = {"fam": PolicyEntry(frozenset({"cheap"}), frozenset(), 1, 1000)}
    pol = CapabilityPolicy(version=99, entries=src)
    src["fam2"] = PolicyEntry(frozenset({"deep"}), frozenset(), 2, 2000)  # mutate the source
    assert "fam2" not in pol.entries  # policy took a defensive copy
    assert pol.version == 99
