import sys
import argparse
import logging
from pathlib import Path
import json
from datetime import datetime

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Predicting Material Stiffness from Microstructure Images"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--n_samples",
        type=int,
        default=100,
        help="Number of samples to generate"
    )
    parser.add_argument(
        "--task",
        type=str,
        default="all",
        choices=["all", "generate", "train", "evaluate", "verify"],
        help="Task to execute"
    )
    return parser.parse_args()

def run_generation_pipeline(seed, n_samples):
    """Run the data generation pipeline."""
    logging.info(f"Starting generation pipeline with seed={seed}, n_samples={n_samples}")
    
    # Import and run generation components
    from code.data_generation.generate_microstructures import main as generate_main
    from code.data_generation.compute_stiffness import main as compute_main
    from code.data_generation.validate_tensors import main as validate_main
    
    # Run generation
    logging.info("Generating microstructures...")
    generate_main()
    
    # Compute stiffness
    logging.info("Computing stiffness tensors...")
    compute_main()
    
    # Validate tensors
    logging.info("Validating tensors...")
    validate_main()
    
    logging.info("Generation pipeline completed successfully")

def run_verification():
    """Run governance verification tasks."""
    logging.info("Running governance verification...")
    
    # Run T005v verification
    from code.utils.verify_spec_anova import main as verify_anova_main
    
    logging.info("Verifying Spec/Plan alignment (T005v)...")
    verify_anova_main()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if args.task == "verify":
        run_verification()
    elif args.task == "generate":
        run_generation_pipeline(args.seed, args.n_samples)
    elif args.task == "all":
        run_verification()
        run_generation_pipeline(args.seed, args.n_samples)
    else:
        logging.error(f"Unknown task: {args.task}")
        sys.exit(1)

if __name__ == "__main__":
    main()
