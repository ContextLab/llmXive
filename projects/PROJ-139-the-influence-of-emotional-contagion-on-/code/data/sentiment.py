"""
Sentiment analysis module.
Implements VADER sentiment analysis and validation against human-annotated corpus.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords

from config.settings import get_config
from utils.logging_config import get_logger

# Ensure NLTK resources are downloaded
try:
    from nltk.data import find
    find('sentiment/vader_lexicon.zip')
    find('corpora/stopwords')
except LookupError:
    import nltk
    nltk.download('vader_lexicon')
    nltk.download('stopwords')

logger = get_logger(__name__)


def load_annotated_corpus(corpus_path: Path) -> pd.DataFrame:
    """
    Load the human-annotated corpus from T007a.
    Expected format: JSON or CSV with 'text' and 'label' columns.
    """
    if not corpus_path.exists():
        raise FileNotFoundError(f"Annotated corpus not found at {corpus_path}")

    if corpus_path.suffix == '.json':
        with open(corpus_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = pd.DataFrame([data])
    elif corpus_path.suffix == '.csv':
        df = pd.read_csv(corpus_path)
    else:
        raise ValueError(f"Unsupported file format: {corpus_path.suffix}")

    required_cols = {'text', 'label'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Corpus must contain columns: {required_cols}")

    logger.info(f"Loaded {len(df)} annotated comments from {corpus_path}")
    return df


def apply_vader_sentiment(df: pd.DataFrame, text_col: str = 'text') -> pd.DataFrame:
    """
    Apply VADER sentiment analysis to the text column.
    Adds 'vader_compound', 'vader_pos', 'vader_neu', 'vader_neg' columns.
    """
    sia = SentimentIntensityAnalyzer()

    def get_scores(text):
        if not isinstance(text, str) or not text.strip():
            return {'compound': 0.0, 'pos': 0.0, 'neu': 0.0, 'neg': 0.0}
        return sia.polarity_scores(text)

    scores = df[text_col].apply(get_scores)
    score_df = pd.DataFrame(scores.tolist(), index=df.index)
    score_df.columns = [f'vader_{col}' for col in score_df.columns]

    result = pd.concat([df, score_df], axis=1)
    logger.info(f"Applied VADER sentiment to {len(result)} comments")
    return result


def validate_vader_against_corpus(
    corpus_df: pd.DataFrame,
    report_path: Path,
    label_col: str = 'label'
) -> Dict[str, Any]:
    """
    Validate VADER scores against human annotations.
    Reads the existing T007b report to verify Kappa statistics exist.
    Updates the report with VADER validation results.
    """
    if not report_path.exists():
        raise FileNotFoundError(
            f"Validation report from T007b not found at {report_path}. "
            "T007b must complete before T014."
        )

    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)

    # Verify Kappa statistics exist
    if 'kappa' not in report:
        raise ValueError(
            f"Kappa statistics missing in {report_path}. "
            "T007b did not generate valid inter-rater reliability metrics."
        )

    logger.info(f"Found Kappa statistic: {report['kappa']}")

    # Apply VADER to the corpus
    annotated_df = apply_vader_sentiment(corpus_df, text_col='text')

    # Compute agreement between VADER and human labels
    def vader_to_label(compound: float) -> str:
        if compound >= 0.05:
            return 'positive'
        elif compound <= -0.05:
            return 'negative'
        else:
            return 'neutral'

    annotated_df['vader_label'] = annotated_df['vader_compound'].apply(vader_to_label)

    # Calculate agreement metrics
    agreement_mask = annotated_df[label_col] == annotated_df['vader_label']
    agreement_rate = agreement_mask.mean()

    # Compute Cohen's Kappa between VADER and human labels
    from sklearn.metrics import cohen_kappa_score

    # Filter out rows with missing labels
    valid_mask = annotated_df[label_col].notna() & annotated_df['vader_label'].notna()
    if valid_mask.sum() < 2:
        logger.warning("Insufficient valid data for Kappa calculation")
        kappa_score = None
    else:
        kappa_score = cohen_kappa_score(
            annotated_df.loc[valid_mask, label_col],
            annotated_df.loc[valid_mask, 'vader_label']
        )

    # Update report with VADER validation results
    report['vader_validation'] = {
        'status': 'validated',
        'kappa_vs_human': kappa_score,
        'agreement_rate': float(agreement_rate),
        'sample_size': int(len(annotated_df)),
        'valid_sample_size': int(valid_mask.sum()),
        'vader_thresholds': {
            'positive': 0.05,
            'negative': -0.05
        }
    }

    report['validation_status'] = 'complete'
    report['validated_at'] = pd.Timestamp.now().isoformat()

    # Ensure parent directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Write updated report
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"VADER validation complete. Updated report saved to {report_path}")
    logger.info(f"VADER vs Human Kappa: {kappa_score}, Agreement Rate: {agreement_rate:.2%}")

    return report


def main():
    """
    Main entry point for T014: VADER validation against human-annotated corpus.
    """
    config = get_config()

    # Paths
    corpus_path = config.data_paths.raw / 'annotations.json'
    report_path = config.data_paths.processed / 'vader_validation_report.json'

    logger.info(f"Starting VADER validation for T014")
    logger.info(f"Corpus path: {corpus_path}")
    logger.info(f"Report path: {report_path}")

    try:
        # Load annotated corpus
        corpus_df = load_annotated_corpus(corpus_path)

        # Validate VADER against corpus
        report = validate_vader_against_corpus(
            corpus_df,
            report_path,
            label_col='label'
        )

        # Output summary
        print(f"VADER Validation Complete")
        print(f"  Kappa (VADER vs Human): {report['vader_validation']['kappa_vs_human']}")
        print(f"  Agreement Rate: {report['vader_validation']['agreement_rate']:.2%}")
        print(f"  Sample Size: {report['vader_validation']['sample_size']}")
        print(f"  Report saved to: {report_path}")

    except FileNotFoundError as e:
        logger.error(f"Required file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during VADER validation")
        raise


if __name__ == '__main__':
    main()
