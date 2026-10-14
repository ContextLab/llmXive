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
import hashlib
import yaml
from llmxive_toolkit import paths
from pathlib import Path

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

def compute_checksums(raw_dir: Optional[Path] = None) -> Dict[str, str]:
    """
    Compute SHA-256 checksums for all files under the raw data directory.

    The function writes a manifest file ``checksums.sha256`` in the same
    directory, containing lines of the form:

        <checksum>  <relative_path>

    It also records the manifest in a project‑level YAML file
    ``project_state.yaml`` under the top‑level key ``artifact_hashes``.

    Returns:
        A dictionary mapping relative file paths (POSIX style) to their
        SHA-256 checksum strings.
    """
    logger = get_logger(__name__)

    # Determine the raw data directory; default to the project convention.
    if raw_dir is None:
        raw_dir = paths.data("raw")
    else:
        raw_dir = Path(raw_dir)

    if not raw_dir.is_dir():
        logger.error(f"Raw data directory does not exist: {raw_dir}")
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    checksum_dict: Dict[str, str] = {}
    manifest_lines: List[str] = []

    # Walk the directory (non‑recursive as per spec – only direct children)
    for entry in raw_dir.iterdir():
        if entry.is_file():
            rel_path = entry.relative_to(raw_dir).as_posix()
            # Compute SHA‑256
            hasher = hashlib.sha256()
            with entry.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            checksum = hasher.hexdigest()
            checksum_dict[rel_path] = checksum
            manifest_lines.append(f"{checksum}  {rel_path}")

    # Write the manifest file
    manifest_path = raw_dir / "checksums.sha256"
    with manifest_path.open("w", encoding="utf-8") as mf:
        mf.write("\n".join(manifest_lines) + ("\n" if manifest_lines else ""))

    logger.info(f"Wrote checksum manifest to {manifest_path}")

    # Record in project state YAML
    state_path = Path("project_state.yaml")
    state_data = {}
    if state_path.exists():
        try:
            with state_path.open("r", encoding="utf-8") as sf:
                state_data = yaml.safe_load(sf) or {}
        except Exception as e:
            logger.warning(f"Failed to read existing state file: {e}")

    state_data["artifact_hashes"] = checksum_dict
    with state_path.open("w", encoding="utf-8") as sf:
        yaml.safe_dump(state_data, sf, sort_keys=False)

    logger.info(f"Updated project state manifest at {state_path}")

    return checksum_dict

__all__ = [
    "setup_logging",
    "get_logger",
    "load_config_env",
    "validate_environment",
    "calculate_vif",
    "check_vif_threshold",
    "calculate_flesch_kincaid",
    "calculate_jaccard_similarity",
    "calculate_semantic_similarity",
    "validate_fidelity_scores",
    "validate_readiness_for_tier_generation",
    "compute_checksums",
]
