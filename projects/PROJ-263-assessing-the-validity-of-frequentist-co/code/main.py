import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Import from existing modules as per API surface
from config import load_config, get_data_dir, get_output_dir, get_simulation_config, set_random_seed, initialize_random_state
from data_cleaner import clean_dataset_for_simulation
from population_mean_calculator import calculate_population_means, save_population_means
from simulation import run_monte_carlo_simulation, load_population_means
from coverage import create_coverage_record, save_coverage_records
from edge_case_handler import process_datasets_for_simulation

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure logging for the simulation workflow."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Monte Carlo Simulation for CI Validity")
    parser.add_argument('--config', type=str, default='config/simulation_config.yaml',
                        help='Path to configuration file')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducibility')
    parser.add_argument('--datasets', type=str, nargs='+', default=None,
                        help='Specific datasets to process (optional)')
    return parser.parse_args()

def load_and_prepare_datasets(config: dict, logger: logging.Logger, specific_datasets: list = None) -> dict:
    """Load and clean datasets, handling edge cases."""
    logger.info("Loading and preparing datasets...")
    data_dir = get_data_dir(config)
    raw_data_dir = Path(data_dir) / "raw"
    
    # Ensure raw data exists (in a real run, this would be populated by download tasks)
    # For this task, we assume the download task (T016) has been run or will be run.
    # We proceed with the datasets specified or from config.
    
    datasets_to_process = specific_datasets or config.get('datasets', [])
    if not datasets_to_process:
        logger.warning("No datasets specified in config or arguments. Exiting.")
        return {}

    processed_datasets = {}
    for dataset_id in datasets_to_process:
        try:
            logger.info(f"Processing dataset: {dataset_id}")
            # This function handles loading, cleaning, and validation
            cleaned_data = clean_dataset_for_simulation(dataset_id, raw_data_dir, logger)
            if cleaned_data is not None:
                processed_datasets[dataset_id] = cleaned_data
            else:
                logger.warning(f"Dataset {dataset_id} was skipped due to validation errors.")
        except Exception as e:
            logger.error(f"Failed to process dataset {dataset_id}: {e}")
    
    return processed_datasets

def run_simulation_workflow(config: dict, datasets: dict, logger: logging.Logger) -> list:
    """Run the main Monte Carlo simulation loop."""
    logger.info("Starting simulation workflow...")
    sim_config = get_simulation_config(config)
    sample_sizes = sim_config.get('sample_sizes', [10, 20, 30])
    n_replications = sim_config.get('n_replications', 1000)
    confidence_levels = sim_config.get('confidence_levels', [0.95])
    
    all_records = []
    
    for dataset_id, data in datasets.items():
        logger.info(f"Running simulation for dataset: {dataset_id}")
        
        # Calculate population means if not already done
        pop_means_path = Path(get_data_dir(config)) / "processed" / "population_means.json"
        if not pop_means_path.exists():
            logger.info("Calculating population means...")
            pop_means = calculate_population_means(dataset_id, data, logger)
            save_population_means(dataset_id, pop_means, pop_means_path)
        else:
            logger.info(f"Loading existing population means from {pop_means_path}")
            # In a real scenario, we would load from file here
            # For this implementation, we assume the simulation module handles loading
        
        # Run Monte Carlo simulation
        records = run_monte_carlo_simulation(
            dataset_id=dataset_id,
            data=data,
            sample_sizes=sample_sizes,
            n_replications=n_replications,
            confidence_levels=confidence_levels,
            logger=logger
        )
        all_records.extend(records)
    
    return all_records

def save_results(records: list, config: dict, logger: logging.Logger):
    """Save coverage records to the specified output file."""
    logger.info("Saving results...")
    output_dir = get_output_dir(config)
    output_path = Path(output_dir) / "coverage_records.json"
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Use the coverage module's save function
    save_coverage_records(records, output_path)
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for the simulation."""
    args = parse_arguments()
    logger = setup_logging()
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Initialize random state
        seed = args.seed if args.seed is not None else config.get('random_seed')
        if seed is not None:
            set_random_seed(seed)
            initialize_random_state(seed)
            logger.info(f"Random seed set to: {seed}")
        
        # Load and prepare datasets
        datasets = load_and_prepare_datasets(config, logger, args.datasets)
        
        if not datasets:
            logger.error("No datasets were successfully loaded. Exiting.")
            sys.exit(1)
        
        # Run simulation
        records = run_simulation_workflow(config, datasets, logger)
        
        if not records:
            logger.warning("No simulation records were generated.")
            sys.exit(0)
        
        # Save results
        save_results(records, config, logger)
        
        logger.info("Simulation completed successfully.")
        
    except Exception as e:
        logger.exception(f"An error occurred during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
