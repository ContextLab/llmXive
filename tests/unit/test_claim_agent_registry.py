"""T041 (spec 016, FR-001) — the claim-producing-agent registry is complete."""

from __future__ import annotations

import inspect

from llmxive.claims.agents import (
    CLAIM_PRODUCING_AGENTS,
    CLAIM_PRODUCING_STAGE_IDS,
    is_claim_producing,
)


def test_registry_covers_every_fr001_doc_producing_stage():
    # FR-001 enumerates: spec, clarify, plan, tasks, implement, and the paper-
    # stage equivalents, plus flesh-out and any results/summary producers.
    required = {
        "spec", "clarify", "plan", "tasks", "implement",
        "flesh_out", "paper_spec", "paper_clarify", "paper", "results_summary",
    }
    assert required <= CLAIM_PRODUCING_STAGE_IDS
    assert is_claim_producing("spec")
    assert not is_claim_producing("mechanical_scaffolding")


def test_registry_entries_are_well_formed():
    for stage_id, description in CLAIM_PRODUCING_AGENTS:
        assert stage_id and isinstance(stage_id, str)
        assert description and isinstance(description, str)
    # no duplicate stage ids
    ids = [a[0] for a in CLAIM_PRODUCING_AGENTS]
    assert len(ids) == len(set(ids))


def test_chokepoint_coverage_is_path_based_not_stage_gated():
    """The real coverage guarantee: the shared write chokepoint processes every
    produced ``.md`` / ``.tex`` artifact regardless of which stage produced it,
    so no doc-producing agent can bypass the claim layer. Assert the chokepoint
    source runs the claim layer over artifact paths (not a per-stage allowlist)."""
    from llmxive.speckit import slash_command

    src = inspect.getsource(slash_command._validate_artifact_citations)
    assert "process_document" in src  # claim layer is invoked at the chokepoint
    assert ".md" in src or ".tex" in src  # gated by artifact suffix, not stage id
