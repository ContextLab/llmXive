"""
Judge Service for LLM-based consistency scoring and rule-based metric calculation.

This module implements:
1. Judge scoring (T025): LLM-based consistency scoring using Likert scale.
2. Rule-based scoring (T026): Sentiment and coherence alignment using VADER/BERT.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import re

# Try to import VADER; if not available, we rely on the fact that it's in requirements.txt
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logging.warning("vaderSentiment not installed. Rule-based scoring will be unavailable.")

from src.lib.config import get_config
from src.lib.utils import get_logger

logger = get_logger(__name__)
config = get_config()

# Constants for rule-based scoring
SENTIMENT_WEIGHT = 0.6
COHERENCE_WEIGHT = 0.4
SENTIMENT_THRESHOLD_POSITIVE = 0.1
SENTIMENT_THRESHOLD_NEGATIVE = -0.1
COHERENCE_THRESHOLD = 0.3  # Placeholder for BERT coherence; using VADER for now

def load_judge_model():
    """
    Load the Judge model (LLM) for consistency scoring.
    Implemented in T025; placeholder here for structure.
    """
    # In a real implementation, this would load the model using src/models/loader.py
    # For now, we assume the model is loaded externally or via a service.
    return None

def judge_score_response(response: str, target_phase: str, judge_model=None) -> Tuple[float, bool]:
    """
    T025 Implementation: LLM-based consistency scoring.
    
    Args:
        response: The model's response text.
        target_phase: The target psychological phase (e.g., 'Coarse', 'Fine').
        judge_model: The loaded Judge model (optional).
        
    Returns:
        Tuple of (score, adherence_flag).
        score: Float between 0.0 and 5.0 (Likert scale).
        adherence_flag: Boolean indicating if the response adheres to the target phase.
    """
    # Placeholder for actual LLM-based scoring logic.
    # In a real implementation, this would call the Judge model.
    # For now, we return a dummy score and flag based on simple heuristics.
    # TODO: Replace with actual LLM inference.
    
    # Dummy implementation for structure
    score = 3.0  # Neutral score
    adherence_flag = True  # Assume adherence for now
    
    # In a real scenario, we would:
    # 1. Construct a prompt for the Judge model.
    # 2. Call the model.
    # 3. Parse the output to extract score and adherence.
    # 4. Clamp the score to [0, 5].
    
    return score, adherence_flag

def calculate_rule_score(response: str, keywords: List[str]) -> float:
    """
    T026 Implementation: Rule-based scoring metric.
    
    Calculates a discrete score based on sentiment alignment and coherence,
    using VADER (or BERT if available) as per FR-004. This is distinct from
    the Judge model scoring.
    
    Args:
        response: The model's response text.
        keywords: List of keywords associated with the target phase (for context,
                  though we use sentiment/coherence, not keyword presence).
    
    Returns:
        A float score between 0.0 and 1.0 representing the rule-based consistency.
    
    Raises:
        ImportError: If VADER is not installed and required.
    """
    if not VADER_AVAILABLE:
        raise ImportError("vaderSentiment is required for rule-based scoring. "
                          "Please install it via 'pip install vaderSentiment'.")
    
    analyzer = SentimentIntensityAnalyzer()
    
    # 1. Sentiment Analysis
    sentiment_scores = analyzer.polarity_scores(response)
    compound = sentiment_scores['compound']
    
    # Normalize compound to [0, 1] for scoring (compound is in [-1, 1])
    # We map -1 -> 0, 0 -> 0.5, 1 -> 1
    normalized_sentiment = (compound + 1) / 2.0
    
    # 2. Coherence Analysis (Simplified: using sentence count and length variance)
    # In a real implementation, this would use a BERT-based model for coherence.
    # For now, we use a heuristic based on sentence structure.
    sentences = re.split(r'[.!?]+', response)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) < 2:
        coherence_score = 0.5  # Low coherence if too few sentences
    else:
        # Calculate variance in sentence lengths as a proxy for coherence
        lengths = [len(s.split()) for s in sentences]
        mean_len = sum(lengths) / len(lengths)
        variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
        
        # Lower variance implies more consistent sentence structure -> higher coherence
        # Normalize variance to [0, 1] (arbitrary threshold)
        coherence_score = max(0.0, 1.0 - (variance / 100.0))  # Cap variance impact
    
    # 3. Combine Scores
    # Weighted average: Sentiment (60%) + Coherence (40%)
    final_score = (SENTIMENT_WEIGHT * normalized_sentiment) + (COHERENCE_WEIGHT * coherence_score)
    
    # Clamp to [0, 1]
    final_score = max(0.0, min(1.0, final_score))
    
    logger.debug(f"Rule-based score calculated: Sentiment={normalized_sentiment:.3f}, "
                 f"Coherence={coherence_score:.3f}, Final={final_score:.3f}")
    
    return final_score

def run_judge_evaluation(response: str, target_phase: str, keywords: List[str], judge_model=None) -> Dict[str, Any]:
    """
    Runs both Judge and Rule-based evaluation on a response.
    
    Args:
        response: The model's response text.
        target_phase: The target psychological phase.
        keywords: Keywords for the target phase.
        judge_model: Optional Judge model instance.
    
    Returns:
        Dictionary containing:
            - judge_score: Float (0-5)
            - judge_adherence_flag: Bool
            - rule_score: Float (0-1)
            - combined_score: Weighted average (if needed)
    """
    judge_score, judge_flag = judge_score_response(response, target_phase, judge_model)
    rule_score = calculate_rule_score(response, keywords)
    
    # Example combination: Normalize judge_score to [0, 1] and average
    normalized_judge = judge_score / 5.0
    combined_score = (normalized_judge + rule_score) / 2.0
    
    return {
        "judge_score": judge_score,
        "judge_adherence_flag": judge_flag,
        "rule_score": rule_score,
        "combined_score": combined_score
    }

def main():
    """
    Main entry point for testing the judge service.
    """
    # Example usage
    test_response = "The character displayed a consistent and clear emotional response to the situation, " \
                    "showing resilience and adaptability in the face of adversity."
    test_keywords = ["resilience", "adaptability", "emotional"]
    test_phase = "Fine"
    
    result = run_judge_evaluation(test_response, test_phase, test_keywords)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()