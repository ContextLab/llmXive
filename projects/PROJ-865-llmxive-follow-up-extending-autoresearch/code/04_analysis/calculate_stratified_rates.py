"""
Calculate Success Rate of First Pivot stratified by failure type.

This script loads the merged results from T022 (results.csv), calculates the
success rate for each failure type, and verifies that the weighted average
of these rates equals the overall success rate.

Output: data/derived/stratified_success_rates.csv
"""

import json
import csv
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict

# Add project root to path for imports if running as script
if "code" not in sys.path[0]:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import TIMEOUT_SECONDS

logger = get_logger(__name__)

def load_results_csv(filepath: Path) -> List[Dict[str, Any]]:
    """Load the merged results CSV file."""
    if not filepath.exists():
        logger.error(f"Results file not found: {filepath}")
        raise FileNotFoundError(f"Results file not found: {filepath}")

    results = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row["time_to_pivot"] = float(row["time_to_pivot"])
            row["success"] = row["success"].lower() == "true"
            results.append(row)

    if not results:
        logger.error("Results file is empty.")
        raise ValueError("Results file is empty.")

    return results

def calculate_stratified_rates(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """
    Calculate success rate stratified by failure_type.

    Returns a dict: { failure_type: { "rate": float, "count": int, "successes": int } }
    """
    stats = defaultdict(lambda: {"successes": 0, "total": 0})

    for row in results:
        failure_type = row["failure_type"]
        stats[failure_type]["total"] += 1
        if row["success"]:
            stats[failure_type]["successes"] += 1

    rates = {}
    for failure_type, data in stats.items():
        rate = data["successes"] / data["total"] if data["total"] > 0 else 0.0
        rates[failure_type] = {
            "rate": rate,
            "count": data["total"],
            "successes": data["successes"]
        }

    return rates

def verify_weighted_average(stratified_rates: Dict[str, Dict[str, float]], overall_success_rate: float, tolerance: float = 1e-6) -> bool:
    """
    Verify that the sum of rates weighted by sample size equals the overall success rate.

    Weighted Average = Sum(rate_i * count_i) / Sum(count_i)
    """
    total_count = 0
    weighted_sum = 0.0

    for data in stratified_rates.values():
        count = data["count"]
        rate = data["rate"]
        weighted_sum += rate * count
        total_count += count

    if total_count == 0:
        logger.warning("Total count is zero, cannot verify weighted average.")
        return False

    calculated_overall = weighted_sum / total_count
    diff = abs(calculated_overall - overall_success_rate)

    logger.info(f"Overall success rate: {overall_success_rate:.4f}")
    logger.info(f"Weighted average from stratified rates: {calculated_overall:.4f}")
    logger.info(f"Difference: {diff:.6f}")

    if diff > tolerance:
        logger.error(f"Weighted average mismatch! Diff: {diff}")
        return False

    return True

def write_stratified_rates_csv(rates: Dict[str, Dict[str, float]], output_path: Path) -> None:
    """Write the stratified rates to a CSV file in long format."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["failure_type", "rate", "count", "successes"])

        # Sort by failure_type for reproducibility
        for failure_type in sorted(rates.keys()):
            data = rates[failure_type]
            writer.writerow([
                failure_type,
                f"{data['rate']:.6f}",
                data["count"],
                data["successes"]
            ])

    logger.info(f"Stratified rates written to {output_path}")

def save_stratified_rates_json(rates: Dict[str, Dict[str, float]], overall_rate: float, output_path: Path) -> None:
    """Save the results as JSON for downstream tasks."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "overall_success_rate": overall_rate,
        "stratified_rates": {
            k: {
                "rate": v["rate"],
                "count": v["count"],
                "successes": v["successes"]
            }
            for k, v in rates.items()
        }
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Stratified rates JSON written to {output_path}")

def main() -> int:
    """Main entry point."""
    log_stage_start("calculate_stratified_rates")

    # Paths
    results_csv_path = Path("data/derived/results.csv")
    output_csv_path = Path("data/derived/stratified_success_rates.csv")
    output_json_path = Path("data/derived/stratified_success_rates.json")

    try:
        # Load data
        logger.info(f"Loading results from {results_csv_path}")
        results = load_results_csv(results_csv_path)

        # Calculate overall success rate
        total_successes = sum(1 for r in results if r["success"])
        total_count = len(results)
        overall_rate = total_successes / total_count if total_count > 0 else 0.0

        # Calculate stratified rates
        logger.info("Calculating stratified success rates...")
        stratified_rates = calculate_stratified_rates(results)

        # Verify weighted average
        logger.info("Verifying weighted average consistency...")
        is_valid = verify_weighted_average(stratified_rates, overall_rate)

        if not is_valid:
            logger.error("Verification failed. Exiting with error.")
            return 1

        # Write outputs
        logger.info("Writing output files...")
        write_stratified_rates_csv(stratified_rates, output_csv_path)
        save_stratified_rates_json(stratified_rates, overall_rate, output_json_path)

        log_stage_end("calculate_stratified_rates", status="success")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        log_stage_end("calculate_stratified_rates", status="failed", error=str(e))
        return 1
    except ValueError as e:
        logger.error(f"Data error: {e}")
        log_stage_end("calculate_stratified_rates", status="failed", error=str(e))
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        log_stage_end("calculate_stratified_rates", status="failed", error=str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())