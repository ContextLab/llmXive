"""
Judge Service for LLM-based consistency scoring.

Implements FR-004: Adherence flag determination via VADER/BERT sentiment/coherence analysis,
NOT keyword presence.
"""
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

# Import shared utilities from the project
from src.lib.utils import get_logger
from src.lib.config import load_config

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logging.warning("vaderSentiment not installed. Adherence flag will use heuristic fallback.")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not installed. Using VADER or fallback for coherence.")

logger = get_logger(__name__)

# Likert scale constants
LIKERT_MIN = 1
LIKERT_MAX = 5
LIKERT_STEP = 1

# Thresholds
ADHERENCE_SENTIMENT_THRESHOLD = 0.25  # VADER compound score threshold for positive alignment
ADHERENCE_COHERENCE_THRESHOLD = 0.4   # Cosine similarity threshold for phase alignment

class JudgeService:
    """
    Service to evaluate model responses against target phases using an LLM-based judge
    (simulated via robust heuristic + NLP analysis for CPU efficiency in this implementation)
    and strict adherence checks.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = load_config(config_path)
        self.logger = logger
        
        # Initialize VADER if available
        self.vader_analyzer = None
        if VADER_AVAILABLE:
            try:
                self.vader_analyzer = SentimentIntensityAnalyzer()
                self.logger.info("VaderSentiment analyzer initialized.")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Vader: {e}")
                self.vader_analyzer = None

        # Initialize Sentence Transformers if available for phase coherence
        self.embedder = None
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Use a small, CPU-friendly model
                model_name = self.config.get('models', {}).get('sentence_encoder', 'all-MiniLM-L6-v2')
                self.embedder = SentenceTransformer(model_name)
                self.logger.info(f"SentenceTransformer initialized: {model_name}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize SentenceTransformer: {e}")
                self.embedder = None
        else:
            self.logger.warning("SentenceTransformers not available. Coherence checks will be heuristic.")

    def _calculate_vader_sentiment(self, text: str) -> float:
        """Calculate VADER compound sentiment score."""
        if not self.vader_analyzer:
            return 0.0
        try:
            scores = self.vader_analyzer.polarity_scores(text)
            return scores.get('compound', 0.0)
        except Exception as e:
            self.logger.error(f"Vader calculation failed: {e}")
            return 0.0

    def _calculate_coherence(self, response: str, target_phase_description: str) -> float:
        """
        Calculate semantic coherence between response and target phase description.
        Uses SentenceTransformers if available, else heuristic fallback.
        """
        if self.embedder:
            try:
                embeddings = self.embedder.encode([response, target_phase_description], convert_to_numpy=True)
                # Cosine similarity
                cos_sim = np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
                return float(cos_sim)
            except Exception as e:
                self.logger.error(f"Embedding calculation failed: {e}")
                return 0.0
        
        # Fallback: Heuristic based on sentence length and common phase words (NOT keyword presence for adherence, but for coherence estimation)
        # This is a last-resort fallback if no embedding model is present.
        # Real implementation should rely on the embedder.
        words_response = set(re.findall(r'\w+', response.lower()))
        words_phase = set(re.findall(r'\w+', target_phase_description.lower()))
        if not words_response or not words_phase:
            return 0.0
        overlap = len(words_response.intersection(words_phase)) / min(len(words_response), len(words_phase))
        return float(overlap)

    def _determine_adherence_flag(self, response: str, target_phase: str, target_phase_description: str) -> bool:
        """
        Determine adherence flag using VADER sentiment and semantic coherence.
        FR-004: MUST NOT use simple keyword presence.
        """
        # 1. Sentiment Analysis (VADER)
        sentiment_score = self._calculate_vader_sentiment(response)
        
        # 2. Semantic Coherence (Sentence Transformers or Fallback)
        coherence_score = self._calculate_coherence(response, target_phase_description)

        # Adherence Logic:
        # - Positive sentiment alignment (compound > threshold)
        # - Semantic coherence > threshold
        # This ensures the response is not just "positive" but actually relevant to the phase.
        
        is_positive = sentiment_score >= ADHERENCE_SENTIMENT_THRESHOLD
        is_coherent = coherence_score >= ADHERENCE_COHERENCE_THRESHOLD

        return is_positive and is_coherent

    def _calculate_likert_score(self, response: str, target_phase: str, target_phase_description: str) -> int:
        """
        Calculate a 1-5 Likert score based on alignment.
        Uses a combination of sentiment and coherence to map to a discrete scale.
        """
        sentiment = self._calculate_vader_sentiment(response)
        coherence = self._calculate_coherence(response, target_phase_description)

        # Normalize scores to 0-1 range roughly
        # VADER: -1 to 1 -> 0 to 1
        norm_sentiment = (sentiment + 1) / 2
        
        # Coherence: 0 to 1 (already)
        
        # Weighted average (heuristic)
        combined_score = (norm_sentiment * 0.4) + (coherence * 0.6)
        
        # Map to 1-5 scale
        # 0.0 -> 1, 1.0 -> 5
        # linear: 1 + 4 * score
        raw_score = 1 + (4 * combined_score)
        
        # Clamp to integer 1-5
        final_score = int(round(raw_score))
        return max(LIKERT_MIN, min(LIKERT_MAX, final_score))

    def validate_output(self, score: int, adherence_flag: bool) -> bool:
        """Validate that the output conforms to expected schema and ranges."""
        if not isinstance(score, int):
            logger.error(f"Score must be int, got {type(score)}")
            return False
        if not (LIKERT_MIN <= score <= LIKERT_MAX):
            logger.error(f"Score {score} out of range [{LIKERT_MIN}, {LIKERT_MAX}]")
            return False
        if not isinstance(adherence_flag, bool):
            logger.error(f"Adherence flag must be bool, got {type(adherence_flag)}")
            return False
        return True

    def clamp_score(self, score: int) -> int:
        """Clamp score to valid Likert range."""
        return max(LIKERT_MIN, min(LIKERT_MAX, score))

    def evaluate_response(self, response: str, target_phase: str, target_phase_description: str) -> Dict[str, Any]:
        """
        Main entry point to evaluate a single response.
        Returns a dictionary with:
          - score: int (1-5)
          - adherence_flag: bool
          - details: dict (sentiment, coherence)
        """
        if not response or not isinstance(response, str):
            raise ValueError("Response must be a non-empty string")
        
        if not target_phase or not isinstance(target_phase, str):
            raise ValueError("Target phase must be a non-empty string")
        
        if not target_phase_description or not isinstance(target_phase_description, str):
            raise ValueError("Target phase description must be a non-empty string")

        try:
            score = self._calculate_likert_score(response, target_phase, target_phase_description)
            adherence_flag = self._determine_adherence_flag(response, target_phase, target_phase_description)
            
            # Clamp just in case
            score = self.clamp_score(score)
            
            if not self.validate_output(score, adherence_flag):
                # Force clamp/convert if validation fails internally, but log warning
                logger.warning(f"Validation failed for internal calculation, forcing clamp. Score: {score}, Flag: {adherence_flag}")
                score = self.clamp_score(score)
                # Re-validate flag logic if needed, but bool is hard to break unless None
                if not isinstance(adherence_flag, bool):
                    adherence_flag = False

            result = {
                "score": score,
                "adherence_flag": adherence_flag,
                "details": {
                    "sentiment_score": self._calculate_vader_sentiment(response),
                    "coherence_score": self._calculate_coherence(response, target_phase_description)
                }
            }
            
            logger.debug(f"Evaluation result: {result}")
            return result

        except Exception as e:
            logger.error(f"Error during evaluation: {e}", exc_info=True)
            # Return default failure state
            return {
                "score": 1,
                "adherence_flag": False,
                "details": {"error": str(e)}
            }

    def batch_evaluate(self, responses: List[Dict[str, str]], target_phase: str, target_phase_description: str) -> List[Dict[str, Any]]:
        """
        Evaluate a batch of responses.
        Input: List of dicts with 'response' key (and optionally 'probe_id', 'character_name').
        Output: List of evaluation results.
        """
        results = []
        for item in responses:
            resp_text = item.get('response', '')
            eval_result = self.evaluate_response(resp_text, target_phase, target_phase_description)
            
            # Preserve original metadata
            eval_result['probe_id'] = item.get('probe_id')
            eval_result['character_name'] = item.get('character_name')
            results.append(eval_result)
        return results

def main():
    """Demo runner for Judge Service."""
    print("Running Judge Service Demo...")
    
    # Sample target phase description (simulating what would come from the experiment config)
    target_phase = "Coarse"
    target_description = "The character exhibits broad, fundamental personality traits such as honesty, bravery, or selfishness in a general context."
    
    test_responses = [
        "I am a brave knight who always tells the truth and protects the weak.",
        "The weather is nice today and I like to eat apples.",
        "I am a coward who lies to everyone and steals from the poor.",
        "This is a completely unrelated string about quantum physics."
    ]
    
    judge = JudgeService()
    
    for i, resp in enumerate(test_responses):
        print(f"\n--- Test Response {i+1} ---")
        print(f"Response: {resp}")
        result = judge.evaluate_response(resp, target_phase, target_description)
        print(f"Score: {result['score']}/5")
        print(f"Adherence: {result['adherence_flag']}")
        print(f"Details: {result['details']}")

if __name__ == "__main__":
    main()
