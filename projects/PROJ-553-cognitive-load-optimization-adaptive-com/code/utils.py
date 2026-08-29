import os
import re
import math
import logging
import sys
from typing import List, Dict, Union, Optional, Any, Tuple
import textstat
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def setup_logging() -> logging.Logger:
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)

def load_config_env(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from environment variables or a file."""
    config = {}
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    # Override with environment variables
    for key in list(config.keys()):
        if key in os.environ:
            config[key] = os.environ[key]
    return config

def validate_environment() -> bool:
    """Validate that required environment variables are set."""
    required_vars = ['DATA_DIR', 'PROJECT_ROOT']
    for var in required_vars:
        if var not in os.environ:
            logging.error(f"Missing required environment variable: {var}")
            return False
    return True

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        df: DataFrame containing the features
        features: List of feature column names
        
    Returns:
        Dictionary mapping feature names to their VIF values
    """
    import pandas as pd
    vif_data = {}
    X = df[features].dropna()
    if X.empty or len(X) < 2:
        return {f: float('inf') for f in features}
    
    for i, feature in enumerate(features):
        if feature not in df.columns:
            continue
        y = df[feature].dropna()
        X_other = df[[f for f in features if f != feature]].dropna()
        if len(y) != len(X_other):
            # Align indices
            common_idx = y.index.intersection(X_other.index)
            y = y.loc[common_idx]
            X_other = X_other.loc[common_idx]
        
        if len(y) < 2:
            vif_data[feature] = float('inf')
            continue
        
        try:
            from sklearn.linear_model import LinearRegression
            model = LinearRegression()
            model.fit(X_other, y)
            r_squared = model.score(X_other, y)
            if r_squared >= 1.0:
                vif_data[feature] = float('inf')
            else:
                vif_data[feature] = 1.0 / (1.0 - r_squared)
        except Exception as e:
            logging.warning(f"Could not calculate VIF for {feature}: {e}")
            vif_data[feature] = float('inf')
    
    return vif_data

def check_vif_threshold(vif_values: Dict[str, float], threshold: float = 5.0) -> List[str]:
    """
    Check which features exceed the VIF threshold.
    
    Args:
        vif_values: Dictionary of feature VIF values
        threshold: VIF threshold (default 5.0)
        
    Returns:
        List of feature names exceeding the threshold
    """
    return [f for f, v in vif_values.items() if v > threshold]

def calculate_flesch_kincaid(text: str) -> float:
    """
    Calculate Flesch-Kincaid readability score.
    
    Args:
        text: Input text string
        
    Returns:
        Flesch-Kincaid Grade Level score
    """
    if not text or not isinstance(text, str):
        return 0.0
    try:
        # textstat.flesch_reading_ease returns 0-100, lower is harder
        # textstat.flesch_kincaid_grade returns grade level (0-18+)
        score = textstat.flesch_kincaid_grade(text)
        return float(score)
    except Exception as e:
        logging.warning(f"Could not calculate Flesch-Kincaid for text: {e}")
        return 0.0

def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """
    Calculate Jaccard similarity between two texts based on word sets.
    
    Args:
        text1: First text string
        text2: Second text string
        
    Returns:
        Jaccard similarity coefficient (0.0 to 1.0)
    """
    if not text1 or not text2:
        return 0.0
    
    # Normalize: lowercase and split into words
    words1 = set(re.findall(r'\b\w+\b', text1.lower()))
    words2 = set(re.findall(r'\b\w+\b', text2.lower()))
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity between two texts using TF-IDF and cosine similarity.
    
    This is a lightweight CPU-safe approach that does not require heavy embeddings.
    
    Args:
        text1: First text string
        text2: Second text string
        
    Returns:
        Cosine similarity score (0.0 to 1.0)
    """
    if not text1 or not text2:
        return 0.0
    
    try:
        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        return float(similarity[0][0])
    except Exception as e:
        logging.warning(f"Could not calculate semantic similarity: {e}")
        return 0.0

def validate_fidelity_scores(
    source_text: str, 
    generated_text: str, 
    jaccard_threshold: float = 0.85, 
    semantic_threshold: float = 0.90
) -> Tuple[bool, float, float, str]:
    """
    Validate that generated text maintains fidelity to the source text.
    
    Args:
        source_text: The original source text
        generated_text: The generated/simplified/complex text
        jaccard_threshold: Minimum required Jaccard similarity (default 0.85)
        semantic_threshold: Minimum required semantic similarity (default 0.90)
        
    Returns:
        Tuple of (is_valid, jaccard_score, semantic_score, error_message)
        - is_valid: True if both thresholds are met
        - error_message: Description of failure if any, empty string if valid
    """
    jaccard_score = calculate_jaccard_similarity(source_text, generated_text)
    semantic_score = calculate_semantic_similarity(source_text, generated_text)
    
    errors = []
    
    if jaccard_score < jaccard_threshold:
        errors.append(f"Jaccard similarity {jaccard_score:.3f} < threshold {jaccard_threshold}")
    
    if semantic_score < semantic_threshold:
        errors.append(f"Semantic similarity {semantic_score:.3f} < threshold {semantic_threshold}")
    
    is_valid = len(errors) == 0
    error_message = "; ".join(errors) if errors else ""
    
    return is_valid, jaccard_score, semantic_score, error_message

def validate_readiness_for_tier_generation(
    source_text: str, 
    simple_text: str, 
    complex_text: str,
    fk_threshold: float = 5.0,
    jaccard_threshold: float = 0.85,
    semantic_threshold: float = 0.90
) -> Tuple[bool, Dict[str, Any], str]:
    """
    Validate all constraints for tier generation before saving.
    
    Checks:
    1. Monotonic FK progression: simple < moderate < complex with >= 5 point diff
    2. Jaccard similarity >= 0.85 for both tiers
    3. Semantic similarity >= 0.90 for both tiers
    
    Args:
        source_text: Original instructional unit text
        simple_text: Generated simple tier
        complex_text: Generated complex tier
        fk_threshold: Minimum FK difference between tiers (default 5.0)
        jaccard_threshold: Minimum Jaccard similarity (default 0.85)
        semantic_threshold: Minimum semantic similarity (default 0.90)
        
    Returns:
        Tuple of (is_valid, metrics_dict, error_message)
    """
    # Calculate FK scores
    fk_source = calculate_flesch_kincaid(source_text)
    fk_simple = calculate_flesch_kincaid(simple_text)
    fk_complex = calculate_flesch_kincaid(complex_text)
    
    # Calculate fidelity scores
    jaccard_simple, sem_simple = 0.0, 0.0
    is_valid_simple, jaccard_simple, sem_simple, err_simple = validate_fidelity_scores(
        source_text, simple_text, jaccard_threshold, semantic_threshold
    )
    
    jaccard_complex, sem_complex = 0.0, 0.0
    is_valid_complex, jaccard_complex, sem_complex, err_complex = validate_fidelity_scores(
        source_text, complex_text, jaccard_threshold, semantic_threshold
    )
    
    errors = []
    
    # Check monotonic FK progression
    if not (fk_simple < fk_source < fk_complex):
        errors.append(f"FK progression failed: simple={fk_simple:.2f}, source={fk_source:.2f}, complex={fk_complex:.2f}")
    
    # Check FK differences
    if (fk_source - fk_simple) < fk_threshold:
        errors.append(f"FK difference (source-simple) {fk_source - fk_simple:.2f} < {fk_threshold}")
    
    if (fk_complex - fk_source) < fk_threshold:
        errors.append(f"FK difference (complex-source) {fk_complex - fk_source:.2f} < {fk_threshold}")
    
    # Check fidelity
    if not is_valid_simple:
        errors.append(f"Simple tier fidelity failed: {err_simple}")
    
    if not is_valid_complex:
        errors.append(f"Complex tier fidelity failed: {err_complex}")
    
    is_valid = len(errors) == 0
    
    metrics = {
        "fk_source": fk_source,
        "fk_simple": fk_simple,
        "fk_complex": fk_complex,
        "jaccard_simple": jaccard_simple,
        "semantic_simple": sem_simple,
        "jaccard_complex": jaccard_complex,
        "semantic_complex": sem_complex,
        "fk_diff_simple": fk_source - fk_simple,
        "fk_diff_complex": fk_complex - fk_source
    }
    
    error_message = "; ".join(errors) if errors else ""
    
    return is_valid, metrics, error_message
