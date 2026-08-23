import argparse
import logging
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.experiments.scaling import main as run_scaling_study_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Run scaling study for cortical column LLMs")
    parser.add_argument("--base-columns", type=int, default=4, help="Base number of columns")
    parser.add_argument("--multipliers", type=str, default="1,2,4", help="Comma-separated multipliers")
    parser.add_argument("--output", type=str, default="data/results/scaling_law.csv", help="Output CSV path")
    parser.add_argument("--train-size", type=int, default=5000, help="Training data size")
    parser.add_argument("--test-size", type=int, default=1000, help="Test data size")
    
    args = parser.parse_args()

    logger.info(f"Starting scaling study with base_columns={args.base_columns}")
    logger.info(f"Multipliers: {args.multipliers}")
    logger.info(f"Output: {args.output}")

    # Parse multipliers
    multipliers = [int(x) for x in args.multipliers.split(',')]

    # Import and run the study
    from src.experiments.scaling import run_scaling_study, create_scaling_configs, train_scaling_variant, save_scaling_results, verify_scaling_output
    
    # Generate data
    from src.data.benchmarks import generate_training_data
    train_data = generate_training_data(n_samples=args.train_size, seed=42)
    test_data = generate_training_data(n_samples=args.test_size, seed=123)

    configs = create_scaling_configs(args.base_columns, multipliers)
    results = []

    for config in configs:
        result = train_scaling_variant(config, train_data, test_data)
        results.append(result)

    save_scaling_results(results, args.output)

    if not verify_scaling_output(args.output):
        logger.error("Scaling output verification failed!")
        sys.exit(1)

    logger.info("Scaling study completed successfully")

if __name__ == "__main__":
    main()
