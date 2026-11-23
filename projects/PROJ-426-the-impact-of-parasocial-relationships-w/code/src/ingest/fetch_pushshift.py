"""
Fetch AI companion interaction logs from the Pushshift API.

This script retrieves Reddit comments from the subreddits
r/Replika, r/characterAI, and r/AICompanions for the time window
defined by the earliest and latest timestamps present in the
loneliness dataset. The window is **strictly preceding** each
survey timestamp, i.e. it spans from the earliest survey date to the
latest survey date (both inclusive). The script respects the
project‑wide retry policy (exponential back‑off, max 5 retries) and
the rate‑limit of ≤ 100 requests per minute.

Output:
    data/raw/pushshift_logs.parquet
    data/raw/pushshift_request_params.json   # log of request parameters for validation
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import requests

# Project utilities
from src.utils.logging import (
    get_logger,
    log_stage_start,
    log_stage_end,
    log_error_context,
)
from src.utils.retry_policy import retry_with_backoff, RetryConfig
from src.utils.rate_limit_handler import (
    RateLimitError,
    is_rate_limited,
    handle_429_response,
)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
PUSHSHIFT_API_URL = "https://api.pushshift.io/reddit/search/comment/"
TARGET_SUBREDDITS = ["Replika", "characterAI", "AICompanions"]
# Pushshift allows at most 500 items per request; the task explicitly
# requires `size=500`.
REQUEST_SIZE = 500

# Retry policy required by the task (max 5 retries, 30 s timeout)
RETRY_CONFIG = RetryConfig(
    max_retries=5,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
    exceptions=(requests.exceptions.RequestException,),
)

# Rate‑limit handling – ≤ 100 requests/min ⇒ at least 0.6 s between calls
MIN_SECONDS_BETWEEN_REQUESTS = 0.6

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_loneliness_window(loneliness_path: Path) -> Dict[str, datetime]:
    """
    Load the earliest and latest timestamps from the loneliness dataset.

    The dataset is expected to contain a column named ``timestamp`` that can
    be parsed by ``pandas.to_datetime``.  The function returns a dict with
    ``start_date`` and ``end_date`` as ``datetime`` objects (UTC).

    Raises:
        FileNotFoundError: If the parquet file does not exist.
        ValueError: If the ``timestamp`` column is missing.
    """
    if not loneliness_path.exists():
        raise FileNotFoundError(f"Loneliness dataset not found at {loneliness_path}")

    df = pd.read_parquet(loneliness_path, columns=["timestamp"])
    if "timestamp" not in df.columns:
        raise ValueError("Loneliness dataset missing required column 'timestamp'")

    # Ensure timestamps are timezone‑aware UTC
    timestamps = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    if timestamps.isna().any():
        raise ValueError("Loneliness dataset contains unparsable timestamps")

    start_date = timestamps.min().to_pydatetime()
    end_date = timestamps.max().to_pydatetime()

    logger.info(
        f"Derived survey window from loneliness data: "
        f"{start_date.isoformat()} → {end_date.isoformat()}"
    )
    return {"start_date": start_date, "end_date": end_date}


@retry_with_backoff(retry_config=RETRY_CONFIG)
def _make_pushshift_request(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform a single GET request to the Pushshift API with retry logic.

    The decorator handles exponential back‑off for network‑related
    exceptions.  Rate‑limit (HTTP 429) responses are translated into a
    ``RateLimitError`` so that the outer loop can pause appropriately.
    """
    response = requests.get(PUSHSHIFT_API_URL, params=params, timeout=30)

    # Detect explicit rate‑limit status code
    if is_rate_limited(response):
        raise RateLimitError(
            f"Rate limited: {response.status_code}",
            retry_after=handle_429_response(
                response.status_code,
                response.headers,
                RETRY_CONFIG,
                attempt=0,  # the decorator will handle further attempts
            ),
        )

    response.raise_for_status()
    return response.json()


def _fetch_subreddit_logs(
    subreddit: str,
    start_ts: int,
    end_ts: int,
) -> List[Dict[str, Any]]:
    """
    Retrieve all comments from a single subreddit within the given time
    window using pagination.

    The API returns results sorted by ``created_utc`` ascending.  We
    paginate by repeatedly advancing the ``after`` parameter to the
    highest timestamp seen so far plus one second.

    Returns:
        List of comment objects (raw JSON dicts) enriched with a few
        metadata fields.
    """
    logs: List[Dict[str, Any]] = []
    after = start_ts

    while after < end_ts:
        params = {
            "subreddit": subreddit,
            "size": REQUEST_SIZE,
            "after": after,
            "before": end_ts,
            "sort": "asc",  # ascending to make pagination straightforward
            "sort_type": "created_utc",
        }

        logger.debug(
            f"Requesting {subreddit}: after={after}, before={end_ts}, size={REQUEST_SIZE}"
        )

        try:
            result = _make_pushshift_request(params)
        except RateLimitError as e:
            # Respect the Retry‑After value if supplied; otherwise fall back
            # to the exponential back‑off delay calculated by the retry
            # decorator.
            wait_seconds = e.retry_after or 5
            logger.warning(
                f"Rate limit encountered for subreddit {subreddit}. "
                f"Sleeping for {wait_seconds}s before retry."
            )
            time.sleep(wait_seconds)
            continue
        except Exception as exc:
            logger.error(
                f"Failed to fetch logs for subreddit {subreddit}: {exc}"
            )
            # Abort fetching this subreddit; the outer caller will decide
            # whether to continue with other subreddits.
            break

        # Record the parameters used for this request for later validation
        _record_request_params(subreddit, params)

        data = result.get("data", [])
        if not data:
            logger.debug(
                f"No more data returned for subreddit {subreddit} (after={after})."
            )
            break

        for comment in data:
            # Enrich with additional fields useful downstream
            comment["source_subreddit"] = subreddit
            comment["fetched_at"] = datetime.utcnow().isoformat()
            logs.append(comment)

        # Update the cursor – the newest timestamp in this batch
        latest_ts = max(item["created_utc"] for item in data)
        after = int(latest_ts) + 1  # move past the last seen record

        logger.debug(
            f"Fetched {len(data)} comments from {subreddit}; "
            f"advancing cursor to {after}"
        )

        # Respect the global rate‑limit
        time.sleep(MIN_SECONDS_BETWEEN_REQUESTS)

    return logs

# ----------------------------------------------------------------------
# Request‑parameter logging
# ----------------------------------------------------------------------
_request_log: List[Dict[str, Any]] = []  # module‑level accumulator


def _record_request_params(subreddit: str, params: Dict[str, Any]) -> None:
    """
    Store a shallow copy of the request parameters for later validation.
    Only the keys relevant to the task are retained.
    """
    _request_log.append(
        {
            "subreddit": subreddit,
            "size": params.get("size"),
            "before": params.get("before"),
            "after": params.get("after"),
        }
    )


def _write_request_log(output_dir: Path) -> None:
    """
    Write the accumulated request‑parameter log to JSON.
    The file is written alongside the Pushshift Parquet output.
    """
    output_path = output_dir / "pushshift_request_params.json"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(_request_log, f, indent=2)
        logger.info(f"Pushshift request parameter log written to {output_path}")
    except Exception as exc:
        logger.error(f"Failed to write request parameter log: {exc}")
        # Not fatal for the main data collection; continue silently.


def fetch_all_pushshift_logs(
    loneliness_path: Path,
    output_path: Path,
) -> None:
    """
    Orchestrates the full Pull‑Shift download.

    Args:
        loneliness_path: Path to ``data/raw/loneliness_dataset.parquet``.
        output_path: Desired location for the aggregated Parquet file
                     (``data/raw/pushshift_logs.parquet``).

    The function writes a Parquet file containing all retrieved comment
    objects.  If no comments are found, an empty Parquet file with the
    expected schema is still created.
    """
    log_stage_start(logger, "Pushshift Log Fetching")

    # ------------------------------------------------------------------
    # Determine the survey window
    # ------------------------------------------------------------------
    window = _load_loneliness_window(loneliness_path)
    start_ts = int(window["start_date"].timestamp())
    end_ts = int(window["end_date"].timestamp())

    logger.info(
        f"Fetching Pushshift comments for window "
        f"{window['start_date'].isoformat()} – {window['end_date'].isoformat()}"
    )

    # ------------------------------------------------------------------
    # Retrieve logs for each target subreddit
    # ------------------------------------------------------------------
    all_logs: List[Dict[str, Any]] = []
    for subreddit in TARGET_SUBREDDITS:
        subreddit_logs = _fetch_subreddit_logs(subreddit, start_ts, end_ts)
        all_logs.extend(subreddit_logs)
        logger.info(
            f"Subreddit r/{subreddit}: retrieved {len(subreddit_logs)} comments"
        )

    # ------------------------------------------------------------------
    # Persist results
    # ------------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if all_logs:
        df = pd.DataFrame(all_logs)

        # Convert the epoch‑seconds field to a proper datetime column
        if "created_utc" in df.columns:
            df["created_utc"] = pd.to_datetime(df["created_utc"], unit="s", utc=True)

        # Normalise column order (optional but helpful for downstream tests)
        desired_order = [
            "author",          # raw Reddit username (may be None for deleted)
            "body",
            "created_utc",
            "score",
            "subreddit",
            "source_subreddit",
            "id",
            "parent_id",
            "link_id",
            "fetched_at",
        ]
        existing = [col for col in desired_order if col in df.columns]
        df = df[existing + [c for c in df.columns if c not in existing]]

        df.to_parquet(output_path, index=False)
        logger.info(
            f"Saved {len(df)} Pushshift comment records to {output_path}"
        )
    else:
        # Create an empty DataFrame with the minimal expected schema
        empty_df = pd.DataFrame(
            columns=[
                "author",
                "body",
                "created_utc",
                "score",
                "subreddit",
                "source_subreddit",
                "id",
                "parent_id",
                "link_id",
                "fetched_at",
            ]
        )
        empty_df.to_parquet(output_path, index=False)
        logger.warning(
            f"No comments were retrieved; created empty file at {output_path}"
        )

    # Write the request‑parameter log for validation (T016)
    _write_request_log(output_path.parent)

    log_stage_end(logger, "Pushshift Log Fetching", success=True)


def main() -> None:
    """
    Entry‑point used by the test suite and by developers.

    The script assumes it is executed from the repository root (the same
    directory that contains the ``code`` folder).  All paths are built
    relative to that root using ``Path(__file__)`` navigation.
    """
    # Configure a simple console logger if the application hasn't set one
    logging.basicConfig(level=logging.INFO)

    project_root = Path(__file__).resolve().parents[2]  # code/src/ingest/… → project root
    loneliness_path = project_root / "data" / "raw" / "loneliness_dataset.parquet"
    output_path = project_root / "data" / "raw" / "pushshift_logs.parquet"

    try:
        fetch_all_pushshift_logs(loneliness_path, output_path)
        logger.info("Pushshift log collection completed successfully.")
    except Exception as exc:
        log_error_context(logger, "Pushshift log collection failed", error=exc)
        raise


if __name__ == "__main__":
    main()
