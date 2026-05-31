"""Transient fill-layer entities (spec 017, data-model.md).

FetchedSource  — a source whose text was actually retrieved by a channel.
FillProvenance — records the origin of a corrected claim value.
FillResult     — the terminal outcome of one fill attempt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FetchedSource:
    """A resolvable source whose text was actually retrieved by a channel.

    Fields
    ------
    channel    : one of oeis | wikidata | wikipedia | theorem | paper
    source_id  : stable identifier (OEIS A-number, Wikidata Q-id, etc.)
    url        : resolvable URL
    title      : human-readable title (may be None)
    text       : the fetched text the value must be located in (non-empty)
    authority  : channel authority rank (lower = higher authority)
    """

    channel: str
    source_id: str
    url: str
    title: str | None
    text: str
    authority: int

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError("FetchedSource.text must be non-empty")


@dataclass(frozen=True)
class FillProvenance:
    """Provenance record stored inside Claim.evidence (FR-004).

    Stored shape inside Claim.evidence:
        evidence:
          filled: true
          fill:
            value: "9988"
            source_id: "A002863"
            url: "https://oeis.org/A002863"
            quote: "13 9988"
            channel: "oeis"
            conflicts: []
    """

    value: str
    source_id: str
    url: str
    quote: str
    channel: str
    conflicts: list[dict[str, str]]  # frozen=True keeps the reference immutable

    def to_dict(self) -> dict[str, Any]:
        """Serialisable representation for storage in Claim.evidence."""
        return {
            "value": self.value,
            "source_id": self.source_id,
            "url": self.url,
            "quote": self.quote,
            "channel": self.channel,
            "conflicts": list(self.conflicts),
        }


@dataclass(frozen=True)
class FillResult:
    """Terminal outcome of one fill attempt (transient).

    status          : "filled" | "blocked"
    value           : corrected value when filled, None otherwise
    provenance      : FillProvenance when filled, None otherwise
    channels_tried  : ordered list of channel names attempted (observability)
    reason          : human-readable reason for blocked, or "" when filled
    """

    status: str
    value: str | None
    provenance: FillProvenance | None
    channels_tried: list[str]
    reason: str

    def __post_init__(self) -> None:
        if self.status not in {"filled", "blocked"}:
            raise ValueError(
                f"FillResult.status must be 'filled' or 'blocked', got {self.status!r}"
            )
        if self.status == "filled":
            if self.value is None:
                raise ValueError("A 'filled' FillResult must have a non-null value")
            if self.provenance is None:
                raise ValueError("A 'filled' FillResult must have a non-null provenance")

    # --- factories -----------------------------------------------------------

    @classmethod
    def filled(
        cls,
        value: str,
        provenance: FillProvenance,
        channels_tried: list[str],
    ) -> FillResult:
        """Convenience constructor for a successful fill."""
        return cls(
            status="filled",
            value=value,
            provenance=provenance,
            channels_tried=channels_tried,
            reason="",
        )

    @classmethod
    def blocked(
        cls,
        reason: str,
        channels_tried: list[str],
    ) -> FillResult:
        """Convenience constructor for a blocked (unfillable) claim."""
        return cls(
            status="blocked",
            value=None,
            provenance=None,
            channels_tried=channels_tried,
            reason=reason,
        )


__all__ = ["FetchedSource", "FillProvenance", "FillResult"]
