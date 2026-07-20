"""
Bias check analysis for excluded entries.
"""
import os
import json
import logging
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

@dataclass
class BiasReport:
    summary: Dict[str, int]
    total_excluded: int
    report: List[Dict[str, Any]]

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

    for reason in exclusion_reasons:
        # Count by category
        category_counts[reason.category] = category_counts.get(reason.category, 0) + 1
        
        # Add to detailed report
        detailed_report.append({
            "material_id": reason.material_id,
            "reason": reason.reason,
            "category": reason.category
        })

    # Check for small families (example logic)
    # This is a placeholder for actual family analysis if data supports it
    # For now, we just report the categories

    report = BiasReport(
        summary=category_counts,
        total_excluded=len(exclusion_reasons),
        report=detailed_report
    )

    # Log bias check results
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