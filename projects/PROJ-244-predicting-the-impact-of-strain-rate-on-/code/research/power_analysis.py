import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "data" / "logs"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "power_analysis.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def perform_power_analysis(sample_size_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform power analysis based on sample size estimates.
    Rules:
    - If N < 1000, flag as "Underpowered".
    - If any alloy family N < 50, flag as "Underpowered".
    """
    total_n = sample_size_data.get("total_sample_size", 0)
    family_counts = sample_size_data.get("per_family_counts", {})
    
    is_underpowered = False
    flags = []
    recommendations = []

    if total_n < 1000:
        is_underpowered = True
        flags.append(f"Total sample size (N={total_n}) is less than 1000.")
        recommendations.append("Increase overall data collection or simulation scope.")

    for family, count in family_counts.items():
        if count < 50:
            is_underpowered = True
            flags.append(f"Alloy family '{family}' has N={count}, which is less than 50.")
            recommendations.append(f"Increase data for '{family}' family.")

    return {
        "is_underpowered": is_underpowered,
        "total_sample_size": total_n,
        "per_family_counts": family_counts,
        "flags": flags,
        "recommendations": recommendations,
        "status": "Underpowered" if is_underpowered else "Adequate"
    }

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the power analysis report to a JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Power analysis report saved to {output_path}")

def main():
    """
    Main entry point for power analysis (T010).
    """
    logger.info("Starting power analysis (T010).")
    
    # Load sample size estimate from T009
    sample_size_path = DATA_DIR / "sample_size_estimate.json"
    if not sample_size_path.exists():
        logger.error(f"Sample size estimate not found at {sample_size_path}. Run T009 first.")
        return 1
    
    with open(sample_size_path, 'r') as f:
        sample_data = json.load(f)
    
    report = perform_power_analysis(sample_data)
    
    output_path = DATA_DIR / "power_analysis_report.json"
    save_report(report, output_path)
    
    logger.info(f"Power Analysis Status: {report['status']}")
    if report['flags']:
        logger.warning("Flags:")
        for flag in report['flags']:
            logger.warning(f"  - {flag}")
        logger.info("Recommendations:")
        for rec in report['recommendations']:
            logger.info(f"  - {rec}")
    else:
        logger.info("No power issues detected.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
