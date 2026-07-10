"""
CLI entry point for the Solvent Effects on Photo-Fries Rearrangement pipeline.

This module configures and executes a series of solvent experiments spanning
non-polar to moderate-polar conditions (low to moderate dielectric constant).
It orchestrates the workflow:
1. Validates environmental conditions (via T014).
2. Loads solvent properties from the versioned lookup table (T006/T008).
3. Filters solvents based on the requested dielectric constant range.
4. Logs the run configuration and environmental parameters.
5. Triggers the data ingestion or synthetic generation pipeline.

Dependencies:
- code/analysis/environment.py (T014)
- code/data/loaders.py (T008)
- code/data/ingest.py (T015b)
- code/data/generate_synthetic.py (T015)
- code/config.py (T009)
- code/utils/seeds.py (T004)
- code/utils/logging.py (T005)
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from project modules
from config import get_processed_data_path, get_raw_data_path, get_chemicals_path
from utils.seeds import set_seed
from utils.logging import setup_logging, log_environmental_params, log_compliance_check
from analysis.environment import validate_environmental_conditions, record_run_environment, get_environment_summary
from data.loaders import get_solvent_properties, get_all_solvents, get_dielectric_constant_range, SolventDataError
from data.ingest import ingest_real_transient_absorption_data
from data.generate_synthetic import generate_synthetic_traces

# Configure logger for this module
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for the solvent series configuration."""
    parser = argparse.ArgumentParser(
        description="Configure and execute a solvent series for Photo-Fries rearrangement kinetics."
    )
    parser.add_argument(
        "--solvents",
        type=str,
        nargs="+",
        default=None,
        help="Specific solvent names to include in the series. If None, uses range filtering."
    )
    parser.add_argument(
        "--epsilon-min",
        type=float,
        default=1.0,
        help="Minimum dielectric constant (epsilon) for the solvent series."
    )
    parser.add_argument(
        "--epsilon-max",
        type=float,
        default=15.0,
        help="Maximum dielectric constant (epsilon) for the solvent series."
    )
    parser.add_argument(
        "--use-synthetic",
        action="store_true",
        default=False,
        help="Force use of synthetic data generation (fallback for CI/testing)."
    )
    parser.add_argument(
        "--real-data-path",
        type=str,
        default=None,
        help="Path to real transient absorption data file. If provided, ingestion is attempted."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Override default output directory for processed logs."
    )
    return parser.parse_args()


def select_solvents(
    epsilon_min: float,
    epsilon_max: float,
    specific_solvents: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Select solvents from the lookup table based on dielectric constant range
    or specific names.

    Args:
        epsilon_min: Minimum dielectric constant.
        epsilon_max: Maximum dielectric constant.
        specific_solvents: Optional list of specific solvent names.

    Returns:
        List of solvent property dictionaries.

    Raises:
        SolventDataError: If no solvents match the criteria or specific names are invalid.
    """
    try:
        if specific_solvents:
            logger.info(f"Selecting specific solvents: {specific_solvents}")
            selected = []
            for name in specific_solvents:
                props = get_solvent_properties(name)
                if props:
                    selected.append(props)
                    logger.debug(f"Loaded solvent: {name} (ε={props.get('dielectric_constant')})")
                else:
                    logger.warning(f"Solvent '{name}' not found in lookup table.")
            
            if not selected:
                raise SolventDataError("No valid solvents found in the provided list.")
            return selected
        else:
            logger.info(f"Filtering solvents by dielectric constant range: [{epsilon_min}, {epsilon_max}]")
            all_solvents = get_all_solvents()
            filtered = [
                s for s in all_solvents
                if epsilon_min <= s.get("dielectric_constant", 0) <= epsilon_max
            ]
            
            if not filtered:
                raise SolventDataError(
                    f"No solvents found in range [{epsilon_min}, {epsilon_max}]. "
                    f"Available range: {get_dielectric_constant_range()}"
                )
            
            logger.info(f"Selected {len(filtered)} solvents for the series.")
            return filtered

    except SolventDataError:
        raise
    except Exception as e:
        raise SolventDataError(f"Error selecting solvents: {str(e)}")


def run_experiment_series(
    solvents: List[Dict[str, Any]],
    use_synthetic: bool,
    real_data_path: Optional[str],
    seed: int,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute the experimental protocol for the selected solvent series.

    1. Validates environmental conditions.
    2. Records the run environment.
    3. Ingests real data or generates synthetic traces.
    4. Logs the configuration and results.

    Args:
        solvents: List of solvent configurations.
        use_synthetic: Flag to force synthetic data generation.
        real_data_path: Path to real data file if available.
        seed: Random seed.
        output_dir: Optional override for output directory.

    Returns:
        Summary dictionary of the run.
    """
    set_seed(seed)
    logger.info(f"Running experiment series with seed: {seed}")
    
    # 1. Validate and Record Environment
    logger.info("Validating environmental conditions...")
    is_valid, issues = validate_environmental_conditions()
    if not is_valid:
        logger.warning(f"Environmental validation warnings: {issues}")
        # We proceed but log the warnings as per SC-010 handling
    
    env_summary = record_run_environment()
    logger.info(f"Environment recorded: {env_summary}")
    
    # 2. Determine Data Source
    processed_path = Path(output_dir) if output_dir else get_processed_data_path()
    processed_path.mkdir(parents=True, exist_ok=True)
    
    data_source = "synthetic"
    raw_data_file = None
    
    if real_data_path and not use_synthetic:
        logger.info(f"Attempting to ingest real data from: {real_data_path}")
        if os.path.exists(real_data_path):
            raw_data_file = real_data_path
            data_source = "real"
        else:
            logger.error(f"Real data file not found at: {real_data_path}. "
                         "Falling back to synthetic data generation as per T015 logic.")
            data_source = "synthetic"
    elif use_synthetic:
        logger.info("Forcing synthetic data generation.")
        data_source = "synthetic"
    
    # 3. Process Data
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "solvents": [s["name"] for s in solvents],
        "epsilon_range": {
            "min": min(s["dielectric_constant"] for s in solvents),
            "max": max(s["dielectric_constant"] for s in solvents)
        },
        "environment": env_summary,
        "data_source": data_source,
        "runs": []
    }
    
    for solvent in solvents:
        solvent_name = solvent["name"]
        logger.info(f"Processing solvent: {solvent_name} (ε={solvent['dielectric_constant']})")
        
        run_result = {
            "solvent": solvent_name,
            "epsilon": solvent["dielectric_constant"],
            "status": "completed"
        }
        
        if data_source == "real":
            # Ingest real data for this solvent (simulated by filtering or mapping)
            # In a real scenario, the ingest function would handle the file parsing
            # Here we assume the real_data_path contains data for the series or a specific run
            try:
                # We call the ingest function which validates the file existence
                # and returns the data structure. For this CLI, we assume the file
                # contains the necessary data for the series.
                data_df = ingest_real_transient_absorption_data(raw_data_file)
                # In a real implementation, we would filter data_df by solvent_name
                # For now, we log the ingestion success
                run_result["data_points"] = len(data_df) if data_df is not None else 0
            except Exception as e:
                run_result["status"] = "failed"
                run_result["error"] = str(e)
                logger.error(f"Failed to ingest data for {solvent_name}: {e}")
        else:
            # Generate synthetic traces
            try:
                trace_data = generate_synthetic_traces(
                    solvent_name=solvent_name,
                    epsilon=solvent["dielectric_constant"],
                    seed=seed
                )
                run_result["data_points"] = len(trace_data) if trace_data is not None else 0
            except Exception as e:
                run_result["status"] = "failed"
                run_result["error"] = str(e)
                logger.error(f"Failed to generate synthetic data for {solvent_name}: {e}")
        
        results["runs"].append(run_result)
    
    # 4. Log Compliance
    log_compliance_check("solvent_series_config", results)
    
    # 5. Save Summary
    summary_file = processed_path / "experiment_series_summary.json"
    with open(summary_file, "w") as f:
        import json
        json.dump(results, f, indent=2)
    
    logger.info(f"Experiment series summary saved to: {summary_file}")
    return results


def main():
    """Main entry point for the CLI."""
    args = parse_arguments()
    
    # Setup logging
    log_level = logging.DEBUG if args.use_synthetic else logging.INFO
    setup_logging(level=log_level)
    
    logger.info("Starting Solvent Effects Pipeline (T013)")
    
    try:
        # Select solvents
        solvents = select_solvents(
            epsilon_min=args.epsilon_min,
            epsilon_max=args.epsilon_max,
            specific_solvents=args.solvents
        )
        
        # Run the series
        results = run_experiment_series(
            solvents=solvents,
            use_synthetic=args.use_synthetic,
            real_data_path=args.real_data_path,
            seed=args.seed,
            output_dir=args.output_dir
        )
        
        logger.info("Pipeline execution completed successfully.")
        print(f"Completed: {len(results['runs'])} runs processed.")
        
    except SolventDataError as e:
        logger.critical(f"Data configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()