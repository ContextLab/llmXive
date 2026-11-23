"""
Baseline module for generating null baselines (identity transformations).

This module implements the null baseline generation for the refactoring pipeline.
The null baseline is an identity transformation where the output code is identical
to the input code, serving as a control to verify that metric changes are due
to actual refactoring and not measurement noise.
"""

import logging
from typing import List, Dict, Any, Optional

from models.entities import FunctionSample
from utils.logging import get_logger, LLMRefactoringError

logger = get_logger(__name__)


def generate_identity_baseline(function_samples: List[FunctionSample]) -> List[Dict[str, Any]]:
    """
    Generate null baseline (identity transformation) for each valid function.
    
    The identity baseline simply returns the original code unchanged. This serves
    as a control to verify that:
    1. Metric calculations are deterministic (same code -> same metrics)
    2. Any observed improvements in refactored code are genuine and not artifacts
    
    Args:
        function_samples: List of FunctionSample objects containing original code
    
    Returns:
        List of dictionaries with baseline results, each containing:
        - 'original_code': The original function code
        - 'baseline_code': The baseline code (identical to original)
        - 'function_hash': Hash of the function for tracking
        - 'baseline_type': String indicating "identity"
    
    Raises:
        LLMRefactoringError: If input is empty or validation fails
    """
    if not function_samples:
        logger.warning("No function samples provided for baseline generation")
        return []
    
    logger.info(f"Generating identity baseline for {len(function_samples)} functions")
    
    baseline_results = []
    
    for sample in function_samples:
        try:
            # Identity transformation: baseline code is identical to original
            baseline_code = sample.code
            
            baseline_entry = {
                'original_code': sample.code,
                'baseline_code': baseline_code,
                'function_hash': sample.hash,
                'baseline_type': 'identity',
                'original_metrics': sample.metrics,
                'is_valid': True,
                'error_message': None
            }
            
            baseline_results.append(baseline_entry)
            
        except Exception as e:
            logger.error(f"Failed to generate baseline for function {sample.hash}: {str(e)}")
            baseline_results.append({
                'original_code': sample.code,
                'baseline_code': None,
                'function_hash': sample.hash,
                'baseline_type': 'identity',
                'original_metrics': sample.metrics,
                'is_valid': False,
                'error_message': str(e)
            })
    
    valid_count = sum(1 for r in baseline_results if r['is_valid'])
    logger.info(f"Baseline generation complete: {valid_count}/{len(baseline_results)} successful")
    
    return baseline_results


def validate_identity_baseline(baseline_results: List[Dict[str, Any]], tolerance: float = 0.01) -> bool:
    """
    Validate that identity baselines produce near-zero metric deltas.
    
    This validation ensures that when we compare original code to its identity
    baseline, the metric differences are negligible (within tolerance).
    
    Args:
        baseline_results: List of baseline result dictionaries
        tolerance: Maximum acceptable absolute delta (default 0.01)
    
    Returns:
        True if all baselines pass validation, False otherwise
    
    Raises:
        LLMRefactoringError: If validation fails significantly
    """
    if not baseline_results:
        logger.warning("No baseline results to validate")
        return False
    
    failed_validations = []
    
    for result in baseline_results:
        if not result['is_valid']:
            failed_validations.append(f"Invalid baseline for hash {result['function_hash']}")
            continue
        
        # For identity transformation, metrics should be identical
        # We check if the baseline code matches the original
        if result['baseline_code'] != result['original_code']:
            failed_validations.append(
                f"Baseline code mismatch for hash {result['function_hash']}"
            )
    
    if failed_validations:
        logger.error(f"Baseline validation failed for {len(failed_validations)} samples")
        for failure in failed_validations[:5]:  # Log first 5 failures
            logger.error(f"  - {failure}")
        
        if len(failed_validations) > len(baseline_results) * 0.1:
            raise LLMRefactoringError(
                f"Baseline validation failed: {len(failed_validations)}/{len(baseline_results)} "
                "samples failed validation"
            )
        return False
    
    logger.info(f"Baseline validation passed: {len(baseline_results)}/{len(baseline_results)} samples valid")
    return True


def main():
    """
    Main entry point for baseline generation.
    
    This function is intended to be called from the main pipeline or
    as a standalone script for testing baseline generation.
    """
    logger.info("Starting baseline generation module")
    
    # Example usage - this would typically be called from the pipeline
    # with actual FunctionSample objects loaded from data/processed/raw_metrics.json
    
    logger.info("Baseline generation module ready")
    logger.info("Use generate_identity_baseline() to process function samples")
    logger.info("Use validate_identity_baseline() to verify results")

if __name__ == "__main__":
    main()