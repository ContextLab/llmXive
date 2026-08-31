import os
import re
import math
import logging
import sys
from typing import List, Dict, Union, Optional, Any, Tuple
import pandas as pd
import numpy as np

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def get_logger(name: str = __name__):
    """Get a logger instance."""
    return logging.getLogger(name)

def load_config_env(config_path: str = "config.env") -> Dict[str, str]:
    """Load environment variables from a config file."""
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    return config

def validate_environment(config: Dict[str, str]) -> bool:
    """Validate required environment variables."""
    required_keys = ['DATA_DIR', 'MODEL_DIR']
    for key in required_keys:
        if key not in config:
            logging.error(f"Missing required config key: {key}")
            return False
    return True

def calculate_vif(df: pd.DataFrame, feature_cols: List[str], target_col: str) -> float:
    """
    Calculate Variance Inflation Factor (VIF) for a target column.
    VIF = 1 / (1 - R^2) where R^2 is from regressing target_col on feature_cols.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column {target_col} not in DataFrame")
    
    # Prepare data
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Handle constant features or zero variance
    if X.shape[1] == 0:
        return 1.0
    
    # Simple linear regression to get R^2
    # Using numpy for speed and avoiding sklearn dependency if not needed, 
    # but sklearn is in requirements. Let's use numpy for VIF calculation.
    try:
        # Add intercept
        X_with_intercept = np.column_stack([np.ones(X.shape[0]), X])
        coeffs, residuals, rank, s = np.linalg.lstsq(X_with_intercept, y, rcond=None)
        
        # Calculate predictions
        y_pred = X_with_intercept @ coeffs
        
        # Calculate R^2
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        
        if ss_tot == 0:
            return 1.0
        
        r_squared = 1 - (ss_res / ss_tot)
        
        # VIF calculation
        if r_squared >= 1.0:
            return float('inf')
        
        vif = 1.0 / (1.0 - r_squared)
        return float(vif)
    except Exception as e:
        logging.error(f"Error calculating VIF: {e}")
        return float('inf')

def check_vif_threshold(vif_value: float, threshold: float = 5.0) -> bool:
    """Check if VIF value exceeds threshold."""
    return vif_value > threshold

def calculate_flesch_kincaid(text: str) -> float:
    """
    Calculate Flesch-Kincaid Readability Score.
    FK = 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words)
    """
    if not text or not isinstance(text, str):
        return 0.0
    
    # Count sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    num_sentences = max(len(sentences), 1)
    
    # Count words
    words = re.findall(r'\b\w+\b', text.lower())
    num_words = len(words)
    if num_words == 0:
        return 0.0
    
    # Count syllables (approximate)
    def count_syllables(word: str) -> int:
        word = word.lower()
        if len(word) <= 3:
            return 1
        count = 0
        vowels = 'aeiouy'
        prev_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        if word.endswith('e'):
            count -= 1
        return max(count, 1)
    
    total_syllables = sum(count_syllables(word) for word in words)
    
    # Calculate score
    score = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (total_syllables / num_words)
    return max(0.0, score)

def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity between two texts."""
    if not text1 or not text2:
        return 0.0
    
    set1 = set(text1.lower().split())
    set2 = set(text2.lower().split())
    
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    if union == 0:
        return 0.0
    
    return intersection / union

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity using TF-IDF and cosine similarity.
    Lightweight CPU-safe implementation.
    """
    if not text1 or not text2:
        return 0.0
    
    # Simple TF-IDF approximation
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    
    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(similarity)
    except Exception as e:
        logging.warning(f"Semantic similarity calculation failed: {e}. Returning 0.0.")
        return 0.0

def validate_fidelity_scores(simple_score: float, moderate_score: float, complex_score: float, 
                             jaccard: float, semantic: float) -> bool:
    """Validate tier generation fidelity scores."""
    # Check monotonic progression
    if not (simple_score < moderate_score < complex_score):
        logging.error("Readability scores not monotonic: simple < moderate < complex")
        return False
    
    # Check differences >= 5
    if (moderate_score - simple_score) < 5.0:
        logging.error("Difference between simple and moderate < 5")
        return False
    if (complex_score - moderate_score) < 5.0:
        logging.error("Difference between moderate and complex < 5")
        return False
    
    # Check Jaccard >= 0.85
    if jaccard < 0.85:
        logging.error(f"Jaccard similarity {jaccard:.2f} < 0.85")
        return False
    
    # Check Semantic >= 0.90
    if semantic < 0.90:
        logging.error(f"Semantic similarity {semantic:.2f} < 0.90")
        return False
    
    return True

def validate_readiness_for_tier_generation() -> bool:
    """Check if prerequisites for tier generation are met."""
    # Check if instructional units exist
    units_path = "data/processed/instructional_units.csv"
    if not os.path.exists(units_path):
        logging.error("Instructional units not found. Run T022 first.")
        return False
    
    # Check if golden set exists (for load model dependency)
    golden_path = "data/processed/golden_set.csv"
    if not os.path.exists(golden_path):
        logging.error("Golden set not found. Run T007b first.")
        return False
    
    return True
