"""
Outcome-type detection heuristics for A/B test summaries.

Detects whether a test summary describes a binary (proportion) outcome
or a continuous (mean) outcome based on available metrics.
"""
import logging
from typing import Dict, Any, Optional, Tuple
from code.src.utils.logger import get_default_logger

# Outcome types
OUTCOME_BINARY = "binary"
OUTCOME_CONTINUOUS = "continuous"
OUTCOME_UNKNOWN = "unknown"

def detect_outcome_type(summary: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """
    Detect the outcome type (binary vs continuous) from an A/B test summary.
    
    Heuristics:
    1. If 'conversion_rate' or 'baseline_conversion' or 'treatment_conversion'
       is present, it's binary (proportion-based).
    2. If 'mean_control' or 'mean_treatment' or 'std_control' or 'std_treatment'
       is present, it's continuous (mean-based).
    3. If 'metric_type' or 'outcome_type' field explicitly states the type, use it.
    4. If 'test_type' field mentions 'z-test' or 'proportion' -> binary.
    5. If 'test_type' field mentions 't-test' or 'mean' -> continuous.
    6. If 'p_value' is present with 'effect_size' but no conversion rates,
       check if effect_size is a difference in proportions (0-1 range) -> binary.
    
    Args:
        summary: Dictionary containing extracted A/B test metrics.
    
    Returns:
        Tuple of (outcome_type, confidence_note)
        outcome_type: One of "binary", "continuous", or "unknown"
        confidence_note: Optional explanation for the detection
    """
    logger = get_default_logger(__name__)
    
    if not isinstance(summary, dict):
        logger.warning("Invalid summary format: expected dict, got %s", type(summary))
        return OUTCOME_UNKNOWN, "Invalid summary format"
    
    # Check explicit type indicators first
    explicit_type = summary.get('outcome_type') or summary.get('metric_type')
    if explicit_type:
        explicit_lower = explicit_type.lower()
        if 'binary' in explicit_lower or 'proportion' in explicit_lower or 'conversion' in explicit_lower:
            return OUTCOME_BINARY, f"Explicit type indicator: {explicit_type}"
        elif 'continuous' in explicit_lower or 'mean' in explicit_lower or 'duration' in explicit_lower:
            return OUTCOME_CONTINUOUS, f"Explicit type indicator: {explicit_type}"
    
    # Check test type indicators
    test_type = summary.get('test_type')
    if test_type:
        test_lower = test_type.lower()
        if 'z-test' in test_lower or 'proportion' in test_lower or 'chi-square' in test_lower:
            return OUTCOME_BINARY, f"Test type indicator: {test_type}"
        elif 't-test' in test_lower or 'welch' in test_lower:
            return OUTCOME_CONTINUOUS, f"Test type indicator: {test_type}"
    
    # Check for conversion rate fields (binary indicator)
    conversion_fields = [
        'conversion_rate', 'baseline_conversion', 'treatment_conversion',
        'control_conversion', 'baseline_rate', 'treatment_rate',
        'control_rate', 'baseline_conversions', 'treatment_conversions',
        'control_conversions', 'baseline_successes', 'treatment_successes'
    ]
    
    has_conversion = any(field in summary for field in conversion_fields)
    
    # Check for mean/std fields (continuous indicator)
    continuous_fields = [
        'mean_control', 'mean_treatment', 'mean_baseline', 'mean_variant',
        'std_control', 'std_treatment', 'std_baseline', 'std_variant',
        'standard_deviation_control', 'standard_deviation_treatment'
    ]
    
    has_continuous = any(field in summary for field in continuous_fields)
    
    # Check for effect size type
    effect_size = summary.get('effect_size')
    effect_size_type = summary.get('effect_size_type')
    
    if effect_size_type:
        effect_lower = effect_size_type.lower()
        if 'proportion' in effect_lower or 'risk' in effect_lower or 'odds' in effect_lower:
            return OUTCOME_BINARY, f"Effect size type: {effect_size_type}"
        elif 'mean' in effect_lower or 'difference' in effect_lower:
            # Could be either, check value range
            if effect_size is not None and 0 <= effect_size <= 1:
                return OUTCOME_BINARY, "Effect size in [0,1] range suggests proportion"
    
    # Heuristic: If conversion fields present, it's binary
    if has_conversion:
        return OUTCOME_BINARY, "Conversion rate fields detected"
    
    # Heuristic: If mean/std fields present, it's continuous
    if has_continuous:
        return OUTCOME_CONTINUOUS, "Mean/standard deviation fields detected"
    
    # Check sample size context
    n_control = summary.get('n_control') or summary.get('n_baseline') or summary.get('sample_size_control')
    n_treatment = summary.get('n_treatment') or summary.get('n_variant') or summary.get('sample_size_treatment')
    
    # If we have p_value and effect_size but no clear indicator
    p_value = summary.get('p_value')
    
    if p_value is not None and effect_size is not None:
        # Small effect sizes (< 1) with large sample sizes often indicate proportions
        if n_control and n_treatment:
            avg_n = (n_control + n_treatment) / 2
            if avg_n > 1000 and effect_size < 0.5:
                # Could be either, but small effects with large N often proportions
                logger.debug("Large sample with small effect: ambiguous")
    
    # Default to unknown if no indicators found
    logger.debug("Could not determine outcome type from summary: %s", summary.keys())
    return OUTCOME_UNKNOWN, "No clear indicators found"

def detect_outcome_type_from_summaries(summaries: list) -> Dict[str, Any]:
    """
    Detect outcome types for a list of summaries and return statistics.
    
    Args:
        summaries: List of A/B test summary dictionaries.
    
    Returns:
        Dictionary with detection results and statistics.
    """
    results = {
        'binary_count': 0,
        'continuous_count': 0,
        'unknown_count': 0,
        'total_count': len(summaries),
        'detections': []
    }
    
    for i, summary in enumerate(summaries):
        outcome_type, note = detect_outcome_type(summary)
        results['detections'].append({
            'index': i,
            'outcome_type': outcome_type,
            'note': note
        })
        
        if outcome_type == OUTCOME_BINARY:
            results['binary_count'] += 1
        elif outcome_type == OUTCOME_CONTINUOUS:
            results['continuous_count'] += 1
        else:
            results['unknown_count'] += 1
    
    return results

def main():
    """
    Main entry point for testing the detector.
    Reads test data from a file if provided, otherwise runs self-tests.
    """
    import sys
    import json
    
    logger = get_default_logger(__name__)
    
    # Test cases
    test_cases = [
        {
            "name": "Binary with conversion rate",
            "data": {
                "baseline_conversion": 0.05,
                "treatment_conversion": 0.07,
                "n_baseline": 1000,
                "n_treatment": 1000
            },
            "expected": OUTCOME_BINARY
        },
        {
            "name": "Continuous with means",
            "data": {
                "mean_control": 10.5,
                "mean_treatment": 12.3,
                "std_control": 2.1,
                "std_treatment": 2.5,
                "n_control": 50,
                "n_treatment": 50
            },
            "expected": OUTCOME_CONTINUOUS
        },
        {
            "name": "Explicit binary type",
            "data": {
                "outcome_type": "binary",
                "p_value": 0.03
            },
            "expected": OUTCOME_BINARY
        },
        {
            "name": "Explicit continuous type",
            "data": {
                "metric_type": "continuous",
                "test_type": "t-test"
            },
            "expected": OUTCOME_CONTINUOUS
        },
        {
            "name": "Z-test indication",
            "data": {
                "test_type": "two-proportion z-test",
                "effect_size": 0.02
            },
            "expected": OUTCOME_BINARY
        },
        {
            "name": "Welch t-test indication",
            "data": {
                "test_type": "Welch's t-test",
                "effect_size": 1.5
            },
            "expected": OUTCOME_CONTINUOUS
        },
        {
            "name": "Unknown type",
            "data": {
                "p_value": 0.04
            },
            "expected": OUTCOME_UNKNOWN
        }
    ]
    
    all_passed = True
    for case in test_cases:
        outcome_type, note = detect_outcome_type(case['data'])
        passed = outcome_type == case['expected']
        status = "PASS" if passed else "FAIL"
        
        if not passed:
            all_passed = False
            logger.error("%s: %s - Expected %s, got %s (note: %s)", 
                         status, case['name'], case['expected'], outcome_type, note)
        else:
            logger.info("%s: %s - %s (note: %s)", 
                        status, case['name'], outcome_type, note)
    
    if all_passed:
        logger.info("All self-tests passed!")
        return 0
    else:
        logger.error("Some self-tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
