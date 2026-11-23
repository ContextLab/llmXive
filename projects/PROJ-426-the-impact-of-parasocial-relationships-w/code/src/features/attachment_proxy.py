"""
Attachment Proxy Feature Extraction

This module implements the attachment‑proxy feature extraction required for
task **T009**.  It loads the ECAR lexicon, the baseline‑window configuration,
and the matched‑user dataset, then computes normalized anxiety and avoidance
scores for each user based on their baseline posts.

The output is written to ``data/processed/attachment_scores.parquet`` and
contains the following columns:

- ``user_id``                – 64‑character SHA‑256 hash (from matching step)
- ``attachment_anxiety_score``   – float in the range [0, 1]
- ``attachment_avoidance_score`` – float in the range [0, 1]

Users that lack baseline text or for which the lexicon scan cannot be
performed are excluded (FR‑004b).

The module provides a ``compute_attachment_scores`` function that is used
by the ``main`` entry point and can also be imported by the unit test
``tests/unit/test_attachment_proxy.py``.
"""

import logging
from pathlib import Path
from typing import Tuple

import pandas as pd
import yaml
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def _load_lexicon(lexicon_path: Path) -> pd.DataFrame:
    """
    Load the ECAR lexicon CSV and validate its basic schema.

    Expected columns:
        - ``keyword`` (string)
        - ``anxiety_weight`` (numeric)
        - ``avoidance_weight`` (numeric)

    Parameters
    ----------
    lexicon_path: Path
        Path to ``data/lexicons/ecar_lexicon.csv``.

    Returns
    -------
    pd.DataFrame
        The lexicon dataframe.
    """
    if not lexicon_path.exists():
        raise FileNotFoundError(f"ECAR lexicon not found at {lexicon_path}")

    df = pd.read_csv(lexicon_path)

    required = {"keyword", "anxiety_weight", "avoidance_weight"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Lexicon missing required columns: {missing}")

    # Ensure numeric columns are floats
    df["anxiety_weight"] = pd.to_numeric(df["anxiety_weight"], errors="coerce").fillna(0.0)
    df["avoidance_weight"] = pd.to_numeric(df["avoidance_weight"], errors="coerce").fillna(0.0)

    return df


def _load_config(config_path: Path) -> int:
    """
    Load the baseline‑window configuration YAML.

    The file must contain a key ``baseline_days_preceding`` that specifies
    how many days prior to the first survey timestamp constitute the
    baseline window.

    Parameters
    ----------
    config_path: Path
        Path to ``config/baseline_window_config.yaml``.

    Returns
    -------
    int
        Number of days preceding the first survey to treat as baseline.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Baseline window config not found at {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if not isinstance(cfg, dict) or "baseline_days_preceding" not in cfg:
        raise ValueError(
            "Config must be a mapping containing 'baseline_days_preceding'"
        )

    days = int(cfg["baseline_days_preceding"])
    if days <= 0:
        raise ValueError("'baseline_days_preceding' must be a positive integer")
    return days


def _tokenize(text: str) -> Tuple[list, int]:
    """
    Very simple whitespace tokenizer.

    Returns a list of tokens and the token count.
    """
    tokens = text.split()
    return tokens, len(tokens)


def _compute_scores_for_text(
    text: str, lexicon_df: pd.DataFrame
) -> Tuple[float, float]:
    """
    Compute raw anxiety and avoidance scores for a single piece of text.

    The algorithm counts occurrences of each lexicon keyword (case‑insensitive)
    and sums the associated weights.  The sums are then divided by the number
    of tokens in the text to obtain normalized scores in the range [0, 1].

    Parameters
    ----------
    text: str
        Baseline post text.
    lexicon_df: pd.DataFrame
        ECAR lexicon with columns ``keyword``, ``anxiety_weight``,
        ``avoidance_weight``.

    Returns
    -------
    Tuple[float, float]
        (anxiety_score, avoidance_score)
    """
    tokens, token_count = _tokenize(text)
    if token_count == 0:
        # No tokens – caller should treat this as a failure case.
        raise ValueError("Baseline text contains no tokens")

    # Build a lookup for fast weight aggregation
    # Lower‑case keywords for case‑insensitive matching
    lexicon_lookup = {
        kw.lower(): (aw, av) for kw, aw, av in zip(
            lexicon_df["keyword"],
            lexicon_df["anxiety_weight"],
            lexicon_df["avoidance_weight"],
        )
    }

    anxiety_sum = 0.0
    avoidance_sum = 0.0

    for token in tokens:
        key = token.lower()
        if key in lexicon_lookup:
            aw, av = lexicon_lookup[key]
            anxiety_sum += aw
            avoidance_sum += av

    # Normalise by total token count
    anxiety_score = anxiety_sum / token_count
    avoidance_score = avoidance_sum / token_count

    # Clamp to [0, 1] to guard against pathological weight totals
    anxiety_score = max(0.0, min(1.0, anxiety_score))
    avoidance_score = max(0.0, min(1.0, avoidance_score))

    return anxiety_score, avoidance_score


# ----------------------------------------------------------------------
# Core computation
# ----------------------------------------------------------------------


def compute_attachment_scores(
    matched_path: Path,
    lexicon_path: Path,
    config_path: Path,
    output_path: Path,
    logger: logging.Logger = None,
) -> pd.DataFrame:
    """
    Compute attachment‑anxiety and attachment‑avoidance scores for each
    matched user and write the results to ``output_path`` as Parquet.

    Parameters
    ----------
    matched_path: Path
        Path to ``data/processed/matched_users.parquet``.
    lexicon_path: Path
        Path to ``data/lexicons/ecar_lexicon.csv``.
    config_path: Path
        Path to ``config/baseline_window_config.yaml``.
    output_path: Path
        Destination for the resulting Parquet file.
    logger: logging.Logger, optional
        Logger instance; if omitted a module‑level logger is created.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ``user_id``, ``attachment_anxiety_score``,
        ``attachment_avoidance_score``.
    """
    if logger is None:
        logger = get_logger(__name__)

    logger.info("Loading ECAR lexicon")
    lexicon_df = _load_lexicon(lexicon_path)

    logger.info("Loading baseline window configuration")
    baseline_days = _load_config(config_path)

    logger.info(f"Baseline window: {baseline_days} days preceding first survey")

    logger.info(f"Loading matched users from {matched_path}")
    matched_df = pd.read_parquet(matched_path)

    # Expected columns in the matched dataset:
    #   - user_id (hashed identifier)
    #   - baseline_text (raw text of the baseline post)
    #   - timestamp (survey timestamp, used to locate the baseline window)
    required_cols = {"user_id", "baseline_text", "timestamp"}
    missing = required_cols - set(matched_df.columns)
    if missing:
        raise ValueError(
            f"Matched dataset is missing required columns: {missing}"
        )

    # Ensure timestamps are proper pandas datetime objects (UTC)
    matched_df["timestamp"] = pd.to_datetime(
        matched_df["timestamp"], utc=True, errors="coerce"
    )
    if matched_df["timestamp"].isna().any():
        raise ValueError("Unparsable timestamps found in matched data")

    # Determine each user's first survey timestamp
    first_ts = (
        matched_df.groupby("user_id")["timestamp"]
        .min()
        .reset_index(name="first_survey_ts")
    )
    # Merge back to have a per‑row view of the baseline window
    merged = matched_df.merge(first_ts, on="user_id", how="left")

    # Compute the start of the baseline window
    merged["baseline_start"] = merged["first_survey_ts"] - pd.Timedelta(
        days=baseline_days
    )
    merged["baseline_end"] = merged["first_survey_ts"]

    # Keep only rows whose timestamp falls inside the baseline window
    in_window = (
        (merged["timestamp"] >= merged["baseline_start"])
        & (merged["timestamp"] < merged["baseline_end"])
    )
    baseline_df = merged[in_window].copy()

    # If a user has multiple rows in the baseline window we concatenate
    # the texts so that the lexicon scan sees the full baseline corpus.
    baseline_df["baseline_text"] = baseline_df["baseline_text"].fillna("")
    agg = (
        baseline_df.groupby("user_id")["baseline_text"]
        .apply(lambda texts: " ".join(texts))
        .reset_index()
    )

    # Prepare list to collect results
    results = []

    excluded_users = 0

    for _, row in agg.iterrows():
        user_id = row["user_id"]
        text = row["baseline_text"]

        if not isinstance(text, str) or not text.strip():
            # No usable baseline text – exclude user (FR‑004b)
            excluded_users += 1
            logger.debug(
                f"User {user_id} excluded due to missing or empty baseline text"
            )
            continue

        try:
            anxiety_score, avoidance_score = _compute_scores_for_text(
                text, lexicon_df
            )
        except Exception as exc:
            # Any error while scanning the lexicon leads to exclusion
            excluded_users += 1
            logger.warning(
                f"Lexicon scan failed for user {user_id}: {exc}. User excluded."
            )
            continue

        results.append(
            {
                "user_id": user_id,
                "attachment_anxiety_score": anxiety_score,
                "attachment_avoidance_score": avoidance_score,
            }
        )

    logger.info(
        f"Attachment scores computed for {len(results)} users; "
        f"{excluded_users} users excluded."
    )

    result_df = pd.DataFrame(results)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result_df.to_parquet(output_path, index=False)
    logger.info(f"Attachment scores written to {output_path}")

    # Store exclusion count as an attribute for downstream validation (optional)
    result_df.attrs["excluded_user_count"] = excluded_users

    return result_df


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def main() -> None:
    """
    Command‑line entry point used by developers and the test suite.

    The function resolves canonical project paths via ``llmxive_toolkit.paths``,
    invokes :func:`compute_attachment_scores`, and logs progress.
    """
    logger = get_logger(__name__)

    # Resolve canonical locations
    matched_path = paths.processed("matched_users.parquet")
    lexicon_path = paths.lexicons("ecar_lexicon.csv")
    config_path = paths.config("baseline_window_config.yaml")
    output_path = paths.processed("attachment_scores.parquet")

    compute_attachment_scores(
        matched_path=matched_path,
        lexicon_path=lexicon_path,
        config_path=config_path,
        output_path=output_path,
        logger=logger,
    )


if __name__ == "__main__":
    main()