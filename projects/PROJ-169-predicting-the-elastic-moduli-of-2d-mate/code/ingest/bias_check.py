"""
Bias check analysis for excluded entries.
Analyzes exclusion logs to identify potential biases in the dataset filtering process.
"""
import os
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from utils.logger import get_logger, log_bias_check

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@dataclass
class ExclusionReason:
    material_id: str
    reason: str
    category: str
    family_id: Optional[str] = None

@dataclass
class BiasReport:
    summary: Dict[str, int]
    total_excluded: int
    report: List[Dict[str, Any]]
    small_families: List[str]
    warnings: List[str]

def load_exclusion_log(input_path: Path) -> List[ExclusionReason]:
    """Load exclusion log from JSON file."""
    if not input_path.exists():
        logger.warning(f"Exclusion log not found at {input_path}. Returning empty list.")
        return []
    
    with open(input_path, "r") as f:
        data = json.load(f)
    
    return [ExclusionReason(**item) for item in data]

def analyze_exclusion_bias(exclusion_reasons: List[ExclusionReason]) -> BiasReport:
    """Analyze the bias in excluded entries."""
    category_counts: Dict[str, int] = {}
    detailed_report = []
    family_counts: Dict[str, int] = {}
    warnings = []

    for reason in exclusion_reasons:
        # Count by category
        category_counts[reason.category] = category_counts.get(reason.category, 0) + 1
        
        # Track family occurrences
        if reason.family_id:
            family_counts[reason.family_id] = family_counts.get(reason.family_id, 0) + 1

        # Add to detailed report
        detailed_report.append({
            "material_id": reason.material_id,
            "reason": reason.reason,
            "category": reason.category,
            "family_id": reason.family_id
        })

    # Identify small families (families with very few excluded entries might indicate bias)
    # Threshold: families with < 2 excluded entries are flagged as "small"
    small_families = [fam for fam, count in family_counts.items() if count < 2]

    # Generate warnings for significant biases
    if category_counts:
        max_category = max(category_counts, key=category_counts.get)
        max_count = category_counts[max_category]
        total = sum(category_counts.values())
        
        if total > 0:
            ratio = max_count / total
            if ratio > 0.8:
                warnings.append(f"High bias detected: {max_category} accounts for {ratio:.1%} of exclusions.")
    
    if not exclusion_reasons:
        warnings.append("No exclusions found. Verify that filtering is active.")

    report = BiasReport(
        summary=category_counts,
        total_excluded=len(exclusion_reasons),
        report=detailed_report,
        small_families=small_families,
        warnings=warnings
    )

    # Log bias check results using the project logger
    log_bias_check(report.summary)

    return report

def write_bias_report(report: BiasReport, output_path: Path) -> None:
    """Write bias report to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_dict = asdict(report)
    with open(output_path, "w") as f:
        json.dump(report_dict, f, indent=2)
    logger.info(f"Bias report written to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run bias check on excluded entries.")
    parser.add_argument("--input", type=str, required=True, help="Path to exclusion log JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output bias report JSON")
    
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    exclusion_reasons = load_exclusion_log(input_path)
    report = analyze_exclusion_bias(exclusion_reasons)
    write_bias_report(report, output_path)

if __name__ == "__main__":
    main()