"""
Sentiment analysis module for calculating cohesion proxy scores.
Handles language detection, VADER analysis, and edge cases for empty text.
"""
import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import json
from pathlib import Path
import re

# Conditional imports for optional dependencies
try:
    from langdetect import detect, DetectorFactory
    from langdetect.lang_detect_exception import LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logging.warning("langdetect not installed. Language detection will be skipped.")

try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    import nltk
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("nltk not installed. Sentiment analysis will be skipped.")

from config import get_config, ensure_directories_exist

# Set seed for langdetect to ensure reproducibility
if LANGDETECT_AVAILABLE:
    DetectorFactory.seed = 0

logger = logging.getLogger(__name__)

@dataclass
class SentimentResult:
    """Container for sentiment analysis results."""
    comment_id: str
    project_id: str
    pair_id: str
    text: str
    language: str
    is_english: bool
    compound_score: Optional[float]
    positive: Optional[float]
    neutral: Optional[float]
    negative: Optional[float]

def initialize_nltk() -> bool:
    """Initialize NLTK resources required for VADER."""
    if not NLTK_AVAILABLE:
        return False
    try:
        nltk.download('vader_lexicon', quiet=True)
        return True
    except Exception as e:
        logger.error(f"Failed to initialize NLTK: {e}")
        return False

def detect_language(text: str) -> Tuple[str, float]:
    """
    Detect the language of a text string.
    Returns (language_code, confidence).
    """
    if not LANGDETECT_AVAILABLE:
        return "unknown", 0.0

    if not text or not isinstance(text, str) or len(text.strip()) == 0:
        return "unknown", 0.0

    try:
        # Clean text to avoid detection errors
        clean_text = re.sub(r'[^\w\s]', '', text).strip()
        if len(clean_text) < 20:
            # Too short for reliable detection, assume English or skip
            return "en", 0.95

        lang = detect(clean_text)
        return lang, 1.0
    except LangDetectException:
        return "unknown", 0.0
    except Exception as e:
        logger.warning(f"Language detection failed for text snippet: {str(e)}")
        return "unknown", 0.0

def filter_by_language(comments: List[Dict[str, Any]], min_confidence: float = 0.95) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter comments to keep only English ones with sufficient confidence.
    Returns (english_comments, excluded_comments).
    """
    english_comments = []
    excluded_comments = []

    for comment in comments:
        text = comment.get('body', '')
        lang, conf = detect_language(text)
        comment['detected_language'] = lang
        comment['lang_confidence'] = conf

        if lang == 'en' and conf >= min_confidence:
            english_comments.append(comment)
        else:
            excluded_comments.append(comment)

    return english_comments, excluded_comments

def analyze_sentiment(text: str) -> Dict[str, float]:
    """
    Analyze sentiment of a text using VADER.
    Returns dict with compound, pos, neu, neg scores.
    """
    if not NLTK_AVAILABLE:
        return {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0}

    if not text or not isinstance(text, str) or len(text.strip()) == 0:
        # Edge case: empty or whitespace-only text
        # Return neutral scores
        return {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0}

    try:
        analyzer = SentimentIntensityAnalyzer()
        scores = analyzer.polarity_scores(text)
        return scores
    except Exception as e:
        logger.warning(f"Sentiment analysis failed for text: {str(e)}")
        return {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0}

def process_comments_for_sentiment(
    comments: List[Dict[str, Any]],
    min_confidence: float = 0.95
) -> Tuple[List[SentimentResult], Dict[str, int]]:
    """
    Process a list of comments for sentiment analysis.
    Filters by language, analyzes sentiment, and returns structured results.

    Args:
        comments: List of comment dicts with keys: id, project_id, pair_id, body, etc.
        min_confidence: Minimum confidence threshold for language detection.

    Returns:
        Tuple of (list of SentimentResult objects, exclusion stats dict).
    """
    if not NLTK_AVAILABLE:
        logger.error("NLTK not available. Cannot perform sentiment analysis.")
        return [], {}

    if not initialize_nltk():
        logger.error("Failed to initialize NLTK. Cannot perform sentiment analysis.")
        return [], {}

    # Filter by language
    english_comments, excluded_comments = filter_by_language(comments, min_confidence)

    # Track exclusion stats per project
    exclusion_stats = {}
    for comment in comments:
        proj = comment.get('project_id', 'unknown')
        if proj not in exclusion_stats:
            exclusion_stats[proj] = {'total': 0, 'excluded': 0}
        exclusion_stats[proj]['total'] += 1

    for comment in excluded_comments:
        proj = comment.get('project_id', 'unknown')
        if proj in exclusion_stats:
            exclusion_stats[proj]['excluded'] += 1

    results = []
    for comment in english_comments:
        text = comment.get('body', '')
        scores = analyze_sentiment(text)

        result = SentimentResult(
            comment_id=comment.get('id', ''),
            project_id=comment.get('project_id', ''),
            pair_id=comment.get('pair_id', ''),
            text=text,
            language=comment.get('detected_language', 'en'),
            is_english=True,
            compound_score=scores['compound'],
            positive=scores['pos'],
            neutral=scores['neu'],
            negative=scores['neg']
        )
        results.append(result)

    logger.info(f"Processed {len(results)} English comments, excluded {len(excluded_comments)} non-English.")
    return results, exclusion_stats

def calculate_project_cohesion_proxy(
    sentiment_results: List[SentimentResult],
    project_id: str
) -> Optional[float]:
    """
    Calculate the project-level cohesion proxy score.
    Uses weighted average of compound scores based on comment count.

    Args:
        sentiment_results: List of SentimentResult objects.
        project_id: Project identifier.

    Returns:
        float: Cohesion proxy score (mean compound score) or None if no data.
    """
    if not sentiment_results:
        # EDGE CASE: No text content for this project
        # Per T021: Assign 0 or flag "no_text_data"
        # We return 0.0 and log the condition
        logger.warning(f"No sentiment data available for project {project_id}. Assigning cohesion_proxy_score = 0.0")
        return 0.0

    project_results = [r for r in sentiment_results if r.project_id == project_id]

    if not project_results:
        # EDGE CASE: Project exists but no text content after filtering
        logger.warning(f"No text content found for project {project_id} after filtering. Assigning cohesion_proxy_score = 0.0")
        return 0.0

    # Calculate mean compound score
    compound_scores = [r.compound_score for r in project_results if r.compound_score is not None]

    if not compound_scores:
        logger.warning(f"No valid compound scores for project {project_id}. Assigning cohesion_proxy_score = 0.0")
        return 0.0

    mean_score = sum(compound_scores) / len(compound_scores)
    return mean_score

def ensure_directories_exist(*args, **kwargs):
    """
    Flexible directory creation wrapper.
    Handles multiple call signatures from different modules.

    Call signatures supported:
    1. ensure_directories_exist(config) - config object with data_dir
    2. ensure_directories_exist([dir_path], logger) - list of paths
    3. ensure_directories_exist([project_root]) - single item list
    4. ensure_directories_exist(output_path) - Path object
    5. ensure_directories_exist() - no args, does nothing
    """
    # If no arguments, do nothing (graceful no-op)
    if not args and not kwargs:
        return

    # Extract paths from various argument patterns
    paths_to_create = []

    # Pattern 1: Single config object
    if len(args) == 1 and hasattr(args[0], 'get'):
        config = args[0]
        data_dir = config.get('data_dir') or config.get('data_dir', get_config().get('data_dir', 'data'))
        if data_dir:
            paths_to_create.append(Path(data_dir))
            paths_to_create.append(Path(data_dir) / 'raw')
            paths_to_create.append(Path(data_dir) / 'derived')
            paths_to_create.append(Path(data_dir) / 'validation')
            paths_to_create.append(Path(data_dir) / 'logs')

    # Pattern 2: List of paths (possibly with logger as second arg)
    elif len(args) >= 1 and isinstance(args[0], list):
        for item in args[0]:
            if isinstance(item, (str, Path)):
                paths_to_create.append(Path(item))
            elif isinstance(item, dict) and 'path' in item:
                paths_to_create.append(Path(item['path']))

    # Pattern 3: Single Path or string argument
    elif len(args) == 1 and isinstance(args[0], (str, Path)):
        paths_to_create.append(Path(args[0]))

    # Pattern 4: Keyword argument 'paths'
    if 'paths' in kwargs and isinstance(kwargs['paths'], list):
        for item in kwargs['paths']:
            if isinstance(item, (str, Path)):
                paths_to_create.append(Path(item))

    # Create all directories
    for path in paths_to_create:
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {path}")
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            raise

def main():
    """Main entry point for sentiment analysis pipeline."""
    import argparse
    import pandas as pd

    parser = argparse.ArgumentParser(description='Run sentiment analysis on project comments.')
    parser.add_argument('--input', type=str, required=True, help='Path to input events JSON file.')
    parser.add_argument('--output', type=str, required=True, help='Path to output parquet file.')
    parser.add_argument('--min-confidence', type=float, default=0.95, help='Minimum language detection confidence.')
    args = parser.parse_args()

    config = get_config()
    ensure_directories_exist(config)

    # Load raw events
    logger.info(f"Loading events from {args.input}")
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            events = json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        sys.exit(1)

    # Extract comments with pair information
    comments = []
    for event in events:
        if event.get('type') == 'comment':
            comment = {
                'id': event.get('id', ''),
                'project_id': event.get('project_id', ''),
                'pair_id': event.get('pair_id', ''),
                'body': event.get('body', ''),
                'author': event.get('author', '')
            }
            comments.append(comment)

    if not comments:
        logger.warning("No comments found in input data.")
        # EDGE CASE: No text content at all
        # Create empty output file with correct schema
        empty_df = pd.DataFrame(columns=[
            'comment_id', 'project_id', 'pair_id', 'text',
            'language', 'is_english', 'compound_score',
            'positive', 'neutral', 'negative'
        ])
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        empty_df.to_parquet(output_path, index=False)
        logger.info(f"Created empty output file at {args.output}")
        return

    # Process sentiment
    results, exclusion_stats = process_comments_for_sentiment(comments, args.min_confidence)

    # Log exclusion rates per project
    exclusion_log = []
    for proj_id, stats in exclusion_stats.items():
        rate = stats['excluded'] / stats['total'] if stats['total'] > 0 else 0.0
        exclusion_log.append({
            'project_id': proj_id,
            'total_comments': stats['total'],
            'excluded_count': stats['excluded'],
            'exclusion_rate': rate
        })
        logger.info(f"Project {proj_id}: {stats['total']} total, {stats['excluded']} excluded (rate: {rate:.2%})")

    # Save exclusion log
    exclusion_log_path = Path(config.get('data_dir', 'data')) / 'logs' / 'exclusion_rate.json'
    with open(exclusion_log_path, 'w', encoding='utf-8') as f:
        json.dump(exclusion_log, f, indent=2)
    logger.info(f"Saved exclusion rates to {exclusion_log_path}")

    # Convert results to DataFrame
    if results:
        df = pd.DataFrame([
            {
                'comment_id': r.comment_id,
                'project_id': r.project_id,
                'pair_id': r.pair_id,
                'text': r.text,
                'language': r.language,
                'is_english': r.is_english,
                'compound_score': r.compound_score,
                'positive': r.positive,
                'neutral': r.neutral,
                'negative': r.negative
            }
            for r in results
        ])
    else:
        # EDGE CASE: No valid comments after filtering
        df = pd.DataFrame(columns=[
            'comment_id', 'project_id', 'pair_id', 'text',
            'language', 'is_english', 'compound_score',
            'positive', 'neutral', 'negative'
        ])

    # Save output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved sentiment results to {args.output}")

    # Calculate and log project-level cohesion scores
    project_scores = {}
    all_projects = set(r.project_id for r in results) | set(e.get('project_id') for e in comments)
    for proj in all_projects:
        score = calculate_project_cohesion_proxy(results, proj)
        project_scores[proj] = score
        logger.info(f"Project {proj} cohesion_proxy_score: {score}")

    # Save project scores
    scores_path = Path(config.get('data_dir', 'data')) / 'derived' / 'cohesion_scores.csv'
    scores_df = pd.DataFrame([
        {'project_id': p, 'cohesion_proxy_score': s}
        for p, s in project_scores.items()
    ])
    scores_df.to_csv(scores_path, index=False)
    logger.info(f"Saved project cohesion scores to {scores_path}")

if __name__ == "__main__":
    main()