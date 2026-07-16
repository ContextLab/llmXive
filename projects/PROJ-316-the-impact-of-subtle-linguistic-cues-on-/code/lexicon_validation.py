"""
Lexicon Validation Script
-------------------------

This script implements the pragmatic validation of the hedge lexicon
(FR-010) as required by task **T001d**. It loads the conversation turns
and human annotation ratings, samples a subset of turns, computes the
precision of the lexicon against the human annotations, and writes the
results to ``data/derived/lexicon_validation_results.yaml``.

The public API (functions imported by the test suite) includes:
  - ``load_conversations()``
  - ``load_ratings()``
  - ``tokenize_text(text: str) -> List[str]``
  - ``find_lexicon_matches(tokens: List[str]) -> Set[str]``
  - ``sample_turns(df: pd.DataFrame, n: int) -> pd.DataFrame``
  - ``validate_lexicon_precision(
        conversations: pd.DataFrame,
        ratings: pd.DataFrame,
        sample_size: int = 100
    ) -> Tuple[float, int, int]``
  - ``write_validation_results(precision: float, output_path: Path) -> None``
  - ``main()`` – entry‑point for CLI execution.

The script is deliberately self‑contained, uses only the declared
dependencies (``pandas``, ``pyyaml`` and the Python standard library),
and raises clear errors if required input files are missing.
"""

import argparse
import logging
import random
import re
from pathlib import Path
from typing import List, Set, Tuple

import pandas as pd
import yaml

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
_handler = logging.StreamHandler()
_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
LOGGER.addHandler(_handler)

# A small but representative hedge lexicon (15 words/phrases)
HEDGE_LEXICON: Set[str] = {
    "perhaps",
    "maybe",
    "possibly",
    "might",
    "could",
    "i think",
    "i believe",
    "it seems",
    "apparently",
    "likely",
    "probably",
    "presumably",
    "assume",
    "suggest",
    "estimate",
}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_conversations() -> pd.DataFrame:
    """
    Load the raw conversation turns from ``data/raw/conversations.jsonl``.

    Returns
    -------
    pd.DataFrame
        Columns: ``conversation_id``, ``turn_id``, ``text``.
    """
    conv_path = Path("data/raw/conversations.jsonl")
    if not conv_path.is_file():
        raise FileNotFoundError(f"Conversations file not found: {conv_path}")

    # Each line is a JSON object; we read them into a list of dicts.
    records = []
    with conv_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = pd.read_json(line, typ="series")
            except ValueError as exc:
                raise ValueError(f"Invalid JSON line in {conv_path}: {line}") from exc
            # Ensure required columns exist
            for col in ("conversation_id", "turn_id", "text"):
                if col not in record:
                    raise KeyError(
                        f"Missing required column '{col}' in conversation record: {record}"
                    )
            records.append(record)

    df = pd.DataFrame(records)
    LOGGER.info("Loaded %d conversation turns", len(df))
    return df

def load_ratings() -> pd.DataFrame:
    """
    Load the human authenticity/hedge ratings from
    ``data/processed/ratings.csv``.
    Expected columns include at least:
        - ``conversation_id``
        - ``turn_id``
        - ``hedge_present`` (binary 0/1 or boolean)

    Returns
    -------
    pd.DataFrame
    """
    ratings_path = Path("data/processed/ratings.csv")
    if not ratings_path.is_file():
        raise FileNotFoundError(f"Ratings file not found: {ratings_path}")

    df = pd.read_csv(ratings_path, dtype=str)

    # Normalise column names to lower case for robustness
    df.columns = [c.lower() for c in df.columns]

    required = {"conversation_id", "turn_id"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Ratings CSV missing required columns: {missing}")

    # Heuristic: look for a column indicating human hedge judgement.
    # Accept several possible names.
    hedge_col_candidates = [
        "hedge_present",
        "hedge",
        "human_hedge",
        "has_hedge",
    ]
    hedge_col = None
    for cand in hedge_col_candidates:
        if cand in df.columns:
            hedge_col = cand
            break

    if hedge_col is None:
        raise KeyError(
            f"Ratings CSV must contain a hedge annotation column. "
            f"Checked candidates: {hedge_col_candidates}"
        )

    # Convert to boolean (treat '1', 'true', 'yes' as True)
    df[hedge_col] = df[hedge_col].astype(str).str.lower().map(
        {"1": True, "true": True, "yes": True, "0": False, "false": False, "no": False}
    )
    df.rename(columns={hedge_col: "hedge_present"}, inplace=True)

    LOGGER.info("Loaded %d rating rows", len(df))
    return df

def tokenize_text(text: str) -> List[str]:
    """
    Very simple tokenizer: lower‑case and split on non‑word characters.
    Returns a list of tokens.
    """
    if not isinstance(text, str):
        raise TypeError("Input text must be a string")
    # Use regex to extract word tokens (including apostrophes)
    tokens = re.findall(r"\b\w[\w']*\b", text.lower())
    return tokens

def find_lexicon_matches(tokens: List[str]) -> Set[str]:
    """
    Return the subset of tokens that appear in the hedge lexicon.
    Multi‑word lexicon entries (e.g., \"i think\") are detected by
    joining neighbouring tokens.
    """
    token_set = set(tokens)
    matches: Set[str] = set()

    # Single‑word entries
    for word in HEDGE_LEXICON:
        if " " not in word:
            if word in token_set:
                matches.add(word)

    # Multi‑word entries: slide a window over the token list
    for phrase in (w for w in HEDGE_LEXICON if " " in w):
        phrase_tokens = phrase.split()
        n = len(phrase_tokens)
        for i in range(len(tokens) - n + 1):
            if tokens[i : i + n] == phrase_tokens:
                matches.add(phrase)
    return matches

def sample_turns(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """
    Randomly sample ``n`` rows from the conversation DataFrame.
    If ``n`` exceeds the number of available rows, all rows are returned.
    """
    if n <= 0:
        raise ValueError("Sample size must be a positive integer")
    total = len(df)
    if total == 0:
        raise ValueError("Cannot sample from an empty DataFrame")
    if n >= total:
        LOGGER.info(
            "Requested sample size %d >= total rows %d – returning all rows",
            n,
            total,
        )
        return df.copy()
    sampled = df.sample(n=n, random_state=42).reset_index(drop=True)
    LOGGER.info("Sampled %d turns out of %d total", n, total)
    return sampled

def validate_lexicon_precision(
    conversations: pd.DataFrame,
    ratings: pd.DataFrame,
    sample_size: int = 100,
) -> Tuple[float, int, int]:
    """
    Compute the precision of the hedge lexicon against human annotations.

    Precision = |Lexicon ∩ Human| / |Lexicon|

    Parameters
    ----------
    conversations : pd.DataFrame
        Must contain ``conversation_id``, ``turn_id`` and ``text``.
    ratings : pd.DataFrame
        Must contain ``conversation_id``, ``turn_id`` and ``hedge_present``.
    sample_size : int, optional
        Number of turns to sample for the validation (default 100).

    Returns
    -------
    precision : float
        Ratio as defined above (0.0 – 1.0). If the lexicon makes no
        predictions on the sampled data, precision is defined as 1.0.
    lexicon_matches : int
        Number of sampled turns where the lexicon found at least one hedge.
    true_positives : int
        Number of sampled turns where both lexicon and human annotation
        indicate a hedge.
    """
    # Merge conversations with ratings on conversation_id & turn_id
    merged = pd.merge(
        conversations,
        ratings,
        on=["conversation_id", "turn_id"],
        how="inner",
    )
    if merged.empty:
        raise ValueError(
            "No overlapping conversation/turn pairs between conversations and ratings."
        )

    sampled = sample_turns(merged, sample_size)

    lexicon_matches = 0
    true_positives = 0

    for _, row in sampled.iterrows():
        tokens = tokenize_text(row["text"])
        matches = find_lexicon_matches(tokens)
        if matches:
            lexicon_matches += 1
            if row["hedge_present"]:
                true_positives += 1

    if lexicon_matches == 0:
        precision = 1.0
    else:
        precision = true_positives / lexicon_matches

    LOGGER.info(
        "Lexicon precision on sample: %.3f (%d TP / %d matches)",
        precision,
        true_positives,
        lexicon_matches,
    )
    return precision, lexicon_matches, true_positives

def write_validation_results(precision: float, output_path: Path) -> None:
    """
    Write the validation outcome to a YAML file.

    The file contains:
        precision: <float>
        flag: true|false   # true if precision < 0.8
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    flag = precision < 0.8
    data = {"precision": round(precision, 4), "flag": flag}
    with output_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    LOGGER.info(
        "Wrote lexicon validation results to %s (flag=%s)",
        output_path,
        flag,
    )

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate hedge lexicon precision against human annotations."
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=100,
        help="Number of turns to sample for validation (default: 100)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/derived/lexicon_validation_results.yaml"),
        help="Path to write the validation YAML file",
    )
    args = parser.parse_args()

    # Load data
    conversations = load_conversations()
    ratings = load_ratings()

    # Compute precision
    precision, _, _ = validate_lexicon_precision(
        conversations, ratings, sample_size=args.sample_size
    )

    # Write results
    write_validation_results(precision, args.output)

if __name__ == "__main__":
    main()
