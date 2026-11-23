"""
Sentiment Analysis Module for Emotional Contagion Pipeline.

This module applies VADER (Valence Aware Dictionary and sEntiment Reasoner)
from NLTK to compute compound sentiment scores for posts in the valid dataset.
Scores are bounded to [-1.0, 1.0].
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    import nltk
except ImportError:
    raise ImportError(
        "NLTK is required for sentiment analysis. "
        "Install with: pip install nltk"
    )

# Ensure VADER lexicon is downloaded
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

logger = logging.getLogger(__name__)


def load_valid_dataset(input_path: Path) -> pd.DataFrame:
    """
    Load the valid threads dataset produced by T019/T019a.

    Args:
        input_path: Path to the CSV file containing valid threads.

    Returns:
        DataFrame with thread data.
    """
    if not input_path.exists():
        raise FileNotFoundError(
            f"Valid dataset not found at {input_path}. "
            "Ensure T019 and T019a have been executed successfully."
        )

    df = pd.read_csv(input_path)

    # Verify required columns exist
    required_cols = ['thread_id', 'post_id', 'text', 'timestamp', 'author_id', 'sentiment_score']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in valid dataset: {missing_cols}. "
            "The dataset must contain thread_id, post_id, text, and existing sentiment_score."
        )

    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df


def apply_vader_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply VADER sentiment analysis to the 'text' column.

    Computes the compound score and bounds it to [-1.0, 1.0].
    Overwrites the 'sentiment_score' column with the new VADER score.

    Args:
        df: DataFrame containing the 'text' column.

    Returns:
        DataFrame with updated 'sentiment_score' column.
    """
    analyzer = SentimentIntensityAnalyzer()

    def get_compound_score(text: str) -> float:
        if not isinstance(text, str) or not text.strip():
            return 0.0
        try:
            scores = analyzer.polarity_scores(text)
            compound = scores.get('compound', 0.0)
            # Ensure bounds [-1.0, 1.0]
            return max(-1.0, min(1.0, compound))
        except Exception as e:
            logger.warning(f"Failed to analyze sentiment for text snippet: {e}")
            return 0.0

    logger.info("Applying VADER sentiment analysis...")
    df['sentiment_score'] = df['text'].apply(get_compound_score)

    # Validate bounds
    if df['sentiment_score'].min() < -1.0 or df['sentiment_score'].max() > 1.0:
        raise RuntimeError("Sentiment scores out of bounds [-1.0, 1.0].")

    logger.info(f"Sentiment analysis complete. Range: [{df['sentiment_score'].min():.4f}, {df['sentiment_score'].max():.4f}]")
    return df


def save_processed_sentiment(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the sentiment-analyzed dataset to CSV.

    Args:
        df: DataFrame with sentiment scores.
        output_path: Path to save the output CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved sentiment-analyzed dataset to {output_path}")


def main() -> None:
    """
    Main entry point for the sentiment analysis pipeline (T013).

    Reads from data/processed/valid_threads.csv and writes to
    data/processed/valid_threads_sentiment.csv.
    """
    # Paths relative to project root
    project_root = Path(__file__).resolve().parents[2]
    input_path = project_root / "data" / "processed" / "valid_threads.csv"
    output_path = project_root / "data" / "processed" / "valid_threads_sentiment.csv"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Load valid dataset (produced by T019/T019a)
        df = load_valid_dataset(input_path)

        # Apply VADER
        df_analyzed = apply_vader_sentiment(df)

        # Save results
        save_processed_sentiment(df_analyzed, output_path)

        logger.info("T013 Sentiment Analysis completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Data not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()
