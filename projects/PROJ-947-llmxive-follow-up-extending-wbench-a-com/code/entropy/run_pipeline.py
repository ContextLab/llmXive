import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Import from existing API surface
from config import get_config
from utils.logging import get_logger, log_info, log_error, log_exception
from utils.errors import PipelineError, fail_loudly
from entropy.scorer import main as run_scorer_main
from entropy.generator import main as run_generator_main
from entropy.validator import main as run_validator_main

logger = get_logger(__name__)

def pre_run_variance_check(complexity_scores_path: str = "data/processed/complexity_scores.csv", 
                           min_variance: float = 0.05) -> bool:
    """
    Pre-run validation to abort if variance of complexity scores is too low.
    
    This implements SC-005: Ensure sufficient diversity in complexity scores
    before proceeding with downstream analysis.
    
    Args:
        complexity_scores_path: Path to the complexity scores CSV file
        min_variance: Minimum acceptable variance threshold (default 0.05)
        
    Returns:
        True if variance check passes, False otherwise
        
    Raises:
        PipelineError: If the complexity scores file doesn't exist or variance is below threshold
    """
    scores_path = Path(complexity_scores_path)
    
    if not scores_path.exists():
        # File doesn't exist yet - this is expected on first run
        # The pipeline will generate it, so we allow it to proceed
        log_info(f"Complexity scores file not found yet: {scores_path}. "
                "Pipeline will generate it. Skipping variance check.")
        return True
    
    try:
        df = pd.read_csv(scores_path)
        
        if 'complexity_score' not in df.columns:
            fail_loudly(
                f"Required column 'complexity_score' not found in {scores_path}. "
                f"Available columns: {list(df.columns)}"
            )
        
        scores = df['complexity_score'].dropna()
        
        if len(scores) == 0:
            fail_loudly(
                f"No valid complexity scores found in {scores_path}. "
                "Cannot perform variance check."
            )
        
        variance = scores.var()
        mean_score = scores.mean()
        
        log_info(f"Complexity scores variance check: variance={variance:.6f}, "
                f"mean={mean_score:.6f}, count={len(scores)}")
        
        if variance < min_variance:
            fail_loudly(
                f"Variance check FAILED: complexity scores variance ({variance:.6f}) "
                f"is below minimum threshold ({min_variance}). "
                f"Mean score: {mean_score:.6f}, N={len(scores)}. "
                f"This indicates insufficient diversity in the generated variants. "
                f"Per SC-005, the pipeline must abort to prevent invalid analysis."
            )
        
        log_info(f"Variance check PASSED: variance={variance:.6f} >= {min_variance}")
        return True
        
    except pd.errors.EmptyDataError:
        fail_loudly(f"Complexity scores file is empty: {scores_path}")
    except Exception as e:
        log_exception(e)
        fail_loudly(f"Failed to read or validate complexity scores: {e}")

def run_pipeline():
    """
    Execute the full entropy analysis pipeline:
    1. Generate variants (T013)
    2. Validate variants (T014)
    3. Compute complexity scores (T015)
    4. Pre-run variance check (T017) - NEW
    5. Continue with downstream processing if check passes
    """
    logger.info("Starting entropy analysis pipeline")
    
    config = get_config()
    
    try:
        # Step 1: Generate variants
        log_info("Step 1: Generating sequence variants...")
        run_generator_main()
        
        # Step 2: Validate variants
        log_info("Step 2: Validating sequence variants...")
        run_validator_main()
        
        # Step 3: Compute complexity scores
        log_info("Step 3: Computing complexity scores...")
        run_scorer_main()
        
        # Step 4: Pre-run variance check (T017)
        log_info("Step 4: Running pre-run variance check (SC-005)...")
        scores_path = config.get('paths', {}).get('complexity_scores', 
                                                  'data/processed/complexity_scores.csv')
        min_variance = config.get('scoring', {}).get('min_variance', 0.05)
        
        variance_check_passed = pre_run_variance_check(
            complexity_scores_path=scores_path,
            min_variance=min_variance
        )
        
        if not variance_check_passed:
            log_error("Variance check failed. Pipeline aborted.")
            raise PipelineError("Pre-run variance check failed. Pipeline aborted.")
        
        log_info("Variance check passed. Pipeline continuing...")
        
        # Step 5: Continue with downstream processing
        # (Future tasks like inference and analysis would go here)
        log_info("Pipeline completed successfully")
        
    except PipelineError as e:
        log_error(f"Pipeline error: {e}")
        raise
    except Exception as e:
        log_exception(e)
        raise

def main():
    """Entry point for the pipeline script."""
    try:
        run_pipeline()
    except PipelineError as e:
        log_error(f"Pipeline failed: {e}")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()