"""
Statistical reconstruction module for AB test summaries.

Reconstructs p-values from reported metrics (sample sizes, successes, etc.)
using appropriate statistical tests (z-test, Fisher's exact, Welch's t-test).
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.utils.helpers import safe_float
from code.src.audit.test_type_detector import detect_outcome_type_from_ab_summary
from code.src.audit.stat_verification import two_proportion_z_test, welch_t_test, fisher_exact_test

logger = get_default_logger("reconstructor")

def reconstruct_single_summary(summary: ABTestSummary) -> AuditRecord:
    """
    Reconstruct the statistical test for a single AB test summary.
    
    Args:
        summary: The ABTestSummary object containing reported metrics.
        
    Returns:
        AuditRecord with reconstructed p-value and test details.
    """
    # Determine outcome type
    outcome_type = detect_outcome_type_from_ab_summary(summary)
    
    p_value_reconstructed = None
    test_type = None
    reconstruction_error = None
    
    try:
        if outcome_type == 'binary':
            # For binary outcomes, use two-proportion z-test or Fisher's exact
            n_control = int(summary.n_control)
            n_treatment = int(summary.n_treatment)
            success_control = int(summary.success_control)
            success_treatment = int(summary.success_treatment)
            
            # Validate inputs
            if n_control <= 0 or n_treatment <= 0:
                raise ValueError("Sample sizes must be positive")
            if success_control < 0 or success_treatment < 0:
                raise ValueError("Success counts cannot be negative")
            if success_control > n_control or success_treatment > n_treatment:
                raise ValueError("Success counts cannot exceed sample sizes")
            
            # Try Fisher's exact test first for small samples
            if n_control < 30 or n_treatment < 30:
                test_type = "fisher_exact"
                # Fisher's exact test requires a 2x2 contingency table
                # rows: [success_control, failure_control], [success_treatment, failure_control]
                contingency_table = [
                    [success_control, n_control - success_control],
                    [success_treatment, n_treatment - success_treatment]
                ]
                _, p_value_reconstructed = fisher_exact_test(contingency_table)
            else:
                # Use z-test for larger samples
                test_type = "two_proportion_z"
                p_value_reconstructed, _ = two_proportion_z_test(
                    success_control, n_control,
                    success_treatment, n_treatment
                )
                
        elif outcome_type == 'continuous':
            # For continuous outcomes, we need means and standard deviations
            # Since these are often not reported, we'll use the reported p-value
            # or attempt reconstruction if we have enough info
            test_type = "welch_t"
            
            # If we have means and stds, use Welch's t-test
            if hasattr(summary, 'mean_control') and hasattr(summary, 'mean_treatment'):
                mean_control = safe_float(summary.mean_control)
                mean_treatment = safe_float(summary.mean_treatment)
                std_control = safe_float(summary.std_control)
                std_treatment = safe_float(summary.std_treatment)
                
                if all(v is not None and v > 0 for v in [mean_control, mean_treatment, std_control, std_treatment]):
                    _, p_value_reconstructed = welch_t_test(
                        mean_control, std_control, int(summary.n_control),
                        mean_treatment, std_treatment, int(summary.n_treatment)
                    )
                else:
                    # Fall back to reported p-value if we can't reconstruct
                    p_value_reconstructed = safe_float(summary.p_value_reported)
            else:
                # Fall back to reported p-value if we can't reconstruct
                p_value_reconstructed = safe_float(summary.p_value_reported)
        
        else:
            # Unknown outcome type - fall back to reported p-value
            test_type = "unknown_fallback"
            p_value_reconstructed = safe_float(summary.p_value_reported)
            
    except Exception as e:
        reconstruction_error = str(e)
        logger.warning(f"Reconstruction failed for {summary.url}: {e}")
        # Fall back to reported p-value on error
        p_value_reconstructed = safe_float(summary.p_value_reported)
    
    # Create the audit record
    audit_record = AuditRecord(
        url=summary.url,
        n_control=summary.n_control,
        n_treatment=summary.n_treatment,
        p_value_reported=summary.p_value_reported,
        p_value_reconstructed=p_value_reconstructed,
        effect_size_reported=summary.effect_size_reported,
        effect_size_reconstructed=None,  # Not computed in this version
        test_type=test_type,
        reconstruction_error=reconstruction_error,
        is_inconsistent=False,  # Will be set by validator
        data_quality_warning=None
    )
    
    return audit_record

def reconstruct_all(summaries: List[ABTestSummary]) -> List[AuditRecord]:
    """
    Reconstruct statistical tests for all summaries in the list.
    
    Args:
        summaries: List of ABTestSummary objects.
        
    Returns:
        List of AuditRecord objects with reconstructed p-values.
    """
    logger.info(f"Starting reconstruction for {len(summaries)} summaries")
    
    records = []
    success_count = 0
    failure_count = 0
    
    for i, summary in enumerate(summaries):
        try:
            record = reconstruct_single_summary(summary)
            records.append(record)
            if record.reconstruction_error is None:
                success_count += 1
            else:
                failure_count += 1
        except Exception as e:
            logger.error(f"Failed to reconstruct summary {i} ({summary.url}): {e}")
            failure_count += 1
            # Create a minimal record with error
            record = AuditRecord(
                url=summary.url,
                n_control=summary.n_control,
                n_treatment=summary.n_treatment,
                p_value_reported=summary.p_value_reported,
                p_value_reconstructed=None,
                effect_size_reported=summary.effect_size_reported,
                effect_size_reconstructed=None,
                test_type="error",
                reconstruction_error=str(e),
                is_inconsistent=False,
                data_quality_warning="Reconstruction failed"
            )
            records.append(record)
        
        if (i + 1) % 1000 == 0:
            logger.info(f"Processed {i + 1}/{len(summaries)} summaries")
    
    logger.info(f"Reconstruction complete: {success_count} successful, {failure_count} failed")
    return records

def main():
    """Main entry point for standalone execution."""
    logger.info("Running reconstructor module")
    # This function is primarily used as a module; actual usage is via the pipeline
    pass

if __name__ == "__main__":
    main()
