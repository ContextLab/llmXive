"""
Script to run simulation on generated graphs and save results.
"""

import argparse
import logging
import sys
from pathlib import Path

from code.src.simulation.run_simulation import main as run_simulation_main

def setup_logging(log_level: int = logging.INFO) -> None:
    """Configure logging for the script."""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main() -> int:
    """Main entry point for the simulation runner script."""
    parser = argparse.ArgumentParser(description="Run simulation on generated graphs")
    parser.add_argument("--config", type=str, default="code/config.yaml",
                      help="Path to configuration file")
    parser.add_argument("--output", type=str, default="data/analysis",
                      help="Output directory for results")
    parser.add_argument("--graphs", type=str, default="data/raw",
                      help="Directory containing generated graphs")
    parser.add_argument("--log-level", type=str, default="INFO",
                      choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                      help="Logging level")

    args = parser.parse_args()
    setup_logging(getattr(logging, args.log_level.upper()))

    try:
        # Convert paths to Path objects
        config_path = Path(args.config)
        output_dir = Path(args.output)
        graphs_dir = Path(args.graphs)

        # Run the simulation
        exit_code = run_simulation_main([
            "--config", str(config_path),
            "--output", str(output_dir),
            "--graphs", str(graphs_dir)
        ])

        return exit_code

    except Exception as e:
        logging.error(f"Simulation runner failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())