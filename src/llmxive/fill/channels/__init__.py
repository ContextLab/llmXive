"""Channel registry: authority ranks and per-kind routing (spec 017)."""

from __future__ import annotations

from llmxive.claims.models import ClaimKind

# Lower integer = higher authority (most trusted source wins in conflict.choose).
AUTHORITY: dict[str, int] = {
    "oeis": 0,
    "wikidata": 1,
    "wikipedia": 2,
    "theorem": 3,
    "paper": 4,
}


def channels_for(kind: ClaimKind, *, math: bool) -> list[str]:
    """Return the ordered channel names to try for *kind* in v1.

    NUMERIC  → [oeis, wikipedia, paper] (+ theorem if math-classified)
    ENTITY_FACT → [wikidata, wikipedia, paper]
    everything else → [] (deferred in v1; claim stays blocked)
    """
    if kind == ClaimKind.NUMERIC:
        channels = ["oeis", "wikipedia", "paper"]
        if math:
            channels.append("theorem")
        return channels
    if kind == ClaimKind.ENTITY_FACT:
        return ["wikidata", "wikipedia", "paper"]
    return []


__all__ = ["AUTHORITY", "channels_for"]
