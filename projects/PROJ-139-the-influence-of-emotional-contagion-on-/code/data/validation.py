import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

def load_processed_data(input_path: str) -> pd.DataFrame:
    """Load the processed threads CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_csv(input_path)

def classify_thread(thread: Dict[str, Any]) -> str:
    """
    Classify a thread based on ground truth availability.
    Returns: 'valid' (has GT), 'valid_no_gt' (Reddit), 'invalid' (excluded).
    """
    platform = thread.get('platform', '').lower()
    
    if platform == 'stackexchange':
        if thread.get('accepted_answer_id') is not None:
            return 'valid'
        else:
            return 'invalid' # No GT for StackExchange without accepted answer
    elif platform == 'reddit':
        # Reddit threads are valid for dataset inclusion but have no external GT
        return 'valid_no_gt'
    else:
        return 'invalid'

def validate_and_classify(df: pd.DataFrame) -> pd.DataFrame:
    """Apply classification to the dataframe."""
    df['classification'] = df.apply(classify_thread, axis=1)
    return df

def save_validated_dataset(df: pd.DataFrame, output_path: str):
    """Save the validated dataset."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved validated dataset to {output_path}")

def save_exclusions_log(exclusions: List[Dict], log_path: str):
    """Save the exclusions log."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w') as f:
        for exc in exclusions:
            f.write(json.dumps(exc) + '\n')
    logger.info(f"Saved exclusions log to {log_path}")

def check_valid_thread_threshold(valid_count: int, total_count: int, threshold: float = 30.0) -> bool:
    """Check if valid threads meet the percentage threshold."""
    if total_count == 0:
        return False
    percentage = (valid_count / total_count) * 100
    return percentage >= threshold

def generate_validity_status_report(df: pd.DataFrame, output_path: str):
    """Generate a JSON report on validity status."""
    total = len(df)
    valid_count = len(df[df['classification'] == 'valid'])
    valid_no_gt_count = len(df[df['classification'] == 'valid_no_gt'])
    invalid_count = len(df[df['classification'] == 'invalid'])
    
    stats = {
        "total_threads": total,
        "valid_count": valid_count,
        "valid_no_gt_count": valid_no_gt_count,
        "invalid_count": invalid_count,
        "valid_percentage": (valid_count / total * 100) if total > 0 else 0,
        "valid_no_gt_percentage": (valid_no_gt_count / total * 100) if total > 0 else 0
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Validity status report saved to {output_path}")

def compute_external_validation_score(thread: Dict[str, Any]) -> Optional[float]:
    """
    Compute the external validation score for a single thread.
    
    Logic:
    - Stack Exchange: Consensus is 'accepted_answer_id' (1 if exists, 0 otherwise).
    - Reddit: Consensus is upvotes > downvotes (1 if true, 0 if false).
      - If upvotes or downvotes are missing, return None.
      - If upvotes == downvotes, return None (Inconclusive).
    
    Returns:
      float: 1.0 (Valid), 0.0 (Invalid), None (Missing/Inconclusive).
    """
    platform = thread.get('platform', '').lower()
    
    if platform == 'stackexchange':
        # For StackExchange, we assume the presence of accepted_answer_id implies validity (1)
        # This is used to validate the consensus mechanism against the GT.
        if thread.get('accepted_answer_id') is not None:
            return 1.0
        else:
            return 0.0
    
    elif platform == 'reddit':
        upvotes = thread.get('upvotes')
        downvotes = thread.get('downvotes')
        
        # Check for missing data
        if upvotes is None or downvotes is None:
            return None
        
        # Check for inconclusive (equal votes)
        if upvotes == downvotes:
            return None
        
        # Determine consensus: upvotes > downvotes
        if upvotes > downvotes:
            return 1.0
        else:
            return 0.0
    
    return None

def run_validation_pipeline(
    input_path: str,
    output_valid_path: str,
    output_all_classified_path: str,
    output_gt_stats_path: str,
    output_compliance_path: str,
    output_missing_votes_log: str
):
    """
    Main pipeline execution for validation and external score computation.
    
    1. Load data.
    2. Classify threads (valid, valid_no_gt, invalid).
    3. Compute external_validation_score for all threads (handling missing votes).
    4. Log missing vote data.
    5. Save outputs.
    6. Generate compliance report.
    """
    logger.info(f"Loading data from {input_path}")
    df = load_processed_data(input_path)
    
    # Classify threads
    logger.info("Classifying threads...")
    df = validate_and_classify(df)
    
    # Initialize external_validation_score column
    df['external_validation_score'] = None
    
    # Track missing vote data for logging
    missing_vote_threads = []
    
    logger.info("Computing external validation scores...")
    for idx, row in df.iterrows():
        score = compute_external_validation_score(row.to_dict())
        
        if score is None:
            # Check if it's due to missing Reddit votes
            if row.get('platform', '').lower() == 'reddit':
                upvotes = row.get('upvotes')
                downvotes = row.get('downvotes')
                if upvotes is None or downvotes is None:
                    missing_vote_threads.append({
                        'thread_id': row.get('thread_id'),
                        'reason': 'Missing upvotes or downvotes',
                        'upvotes': upvotes,
                        'downvotes': downvotes
                    })
            # If None due to inconclusive (equal votes), we just leave it as None, 
            # but we don't log it as "missing data" in the specific log for missing votes.
            # The task specifically asks to log missing upvotes/downvotes.
        
        df.at[idx, 'external_validation_score'] = score
    
    # Log missing vote data
    if missing_vote_threads:
        os.makedirs(os.path.dirname(output_missing_votes_log), exist_ok=True)
        with open(output_missing_votes_log, 'w') as f:
            for item in missing_vote_threads:
                f.write(json.dumps(item) + '\n')
        logger.warning(f"Logged {len(missing_vote_threads)} threads with missing vote data to {output_missing_votes_log}")
    
    # Save all classified threads (including valid_no_gt and invalid)
    save_validated_dataset(df, output_all_classified_path)
    
    # Filter for 'valid' threads only for the valid_threads.csv
    valid_df = df[df['classification'] == 'valid'].copy()
    save_validated_dataset(valid_df, output_valid_path)
    
    # Generate Ground Truth Stats
    total_count = len(df)
    valid_count = len(valid_df)
    valid_percentage = (valid_count / total_count * 100) if total_count > 0 else 0
    
    gt_stats = {
        "total_dataset_count": total_count,
        "valid_dataset_count": valid_count,
        "valid_thread_percentage": valid_percentage
    }
    
    os.makedirs(os.path.dirname(output_gt_stats_path), exist_ok=True)
    with open(output_gt_stats_path, 'w') as f:
        json.dump(gt_stats, f, indent=2)
    logger.info(f"Saved ground truth stats to {output_gt_stats_path}")
    
    # Generate Compliance Report (SC-006)
    is_compliant = valid_percentage >= 30.0
    compliance_report = {
        "sc_006_compliance": is_compliant,
        "status": "pass" if is_compliant else "fail",
        "valid_thread_percentage": valid_percentage,
        "threshold": 30.0
    }
    
    os.makedirs(os.path.dirname(output_compliance_path), exist_ok=True)
    with open(output_compliance_path, 'w') as f:
        json.dump(compliance_report, f, indent=2)
    logger.info(f"Saved compliance report to {output_compliance_path}")
    
    logger.info("Validation pipeline completed successfully.")

def main():
    """Entry point for the validation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run validation pipeline for emotional contagion study.")
    parser.add_argument("--input", type=str, required=True, help="Input CSV path (all_threads_classified.csv)")
    parser.add_argument("--output-valid", type=str, required=True, help="Output path for valid threads CSV")
    parser.add_argument("--output-all", type=str, required=True, help="Output path for all classified threads CSV")
    parser.add_argument("--output-stats", type=str, required=True, help="Output path for ground truth stats JSON")
    parser.add_argument("--output-compliance", type=str, required=True, help="Output path for SC-006 compliance report JSON")
    parser.add_argument("--output-missing-votes", type=str, required=True, help="Output path for missing votes log")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    run_validation_pipeline(
        input_path=args.input,
        output_valid_path=args.output_valid,
        output_all_classified_path=args.output_all,
        output_gt_stats_path=args.output_stats,
        output_compliance_path=args.output_compliance,
        output_missing_votes_log=args.output_missing_votes
    )

if __name__ == "__main__":
    main()
