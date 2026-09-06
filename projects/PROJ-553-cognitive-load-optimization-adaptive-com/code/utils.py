import os
import re
import math
import logging
import sys
from typing import List, Dict, Union, Optional, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy import stats

def setup_logging(name: str = "utils") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def get_logger(name: str = "utils") -> logging.Logger:
    return setup_logging(name)

def load_config_env(config_path: str = "code/config.py") -> Dict[str, Any]:
    """Loads configuration from a python file or environment variables."""
    logger = get_logger()
    config = {}
    if os.path.exists(config_path):
        try:
            spec = __import__(config_path.replace('/', '.').replace('.py', ''), fromlist=[''])
            config = getattr(spec, 'config', {})
        except Exception as e:
            logger.warning(f"Could not load config from {config_path}: {e}")
    return config

def validate_environment() -> bool:
    """Validates that required environment variables or configs exist."""
    logger = get_logger()
    # Placeholder for specific env checks if needed
    return True

def calculate_vif(df: pd.DataFrame, features: List[str]) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for a list of features.
    VIF measures how much the variance of an estimated regression coefficient
    increases if your predictors are correlated.
    
    Args:
        df: DataFrame containing the features.
        features: List of column names to calculate VIF for.
        
    Returns:
        Series of VIF values indexed by feature name.
    """
    logger = get_logger()
    if not features:
        logger.warning("No features provided for VIF calculation.")
        return pd.Series([], dtype=float)
    
    # Ensure we only have numeric columns
    X = df[features].select_dtypes(include=[np.number])
    
    if X.empty:
        logger.warning("No numeric features found in the provided list.")
        return pd.Series([], dtype=float)
    
    # Add intercept column for regression
    X_with_intercept = sm.add_constant(X)
    
    vif_data = pd.Series(index=features, dtype=float)
    
    try:
        import statsmodels.api as sm
        for feature in features:
            y = X_with_intercept[feature]
            X_reg = X_with_intercept.drop(columns=[feature])
            model = sm.OLS(y, X_reg).fit()
            vif_data[feature] = model.rsquared_adj
            # VIF = 1 / (1 - R^2)
            if model.rsquared_adj >= 1.0:
                vif_data[feature] = np.inf
            else:
                vif_data[feature] = 1 / (1 - model.rsquared_adj)
    except ImportError:
        logger.error("statsmodels is required for VIF calculation. Please install it.")
        raise
    except Exception as e:
        logger.error(f"Error calculating VIF: {e}")
        raise
        
    return vif_data

def check_vif_threshold(vif_series: pd.Series, threshold: float = 5.0) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Check which features exceed the VIF threshold and frame descriptive relationships.
    
    Args:
        vif_series: Series of VIF values.
        threshold: Maximum allowed VIF (default 5.0).
        
    Returns:
        Tuple of (list of problematic features, list of diagnostic dicts).
    """
    logger = get_logger()
    problematic = []
    diagnostics = []
    
    for feature, vif in vif_series.items():
        if vif > threshold:
            problematic.append(feature)
            diagnostics.append({
                "feature": feature,
                "vif": vif,
                "status": "HIGH_COLLINEARITY",
                "description": f"Feature '{feature}' has VIF {vif:.2f} > {threshold}. "
                               "This indicates strong multicollinearity. Consider removing this feature "
                               "or combining it with correlated predictors to reduce redundancy."
            })
            logger.warning(f"High collinearity detected: {feature} (VIF={vif:.2f})")
    
    return problematic, diagnostics

def calculate_flesch_kincaid(text: str) -> float:
    """
    Calculate Flesch-Kincaid Grade Level.
    FK = 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
    """
    if not text or not isinstance(text, str):
        return 0.0
    
    # Simple sentence splitting
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    num_sentences = len(sentences) if sentences else 1
    
    # Word splitting
    words = re.findall(r'\b\w+\b', text)
    num_words = len(words) if words else 1
    
    # Syllable counting (approximation)
    def count_syllables(word: str) -> int:
        word = word.lower()
        if len(word) <= 3:
            return 1
        # Remove silent e
        word = re.sub(r'e$', '', word)
        # Count vowel groups
        syllables = len(re.findall(r'[aeiouy]+', word))
        return max(1, syllables)
    
    total_syllables = sum(count_syllables(w) for w in words)
    
    fk = 0.39 * (num_words / num_sentences) + 11.8 * (total_syllables / num_words) - 15.59
    return max(0.0, fk)

def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """
    Calculate Jaccard similarity between two texts based on word sets.
    J(A, B) = |A ∩ B| / |A ∪ B|
    """
    if not text1 or not text2:
        return 0.0
    
    set1 = set(re.findall(r'\b\w+\b', text1.lower()))
    set2 = set(re.findall(r'\b\w+\b', text2.lower()))
    
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
        
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    
    return len(intersection) / len(union) if union else 0.0

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity using TF-IDF and cosine similarity.
    Lightweight CPU-safe approach without heavy embeddings.
    """
    if not text1 or not text2:
        return 0.0
    
    try:
        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(similarity)
    except Exception as e:
        logger = get_logger()
        logger.warning(f"Semantic similarity calculation failed: {e}. Returning 0.0.")
        return 0.0

def validate_fidelity_scores(simple_fk: float, moderate_fk: float, complex_fk: float, 
                             simple_jaccard: float, complex_jaccard: float) -> Dict[str, bool]:
    """
    Validate that tier generation meets fidelity constraints.
    - FK Difference >= 5 points
    - Jaccard Similarity >= 0.85
    """
    results = {
        "simple_fk_diff_valid": (moderate_fk - simple_fk) >= 5.0,
        "complex_fk_diff_valid": (complex_fk - moderate_fk) >= 5.0,
        "simple_jaccard_valid": simple_jaccard >= 0.85,
        "complex_jaccard_valid": complex_jaccard >= 0.85,
        "monotonic_progression": simple_fk < moderate_fk < complex_fk
    }
    return results

def validate_readiness_for_tier_generation(instructional_units_path: str) -> bool:
    """
    Check if instructional units file exists and has content.
    """
    logger = get_logger()
    if not os.path.exists(instructional_units_path):
        logger.error(f"Instructional units file not found: {instructional_units_path}")
        return False
    
    try:
        df = pd.read_csv(instructional_units_path)
        if df.empty:
            logger.error("Instructional units file is empty.")
            return False
        logger.info(f"Readiness check passed: {len(df)} units found.")
        return True
    except Exception as e:
        logger.error(f"Error reading instructional units: {e}")
        return False
