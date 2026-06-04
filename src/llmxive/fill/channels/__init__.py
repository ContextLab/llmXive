"""Channel registry: authority ranks and per-kind routing (spec 017/018)."""

from __future__ import annotations

from llmxive.claims.models import ClaimKind

# Lower integer = higher authority (most trusted source wins in conflict.choose).
# "constants" is the highest authority: library-backed values are exact by definition.
AUTHORITY: dict[str, int] = {
    "constants": 0,
    "oeis": 1,
    "wikidata": 2,
    "wikipedia": 3,
    "theorem": 4,
    "paper": 5,
}

# STRUCTURED vs PROSE substantiation classification (spec 019, single source of
# truth). A STRUCTURED channel returns a value *for* the subject by construction —
# the constants alias table is keyed by name, the OEIS b-file is read by index, a
# Wikidata statement is a subject/predicate/value triple — so literal presence of
# the value in the fetched record already substantiates the subject<->value link.
# A PROSE channel (Wikipedia/theorem/paper full text) is free text where a value
# can appear coincidentally in an unrelated passage; those candidates must clear
# the spec-019 semantic gate (subject-keyword co-occurrence + entailment).
STRUCTURED_CHANNELS: frozenset[str] = frozenset({"constants", "oeis", "wikidata"})


def is_structured(channel: str) -> bool:
    """True iff *channel*'s data structure makes the subject<->value link inherent
    (constants alias table / OEIS b-file by index / Wikidata triple)."""
    return channel in STRUCTURED_CHANNELS


def is_prose(channel: str) -> bool:
    """True iff *channel* is free prose where a value can appear coincidentally.

    Defined as the complement of :func:`is_structured`, so an unknown or
    unclassified channel is treated as PROSE — i.e. it gets the stricter semantic
    gate (fail-closed, spec 019 FR-001)."""
    return not is_structured(channel)


def channels_for(
    kind: ClaimKind, *, math: bool, stage_label: str | None = None
) -> list[str]:
    """Return the ordered channel names to try for *kind* in v1.

    NUMERIC  → [constants, oeis, wikipedia, paper] (+ theorem if math-classified)
    ENTITY_FACT → [wikidata, wikipedia, paper]
    everything else → [] (deferred in v1; claim stays blocked)

    Spec 020 FR-002: in a *planning* stage (specify/clarify/plan/tasks) no
    low-level kind is fetched — returns ``[]`` so there is no external fetch /
    locator call. This is the defense-in-depth boundary; the primary planning
    guarantee is that ``process_document`` never reaches the fill path in a
    planning stage at all.
    """
    from llmxive.claims.stage import is_planning_stage

    if is_planning_stage(stage_label):
        return []
    if kind == ClaimKind.NUMERIC:
        channels = ["constants", "oeis", "wikipedia", "paper"]
        if math:
            channels.append("theorem")
        return channels
    if kind == ClaimKind.ENTITY_FACT:
        return ["wikidata", "wikipedia", "paper"]
    if kind == ClaimKind.MAGNITUDE:
        return ["wikidata", "wikipedia", "paper"]
    if kind == ClaimKind.RELATIONAL:
        return ["wikidata", "wikipedia", "paper"]
    return []


__all__ = [
    "AUTHORITY",
    "STRUCTURED_CHANNELS",
    "channels_for",
    "is_prose",
    "is_structured",
]
