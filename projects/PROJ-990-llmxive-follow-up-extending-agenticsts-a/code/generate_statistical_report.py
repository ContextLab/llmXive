"""
T028: Generate final statistical report.
Aggregates results from token reduction verification and statistical testing
into the final statistical_results.json artifact.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_token_reduction_verification(path: Path) -> Dict[str, Any]:
    """Load token reduction verification results."""
    return load_json_file(path)

def load_statistical_results(path: Path) -> Dict[str, Any]:
    """Load statistical testing results."""
    return load_json_file(path)

def generate_final_report(
    token_reduction_data: Dict[str, Any],
    statistical_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate the final statistical report by aggregating all results.

    Schema: {
        p_value: float,
        effect_size: float,
        test_type: str,
        bonferroni_adjusted: float,
        divergence_status: bool,
        token_reduction_percent: float,
        token_reduction_passed: bool
    }
    """
    report = {
        # From statistical testing (T025)
        "p_value": statistical_data.get("p_value"),
        "effect_size": statistical_data.get("effect_size"),
        "test_type": statistical_data.get("test_type"),
        "bonferroni_adjusted": statistical_data.get("bonferroni_adjusted_p_value"),
        "divergence_status": statistical_data.get("divergence_status"),
        
        # From token reduction verification (T022a)
        "token_reduction_percent": token_reduction_data.get("actual_reduction_percent"),
        "token_reduction_passed": token_reduction_data.get("passed", False)
    }

    # Validate required fields
    required_fields = ["p_value", "effect_size", "test_type", "bonferroni_adjusted", 
                     "divergence_status", "token_reduction_percent", "token_reduction_passed"]
    missing = [f for f in required_fields if report[f] is None]
    if missing:
        raise ValueError(f"Missing required fields in generated report: {missing}")

    return report

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the final report to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Final statistical report saved to {output_path}")

def main():
    """Main entry point for T028."""
    project_root = Path(__file__).parent.parent
    processed_dir = project_root / "data" / "processed"

    # Define input paths
    token_reduction_path = processed_dir / "token_reduction_verification.json"
    statistical_path = processed_dir / "statistical_results.json"
    output_path = processed_dir / "statistical_results.json"

    logger.info("Starting T028: Generate final statistical report")

    try:
        # Load input data
        logger.info(f"Loading token reduction verification from {token_reduction_path}")
        token_reduction_data = load_token_reduction_verification(token_reduction_path)

        logger.info(f"Loading statistical results from {statistical_path}")
        statistical_data = load_statistical_results(statistical_path)

        # Generate final report
        logger.info("Generating final aggregated report")
        final_report = generate_final_report(token_reduction_data, statistical_data)

        # Save report
        save_report(final_report, output_path)

        logger.info("T028 completed successfully")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
