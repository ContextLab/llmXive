"""LMArena leaderboard scores for model selection (paged, keyless fetch + strict name matching).

Ratings come from the public ``lmarena-ai/leaderboard-dataset`` via the Hugging Face
datasets-server ``/filter`` endpoint.  Matching a catalog repo id to an arena model name is
deliberately strict: a name must normalise identically and be unique among the input repos,
otherwise the model simply gets no score (fail closed).  This module is the only caller of
the datasets server; only ``snapshot.py`` calls it.
"""

from __future__ import annotations

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

# The datasets server answers transient 5xx now and then: retry a fixed small number of
# times, then fail closed ("unavailable").
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 0.25

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
    lower = rating if lower_raw is None else _number(lower_raw)
    upper = rating if upper_raw is None else _number(upper_raw)
    if lower is None or upper is None:
        logger.warning("leaderboard row %r skipped: bounds are not finite numbers", name)
        return None
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


def _get_page(client: httpx.Client, base_url: str, params: dict[str, str | int]) -> dict:
    last = "no attempt made"
    for attempt in range(MAX_RETRIES + 1):
        if attempt:
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)
        resp = client.get(base_url, params=params)
        if resp.status_code == 200:
            try:
                body = resp.json()
            except ValueError as exc:
                raise LeaderboardError(f"datasets server returned non-JSON 200: {exc}") from exc
            if not isinstance(body, dict):
                raise LeaderboardError("datasets server returned a non-object body")
            return body
        last = f"HTTP {resp.status_code}"
        if resp.status_code < 500:
            break
    raise LeaderboardError(f"datasets server unavailable: {last}")


def fetch_arena_category(
    category: str, *, base_url: str = DATASETS_SERVER_FILTER_URL, timeout: float = 30.0
) -> list[dict]:
    """Fetch every row of one leaderboard category (keyless), paging to ``num_rows_total``."""
    rows: list[dict] = []
    offset = 0
    total: int | None = None
    last_idx = -1
    with httpx.Client(timeout=timeout) as client:
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
    """Both tracks' scores, or ``None`` (logged) so the snapshot's last-known-good takes over."""
    try:
        return {
            track: parse_arena_rows(fetch_arena_category(cat, base_url=base_url), category=cat)
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
