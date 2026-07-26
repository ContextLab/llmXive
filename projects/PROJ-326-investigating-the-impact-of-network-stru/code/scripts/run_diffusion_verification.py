"""
Script to run diffusion rate verification on simulation results.

This script loads simulation output from data/analysis/simulation_results.json,
calculates diffusion rates for each run, and saves verification results to
data/analysis/diffusion_verification.json.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

from code.src.simulation.diffusion import compute_diffusion_from_simulation

logger = logging.getLogger(__name__)


def load_simulation_results(input_path: Path) -> List[Dict[str, Any]]:
    """Load simulation results from JSON file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Simulation results file not found: {input_path}")

    with open(input_path, "r") as f:
        data = json.load(f)

    # Handle both single object and list of objects
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "results" in data:
        return data["results"]
    else:
        # Assume single result wrapped in a list
        return [data]


def main():
    parser = argparse.ArgumentParser(
        description="Run diffusion rate verification on simulation results."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/analysis/simulation_results.json",
        help="Path to simulation results JSON file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/analysis/diffusion_verification.json",
        help="Path to save diffusion verification results."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level."
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load simulation results
        simulations = load_simulation_results(input_path)
        logger.info(f"Loaded {len(simulations)} simulation results.")

        verification_results = []
        success_count = 0
        failure_count = 0

        for sim in simulations:
            try:
                # Extract necessary fields
                sim_data = {
                    "spatial_variance_history": sim.get("spatial_variance_history"),
                    "time_steps": sim.get("time_steps"),
                    "network_id": sim.get("network_id", "unknown"),
                    "seed": sim.get("seed", -1)
                }

                if sim_data["spatial_variance_history"] is None:
                    logger.warning(
                        f"Skipping {sim_data['network_id']}: "
                        "No spatial_variance_history found."
                    )
                    failure_count += 1
                    continue

                # Compute diffusion
                result = compute_diffusion_from_simulation(sim_data)
                verification_results.append(result)
                success_count += 1

            except Exception as e:
                logger.error(
                    f"Error processing simulation {sim.get('network_id', 'unknown')}: {e}"
                )
                failure_count += 1
                # Add error record
                verification_results.append({
                    "network_id": sim.get("network_id", "unknown"),
                    "error": str(e),
                    "status": "failed"
                })

        # Aggregate summary
        summary = {
            "total_processed": len(simulations),
            "successful": success_count,
            "failed": failure_count,
            "verification_results": verification_results
        }

        # Save results
        with open(output_path, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Diffusion verification complete. Results saved to {output_path}")
        logger.info(f"Success: {success_count}, Failed: {failure_count}")

        return 0

    except Exception as e:
        logger.error(f"Fatal error during diffusion verification: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())