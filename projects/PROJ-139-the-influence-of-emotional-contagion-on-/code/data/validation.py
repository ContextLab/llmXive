"""
Validation module for ground truth classification and external validation scoring.
Handles thread classification, ground truth availability checks, and ambiguity detection.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
GROUND_TRUTH_VALID = 'valid'
GROUND_TRUTH_NO_GT = 'valid_no_gt'
AMBIGUOUS_GT = 'ambiguous'
INVALID_GT = 'invalid'

def load_processed_data(data_path: str) -> pd.DataFrame:
    """Load processed thread data from CSV."""
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    return pd.read_csv(path)

def classify_thread(thread: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """
    Classify a thread based on ground truth availability.
    
    Returns:
        Tuple of (classification_status, reason)
        - 'valid': Ground truth exists (Stack Exchange accepted answer)
        - 'valid_no_gt': Valid thread but no external ground truth (Reddit)
        - 'ambiguous': Multiple accepted answers (Stack Exchange)
        - 'invalid': No decision point or malformed data
    """
    platform = thread.get('platform', '').lower()
    
    if platform == 'stackexchange':
        accepted_answers = thread.get('accepted_answer_id', None)
        
        # Handle multiple accepted answers (ambiguous case)
        if accepted_answers is not None:
            if isinstance(accepted_answers, list):
                if len(accepted_answers) > 1:
                    return (AMBIGUOUS_GT, 'multiple_accepted_answers')
                elif len(accepted_answers) == 1:
                    return (GROUND_TRUTH_VALID, 'accepted_answer_exists')
            elif isinstance(accepted_answers, str):
                # Single string is valid
                return (GROUND_TRUTH_VALID, 'accepted_answer_exists')
            else:
                return (INVALID_GT, 'malformed_accepted_answer')
        else:
            return (INVALID_GT, 'no_accepted_answer')
    
    elif platform == 'reddit':
        # Reddit threads are valid but have no external ground truth
        return (GROUND_TRUTH_NO_GT, 'reddit_no_external_gt')
    
    else:
        return (INVALID_GT, 'unknown_platform')

def validate_and_classify(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply classification to all threads in the dataframe.
    
    Args:
        df: DataFrame with thread data (must have 'platform' column)
        
    Returns:
        DataFrame with added 'classification' and 'classification_reason' columns
    """
    results = []
    ambiguous_threads = []
    
    for idx, row in df.iterrows():
        thread_dict = row.to_dict()
        status, reason = classify_thread(thread_dict)
        
        results.append({
            'thread_id': row.get('thread_id'),
            'classification': status,
            'classification_reason': reason
        })
        
        if status == AMBIGUOUS_GT:
            ambiguous_threads.append({
                'thread_id': row.get('thread_id'),
                'platform': row.get('platform'),
                'accepted_answer_id': row.get('accepted_answer_id'),
                'reason': reason
            })
    
    # Create classification dataframe
    classification_df = pd.DataFrame(results)
    merged_df = df.merge(classification_df, on='thread_id', how='left')
    
    # Log ambiguous threads
    if ambiguous_threads:
        logger.warning(f"Found {len(ambiguous_threads)} threads with ambiguous ground truth")
        # Log to file
        ambiguous_log_path = Path('data/processed/ambiguous_ground_truth.log')
        ambiguous_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(ambiguous_log_path, 'w') as f:
            for thread in ambiguous_threads:
                f.write(json.dumps(thread) + '\n')
        logger.info(f"Logged ambiguous threads to {ambiguous_log_path}")
    
    return merged_df

def save_validated_dataset(df: pd.DataFrame, output_path: str):
    """Save validated dataset to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved validated dataset to {output_path}")

def save_exclusions_log(ambiguous_threads: List[Dict], output_path: str):
    """Save ambiguous ground truth threads to log file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        for thread in ambiguous_threads:
            f.write(json.dumps(thread) + '\n')
    logger.info(f"Saved {len(ambiguous_threads)} ambiguous threads to {output_path}")

def check_valid_thread_threshold(df: pd.DataFrame, threshold: float = 0.30) -> Dict[str, Any]:
    """
    Check if valid threads meet the minimum threshold.
    
    Args:
        df: DataFrame with 'classification' column
        threshold: Minimum fraction of valid threads required (default 0.30)
        
    Returns:
        Dictionary with statistics and compliance status
    """
    total_count = len(df)
    if total_count == 0:
        return {
            'total_dataset_count': 0,
            'valid_dataset_count': 0,
            'valid_thread_percentage': 0.0,
            'status': 'fail',
            'message': 'No threads in dataset'
        }
    
    valid_count = len(df[df['classification'] == GROUND_TRUTH_VALID])
    valid_percentage = (valid_count / total_count) * 100
    
    status = 'pass' if valid_percentage >= (threshold * 100) else 'fail'
    
    return {
        'total_dataset_count': total_count,
        'valid_dataset_count': valid_count,
        'valid_thread_percentage': valid_percentage,
        'threshold': threshold * 100,
        'status': status,
        'message': f'Valid threads: {valid_percentage:.2f}% (threshold: {threshold*100:.2f}%)'
    }

def generate_validity_status_report(df: pd.DataFrame, output_path: str):
    """Generate a JSON report of ground truth statistics."""
    stats = check_valid_thread_threshold(df)
    
    # Add breakdown by classification
    classification_counts = df['classification'].value_counts().to_dict()
    stats['classification_breakdown'] = classification_counts
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Generated validity status report: {output_path}")
    return stats

def compute_external_validation_score(thread: Dict[str, Any]) -> Tuple[Optional[float], Optional[str]]:
    """
    Compute external validation score for a single thread.
    
    For Stack Exchange: 1.0 if accepted answer exists, 0.0 otherwise
    For Reddit: Based on upvote/downvote ratio, or null if missing/inconclusive
    
    Returns:
        Tuple of (score, reason)
    """
    platform = thread.get('platform', '').lower()
    
    if platform == 'stackexchange':
        if thread.get('accepted_answer_id'):
            return (1.0, 'accepted_answer')
        else:
            return (0.0, 'no_accepted_answer')
    
    elif platform == 'reddit':
        upvotes = thread.get('upvotes')
        downvotes = thread.get('downvotes')
        
        if upvotes is None or downvotes is None:
            return (None, 'missing_vote_data')
        
        if upvotes == downvotes:
            return (None, 'inconclusive_tie')
        
        # Simple binary: more upvotes than downvotes = valid consensus
        score = 1.0 if upvotes > downvotes else 0.0
        return (score, 'vote_majority')
    
    else:
        return (None, 'unknown_platform')

def run_validation_pipeline(input_path: str, 
                            output_all_path: str, 
                            output_valid_path: str,
                            stats_output_path: str):
    """
    Run the complete validation pipeline.
    
    Args:
        input_path: Path to input CSV with thread data
        output_all_path: Path to output CSV with all classified threads
        output_valid_path: Path to output CSV with only valid threads
        stats_output_path: Path to output JSON with ground truth statistics
    """
    logger.info(f"Loading data from {input_path}")
    df = load_processed_data(input_path)
    
    logger.info("Classifying threads")
    df_classified = validate_and_classify(df)
    
    # Save all classified threads
    save_validated_dataset(df_classified, output_all_path)
    
    # Filter and save valid threads
    valid_df = df_classified[df_classified['classification'] == GROUND_TRUTH_VALID].copy()
    if len(valid_df) > 0:
        save_validated_dataset(valid_df, output_valid_path)
        logger.info(f"Saved {len(valid_df)} valid threads to {output_valid_path}")
    else:
        # Create empty file with headers
        Path(output_valid_path).parent.mkdir(parents=True, exist_ok=True)
        valid_df.to_csv(output_valid_path, index=False)
        logger.warning(f"No valid threads found, created empty file at {output_valid_path}")
    
    # Generate statistics
    logger.info("Generating ground truth statistics")
    stats = generate_validity_status_report(df_classified, stats_output_path)
    
    # Compute external validation scores for all threads
    logger.info("Computing external validation scores")
    validation_results = []
    for idx, row in df_classified.iterrows():
        thread_dict = row.to_dict()
        score, reason = compute_external_validation_score(thread_dict)
        validation_results.append({
            'thread_id': row.get('thread_id'),
            'external_validation_score': score,
            'validation_reason': reason
        })
    
    validation_df = pd.DataFrame(validation_results)
    df_classified = df_classified.merge(validation_df, on='thread_id', how='left')
    
    # Update output files with validation scores
    save_validated_dataset(df_classified, output_all_path)
    if len(valid_df) > 0:
        valid_df_with_scores = df_classified[df_classified['classification'] == GROUND_TRUTH_VALID].copy()
        save_validated_dataset(valid_df_with_scores, output_valid_path)
    
    logger.info(f"Validation pipeline complete. Stats: {stats['message']}")
    return df_classified, stats

def main():
    """Main entry point for validation pipeline."""
    # Default paths
    input_path = 'data/processed/threads_with_seeds.csv'
    output_all_path = 'data/processed/all_threads_classified.csv'
    output_valid_path = 'data/processed/valid_threads.csv'
    stats_output_path = 'data/processed/ground_truth_stats.json'
    
    # Check if input exists
    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run data extraction first (T009)")
        return 1
    
    try:
        df, stats = run_validation_pipeline(
            input_path=input_path,
            output_all_path=output_all_path,
            output_valid_path=output_valid_path,
            stats_output_path=stats_output_path
        )
        
        # Check threshold compliance
        if stats['status'] == 'fail':
            logger.warning(f"Ground truth threshold not met: {stats['message']}")
            # Note: We log but don't raise error here to allow pipeline to continue
            # The final validation task will check this
        
        return 0
        
    except Exception as e:
        logger.error(f"Validation pipeline failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
