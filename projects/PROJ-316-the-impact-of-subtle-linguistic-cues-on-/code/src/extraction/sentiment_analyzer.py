"""
Sentiment Analyzer Module for Linguistic Feature Extraction.

Implements valence score calculation using vaderSentiment (v3.3.2).
Calculates a composite valence score ranging from -1.0 (most negative) to 1.0 (most positive).
"""
import argparse
import logging
from pathlib import Path
from typing import Optional, List

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize VADER analyzer once at module load for efficiency
_analyzer = SentimentIntensityAnalyzer()


def calculate_valence_score(text: str) -> float:
    """
    Calculate the sentiment valence score for a given text.

    Uses VADER's compound score which is a metric that calculates the sum of all
    the lexicon ratings normalized between -1 (most extreme negative) and 1 (most extreme positive).

    Args:
        text: The input string to analyze.

    Returns:
        float: The compound sentiment score between -1.0 and 1.0.
               Returns 0.0 if the text is empty or contains no valid sentiment tokens.
    """
    if not isinstance(text, str) or not text.strip():
        return 0.0

    try:
        scores = _analyzer.polarity_scores(text)
        return scores.get('compound', 0.0)
    except Exception as e:
        logger.warning(f"Failed to analyze sentiment for text: {text[:50]}... Error: {e}")
        return 0.0


def extract_sentiment_features(df: pd.DataFrame, text_column: str = 'text', output_column: str = 'valence_score') -> pd.DataFrame:
    """
    Extract sentiment features (valence score) from a DataFrame containing conversation text.

    This function applies the VADER sentiment analyzer to each row in the specified text column
    and adds a new column with the resulting valence scores.

    Args:
        df: Input DataFrame containing conversation data.
        text_column: Name of the column containing the text to analyze.
        output_column: Name of the column to create for the valence scores.

    Returns:
        pd.DataFrame: A copy of the input DataFrame with the new valence_score column appended.
    """
    if text_column not in df.columns:
        raise ValueError(f"Column '{text_column}' not found in DataFrame. Available columns: {list(df.columns)}")

    logger.info(f"Calculating valence scores for {len(df)} rows in column '{text_column}'...")

    # Apply the calculation function to the text column
    df_with_sentiment = df.copy()
    df_with_sentiment[output_column] = df_with_sentiment[text_column].apply(calculate_valence_score)

    logger.info(f"Sentiment extraction complete. Range: [{df_with_sentiment[output_column].min():.3f}, {df_with_sentiment[output_column].max():.3f}]")

    return df_with_sentiment


def main():
    """
    CLI entry point for running the sentiment analyzer on a CSV file.

    Usage:
        python -m src.extraction.sentiment_analyzer --input data/raw/conversations.csv --output data/processed/sentiment_features.csv
    """
    parser = argparse.ArgumentParser(description="Extract VADER valence scores from conversation text.")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input CSV file containing conversation text."
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to the output CSV file to save results."
    )
    parser.add_argument(
        "--text-column",
        type=str,
        default="text",
        help="Name of the column containing the text to analyze (default: text)."
    )
    parser.add_argument(
        "--id-column",
        type=str,
        default="conversation_id",
        help="Name of the column containing the conversation ID (default: conversation_id)."
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1

    try:
        # Load data
        logger.info(f"Loading data from {input_path}...")
        df = pd.read_csv(input_path)

        # Validate required columns
        if args.id_column not in df.columns:
            logger.error(f"ID column '{args.id_column}' not found in input file.")
            return 1

        # Extract features
        df_result = extract_sentiment_features(
            df,
            text_column=args.text_column,
            output_column="valence_score"
        )

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save results
        logger.info(f"Saving results to {output_path}...")
        df_result.to_csv(output_path, index=False)

        logger.info("Sentiment analysis complete.")
        return 0

    except Exception as e:
        logger.error(f"An error occurred during processing: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
