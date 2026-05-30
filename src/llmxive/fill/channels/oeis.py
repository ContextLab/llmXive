"""OEIS b-file channel (spec 017, T013/T014).

Fetches OEIS b-files directly (the search API is Cloudflare-blocked).
A-numbers referenced in the claim text or query are resolved via the
b-file URL: https://oeis.org/<A######>/b######.txt

Per librarian resilience pattern: any HTTP failure returns [] / {}.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from llmxive.fill.channels import AUTHORITY
from llmxive.fill.models import FetchedSource
from llmxive.librarian.search import USER_AGENT, _retry_request

if TYPE_CHECKING:
    from llmxive.claims.models import Claim

logger = logging.getLogger(__name__)

# Matches A followed by 6 or 7 digits (standard OEIS A-number format).
_A_NUMBER_RE = re.compile(r"\bA(\d{6,7})\b")


def a_numbers_in(text: str) -> list[str]:
    """Return deduplicated, order-preserving list of OEIS A-numbers in *text*.

    Examples
    --------
    >>> a_numbers_in("See A002863 for prime knots and A000001 for groups")
    ['A002863', 'A000001']
    """
    seen: set[str] = set()
    result: list[str] = []
    for m in _A_NUMBER_RE.finditer(text):
        a_num = f"A{m.group(1)}"
        if a_num not in seen:
            seen.add(a_num)
            result.append(a_num)
    return result


def _parse_bfile(text: str) -> dict[int, int]:
    """Parse OEIS b-file plain text into {index: value} dict.

    Lines beginning with '#' or blank lines are skipped.
    Each data line has the form ``<index> <value>`` (integers).
    """
    result: dict[int, int] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            idx = int(parts[0])
            val = int(parts[1])
            result[idx] = val
        except ValueError:
            continue
    return result


def _bfile_url(a_number: str) -> str:
    """Return the b-file URL for *a_number* (e.g. 'A002863')."""
    # Strip leading 'A', zero-pad to 6 digits for the filename.
    digits = a_number.lstrip("A")
    # The sequence number in the URL path keeps its 'A' prefix; the filename uses the bare number.
    return f"https://oeis.org/{a_number}/b{digits}.txt"


def fetch_bfile(a_number: str, *, timeout: float = 20.0) -> dict[int, int]:
    """Fetch and parse the b-file for *a_number* from OEIS.

    Returns an empty dict on any HTTP or parse failure.
    """
    url = _bfile_url(a_number)
    try:
        r = _retry_request(
            "GET",
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        if r.status_code != 200:
            logger.warning("oeis.fetch_bfile: HTTP %s for %s", r.status_code, url)
            return {}
        return _parse_bfile(r.text)
    except Exception as exc:
        logger.warning("oeis.fetch_bfile: failed for %s: %s", a_number, exc)
        return {}


def _render_bfile(data: dict[int, int]) -> str:
    """Render b-file dict back to 'n value\\n' lines (compact, sorted)."""
    return "\n".join(f"{n} {v}" for n, v in sorted(data.items()))


def search_and_fetch(
    query: str,
    claim: "Claim",
    *,
    timeout: float = 30.0,
) -> list[FetchedSource]:
    """Find A-numbers in the claim/query text, fetch their b-files.

    Returns a list of FetchedSource (one per A-number with a non-empty b-file).
    Returns [] on any failure — never raises into the caller.
    """
    # Collect search text from claim fields + query
    search_text = " ".join([
        query,
        getattr(claim, "raw_text", "") or "",
        getattr(claim, "canonical", "") or "",
    ])
    a_numbers = a_numbers_in(search_text)
    if not a_numbers:
        return []

    results: list[FetchedSource] = []
    for a_num in a_numbers:
        try:
            data = fetch_bfile(a_num, timeout=timeout)
            if not data:
                continue
            text = _render_bfile(data)
            if not text:
                continue
            url = f"https://oeis.org/{a_num}"
            results.append(FetchedSource(
                channel="oeis",
                source_id=a_num,
                url=url,
                title=a_num,
                text=text,
                authority=AUTHORITY["oeis"],
            ))
        except Exception as exc:
            logger.warning("oeis.search_and_fetch: error for %s: %s", a_num, exc)
            continue

    return results


__all__ = ["a_numbers_in", "_parse_bfile", "fetch_bfile", "search_and_fetch"]
