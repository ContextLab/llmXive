import logging
import sys
import json
import hashlib
import time
from pathlib import Path

# Import from local utils
from code.config import PROJECT_ROOT, TARGET_N, MIN_GROUP_SIZE, MIN_SUBREDDITS
from code.utils.logger import setup_logger, log_negation_exclusion, log_abort_condition
from code.utils.schema_validator import validate_dataset_schema

# Import existing functions from this module (self-reference for main orchestration)
# Note: In a real execution, these would be defined earlier in the file.
# For this task, we assume they exist as per the API surface provided.
# We are implementing the `validate_and_save` and `main` functions which are the focus of T018.

def load_sample_for_feasibility():
    """Placeholder for existing function."""
    pass

def compute_lexical_confidence_score():
    """Placeholder for existing function."""
    pass

def check_cpu_feasibility():
    """Placeholder for existing function."""
    pass

def classify_comments(df):
    """Placeholder for existing function."""
    return df

def verify_source_availability():
    """Placeholder for existing function."""
    return True

def verify_subreddit_presence(df):
    """Placeholder for existing function."""
    return True

def fetch_reddit_data():
    """Placeholder for existing function."""
    return None

def anonymize_data(df):
    """Placeholder for existing function."""
    return df

def check_power_analysis():
    """Placeholder for existing function."""
    return True

def validate_and_save(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """
    T018: Post-fetch validation.
    Ensures at least 4,000 comments per group and >= 3 subreddits remain.
    Aborts if conditions not met.
    
    Args:
        df: The processed DataFrame containing 'thread_type' and 'subreddit'.
        logger: The logger instance.
        
    Returns:
        bool: True if validation passes, False otherwise (triggers abort in main).
    """
    import pandas as pd

    if df is None or df.empty:
        log_abort_condition(logger, "Validation failed: DataFrame is empty or None.")
        return False

    # 1. Validate Group Counts (FR-001)
    # Expecting 'thread_type' column with 'Prime' and 'Control'
    if 'thread_type' not in df.columns:
        log_abort_condition(logger, "Validation failed: 'thread_type' column missing.")
        return False

    group_counts = df['thread_type'].value_counts()
    logger.info(f"Group counts: {group_counts.to_dict()}")

    # Check for both groups
    required_groups = ['Prime', 'Control']
    missing_groups = [g for g in required_groups if g not in group_counts.index]
    
    if missing_groups:
        log_abort_condition(logger, f"Validation failed: Missing required groups: {missing_groups}.")
        return False

    # Check minimum count per group
    for group in required_groups:
        count = group_counts[group]
        if count < MIN_GROUP_SIZE:
            log_abort_condition(
                logger, 
                f"Validation failed: Group '{group}' has {count} comments, "
                f"which is below the minimum threshold of {MIN_GROUP_SIZE}."
            )
            return False

    # 2. Validate Subreddit Diversity (Edge Cases)
    if 'subreddit' not in df.columns:
        log_abort_condition(logger, "Validation failed: 'subreddit' column missing.")
        return False

    unique_subreddits = df['subreddit'].nunique()
    logger.info(f"Unique subreddits: {unique_subreddits}")

    if unique_subreddits < MIN_SUBREDDITS:
        log_abort_condition(
            logger, 
            f"Validation failed: Only {unique_subreddits} unique subreddits found. "
            f"Minimum required: {MIN_SUBREDDITS}."
        )
        return False

    logger.info("Post-fetch validation PASSED.")
    return True

def main():
    """
    Main entry point for T018 implementation.
    Orchestrates the full pipeline up to validation and saving.
    """
    import pandas as pd
    
    logger = setup_logger("ingest")
    logger.info("Starting Ingest Pipeline (T018).")

    try:
        # 1. Pre-checks (Power Analysis)
        if not check_power_analysis():
            logger.error("Power analysis check failed. Aborting.")
            sys.exit(1)

        # 2. Source Verification
        if not verify_source_availability():
            logger.error("Source verification failed. Aborting.")
            sys.exit(1)

        # 3. Fetch Data
        logger.info("Fetching Reddit data...")
        df = fetch_reddit_data()
        if df is None:
            logger.error("Data fetching returned None. Aborting.")
            sys.exit(1)

        # 4. Classify
        logger.info("Classifying comments...")
        df = classify_comments(df)

        # 5. Anonymize
        logger.info("Anonymizing data...")
        df = anonymize_data(df)

        # 6. T018: Post-fetch Validation
        logger.info("Running post-fetch validation (T018)...")
        if not validate_and_save(df, logger):
            # validate_and_save logs the specific abort reason
            sys.exit(1)

        # 7. Save Outputs
        logger.info("Saving processed data...")
        output_path = PROJECT_ROOT / "data" / "processed" / "anonymized.csv"
        df.to_csv(output_path, index=False)
        
        counts_path = PROJECT_ROOT / "data" / "processed" / "raw_counts.json"
        counts_data = {
            "total_comments": len(df),
            "prime_count": len(df[df['thread_type'] == 'Prime']),
            "control_count": len(df[df['thread_type'] == 'Control']),
            "unique_subreddits": df['subreddit'].nunique()
        }
        with open(counts_path, 'w') as f:
            json.dump(counts_data, f, indent=2)
        
        logger.info(f"Successfully saved {output_path} and {counts_path}")

    except Exception as e:
        logger.exception(f"Pipeline failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()