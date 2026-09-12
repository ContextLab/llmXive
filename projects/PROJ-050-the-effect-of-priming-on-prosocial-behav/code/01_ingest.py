import logging
import sys
import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
import numpy as np

# Local imports based on API surface
from code.config import TARGET_N, PROJECT_ROOT, RAW_DATA_DIR, PROCESSED_DATA_DIR
from code.utils.logger import setup_logger, log_negation_exclusion, log_abort_condition, get_logger
from code.utils.schema_validator import validate_dataset_schema

# Constants for classification
PRIME_KEYWORDS = [
    "help", "support", "charity", "donate", "volunteer", "kindness", 
    "altruism", "cooperate", "share", "care", "comfort", "assist",
    "empathy", "sympathy", "compassion", "generous", "give", "contribute"
]

# FR-002c: Confidence score feature constants
CONFIDENCE_WINDOW_SIZE = 5
CONFIDENCE_THRESHOLD = 0.6
CPU_TIME_LIMIT_SECONDS = 180  # 3 minutes for feasibility check

def load_sample_for_feasibility(n_samples: int = 1000) -> pd.DataFrame:
    """
    Loads a small sample of data for feasibility testing.
    In a real run, this would fetch from the real source.
    For this task, we assume the data exists from T015/T016 or T014 logic.
    We attempt to load from the processed directory if available, 
    otherwise we raise an error to force real data usage.
    """
    # Try to load existing processed data if T017/T016a ran
    sample_path = PROCESSED_DATA_DIR / "anonymized.csv"
    if sample_path.exists():
        df = pd.read_csv(sample_path)
        return df.head(n_samples)
    
    # If no real data exists, we cannot fake it. 
    # The feasibility check requires real data structure to be meaningful.
    # However, to demonstrate the logic without a full fetch, we will
    # attempt to load a small chunk from the raw source if it exists,
    # or raise a specific error indicating real data is needed.
    raise FileNotFoundError(
        "Real data file 'data/processed/anonymized.csv' not found. "
        "Feasibility check requires real data structure. "
        "Please run T014/T015/T016 first to generate real data."
    )

def compute_lexical_confidence_score(text: str, keyword: str) -> float:
    """
    Computes a lightweight lexical confidence score for a keyword in text.
    This is the candidate implementation for FR-002c.
    
    Logic:
    1. Tokenize text (simple split for speed in feasibility check).
    2. Check for negation window before the keyword.
    3. Check for contextual reinforcement (e.g., "really", "very").
    
    Returns a score between 0.0 and 1.0.
    """
    words = text.lower().split()
    if keyword not in words:
        return 0.0
    
    idx = words.index(keyword)
    window_start = max(0, idx - CONFIDENCE_WINDOW_SIZE)
    window_end = min(len(words), idx + CONFIDENCE_WINDOW_SIZE)
    context = words[window_start:window_end]
    
    # Negation check (simple heuristic)
    negations = ["not", "no", "never", "none", "neither", "hardly"]
    negation_present = any(n in context[:idx - window_start + 1] for n in negations)
    
    # Reinforcement check
    reinforcements = ["really", "very", "truly", "definitely", "absolutely", "certainly"]
    reinforcement_present = any(r in context for r in reinforcements)
    
    score = 1.0
    if negation_present:
        score -= 0.8
    if reinforcement_present:
        score += 0.2
    
    return max(0.0, min(1.0, score))

def check_cpu_feasibility() -> Dict[str, Any]:
    """
    Determines CPU feasibility for FR-002c (confidence score).
    
    This function:
    1. Loads a sample of real data.
    2. Attempts to compute confidence scores for all keywords in the sample.
    3. Measures elapsed time.
    4. If time > CPU_TIME_LIMIT_SECONDS, logs "FR-002c Deferred" and returns failure.
    5. If time < limit, logs success and returns feasibility.
    
    Returns a dictionary with feasibility status and metrics.
    """
    logger = get_logger()
    logger.info("Starting CPU feasibility check for FR-002c (Confidence Score).")
    
    try:
        # Load sample (1000 rows for quick check)
        sample_df = load_sample_for_feasibility(n_samples=1000)
        logger.info(f"Loaded {len(sample_df)} rows for feasibility test.")
        
        if 'text' not in sample_df.columns:
            # Fallback for column name variations
            if 'comment_text' in sample_df.columns:
                text_col = 'comment_text'
            else:
                raise KeyError("No 'text' or 'comment_text' column found in data.")
        else:
            text_col = 'text'
        
        start_time = time.time()
        
        # Compute scores for a subset of keywords to estimate load
        test_keywords = PRIME_KEYWORDS[:3] # Test first 3 keywords
        
        total_scores = []
        for _, row in sample_df.iterrows():
            text = row[text_col]
            row_scores = []
            for kw in test_keywords:
                score = compute_lexical_confidence_score(str(text), kw)
                row_scores.append(score)
            total_scores.append(row_scores)
        
        elapsed_time = time.time() - start_time
        
        # Extrapolate to full dataset (TARGET_N = 10,000)
        # Assuming linear scaling for this simple logic
        estimated_full_time = elapsed_time * (TARGET_N / len(sample_df))
        
        logger.info(f"Sample processing time: {elapsed_time:.2f}s")
        logger.info(f"Estimated full dataset time: {estimated_full_time:.2f}s")
        
        if estimated_full_time > CPU_TIME_LIMIT_SECONDS:
            msg = f"FR-002c Deferred: Estimated time {estimated_full_time:.2f}s exceeds limit {CPU_TIME_LIMIT_SECONDS}s."
            log_abort_condition(msg)
            logger.warning(msg)
            return {
                "feasible": False,
                "reason": "Time limit exceeded",
                "estimated_time": estimated_full_time,
                "limit": CPU_TIME_LIMIT_SECONDS,
                "status": "FR-002c Deferred"
            }
        else:
            msg = f"FR-002c Feasible: Estimated time {estimated_full_time:.2f}s is within limit."
            logger.info(msg)
            return {
                "feasible": True,
                "reason": "Within time limits",
                "estimated_time": estimated_full_time,
                "limit": CPU_TIME_LIMIT_SECONDS,
                "status": "FR-002c Feasible"
            }
            
    except FileNotFoundError as e:
        # If real data is missing, we cannot check feasibility accurately.
        # We must fail loudly rather than fake a result.
        logger.error(f"Feasibility check failed: {e}")
        raise e
    except Exception as e:
        logger.error(f"Feasibility check failed with unexpected error: {e}")
        raise e

def verify_source_availability() -> bool:
    """Verifies the pushshift/reddit source is available."""
    # Placeholder for actual source check (e.g., ping API)
    # For this task, we assume the environment is set up as per T014
    return True

def verify_subreddit_presence(subreddits: List[str]) -> bool:
    """Verifies presence of target subreddits."""
    required = ["r/AskReddit", "r/relationships", "r/socialscience", "r/psychology", "r/dataisbeautiful"]
    # Check intersection
    return all(r in subreddits for r in required)

def fetch_reddit_data() -> pd.DataFrame:
    """Fetches data from pushshift/reddit."""
    # Implementation of T015 logic would go here
    # For T015b, we assume this is handled by the main flow
    raise NotImplementedError("Data fetching is handled in the main flow, not feasibility check.")

def classify_comments(df: pd.DataFrame) -> pd.DataFrame:
    """Classifies comments into Prime/Control groups."""
    # Implementation of T016 logic
    raise NotImplementedError("Classification is handled in the main flow.")

def anonymize_data(df: pd.DataFrame) -> pd.DataFrame:
    """Anonymizes data using SHA-256."""
    # Implementation of T016a logic
    raise NotImplementedError("Anonymization is handled in the main flow.")

def check_power_analysis() -> bool:
    """Checks if power analysis (T013) was successful."""
    # Placeholder
    return True

def validate_and_save(df: pd.DataFrame, output_path: Path) -> bool:
    """Validates and saves the processed data."""
    # Placeholder
    return True

def main():
    """
    Main entry point for T015b: Feasibility Check for FR-002c.
    This script runs the CPU feasibility check and logs the result.
    """
    logger = setup_logger("ingest_feasibility")
    logger.info("=== Starting T015b: Feasibility Check for FR-002c ===")
    
    try:
        result = check_cpu_feasibility()
        
        # Log the final decision explicitly as required by the task
        if result["feasible"]:
            logger.info("RESULT: FR-002c is FEASIBLE. Implementation can proceed.")
        else:
            logger.info("RESULT: FR-002c is NOT FEASIBLE. Feature deferred.")
            logger.warning("FR-002c Deferred")
        
        # Save result to a JSON file for audit trail
        result_path = PROCESSED_DATA_DIR / "feasibility_check_result.json"
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Feasibility result saved to {result_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Cannot perform feasibility check: {e}")
        logger.error("Real data is required. Please ensure T014/T015/T016 have run.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Feasibility check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()