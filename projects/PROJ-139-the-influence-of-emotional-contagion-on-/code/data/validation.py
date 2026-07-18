import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

from config.settings import get_config, DatasetPaths

# Configure logging
logger = logging.getLogger(__name__)

def load_processed_data() -> pd.DataFrame:
    """
    Load the validated dataset from data/processed/valid_threads.csv.
    This file is expected to be created by T019 (validate_and_classify).
    """
    config = get_config()
    path = config.paths.processed / "valid_threads.csv"
    
    if not path.exists():
        raise FileNotFoundError(
            f"Expected file {path} not found. "
            "Please run T019 (validate_and_classify) first to generate valid_threads.csv."
        )
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} valid threads from {path}")
    return df

def classify_thread(thread: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """
    Classify a single thread as 'valid' or 'excluded' based on ground truth availability.
    
    Logic:
    - Stack Exchange: 'valid' if 'accepted_answer_id' exists.
    - Reddit: 'valid' if 'best_answer' heuristic detected (highest upvoted reply with keywords).
    
    Returns:
        Tuple of (status, reason_code)
    """
    source = thread.get('source', '').lower()
    
    if source == 'stackexchange':
        if thread.get('accepted_answer_id') is not None:
            return 'valid', None
        else:
            return 'excluded', 'NO_ACCEPTED_ANSWER'
    
    elif source == 'reddit':
        # Heuristic: Check if the highest upvoted reply has specific keywords indicating a solution
        replies = thread.get('replies', [])
        if not replies:
            return 'excluded', 'NO_REPLIES'
        
        # Sort by upvotes
        sorted_replies = sorted(replies, key=lambda x: x.get('upvotes', 0), reverse=True)
        top_reply = sorted_replies[0]
        top_text = (top_reply.get('body', '') or '').lower()
        
        # Keywords indicating a "best answer" or solution
        solution_keywords = [
            'solution', 'answer', 'resolved', 'fixed', 'solved', 
            'thanks', 'worked', 'correct', 'accepted'
        ]
        
        if any(keyword in top_text for keyword in solution_keywords):
            return 'valid', None
        else:
            return 'excluded', 'NO_BEST_ANSWER_HEURISTIC'
    
    else:
        return 'excluded', 'UNKNOWN_SOURCE'

def validate_and_classify(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply classification logic to the entire dataframe.
    
    Returns:
        DataFrame with 'status' and 'reason_code' columns added.
    """
    def apply_class(row):
        status, reason = classify_thread(row.to_dict())
        return pd.Series({'status': status, 'reason_code': reason})
    
    validation_results = df.apply(apply_class, axis=1)
    df = pd.concat([df, validation_results], axis=1)
    
    valid_count = len(df[df['status'] == 'valid'])
    total_count = len(df)
    logger.info(f"Classification complete: {valid_count}/{total_count} threads are valid.")
    
    return df

def save_validated_dataset(df: pd.DataFrame, output_path: Path):
    """
    Save the valid threads to CSV.
    """
    valid_df = df[df['status'] == 'valid'].copy()
    # Drop helper columns if needed, but keep for now for debugging
    valid_df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(valid_df)} valid threads to {output_path}")

def save_exclusions_log(df: pd.DataFrame, output_path: Path):
    """
    Save excluded threads to a log file (CSV format for easy parsing).
    """
    excluded_df = df[df['status'] == 'excluded'].copy()
    excluded_df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(excluded_df)} excluded threads to {output_path}")

def check_valid_thread_threshold(df: pd.DataFrame, threshold: float = 0.30) -> Tuple[bool, float]:
    """
    Check if the percentage of valid threads meets the threshold.
    
    Returns:
        Tuple of (pass_status, percentage)
    """
    valid_count = len(df[df['status'] == 'valid'])
    total_count = len(df)
    
    if total_count == 0:
        return False, 0.0
    
    percentage = valid_count / total_count
    return percentage >= threshold, percentage

def generate_validity_status_report(df: pd.DataFrame, output_path: Path, threshold: float = 0.30):
    """
    Generate a JSON report on the validity status of the dataset.
    """
    passed, percentage = check_valid_thread_threshold(df, threshold)
    
    report = {
        "valid_thread_percentage": round(percentage, 4),
        "threshold": threshold,
        "status": "pass" if passed else "fail",
        "valid_count": int(len(df[df['status'] == 'valid'])),
        "total_count": int(len(df))
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validity status report saved to {output_path}: {report['status']}")
    return report

def compute_external_validation_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the external validation score (accuracy of consensus vs. ground truth) for valid threads.
    
    Logic:
    - For valid threads (those with ground truth), we compare the 'consensus' outcome
      (e.g., majority sentiment or decision) against the 'ground truth' label.
    - Since we don't have explicit human consensus labels in the raw data yet, 
      we simulate the 'consensus' as the majority sentiment of the top 5 replies.
    - Ground Truth is derived from the 'accepted_answer_id' (SE) or 'best_answer' heuristic (Reddit).
      We map these to a binary label: 1 (Positive/Resolved), 0 (Neutral/Negative/Unresolved).
    
    Mapping:
    - Stack Exchange: accepted_answer_id exists -> Ground Truth = 1. 
      Consensus: If majority of top 5 replies are positive (compound > 0.1), Consensus = 1.
    - Reddit: best_answer heuristic -> Ground Truth = 1.
      Consensus: If majority of top 5 replies are positive, Consensus = 1.
    
    Returns:
        DataFrame with 'external_validation_score' column added (0 or 1 for each thread).
    """
    # Ensure we only process valid threads
    valid_df = df[df['status'] == 'valid'].copy()
    
    if valid_df.empty:
        logger.warning("No valid threads found to compute external validation score.")
        df['external_validation_score'] = np.nan
        return df

    def calculate_score(row):
        source = row.get('source', '').lower()
        replies = row.get('replies', [])
        
        if not replies:
            return np.nan # Cannot compute consensus without replies
        
        # Determine Ground Truth (GT)
        # 1 if ground truth exists and is positive/resolved, 0 otherwise
        # Based on T019 logic: valid implies GT exists.
        # We assume valid threads have a "positive" resolution by definition of having an answer.
        ground_truth = 1 
        
        # Determine Consensus
        # Take top 5 replies (or all if < 5)
        top_replies = replies[:5]
        positive_count = 0
        
        # We need sentiment scores for replies. 
        # Assumption: T013 (sentiment.py) has run and added 'compound' scores to replies?
        # If not, we must compute them here or assume they are present.
        # For robustness, let's assume replies might not have sentiment yet if this runs before T013.
        # However, the task T019a depends on T019, and T013 is US2. 
        # The prompt says T019a depends on T019. It does NOT explicitly say it depends on T013.
        # BUT, to compute consensus, we need sentiment. 
        # If T013 hasn't run, we might need to compute VADER scores here temporarily 
        # or assume the data model includes them.
        # Let's implement a fallback: if 'compound' is missing in replies, compute it.
        
        try:
            from nltk.sentiment import SentimentIntensityAnalyzer
            sia = SentimentIntensityAnalyzer()
        except ImportError:
            raise ImportError("NLTK is required for external validation score calculation. Install with: pip install nltk")

        for reply in top_replies:
            text = reply.get('body', '') or ''
            if not text:
                continue
            
            # Check if sentiment is already present
            if 'compound' in reply:
                score = reply['compound']
            else:
                # Compute on the fly if missing (fallback for pipeline order)
                score = sia.polarity_scores(text)['compound']
            
            if score > 0.1: # Threshold for positive sentiment
                positive_count += 1
        
        consensus = 1 if (positive_count / len(top_replies)) > 0.5 else 0
        
        # Accuracy: 1 if Consensus == Ground Truth, else 0
        return 1 if consensus == ground_truth else 0

    valid_df['external_validation_score'] = valid_df.apply(calculate_score, axis=1)
    
    # Merge back to original df
    # Create a series with index from valid_df
    score_series = valid_df['external_validation_score']
    
    # Initialize the column in the main df with NaN
    df['external_validation_score'] = np.nan
    df.loc[score_series.index, 'external_validation_score'] = score_series.values
    
    logger.info(f"Computed external validation scores for {len(valid_df)} valid threads.")
    return df

def run_validation_pipeline():
    """
    Main entry point for T019a.
    1. Load valid_threads.csv (from T019).
    2. Compute external validation score.
    3. Append score to valid_threads.csv.
    4. Save updated file.
    """
    config = get_config()
    input_path = config.paths.processed / "valid_threads.csv"
    output_path = config.paths.processed / "valid_threads.csv" # Overwrite or create new? Task says "Append".
    # To be safe and idempotent, we read, process, and write back to the same path 
    # or a new path if we want to preserve the intermediate state. 
    # The task says "Append ... to data/processed/valid_threads.csv".
    # We will read, update, and write back.
    
    logger.info("Starting T019a: External Validation Score Computation")
    
    df = load_processed_data()
    df = compute_external_validation_score(df)
    
    # Save the updated file
    df.to_csv(output_path, index=False)
    logger.info(f"Updated {output_path} with external_validation_score")
    
    # Optional: Generate a summary report
    summary = {
        "threads_computed": int(df['external_validation_score'].notna().sum()),
        "accuracy": float(df['external_validation_score'].mean()) if not df.empty else 0.0
    }
    
    report_path = config.paths.processed / "external_validation_summary.json"
    with open(report_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Summary saved to {report_path}")
    return df

def main():
    run_validation_pipeline()

if __name__ == "__main__":
    main()
