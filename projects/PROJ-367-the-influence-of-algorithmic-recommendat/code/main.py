import os
import sys
import logging
import time
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

# Import from sibling modules using the exact API surface provided
from config import ProjectConfig, setup_logging
from ingestion import load_data_from_hf, validate_schema, ingest_and_clean, load_project_data
from metrics import shannon_entropy, calculate_diversity_score, merge_similar_categories

# Configure logger
logger = logging.getLogger(__name__)

def run_verification_test() -> bool:
    """
    Run a verification test using a hardcoded dataset with known entropy values.
    Verifies that the calculated diversity scores match manual calculations within 0.001 tolerance.
    Returns True if all checks pass, False otherwise.
    """
    import pandas as pd
    import numpy as np
    from collections import Counter

    logger.info("Starting verification test with hardcoded dataset...")

    # Hardcoded test dataset with known entropy values
    # Format: user_id, session_id, recommended_categories (list), enrolled_categories (list)
    test_data = [
        {
            "user_id": "U001",
            "session_id": "S001",
            "recommended_categories": ["Math", "Math", "Physics"],
            "enrolled_categories": ["Math", "Physics"]
        },
        {
            "user_id": "U002",
            "session_id": "S002",
            "recommended_categories": ["Art", "Art", "Art", "Music"],
            "enrolled_categories": ["Art", "Music", "Music"]
        },
        {
            "user_id": "U003",
            "session_id": "S003",
            "recommended_categories": ["History", "Science", "Tech"],
            "enrolled_categories": ["History", "Science", "Tech"]
        }
    ]

    df_test = pd.DataFrame(test_data)

    # Manual calculation of expected entropy values
    # Shannon Entropy: H = -sum(p * log2(p))
    
    # U001: Recs [Math, Math, Physics] -> counts: Math=2, Physics=1, total=3
    # p(Math)=2/3, p(Physics)=1/3
    # H_rec = -(2/3 * log2(2/3) + 1/3 * log2(1/3))
    #       = -(2/3 * -0.58496 + 1/3 * -1.58496)
    #       = -( -0.38997 - 0.52832 ) = 0.9183
    # Enrolls [Math, Physics] -> counts: Math=1, Physics=1, total=2
    # p=Math=0.5, p=Phys=0.5
    # H_enr = -(0.5 * log2(0.5) + 0.5 * log2(0.5)) = 1.0
    expected_u001_rec = 0.9182958340544896
    expected_u001_enr = 1.0

    # U002: Recs [Art, Art, Art, Music] -> counts: Art=3, Music=1, total=4
    # p(Art)=0.75, p(Music)=0.25
    # H_rec = -(0.75 * log2(0.75) + 0.25 * log2(0.25))
    #       = -(0.75 * -0.4150 + 0.25 * -2.0)
    #       = -( -0.31125 - 0.5 ) = 0.8113
    # Enrolls [Art, Music, Music] -> counts: Art=1, Music=2, total=3
    # p(Art)=1/3, p(Music)=2/3
    # H_enr = 0.9183 (same as U001 recs)
    expected_u002_rec = 0.8112781244591328
    expected_u002_enr = 0.9182958340544896

    # U003: Recs [History, Science, Tech] -> counts: 1,1,1, total=3
    # p=1/3 each
    # H_rec = -(3 * (1/3 * log2(1/3))) = -log2(1/3) = log2(3) = 1.5850
    # Enrolls same -> 1.5850
    expected_u003_rec = 1.584962500721156
    expected_u003_enr = 1.584962500721156

    expected_values = {
        "U001": {"rec": expected_u001_rec, "enr": expected_u001_enr},
        "U002": {"rec": expected_u002_rec, "enr": expected_u002_enr},
        "U003": {"rec": expected_u003_rec, "enr": expected_u003_enr}
    }

    # Process the test data using the actual pipeline functions
    # We need to adapt the data to the format expected by calculate_diversity_score
    # The function expects a DataFrame with columns 'recommended_categories' and 'enrolled_categories'
    # where each cell is a list of strings.
    
    results = []
    all_passed = True
    tolerance = 0.001

    for _, row in df_test.iterrows():
        user_id = row["user_id"]
        session_id = row["session_id"]
        
        # Calculate diversity scores using the actual implementation
        rec_score = calculate_diversity_score(row["recommended_categories"])
        enr_score = calculate_diversity_score(row["enrolled_categories"])
        
        results.append({
            "user_id": user_id,
            "session_id": session_id,
            "recommendation_diversity_score": rec_score,
            "learner_diversity_score": enr_score
        })

        # Verify against expected values
        expected_rec = expected_values[user_id]["rec"]
        expected_enr = expected_values[user_id]["enr"]

        if abs(rec_score - expected_rec) > tolerance:
            logger.error(f"Verification FAILED for {user_id} rec: got {rec_score}, expected {expected_rec}")
            all_passed = False
        else:
            logger.info(f"Verification PASSED for {user_id} rec: {rec_score}")

        if abs(enr_score - expected_enr) > tolerance:
            logger.error(f"Verification FAILED for {user_id} enr: got {enr_score}, expected {expected_enr}")
            all_passed = False
        else:
            logger.info(f"Verification PASSED for {user_id} enr: {enr_score}")

    if all_passed:
        logger.info("Verification test PASSED: All calculated scores match expected values within tolerance.")
    else:
        logger.error("Verification test FAILED: Some scores do not match expected values.")

    return all_passed

def main() -> int:
    """
    Main entry point for the pipeline.
    Orchestrates data ingestion, metric calculation, and output generation.
    """
    # Setup logging
    config = ProjectConfig()
    setup_logging(config.log_level)

    logger.info("Starting main pipeline execution...")
    start_time = time.time()

    # Ensure output directories exist
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    processed_dir = output_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Load and validate data
        logger.info("Loading data...")
        df = load_project_data(config.data_path)

        if df is None or df.empty:
            logger.error("No data loaded. Exiting.")
            return 1

        logger.info(f"Loaded {len(df)} rows. Validating schema...")
        validate_schema(df)

        # Ingest and clean data
        logger.info("Ingesting and cleaning data...")
        df_clean = ingest_and_clean(df, config)

        if df_clean.empty:
            logger.warning("No valid data after cleaning. Exiting.")
            return 1

        logger.info(f"Cleaned data contains {len(df_clean)} valid rows.")

        # Calculate diversity scores
        logger.info("Calculating diversity scores...")
        
        # Calculate recommendation diversity score
        df_clean["recommendation_diversity_score"] = df_clean["recommended_categories"].apply(
            lambda x: calculate_diversity_score(x) if isinstance(x, list) else np.nan
        )

        # Calculate learner diversity score
        df_clean["learner_diversity_score"] = df_clean["enrolled_categories"].apply(
            lambda x: calculate_diversity_score(x) if isinstance(x, list) else np.nan
        )

        # Select required columns for output
        output_columns = [
            "user_id", 
            "session_id", 
            "recommendation_diversity_score", 
            "learner_diversity_score"
        ]
        
        # Ensure these columns exist
        for col in output_columns:
            if col not in df_clean.columns:
                logger.warning(f"Column {col} not found in processed data. Adding as NaN.")
                df_clean[col] = np.nan

        df_output = df_clean[output_columns].copy()

        # Save to Parquet
        output_path = processed_dir / "diversity_scores.parquet"
        logger.info(f"Saving output to {output_path}")
        df_output.to_parquet(output_path, index=False)

        logger.info(f"Successfully wrote {len(df_output)} rows to {output_path}")

        # Log summary
        logger.info(f"Output columns: {list(df_output.columns)}")
        logger.info(f"Sample data:\n{df_output.head()}")

        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Pipeline completed successfully in {duration:.2f} seconds.")

        # Run verification test if requested (e.g., via environment variable)
        if os.environ.get("RUN_VERIFICATION_TEST", "false").lower() == "true":
            logger.info("Running verification test...")
            if run_verification_test():
                logger.info("Verification test passed.")
            else:
                logger.error("Verification test failed. Check logs for details.")
                return 1

        return 0

    except Exception as e:
        logger.error(f"Pipeline execution failed with error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
