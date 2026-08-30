"""
Main entry point for the pipeline.
Orchestrates data ingestion, metric calculation, modeling, and robustness checks.
Logs runtime for SC-005.
"""
import os
import sys
import logging
import time
import json
from pathlib import Path
from datetime import datetime
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from ingestion import load_project_data, ingest_and_clean, DataSchemaError
from metrics import calculate_diversity_score
from config import PROJECT_ROOT, PROCESSED_DIR, RANDOM_SEED

# Setup Logging
os.makedirs(PROJECT_ROOT / "logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(PROJECT_ROOT / "logs" / "pipeline.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("main")

def run_verification_test():
    """
    Runs a verification test using a hardcoded dataset with known entropy values.
    Verifies output columns and values match manual calculations within 0.001 tolerance.
    """
    logger.info("Running verification test with hardcoded dataset...")
    
    import pandas as pd
    import numpy as np

    # Hardcoded test dataset with known entropy values
    # Scenario 1: Uniform distribution (Max Entropy for 3 categories: log2(3) ≈ 1.585)
    # Scenario 2: Skewed distribution (Lower Entropy)
    # Scenario 3: Single category (Zero Entropy)
    
    test_data = pd.DataFrame({
        'user_id': ['U001', 'U002', 'U003'],
        'session_id': ['S001', 'S002', 'S003'],
        'recommended_categories': [
            ['Math', 'Math', 'Math', 'Physics', 'Physics', 'Physics', 'Chemistry', 'Chemistry', 'Chemistry'], # Uniform 3
            ['Math', 'Math', 'Math', 'Math', 'Physics'], # Skewed
            ['Math', 'Math', 'Math', 'Math', 'Math'] # Single
        ],
        'enrolled_categories': [
            ['Math', 'Physics', 'Chemistry'], # Uniform 3
            ['Math', 'Math', 'Math', 'Physics'], # Skewed
            ['Math'] # Single
        ]
    })

    # Calculate expected values manually
    # Shannon Entropy: -sum(p * log2(p))
    
    # U001 Recs: 3 Math, 3 Physics, 3 Chem -> p=1/3 each. H = -3 * (1/3 * log2(1/3)) = log2(3) ≈ 1.58496
    expected_rec_u001 = np.log2(3)
    
    # U001 Enroll: 1 Math, 1 Phys, 1 Chem -> p=1/3 each. H = log2(3) ≈ 1.58496
    expected_learner_u001 = np.log2(3)

    # U002 Recs: 4 Math, 1 Phys -> p(M)=0.8, p(P)=0.2. H = -(0.8*log2(0.8) + 0.2*log2(0.2)) ≈ 0.7219
    p_m = 4/5
    p_p = 1/5
    expected_rec_u002 = -(p_m * np.log2(p_m) + p_p * np.log2(p_p))
    
    # U002 Enroll: 3 Math, 1 Phys -> p(M)=0.75, p(P)=0.25. H = -(0.75*log2(0.75) + 0.25*log2(0.25)) ≈ 0.8113
    p_m = 3/4
    p_p = 1/4
    expected_learner_u002 = -(p_m * np.log2(p_m) + p_p * np.log2(p_p))

    # U003 Recs: 5 Math -> p=1. H = 0
    expected_rec_u003 = 0.0
    
    # U003 Enroll: 1 Math -> p=1. H = 0
    expected_learner_u003 = 0.0

    expected_values = {
        'U001': {'rec': expected_rec_u001, 'learn': expected_learner_u001},
        'U002': {'rec': expected_rec_u002, 'learn': expected_learner_u002},
        'U003': {'rec': expected_rec_u003, 'learn': expected_learner_u003}
    }

    # Mock the ingestion functions to return our test data
    # We bypass the real loader to ensure the test is deterministic and self-contained
    class MockIngestion:
        @staticmethod
        def load_project_data():
            return test_data
        
        @staticmethod
        def ingest_and_clean(data):
            # Basic validation that columns exist
            if 'recommended_categories' not in data.columns or 'enrolled_categories' not in data.columns:
                raise DataSchemaError("Required columns missing.")
            return data

    # Temporarily replace functions in the module namespace for this test
    # Since we are in the same process, we can just call calculate_diversity_score directly on test_data
    # The main() function logic is extracted here for testing purposes without side effects
    
    cleaned_data = MockIngestion.ingest_and_clean(MockIngestion.load_project_data())
    diversity_results = calculate_diversity_score(cleaned_data)

    # Verify columns
    required_cols = {'user_id', 'session_id', 'recommendation_diversity_score', 'learner_diversity_score'}
    if not required_cols.issubset(set(diversity_results.columns)):
        raise AssertionError(f"Missing required columns. Found: {list(diversity_results.columns)}")

    # Verify values
    tolerance = 0.001
    for _, row in diversity_results.iterrows():
        uid = row['user_id']
        if uid in expected_values:
            rec_diff = abs(row['recommendation_diversity_score'] - expected_values[uid]['rec'])
            learn_diff = abs(row['learner_diversity_score'] - expected_values[uid]['learn'])
            
            if rec_diff > tolerance:
                raise AssertionError(f"Rec score mismatch for {uid}: got {row['recommendation_diversity_score']}, expected {expected_values[uid]['rec']}, diff {rec_diff}")
            if learn_diff > tolerance:
                raise AssertionError(f"Learner score mismatch for {uid}: got {row['learner_diversity_score']}, expected {expected_values[uid]['learn']}, diff {learn_diff}")
    
    logger.info("Verification test PASSED: All scores match manual calculations within tolerance.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Pipeline Entry Point")
    parser.add_argument("--verify", action="store_true", help="Run verification test only")
    args = parser.parse_args()

    if args.verify:
        run_verification_test()
        return

    start_time = time.time()
    logger.info("Pipeline started.")

    try:
        # 1. Ingestion
        logger.info("Step 1: Ingesting and cleaning data...")
        raw_data = load_project_data()
        cleaned_data = ingest_and_clean(raw_data)

        if cleaned_data.empty:
            logger.error("No data remaining after cleaning. Aborting.")
            return

        # 2. Metrics
        logger.info("Step 2: Calculating diversity scores...")
        diversity_results = calculate_diversity_score(cleaned_data)

        # Ensure output directory exists
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

        # Save intermediate results
        output_path = PROCESSED_DIR / "diversity_scores.parquet"
        diversity_results.to_parquet(output_path, index=False)
        logger.info(f"Diversity scores saved to {output_path}")

        # 3. Modeling (Placeholder for T020-T025, just log for now if not implemented yet)
        # Since T015 focuses on US1, we log that modeling is skipped or handled in next tasks
        # But the task description says "orchestrate ingestion and metric calculation", 
        # implying we stop after metrics for this specific task's scope, 
        # or we call the next stages if they exist. 
        # Given T015 is specifically about US1 output, we ensure the parquet is written.
        
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Pipeline completed successfully in {duration:.2f} seconds.")

        # Log runtime for SC-005
        runtime_log = {
            "start": datetime.fromtimestamp(start_time).isoformat(),
            "end": datetime.fromtimestamp(end_time).isoformat(),
            "duration_seconds": duration
        }
        with open(PROJECT_ROOT / "runtime_log.json", "w") as f:
            json.dump(runtime_log, f, indent=2)

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
