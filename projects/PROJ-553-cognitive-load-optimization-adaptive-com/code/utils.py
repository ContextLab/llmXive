import os
import re
import math
import logging
import sys
from typing import List, Dict, Union, Optional, Any
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.feature_selection import variance_threshold
from statsmodels.stats.outliers_influence import variance_inflation_factor
import textstat

# --- Logging Infrastructure Setup ---

_logger_initialized = False
_log_level = logging.INFO

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    project_root: Optional[Path] = None
) -> logging.Logger:
    """
    Configures the project-wide logging infrastructure.

    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file. If None, logs only to console.
        project_root: Optional root path for the project. Defaults to current working directory.

    Returns:
        The configured root logger for the 'llmXive' namespace.
    """
    global _logger_initialized, _log_level
    _log_level = log_level

    if _logger_initialized:
        return logging.getLogger("llmXive")

    logger = logging.getLogger("llmXive")
    logger.setLevel(log_level)

    # Prevent duplicate handlers if called multiple times in same process
    if logger.handlers:
        logger.handlers.clear()

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _logger_initialized = True
    logger.info("Logging infrastructure initialized.")
    return logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieves a logger instance. Ensures logging is initialized if not already.
    """
    global _logger_initialized
    if not _logger_initialized:
        # Default initialization if user didn't call setup_logging explicitly
        setup_logging()
    return logging.getLogger(name)

# --- Environment Configuration Management ---

def load_config_env(prefix: str = "LLMXIVE_") -> Dict[str, Any]:
    """
    Loads configuration variables from environment variables with a specific prefix.

    Args:
        prefix: The prefix for environment variables (e.g., 'LLMXIVE_').

    Returns:
        A dictionary of configuration key-value pairs.
    """
    config = {}
    for key, value in os.environ.items():
        if key.startswith(prefix):
            config_key = key[len(prefix):].lower()
            # Attempt type conversion
            if value.lower() in ('true', 'yes', '1'):
                config[config_key] = True
            elif value.lower() in ('false', 'no', '0'):
                config[config_key] = False
            else:
                try:
                    config[config_key] = int(value)
                except ValueError:
                    try:
                        config[config_key] = float(value)
                    except ValueError:
                        config[config_key] = value
    return config

def validate_environment(required_vars: List[str]) -> bool:
    """
    Validates that required environment variables are set.

    Args:
        required_vars: List of environment variable names to check.

    Returns:
        True if all are present, False otherwise.
    """
    missing = [var for var in required_vars if var not in os.environ]
    if missing:
        logger = get_logger()
        logger.error(f"Missing required environment variables: {missing}")
        return False
    return True

# --- Existing Utility Functions (Extended) ---

def calculate_vif(df: pd.DataFrame, exclude_intercept: bool = True) -> pd.Series:
    """
    Calculates Variance Inflation Factor (VIF) for each feature in a DataFrame.

    Args:
        df: DataFrame containing numeric features.
        exclude_intercept: If True, excludes the first column (often intercept) from calculation.

    Returns:
        A Series with feature names as index and VIF values.
    """
    if exclude_intercept and df.shape[1] > 1:
        # Drop first column if it looks like an intercept or index
        # Assuming standard behavior where first col might be index or intercept
        # For robustness, we select numeric columns only
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] != df.shape[1]:
            logger = get_logger()
            logger.warning("Non-numeric columns detected and excluded from VIF calculation.")
        df = numeric_df

    vif_data = pd.Series(
        [variance_inflation_factor(df.values, i) for i in range(df.shape[1])],
        index=df.columns
    )
    return vif_data

def calculate_flesch_kincaid(text: str) -> float:
    """
    Calculates the Flesch-Kincaid Grade Level for a given text.

    Args:
        text: The input text string.

    Returns:
        The Flesch-Kincaid Grade Level score.
    """
    if not text or not isinstance(text, str):
        return 0.0
    try:
        # textstat returns grade level
        return textstat.flesch_kincaid_grade(text)
    except Exception as e:
        logger = get_logger()
        logger.warning(f"Error calculating Flesch-Kincaid: {e}")
        return 0.0

def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """
    Calculates Jaccard similarity between two texts based on word sets.

    Args:
        text1: First text string.
        text2: Second text string.

    Returns:
        Jaccard similarity coefficient (0.0 to 1.0).
    """
    if not text1 or not text2:
        return 0.0

    def tokenize(text: str) -> set:
        # Simple tokenization: lowercase and split by non-alphanumeric
        return set(re.findall(r'\w+', text.lower()))

    set1 = tokenize(text1)
    set2 = tokenize(text2)

    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0

    intersection = set1.intersection(set2)
    union = set1.union(set2)

    return len(intersection) / len(union) if union else 0.0

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Calculates semantic similarity using TF-IDF and cosine similarity.
    Note: For production, consider lightweight embeddings if dependencies allow.
    Here we use a lightweight CPU-safe approach with sklearn.

    Args:
        text1: First text string.
        text2: Second text string.

    Returns:
        Cosine similarity score (0.0 to 1.0).
    """
    if not text1 or not text2:
        return 0.0

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    try:
        vectorizer = TfidfVectorizer()
        tfidf = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])
        return float(similarity[0][0])
    except Exception as e:
        logger = get_logger()
        logger.warning(f"Error calculating semantic similarity: {e}")
        return 0.0

def check_vif_threshold(vif_series: pd.Series, threshold: float = 5.0) -> List[str]:
    """
    Checks which features exceed the VIF threshold.

    Args:
        vif_series: Series of VIF values.
        threshold: The threshold value (default 5.0).

    Returns:
        List of feature names exceeding the threshold.
    """
    return [col for col, val in vif_series.items() if val > threshold]

def validate_readiness_for_tier_generation(
    source_text: str,
    simple_text: str,
    complex_text: str,
    fk_simple: float,
    fk_complex: float,
    fk_moderate: float,
    jaccard_min: float = 0.85,
    fk_diff_min: float = 5.0
) -> Dict[str, Any]:
    """
    Validates that generated tiers meet the required criteria for tier generation.

    Args:
        source_text: Original instructional unit.
        simple_text: Generated simple tier.
        complex_text: Generated complex tier.
        fk_simple: Flesch-Kincaid score for simple tier.
        fk_complex: Flesch-Kincaid score for complex tier.
        fk_moderate: Flesch-Kincaid score for moderate tier.
        jaccard_min: Minimum Jaccard similarity required.
        fk_diff_min: Minimum Flesch-Kincaid difference required between tiers.

    Returns:
        Dictionary with validation status and details.
    """
    logger = get_logger()
    result = {
        "is_valid": True,
        "issues": []
    }

    # Check monotonic progression
    if not (fk_simple < fk_moderate < fk_complex):
        result["is_valid"] = False
        result["issues"].append(f"Flesch-Kincaid scores not monotonic: {fk_simple} < {fk_moderate} < {fk_complex}")

    # Check differences
    if (fk_moderate - fk_simple) < fk_diff_min:
        result["is_valid"] = False
        result["issues"].append(f"Simple-Moderate diff ({fk_moderate - fk_simple:.2f}) < {fk_diff_min}")

    if (fk_complex - fk_moderate) < fk_diff_min:
        result["is_valid"] = False
        result["issues"].append(f"Moderate-Complex diff ({fk_complex - fk_moderate:.2f}) < {fk_diff_min}")

    # Check Jaccard (assuming we calculate it against source)
    j_simple = calculate_jaccard_similarity(source_text, simple_text)
    j_complex = calculate_jaccard_similarity(source_text, complex_text)

    if j_simple < jaccard_min:
        result["is_valid"] = False
        result["issues"].append(f"Simple tier Jaccard ({j_simple:.2f}) < {jaccard_min}")

    if j_complex < jaccard_min:
        result["is_valid"] = False
        result["issues"].append(f"Complex tier Jaccard ({j_complex:.2f}) < {jaccard_min}")

    if result["is_valid"]:
        logger.info("Tier generation validation passed.")
    else:
        logger.warning(f"Tier generation validation failed: {result['issues']}")

    return result

def validate_fidelity_scores(
    source_text: str,
    generated_text: str,
    jaccard_threshold: float = 0.85,
    semantic_threshold: float = 0.90
) -> Dict[str, bool]:
    """
    Validates fidelity of a generated text against a source.

    Args:
        source_text: Source text.
        generated_text: Generated text.
        jaccard_threshold: Minimum Jaccard similarity.
        semantic_threshold: Minimum semantic similarity.

    Returns:
        Dictionary with validation results.
    """
    jaccard = calculate_jaccard_similarity(source_text, generated_text)
    semantic = calculate_semantic_similarity(source_text, generated_text)

    return {
        "jaccard_passed": jaccard >= jaccard_threshold,
        "semantic_passed": semantic >= semantic_threshold,
        "jaccard_score": jaccard,
        "semantic_score": semantic
    }