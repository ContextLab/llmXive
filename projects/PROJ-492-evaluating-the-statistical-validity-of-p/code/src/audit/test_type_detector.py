"""
Outcome-type detection heuristics for A/B test summaries.

Detects whether a test summary describes a binary (proportion) or continuous
(mean) outcome based on the available metrics.

Implements the following heuristics:
1. If 'baseline_conversion_rate' or 'treatment_conversion_rate' is present -> Binary
2. If 'baseline_mean' or 'treatment_mean' is present -> Continuous
3. If 'baseline_count' and 'treatment_count' are present with conversion rates -> Binary
4. If 'baseline_std' or 'treatment_std' is present -> Continuous
5. Fallback: If both 'conversion_rate' and 'mean' fields are missing, check if
   the test description or metrics imply proportions (e.g., presence of 'n_events')
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants for outcome types
OUTCOME_BINARY = "binary"
OUTCOME_CONTINUOUS = "continuous"
OUTCOME_UNKNOWN = "unknown"

logger: AuditLogger = get_default_logger(__name__)


def detect_outcome_type(summary: ABTestSummary) -> str:
    """
    Detects the outcome type (binary or continuous) for a single A/B test summary.
    
    Args:
        summary: An ABTestSummary object containing extracted metrics.
        
    Returns:
        One of 'binary', 'continuous', or 'unknown'.
        
    Heuristics (in order of priority):
    1. Presence of conversion rate fields (baseline_conversion_rate, treatment_conversion_rate)
    2. Presence of mean/standard deviation fields (baseline_mean, treatment_mean, baseline_std, treatment_std)
    3. Presence of event counts with sample sizes (n_events_baseline, n_events_treatment)
    4. Fallback analysis of test_name or description for keywords
    """
    if summary is None:
        logger.warning("ERR-022", "Received None summary for outcome type detection")
        return OUTCOME_UNKNOWN
    
    # Check for binary indicators (conversion rates)
    has_conversion_rates = (
        summary.baseline_conversion_rate is not None or
        summary.treatment_conversion_rate is not None
    )
    
    # Check for continuous indicators (means or standard deviations)
    has_means = (
        summary.baseline_mean is not None or
        summary.treatment_mean is not None
    )
    has_std_devs = (
        summary.baseline_std is not None or
        summary.treatment_std is not None
    )
    
    # Check for event counts (often associated with binary outcomes)
    has_event_counts = (
        summary.n_events_baseline is not None or
        summary.n_events_treatment is not None
    )
    
    # Priority 1: Conversion rates strongly indicate binary outcome
    if has_conversion_rates:
        logger.debug(f"Detected binary outcome from conversion rates for summary: {summary.source_url}")
        return OUTCOME_BINARY
    
    # Priority 2: Means or standard deviations indicate continuous outcome
    if has_means or has_std_devs:
        logger.debug(f"Detected continuous outcome from mean/std fields for summary: {summary.source_url}")
        return OUTCOME_CONTINUOUS
    
    # Priority 3: Event counts with sample sizes (without conversion rates) suggest binary
    if has_event_counts and (summary.baseline_sample_size is not None or summary.treatment_sample_size is not None):
        logger.debug(f"Detected binary outcome from event counts for summary: {summary.source_url}")
        return OUTCOME_BINARY
    
    # Priority 4: Fallback to keyword analysis in test name or description
    if summary.test_name:
        test_name_lower = summary.test_name.lower()
        binary_keywords = ["conversion", "rate", "proportion", "percentage", "click", "signup", "purchase", "binary"]
        continuous_keywords = ["mean", "average", "duration", "time", "revenue", "amount", "continuous"]
        
        has_binary_keyword = any(keyword in test_name_lower for keyword in binary_keywords)
        has_continuous_keyword = any(keyword in test_name_lower for keyword in continuous_keywords)
        
        if has_binary_keyword and not has_continuous_keyword:
            logger.debug(f"Detected binary outcome from test name keywords: {summary.test_name}")
            return OUTCOME_BINARY
        elif has_continuous_keyword and not has_binary_keyword:
            logger.debug(f"Detected continuous outcome from test name keywords: {summary.test_name}")
            return OUTCOME_CONTINUOUS
    
    if summary.description:
        desc_lower = summary.description.lower()
        binary_keywords = ["conversion", "rate", "proportion", "percentage", "click", "signup", "purchase"]
        continuous_keywords = ["mean", "average", "duration", "time", "revenue", "amount"]
        
        has_binary_keyword = any(keyword in desc_lower for keyword in binary_keywords)
        has_continuous_keyword = any(keyword in desc_lower for keyword in continuous_keywords)
        
        if has_binary_keyword and not has_continuous_keyword:
            logger.debug(f"Detected binary outcome from description keywords")
            return OUTCOME_BINARY
        elif has_continuous_keyword and not has_binary_keyword:
            logger.debug(f"Detected continuous outcome from description keywords")
            return OUTCOME_CONTINUOUS
    
    # Unable to determine
    logger.warning(f"ERR-022", f"Could not determine outcome type for summary: {summary.source_url}")
    return OUTCOME_UNKNOWN


def detect_outcome_types_batch(summaries: List[ABTestSummary]) -> Dict[str, str]:
    """
    Detects outcome types for a batch of A/B test summaries.
    
    Args:
        summaries: List of ABTestSummary objects.
        
    Returns:
        Dictionary mapping summary source_url to detected outcome type.
    """
    results = {}
    for summary in summaries:
        source_url = summary.source_url if summary.source_url else "unknown"
        outcome_type = detect_outcome_type(summary)
        results[source_url] = outcome_type
    return results


def validate_outcome_type_consistency(summaries: List[ABTestSummary]) -> Tuple[int, int, int]:
    """
    Validates that outcome types are consistently detected across a batch.
    
    Returns:
        Tuple of (binary_count, continuous_count, unknown_count)
    """
    counts = {OUTCOME_BINARY: 0, OUTCOME_CONTINUOUS: 0, OUTCOME_UNKNOWN: 0}
    for summary in summaries:
        outcome_type = detect_outcome_type(summary)
        counts[outcome_type] += 1
    return counts[OUTCOME_BINARY], counts[OUTCOME_CONTINUOUS], counts[OUTCOME_UNKNOWN]


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for testing the outcome type detector.
    
    This function creates a few test summaries and verifies the detector
    returns the correct types.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test outcome type detection")
    parser.parse_args(args)
    
    # Create test summaries
    test_summaries = [
        ABTestSummary(
            source_url="http://example.com/test1",
            test_name="Conversion Rate Test",
            baseline_conversion_rate=0.15,
            treatment_conversion_rate=0.18,
            baseline_sample_size=1000,
            treatment_sample_size=1000,
            p_value=0.03
        ),
        ABTestSummary(
            source_url="http://example.com/test2",
            test_name="Average Session Duration Test",
            baseline_mean=120.5,
            treatment_mean=135.2,
            baseline_std=45.0,
            treatment_std=48.0,
            baseline_sample_size=500,
            treatment_sample_size=500,
            p_value=0.01
        ),
        ABTestSummary(
            source_url="http://example.com/test3",
            test_name="Unknown Metric Test",
            baseline_sample_size=200,
            treatment_sample_size=200,
            p_value=0.05
        )
    ]
    
    # Test detection
    for summary in test_summaries:
        outcome_type = detect_outcome_type(summary)
        logger.info(f"Summary: {summary.source_url}, Outcome Type: {outcome_type}")
    
    # Validate consistency
    binary, continuous, unknown = validate_outcome_type_consistency(test_summaries)
    logger.info(f"Batch validation - Binary: {binary}, Continuous: {continuous}, Unknown: {unknown}")
    
    # Verify expected results
    if binary != 1:
        logger.error("ERR-022", f"Expected 1 binary outcome, got {binary}")
        return 1
    if continuous != 1:
        logger.error("ERR-022", f"Expected 1 continuous outcome, got {continuous}")
        return 1
    if unknown != 1:
        logger.error("ERR-022", f"Expected 1 unknown outcome, got {unknown}")
        return 1
    
    logger.info("All outcome type detection tests passed.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
