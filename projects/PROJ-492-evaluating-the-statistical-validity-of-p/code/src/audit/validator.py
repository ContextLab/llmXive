"""
Inconsistency Validator.

Validates A/B test summaries for statistical consistency and generates
audit records.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger

logger = get_default_logger(__name__)

def calculate_absolute_p_difference(reported: float, reconstructed: float) -> float:
    """Calculate absolute difference between p-values."""
    return abs(reported - reconstructed)

def calculate_relative_effect_size_difference(reported: float, reconstructed: float) -> float:
    """Calculate relative difference in effect sizes."""
    if reconstructed == 0:
        return 0.0
    return abs(reported - reconstructed) / abs(reconstructed)

def detect_sample_size_mismatch(record: ABTestSummary) -> bool:
    """Detect if sample sizes are inconsistent or missing."""
    if record.n_control is None or record.n_treatment is None:
        return True
    if record.n_control <= 0 or record.n_treatment <= 0:
        return True
    return False

def check_p_value_consistency(reported: float, reconstructed: float, threshold: float = 0.05) -> bool:
    """Check if p-values are consistent."""
    return calculate_absolute_p_difference(reported, reconstructed) <= threshold

def check_effect_size_consistency(reported: float, reconstructed: float, threshold: float = 0.05) -> bool:
    """Check if effect sizes are consistent."""
    return calculate_relative_effect_size_difference(reported, reconstructed) <= threshold

def create_audit_record(summary: ABTestSummary, is_inconsistent: bool, reason: str) -> AuditRecord:
    """Create an audit record from a summary."""
    return AuditRecord(
        id=summary.id,
        url=summary.url,
        domain=summary.domain,
        year=summary.year,
        is_inconsistent=is_inconsistent,
        reason=reason,
        timestamp=datetime.now().isoformat()
    )

def validate_summary(summary: ABTestSummary) -> AuditRecord:
    """
    Validate a single summary.

    Args:
        summary: The summary to validate.

    Returns:
        AuditRecord with validation result.
    """
    set_rng_seed()
    
    if detect_sample_size_mismatch(summary):
        return create_audit_record(summary, True, "Sample size mismatch or missing")
    
    # Placeholder for actual reconstruction logic
    # In a real implementation, this would call the reconstructor
    reconstructed_p = summary.reported_p_value # Dummy for now
    
    if not check_p_value_consistency(summary.reported_p_value, reconstructed_p):
        return create_audit_record(summary, True, "P-value inconsistency detected")
    
    return create_audit_record(summary, False, "Consistent")

def validate_all_summaries(summaries: List[ABTestSummary]) -> List[AuditRecord]:
    """Validate all summaries in a list."""
    return [validate_summary(s) for s in summaries]

def filter_for_prevalence(records: List[AuditRecord]) -> List[AuditRecord]:
    """Filter records for prevalence calculation (exclude sample size mismatches)."""
    return [r for r in records if "Sample size" not in r.reason]

def write_audit_report(records: List[AuditRecord], output_path: Path) -> None:
    """Write audit report to JSON."""
    data = [r.model_dump() for r in records]
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Audit report written to {output_path}")

def main():
    """Main entry point."""
    # Example usage
    summary = ABTestSummary(
        id="test-1",
        url="http://example.com",
        domain="tech",
        year=2023,
        reported_p_value=0.04,
        n_control=1000,
        n_treatment=1000
    )
    record = validate_summary(summary)
    print(f"Result: {record.is_inconsistent}, Reason: {record.reason}")

if __name__ == "__main__":
    main()
