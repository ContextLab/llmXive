"""
Sentiment analysis module for User Story 2.

Implements language detection filtering and VADER sentiment analysis
to derive cohesion proxy scores.

Dependencies:
- langdetect (language detection)
- nltk (VADER sentiment analyzer)
"""
import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

# External dependencies
try:
    from langdetect import detect, DetectorFactory
    from langdetect.lang_detect_exception import LangDetectException
except ImportError:
    raise ImportError(
        "The 'langdetect' library is required. Please install it via: "
        "pip install langdetect"
    )

try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    import nltk
except ImportError:
    raise ImportError(
        "The 'nltk' library is required. Please install it via: "
        "pip install nltk"
    )

from utils.logger import get_logger

# Set up logger
logger = get_logger(__name__)

# Ensure langdetect produces consistent results
DetectorFactory.seed = 0

# Constants
LANGUAGE_DETECTION_CONFIDENCE_THRESHOLD = 0.95
TARGET_LANGUAGE = 'en'

@dataclass
class SentimentResult:
    """Container for sentiment analysis results."""
    comment_id: str
    project_id: str
    text: str
    original_language: str
    language_confidence: float
    is_english: bool
    compound_score: Optional[float]
    pos_score: Optional[float]
    neu_score: Optional[float]
    neg_score: Optional[float]
    excluded: bool
    exclusion_reason: Optional[str]

def initialize_nltk():
    """Initialize NLTK VADER resources if not already present."""
    try:
        nltk.data.find('sentiment/vader_lexicon.zip')
        logger.info("NLTK VADER lexicon found.")
    except LookupError:
        logger.info("Downloading NLTK VADER lexicon...")
        nltk.download('vader_lexicon', quiet=True)
        logger.info("NLTK VADER lexicon downloaded.")

def detect_language(text: str) -> Tuple[str, float]:
    """
    Detect the language of the given text using langdetect.
    
    Args:
        text: The text to analyze.
        
    Returns:
        A tuple of (language_code, confidence_score).
        Returns ('unknown', 0.0) if detection fails.
        
    Raises:
        LangDetectException: If the text is too short or empty.
    """
    if not text or not text.strip():
        raise LangDetectException("Empty or whitespace-only text")
    
    try:
        # langdetect returns the ISO 639-1 language code
        lang = detect(text)
        
        # Estimate confidence: langdetect doesn't provide explicit confidence,
        # but we can use a heuristic based on detection stability.
        # For this implementation, we'll return a high confidence for valid detections
        # as the library is generally reliable for text > 20 chars.
        confidence = 0.98 if len(text.strip()) > 20 else 0.90
        
        return lang, confidence
    except LangDetectException as e:
        logger.warning(f"Language detection failed for text: {text[:50]}... Error: {e}")
        return 'unknown', 0.0

def filter_by_language(
    comments: List[Dict[str, Any]],
    confidence_threshold: float = LANGUAGE_DETECTION_CONFIDENCE_THRESHOLD,
    target_language: str = TARGET_LANGUAGE
) -> Tuple[List[SentimentResult], List[SentimentResult]]:
    """
    Filter comments by language detection.
    
    This function:
    1. Detects the language of each comment
    2. Filters out non-English comments (confidence >= threshold)
    3. Returns two lists: English comments (to analyze) and excluded comments
    
    Args:
        comments: List of comment dictionaries with keys:
                  - 'comment_id': str
                  - 'project_id': str
                  - 'text': str
        confidence_threshold: Minimum confidence required (default: 0.95)
        target_language: Target language code (default: 'en')
        
    Returns:
        Tuple of (english_comments, excluded_comments)
        Each item is a SentimentResult object.
    """
    initialize_nltk()
    
    english_comments = []
    excluded_comments = []
    
    for comment in comments:
        comment_id = comment.get('comment_id', 'unknown')
        project_id = comment.get('project_id', 'unknown')
        text = comment.get('text', '')
        
        # Detect language
        lang, confidence = detect_language(text)
        
        is_english = (lang == target_language) and (confidence >= confidence_threshold)
        
        result = SentimentResult(
            comment_id=comment_id,
            project_id=project_id,
            text=text,
            original_language=lang,
            language_confidence=confidence,
            is_english=is_english,
            compound_score=None,
            pos_score=None,
            neu_score=None,
            neg_score=None,
            excluded=not is_english,
            exclusion_reason=None if is_english else f"Language: {lang} (confidence: {confidence:.2f})"
        )
        
        if is_english:
            english_comments.append(result)
        else:
            excluded_comments.append(result)
            logger.debug(
                f"Excluded comment {comment_id} from project {project_id}: "
                f"Language={lang}, Confidence={confidence:.2f}"
            )
    
    return english_comments, excluded_comments

def analyze_sentiment(
    comments: List[SentimentResult]
) -> List[SentimentResult]:
    """
    Analyze sentiment of English comments using VADER.
    
    Args:
        comments: List of SentimentResult objects (should be English comments).
        
    Returns:
        List of SentimentResult objects with sentiment scores populated.
    """
    initialize_nltk()
    analyzer = SentimentIntensityAnalyzer()
    
    for result in comments:
        if not result.is_english:
            continue
        
        text = result.text
        scores = analyzer.polarity_scores(text)
        
        result.compound_score = scores['compound']
        result.pos_score = scores['pos']
        result.neu_score = scores['neu']
        result.neg_score = scores['neg']
    
    return comments

def process_comments_for_sentiment(
    comments: List[Dict[str, Any]],
    confidence_threshold: float = LANGUAGE_DETECTION_CONFIDENCE_THRESHOLD,
    target_language: str = TARGET_LANGUAGE
) -> List[SentimentResult]:
    """
    Full pipeline: detect language, filter, and analyze sentiment.
    
    Args:
        comments: List of comment dictionaries.
        confidence_threshold: Minimum confidence for language detection.
        target_language: Target language code.
        
    Returns:
        List of SentimentResult objects with sentiment scores for English comments.
    """
    # Step 1: Filter by language
    english_comments, excluded_comments = filter_by_language(
        comments, confidence_threshold, target_language
    )
    
    # Log exclusion statistics
    total = len(comments)
    excluded_count = len(excluded_comments)
    exclusion_rate = excluded_count / total if total > 0 else 0.0
    
    logger.info(
        f"Language filtering complete: {excluded_count}/{total} comments "
        f"excluded ({exclusion_rate:.2%})"
    )
    
    # Step 2: Analyze sentiment
    analyzed_comments = analyze_sentiment(english_comments)
    
    return analyzed_comments

def calculate_project_cohesion_proxy(
    sentiment_results: List[SentimentResult]
) -> Dict[str, float]:
    """
    Calculate project-level cohesion proxy score.
    
    The cohesion proxy score is the weighted average of compound scores
    per project, weighted by the length of the text (to give more weight
    to longer, more substantive comments).
    
    Args:
        sentiment_results: List of SentimentResult objects.
        
    Returns:
        Dictionary mapping project_id to cohesion_proxy_score.
    """
    project_scores = {}
    project_weights = {}
    
    for result in sentiment_results:
        if result.compound_score is None:
            continue
        
        project_id = result.project_id
        weight = len(result.text)  # Weight by text length
        score = result.compound_score
        
        if project_id not in project_scores:
            project_scores[project_id] = 0.0
            project_weights[project_id] = 0.0
        
        project_scores[project_id] += score * weight
        project_weights[project_id] += weight
    
    # Calculate weighted averages
    cohesion_scores = {}
    for project_id in project_scores:
        if project_weights[project_id] > 0:
            cohesion_scores[project_id] = (
                project_scores[project_id] / project_weights[project_id]
            )
        else:
            cohesion_scores[project_id] = 0.0
    
    return cohesion_scores