"""
Hedge Extractor Module
======================

This module provides functionality to compute the **hedge density** of textual
data. Hedge density is defined as the proportion of words in a document that
belong to a predefined list of hedging expressions (e.g., "maybe", "perhaps",
"I think").

The implementation relies on **NLTK** for tokenisation and uses a static hedge
lexicon that can be extended if required.

Public API
----------
- ``calculate_hedge_density(text: str, hedge_lexicon: Set[str] | None = None) -> float``
  Compute the hedge density for a single piece of text.
- ``extract_hedge_features(df: pd.DataFrame, text_column: str = "text") -> pd.DataFrame``
  Add a ``hedge_density`` column to a DataFrame containing a text column.
- ``main()`` – command‑line entry point that reads an input CSV, calculates the
  feature, and writes the result to an output CSV.

The module is deliberately lightweight and has no external side‑effects other
than writing the output file when executed as a script.
"""

import argparse
import logging
from pathlib import Path
from typing import Set, Optional

import pandas as pd
import nltk
from nltk.tokenize import word_tokenize

# --------------------------------------------------------------------------- #
# Hedge lexicon
# --------------------------------------------------------------------------- #
DEFAULT_HEDGE_LEXICON: Set[str] = {
    "maybe",
    "perhaps",
    "might",
    "could",
    "possibly",
    "might",
    "may",
    "i think",
    "i believe",
    "it seems",
    "it appears",
    "likely",
    "unlikely",
    "probably",
    "presumably",
    "seems",
    "appears",
    "suggest",
    "suggests",
    "suggested",
    "suggesting",
}

# Ensure the NLTK tokenizer data is available.
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:  # pragma: no cover
    nltk.download("punkt")

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def _prepare_lexicon(lexicon: Optional[Set[str]]) -> Set[str]:
    """
    Normalise the supplied lexicon (lower‑case) or fall back to the default.
    """
    if lexicon is None:
        return DEFAULT_HEDGE_LEXICON
    # Normalise to lower case for case‑insensitive matching.
    return {term.lower() for term in lexicon}


def calculate_hedge_density(
    text: str, hedge_lexicon: Optional[Set[str]] = None
) -> float:
    """
    Calculate the proportion of tokens in *text* that are recognised as hedges.

    Parameters
    ----------
    text: str
        The raw text to analyse.
    hedge_lexicon: set[str] | None
        Optional custom hedge set. If ``None`` the built‑in default set is used.

    Returns
    -------
    float
        Hedge density in the range ``[0.0, 1.0]``. Returns ``0.0`` for empty
        strings or when no tokens are present.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    lexicon = _prepare_lexicon(hedge_lexicon)

    # Tokenise and lower‑case for matching.
    tokens = [tok.lower() for tok in word_tokenize(text)]
    total_tokens = len(tokens)
    if total_tokens == 0:
        return 0.0

    # Count tokens that appear in the lexicon.
    hedge_count = sum(1 for token in tokens if token in lexicon)
    density = hedge_count / total_tokens
    return density


def extract_hedge_features(
    df: pd.DataFrame, text_column: str = "text"
) -> pd.DataFrame:
    """
    Append a ``hedge_density`` column to *df* based on the contents of *text_column*.

    Parameters
    ----------
    df: pd.DataFrame
        Input DataFrame containing at least the column named ``text_column``.
    text_column: str
        Name of the column that holds raw textual data.

    Returns
    -------
    pd.DataFrame
        A new DataFrame (a shallow copy) with an additional ``hedge_density`` column.
    """
    if text_column not in df.columns:
        raise ValueError(f"'{text_column}' column not found in the DataFrame")

    # Apply the density calculation row‑wise.
    df_copy = df.copy()
    df_copy["hedge_density"] = df_copy[text_column].apply(calculate_hedge_density)
    return df_copy


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #
def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calculate hedge density for a CSV of conversations."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Path to input CSV containing at least a 'text' column.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="Path where the output CSV with 'hedge_density' will be written.",
    )
    parser.add_argument(
        "--text-column",
        type=str,
        default="text",
        help="Name of the column containing raw text (default: 'text').",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity.",
    )
    return parser


def main() -> None:  # pragma: no cover
    """
    Command‑line interface for the hedge extractor.

    Example
    -------
    ``python -m src.extraction.hedge_extractor \\
         --input data/raw/conversations.csv \\
         --output data/processed/hedge_features.csv``
    """
    args = _build_arg_parser().parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level))

    input_path: Path = args.input
    output_path: Path = args.output

    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logging.info("Loading input data from %s", input_path)
    df = pd.read_csv(input_path)

    logging.info("Calculating hedge density using column '%s'", args.text_column)
    df_with_features = extract_hedge_features(df, text_column=args.text_column)

    logging.info("Writing output to %s", output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_with_features.to_csv(output_path, index=False)
    logging.info("Hedge extraction completed successfully.")


if __name__ == "__main__":  # pragma: no cover
    main()