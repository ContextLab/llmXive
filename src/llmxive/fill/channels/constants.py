"""US2 / T014 — Constants fill channel (spec 018, FR-004/005).

search_and_fetch wraps verify.constants to provide a zero-network,
high-authority FetchedSource for recognized mathematical and physical constants.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from llmxive.fill.channels import AUTHORITY
from llmxive.fill.models import FetchedSource
from llmxive.verify import constants as _const_mod

if TYPE_CHECKING:
    from llmxive.claims.models import Claim


def search_and_fetch(
    query: str,
    claim: Claim,
    *,
    timeout: float = 30.0,
) -> list[FetchedSource]:
    """Return a FetchedSource for a recognized constant, or [] if unknown.

    Probes in this order:
    1. claim.canonical (preferred — most structured form)
    2. claim.raw_text
    3. query (fallback)

    No network I/O is performed. The ``timeout`` parameter is accepted for
    interface compatibility with other channels but is unused.
    """
    candidates = [
        claim.canonical,
        claim.raw_text,
        query,
    ]

    const: _const_mod.CuratedConstant | None = None
    for text in candidates:
        if text:
            const = _const_mod.lookup(text)
            if const is not None:
                break

    if const is None:
        return []

    return [
        FetchedSource(
            channel="constants",
            source_id=const.key,
            url=const.url,
            title=const.key,
            text=f"{const.value} ({const.authority})",
            authority=AUTHORITY["constants"],
        )
    ]


__all__ = ["search_and_fetch"]
