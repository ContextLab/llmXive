"""LMArena leaderboard scores for model selection (paged, keyless fetch + strict name matching).

Ratings come from the public ``lmarena-ai/leaderboard-dataset`` via the Hugging Face
datasets-server ``/filter`` endpoint.  Matching a catalog repo id to an arena model name is
deliberately strict: a name must normalise identically and be unique among the input repos,
otherwise the model simply gets no score (fail closed).  This module is the only caller of
the datasets server; only ``snapshot.py`` calls it.
"""

from __future__ import annotations

import json
import logging
import math
import re
import time
from collections.abc import Iterable, Mapping
from datetime import date
from types import MappingProxyType

import httpx

from llmxive.model_selection.types import ArenaScore, ModelScores, Track

logger = logging.getLogger(__name__)

LMARENA_DATASET = "lmarena-ai/leaderboard-dataset"
LMARENA_CONFIG = "text"
LMARENA_SPLIT = "latest"
DATASETS_SERVER_FILTER_URL = "https://datasets-server.huggingface.co/filter"
PAGE_LENGTH = 100  # the server's maximum; 101 -> HTTP 422
TRACK_CATEGORY: Mapping[Track, str] = MappingProxyType({"reasoning": "overall", "coding": "coding"})

# The datasets server normally answers a page in well under a second, but now and then
# answers 5xx, drops a connection, or leaves one request hanging for a minute or more.
# Each request gets a short timeout; a transport error (timeout, reset, refused) or a
# 5xx is retried on the same page with a linear backoff; a 4xx fails at once. The whole
# fetch (every page of both tracks) runs inside one overall budget, after which it
# fails closed ("unavailable") — never an unbounded wait.
REQUEST_TIMEOUT_S = 10.0
MAX_RETRIES = 4  # retries per page after the first attempt
RETRY_BACKOFF_SECONDS = 0.5  # sleep before retry n is n x this
FETCH_BUDGET_S = 90.0

#: Monotonic clock for :data:`FETCH_BUDGET_S` (module-level so tests can replace it).
_monotonic = time.monotonic

_TRAILING_GROUP = re.compile(r"\s*\([^()]*\)\s*$")


class LeaderboardError(RuntimeError):
    """The leaderboard could not be fetched or was inconsistent."""


def normalise_name(name: str) -> str:
    """Strip trailing ``( ... )`` groups, lowercase, keep only ``[a-z0-9]``."""
    text = name.strip()
    while True:
        stripped = _TRAILING_GROUP.sub("", text)
        if stripped == text:
            break
        text = stripped
    return re.sub(r"[^a-z0-9]", "", text.lower())


def normalise_repo(repo_id: str) -> str:
    return normalise_name(repo_id.split("/", 1)[-1])


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None


def _parse_row(row: Mapping) -> tuple[str, ArenaScore] | None:
    name = row.get("model_name")
    key = normalise_name(name) if isinstance(name, str) else ""
    if not key:
        logger.warning("leaderboard row skipped: unusable model_name %r", name)
        return None
    rating = _number(row.get("rating"))
    if rating is None:
        logger.warning("leaderboard row %r skipped: rating is not a finite number", name)
        return None
    lower_raw, upper_raw = row.get("rating_lower"), row.get("rating_upper")
    if any(raw is not None and _number(raw) is None for raw in (lower_raw, upper_raw)):
        logger.warning("leaderboard row %r skipped: bounds are not finite numbers", name)
        return None
    if lower_raw is None or upper_raw is None:
        # A row missing EITHER bound is a zero-width interval (spec 5.10 "Near-ties"):
        # a half-filled interval would invent a one-sided near-tie band.
        lower = upper = rating
    else:
        lower, upper = _number(lower_raw), _number(upper_raw)
    published = row.get("leaderboard_publish_date")
    try:
        publish_date = date.fromisoformat(published)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        logger.warning("leaderboard row %r skipped: bad publish date %r", name, published)
        return None
    try:
        return key, ArenaScore(rating, lower, upper, publish_date)
    except ValueError as exc:
        logger.warning("leaderboard row %r skipped: %s", name, exc)
        return None


def parse_arena_rows(rows: Iterable[Mapping], *, category: str) -> dict[str, ArenaScore]:
    """Parse rows into ``{normalised name: ArenaScore}``; the highest rating wins a name."""
    out: dict[str, ArenaScore] = {}
    for row in rows:
        if row.get("category") != category:
            raise LeaderboardError(
                f"row category {row.get('category')!r} != requested {category!r} (server ignored the filter)"
            )
        parsed = _parse_row(row)
        if parsed is None:
            continue
        key, score = parsed
        if key not in out or score.rating > out[key].rating:
            out[key] = score
    return out


def _over_budget(last: str) -> LeaderboardError:
    return LeaderboardError(
        f"datasets server unavailable: the fetch exceeded its {FETCH_BUDGET_S:g}s budget (last: {last})"
    )


def _request(
    client: httpx.Client, base_url: str, params: dict[str, str | int], *, deadline: float
) -> tuple[int, bytes]:
    """One GET, read in chunks so a body that trickles in cannot outlast the budget by
    more than one per-request timeout."""
    timeout = min(REQUEST_TIMEOUT_S, deadline - _monotonic())
    chunks: list[bytes] = []
    with client.stream("GET", base_url, params=params, timeout=timeout) as resp:
        for chunk in resp.iter_bytes():
            chunks.append(chunk)
            if _monotonic() >= deadline:
                raise _over_budget("response still arriving")
        return resp.status_code, b"".join(chunks)


def _get_page(
    client: httpx.Client, base_url: str, params: dict[str, str | int], *, deadline: float
) -> dict:
    last = "no attempt made"
    for attempt in range(MAX_RETRIES + 1):
        if attempt:
            pause = RETRY_BACKOFF_SECONDS * attempt
            if pause >= deadline - _monotonic():
                raise _over_budget(last)
            time.sleep(pause)
        if _monotonic() >= deadline:
            raise _over_budget(last)
        try:
            status, raw = _request(client, base_url, params, deadline=deadline)
        except httpx.TransportError as exc:  # read/connect timeout, reset, refused
            last = type(exc).__name__
        else:
            if status == 200:
                try:
                    body = json.loads(raw)
                except ValueError as exc:
                    raise LeaderboardError(f"datasets server returned non-JSON 200: {exc}") from exc
                if not isinstance(body, dict):
                    raise LeaderboardError("datasets server returned a non-object body")
                return body
            last = f"HTTP {status}"
            if status < 500:
                break
        if attempt < MAX_RETRIES:
            logger.warning(
                "LMArena page at offset %s: attempt %d failed (%s); retrying", params["offset"], attempt + 1, last
            )
    raise LeaderboardError(f"datasets server unavailable: {last}")


def fetch_arena_category(
    category: str, *, base_url: str = DATASETS_SERVER_FILTER_URL, deadline: float | None = None
) -> list[dict]:
    """Fetch every row of one leaderboard category (keyless), paging to ``num_rows_total``.

    ``deadline`` is a :data:`_monotonic` time the whole fetch must end by (default:
    :data:`FETCH_BUDGET_S` from now); past it the fetch raises :class:`LeaderboardError`."""
    if deadline is None:
        deadline = _monotonic() + FETCH_BUDGET_S
    rows: list[dict] = []
    offset = 0
    total: int | None = None
    last_idx = -1
    with httpx.Client(timeout=REQUEST_TIMEOUT_S) as client:
        while total is None or offset < total:
            body = _get_page(
                client,
                base_url,
                {
                    "dataset": LMARENA_DATASET,
                    "config": LMARENA_CONFIG,
                    "split": LMARENA_SPLIT,
                    "where": f"\"category\"='{category}'",
                    "offset": offset,
                    "length": PAGE_LENGTH,
                },
                deadline=deadline,
            )
            if body.get("partial") is True:
                raise LeaderboardError("datasets server reported a partial result")
            page_total = body.get("num_rows_total")
            if isinstance(page_total, bool) or not isinstance(page_total, int) or page_total < 0:
                raise LeaderboardError(f"datasets server gave no usable num_rows_total: {page_total!r}")
            if total is None:
                if page_total == 0:
                    raise LeaderboardError(f"leaderboard category {category!r} is empty")
                total = page_total
            elif page_total != total:
                raise LeaderboardError(f"num_rows_total changed mid-fetch: {total} -> {page_total}")
            page = body.get("rows")
            if not isinstance(page, list):
                raise LeaderboardError("datasets server page has no rows list")
            if not page:
                raise LeaderboardError(f"empty page at offset {offset} before total {total}")
            if len(page) > PAGE_LENGTH:
                raise LeaderboardError(f"page at offset {offset} has {len(page)} rows > {PAGE_LENGTH}")
            for item in page:
                row = item.get("row") if isinstance(item, dict) else None
                if not isinstance(row, dict):
                    raise LeaderboardError("datasets server row has no 'row' object")
                idx = item.get("row_idx")
                if isinstance(idx, bool) or not isinstance(idx, int):
                    raise LeaderboardError(f"page at offset {offset} has a row without an integer row_idx")
                # In a filtered query row_idx indexes the whole split (gaps are normal), so
                # a repeated or overlapping page shows up as a non-increasing sequence.
                if idx <= last_idx:
                    raise LeaderboardError(
                        f"page at offset {offset} repeats or reorders rows (row_idx {idx} after {last_idx})"
                    )
                last_idx = idx
                rows.append(row)
            offset += len(page)
    if len(rows) != total:
        raise LeaderboardError(f"fetched {len(rows)} rows but num_rows_total is {total}")
    return rows


def fetch_arena_scores(
    *, base_url: str = DATASETS_SERVER_FILTER_URL
) -> dict[Track, dict[str, ArenaScore]] | None:
    """Both tracks' scores, or ``None`` (logged) so the snapshot's last-known-good takes over.

    Both tracks share ONE :data:`FETCH_BUDGET_S` budget."""
    deadline = _monotonic() + FETCH_BUDGET_S
    try:
        return {
            track: parse_arena_rows(
                fetch_arena_category(cat, base_url=base_url, deadline=deadline), category=cat
            )
            for track, cat in TRACK_CATEGORY.items()
        }
    except (LeaderboardError, httpx.HTTPError) as exc:
        logger.warning("LMArena fetch failed: %s: %s", type(exc).__name__, exc)
        return None


def join_scores(
    repo_ids: Iterable[str], arena: Mapping[Track, Mapping[str, ArenaScore]]
) -> tuple[dict[str, ModelScores], tuple[str, ...]]:
    """Attach scores to repos whose normalised name is unique among the inputs.

    Returns ``(scores by repo id, sorted ambiguous names)``; ambiguous names (shared by two
    or more input repos and present in the arena data) score nothing.
    """
    by_name: dict[str, list[str]] = {}
    for repo in dict.fromkeys(repo_ids):
        by_name.setdefault(normalise_repo(repo), []).append(repo)
    arena_names = {name for table in arena.values() for name in table}
    ambiguous = tuple(sorted(n for n, repos in by_name.items() if len(repos) > 1 and n in arena_names))
    scores: dict[str, ModelScores] = {}
    for name, repos in by_name.items():
        if len(repos) != 1 or not name:
            continue
        reasoning = arena.get("reasoning", {}).get(name)
        coding = arena.get("coding", {}).get(name)
        if reasoning is not None or coding is not None:
            scores[repos[0]] = ModelScores(reasoning=reasoning, coding=coding)
    return scores, ambiguous
