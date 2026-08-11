import os
import re
import math
import logging
import sys
from typing import List, Dict, Union, Optional, Any, Tuple
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def setup_logging():
    """
    Configure basic logging for the project.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('pipeline.log')
        ]
    )
    return logging.getLogger(__name__)

def get_logger(name=__name__):
    """
    Get a logger instance.
    """
    return logging.getLogger(name)

def load_config_env():
    """
    Load environment configuration.
    """
    # Placeholder for config loading logic
    return {}

def validate_environment():
    """
    Validate that required environment variables are set.
    """
    required_vars = ['DATA_DIR', 'MODEL_DIR']
    for var in required_vars:
        if var not in os.environ:
            raise ValueError(f"Environment variable {var} is not set.")
    return True

def calculate_vif(df: pd.DataFrame, col: str) -> float:
    """
    Calculate Variance Inflation Factor (VIF) for a specific column.
    """
    if col not in df.columns:
        raise ValueError(f"Column {col} not found in dataframe.")
    
    # Create a matrix of features excluding the target column
    # VIF is calculated for each feature against all others
    X = df[[c for c in df.columns if c != col]].dropna()
    y = df[col].dropna()
    
    if len(X) < 2 or len(X.columns) < 1:
        return 0.0

    # Fit a linear regression
    try:
        from sklearn.linear_model import LinearRegression
        reg = LinearRegression()
        reg.fit(X, y)
        r_squared = reg.score(X, y)
        if r_squared >= 1.0:
            return float('inf')
        vif = 1 / (1 - r_squared)
        return vif
    except Exception:
        return 0.0

def check_vif_threshold(vif: float, threshold: float = 5.0) -> bool:
    """
    Check if VIF exceeds the threshold.
    """
    return vif > threshold

def calculate_flesch_kincaid(text: str) -> float:
    """
    Calculate Flesch-Kincaid Readability Score.
    """
    if not text or not isinstance(text, str):
        return 0.0
    
    sentences = len(re.findall(r'[.!?]+', text)) or 1
    words = len(re.findall(r'\b\w+\b', text)) or 1
    syllables = sum(1 for char in text if char.lower() in 'aeiouy') or 1 # Simplified syllable count
    
    # Flesch Reading Ease formula
    score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
    return score

def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """
    Calculate Jaccard similarity between two texts.
    """
    if not text1 or not text2:
        return 0.0
    
    set1 = set(text1.lower().split())
    set2 = set(text2.lower().split())
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    if union == 0:
        return 0.0
    return intersection / union

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity using TF-IDF and cosine similarity.
    """
    if not text1 or not text2:
        return 0.0
    
    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform([text1, text2])
    similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])
    return float(similarity[0][0])

def validate_readiness_for_tier_generation():
    """
    Validate that the system is ready for tier generation.
    """
    # Placeholder logic
    return True

def validate_fidelity_scores(simple_score: float, complex_score: float, threshold: float = 0.85):
    """
    Validate fidelity scores against a threshold.
    """
    if simple_score < threshold or complex_score < threshold:
        raise ValueError(f"Fidelity scores below threshold {threshold}")
    return True
