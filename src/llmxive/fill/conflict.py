"""Channel-priority conflict resolution (spec 017, FR-008, PURE).

choose(candidates) — given (FetchedSource, value) pairs from multiple channels,
                     returns the highest-authority (lowest authority int) source's
                     value plus a conflicts list of lower-authority disagreements.
                     Never drops a conflict.  Deterministic by AUTHORITY rank.
"""

from __future__ import annotations

from llmxive.fill.models import FetchedSource


def choose(
    candidates: list[tuple[FetchedSource, str]],
) -> tuple[FetchedSource, str, list[dict]]:
    """Select the highest-authority candidate and record conflicting lower-authority values.

    Parameters
    ----------
    candidates:
        Non-empty list of ``(FetchedSource, value)`` pairs from one or more
        channels.  The ``source.authority`` field carries the rank (lower =
        higher authority; sourced from ``channels.AUTHORITY``).

    Returns
    -------
    (winner_source, winner_value, conflicts)
        ``winner_source`` — the FetchedSource with the lowest authority rank.
        ``winner_value``  — the value extracted from that source.
        ``conflicts``     — list of ``{value, source_id, url, channel}`` dicts
                            for every lower-authority source whose value DIFFERS
                            from ``winner_value``.  Sources that agree with the
                            winner are NOT included (they are corroboration, not
                            conflicts).

    Raises
    ------
    ValueError
        If *candidates* is empty.
    """
    if not candidates:
        raise ValueError("choose() requires at least one candidate")

    # Sort by authority rank (ascending = highest authority first), then by
    # source_id for determinism when authorities are equal.
    ranked = sorted(candidates, key=lambda pair: (pair[0].authority, pair[0].source_id))

    winner_src, winner_val = ranked[0]

    conflicts: list[dict] = []
    for src, val in ranked[1:]:
        if val != winner_val:
            conflicts.append({
                "value": val,
                "source_id": src.source_id,
                "url": src.url,
                "channel": src.channel,
            })

    return winner_src, winner_val, conflicts


__all__ = ["choose"]
