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


def channels_for(kind: ClaimKind, *, math: bool) -> list[str]:
    """Return the ordered channel names to try for *kind* in v1.

    NUMERIC  → [constants, oeis, wikipedia, paper] (+ theorem if math-classified)
    ENTITY_FACT → [wikidata, wikipedia, paper]
    everything else → [] (deferred in v1; claim stays blocked)
    """
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


__all__ = ["AUTHORITY", "channels_for"]
