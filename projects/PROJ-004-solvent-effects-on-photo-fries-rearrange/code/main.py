"""
Main CLI entry point for the Solvent Effects on Photo-Fries Rearrangement project.

This module orchestrates the experimental workflow:
1. Parses command-line arguments for mode (simulate/real) and configuration.
2. Configures the solvent series (multiple solvents, epsilon range low to moderate).
3. Invokes the environment logging module (T014) to record experimental conditions.
4. Executes the selected workflow (simulation or real data ingestion).

Dependencies:
- analysis.environment (T014): For logging environmental parameters.
- data.loaders: For fetching solvent properties.
- data.ingest (T015b): For real data ingestion.
- data.generate_synthetic (T015): For synthetic data generation (fallback).
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Import from sibling modules using the exact API surface provided
from analysis.environment import record_run_environment, write_environment_logs
from data.loaders import get_solvent_properties, get_all_solvents, SolventDataError
from data.ingest import ingest_real_transient_absorption_data
from data.generate_synthetic import generate_synthetic_traces
from utils.logging import setup_logging, log_environmental_params
from utils.seeds import set_seed
from config import get_processed_data_path, get_raw_data_path, ensure_directories


def parse_arguments():
    """
    Parse command-line arguments for the main experiment runner.

    Returns:
        argparse.Namespace: Parsed arguments including mode, solvents, and paths.
    """
    parser = argparse.ArgumentParser(
        description="CLI entry point for Solvent Effects on Photo-Fries Rearrangement."
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["simulate", "real"],
        default="simulate",
        help="Mode of execution: 'simulate' uses synthetic data, 'real' uses real data ingestion."
    )
    parser.add_argument(
        "--solvents",
        type=str,
        nargs="+",
        default=["cyclohexane", "toluene", "acetonitrile", "methanol"],
        help="List of solvent names to include in the series (default: low to moderate epsilon)."
    )
    parser.add_argument(
        "--n-replicates",
        type=int,
        default=3,
        help="Number of replicates per solvent condition (default: 3)."
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Path to real data file (required if mode='real' and USE_REAL_DATA is set)."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level (default: INFO)."
    )
    return parser.parse_args()


def select_solvents(solvent_names):
    """
    Select and validate a series of solvents from the lookup table.

    Args:
        solvent_names (list): List of solvent names to select.

    Returns:
        list: List of validated solvent property dictionaries.

    Raises:
        SystemExit: If a requested solvent is not found in the lookup table.
    """
    selected_solvents = []
    available_solvents = get_all_solvents()
    available_names = [s['name'] for s in available_solvents]

    for name in solvent_names:
        if name not in available_names:
            logging.error(f"Solvent '{name}' not found in lookup table. Available: {available_names}")
            raise SystemExit(1)
        
        props = get_solvent_properties(name)
        if props:
            selected_solvents.append(props)
            logging.info(f"Selected solvent: {name} (ε={props.get('dielectric_constant', 'N/A')})")
        else:
            logging.warning(f"Could not retrieve properties for {name}, skipping.")

    if not selected_solvents:
        logging.error("No valid solvents selected. Exiting.")
        raise SystemExit(1)

    # Sort by dielectric constant (low to moderate)
    selected_solvents.sort(key=lambda x: x.get('dielectric_constant', 0))
    return selected_solvents


def run_experiment_series(solvents, n_replicates, mode, data_path=None):
    """
    Execute the experiment series for the selected solvents.

    This function:
    1. Logs the experimental configuration.
    2. Iterates through each solvent and replicate.
    3. Records environmental conditions for each run.
    4. Generates synthetic data or ingests real data as per mode.

    Args:
        solvents (list): List of validated solvent dictionaries.
        n_replicates (int): Number of replicates per solvent.
        mode (str): Execution mode ('simulate' or 'real').
        data_path (str, optional): Path to real data file.

    Returns:
        dict: Summary of the experiment run.
    """
    ensure_directories()
    processed_path = get_processed_data_path()
    raw_path = get_raw_data_path()

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    environment_logs = []

    logging.info(f"Starting experiment series: Run ID={run_id}")
    logging.info(f"Solvents: {[s['name'] for s in solvents]}")
    logging.info(f"Replicates per solvent: {n_replicates}")
    logging.info(f"Mode: {mode}")

    for solvent in solvents:
        solvent_name = solvent['name']
        epsilon = solvent.get('dielectric_constant', 'Unknown')
        logging.info(f"Processing solvent: {solvent_name} (ε={epsilon})")

        for i in range(1, n_replicates + 1):
            run_name = f"{run_id}_{solvent_name}_rep{i}"
            logging.info(f"  Running replicate {i}/{n_replicates}...")

            # 1. Record environmental conditions (T014 dependency)
            env_data = record_run_environment(
                run_id=run_name,
                solvent_name=solvent_name,
                dielectric_constant=epsilon,
                replicate=i,
                substrate_mass=0.150,  # Example: 150 mg (per FR-007)
                integration_time_ms=100.0  # Example: 100 ms
            )
            environment_logs.append(env_data)

            # 2. Execute data generation/ingestion based on mode
            if mode == "simulate":
                # Generate synthetic trace for this run
                output_file = raw_path / f"synthetic_{run_name}.csv"
                generate_synthetic_traces(
                    output_path=str(output_file),
                    solvent=solvent_name,
                    replicate=i,
                    seed=(i * 100)  # Deterministic seed per replicate
                )
                logging.info(f"    Generated synthetic data: {output_file}")
            elif mode == "real":
                # Ingest real data
                if data_path and os.path.exists(data_path):
                    try:
                        ingest_real_transient_absorption_data(
                            input_path=data_path,
                            output_dir=str(raw_path),
                            solvent=solvent_name,
                            replicate=i,
                            run_id=run_name
                        )
                        logging.info(f"    Ingested real data for {run_name}")
                    except FileNotFoundError as e:
                        logging.error(f"    Real data ingestion failed: {e}")
                        raise
                else:
                    # Fallback to synthetic if real data path is missing (only if USE_REAL_DATA is not enforced)
                    use_real = os.getenv("USE_REAL_DATA", "").lower() == "true"
                    if use_real:
                        logging.error("USE_REAL_DATA=true but data path missing or file not found.")
                        raise FileNotFoundError(f"Real data file not found at {data_path}")
                    
                    logging.warning("Real data path missing, falling back to synthetic (USE_REAL_DATA not enforced).")
                    output_file = raw_path / f"synthetic_{run_name}.csv"
                    generate_synthetic_traces(
                        output_path=str(output_file),
                        solvent=solvent_name,
                        replicate=i,
                        seed=(i * 100)
                    )

    # 3. Write consolidated environment logs (T014 output)
    env_log_path = processed_path / "environment_logs.json"
    write_environment_logs(environment_logs, str(env_log_path))
    logging.info(f"Environment logs written to: {env_log_path}")

    return {
        "run_id": run_id,
        "solvents": [s['name'] for s in solvents],
        "total_runs": len(solvents) * n_replicates,
        "environment_log_path": str(env_log_path)
    }


def main():
    """
    Main entry point for the CLI.
    """
    args = parse_arguments()

    # Setup logging
    setup_logging(level=args.log_level)

    # Set random seeds for reproducibility
    set_seed(args.seed)

    try:
        # Select solvents
        selected_solvents = select_solvents(args.solvents)

        # Run the experiment series
        result = run_experiment_series(
            solvents=selected_solvents,
            n_replicates=args.n_replicates,
            mode=args.mode,
            data_path=args.data_path
        )

        logging.info("Experiment series completed successfully.")
        logging.info(f"Summary: {result}")

    except SolventDataError as e:
        logging.error(f"Solvent data error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()