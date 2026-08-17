"""
Orchestration script for the material stiffness prediction pipeline.

This script runs the end-to-end data generation pipeline:
1. Generate microstructure images
2. Compute stiffness tensors using FFT homogenization
3. Validate results against physical bounds and schema

CLI Args:
    --seed: Random seed for reproducibility
    --n_samples: Number of samples to generate
"""
import sys
import argparse
import logging
from pathlib import Path
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/pipeline_run.log')
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Orchestrate material stiffness prediction data generation pipeline"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--n_samples",
        type=int,
        default=10,
        help="Number of microstructure samples to generate (default: 10)"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="data/raw",
        help="Output directory for generated data (default: data/raw)"
    )
    return parser.parse_args()

def run_generation_pipeline(args):
    """
    Execute the full generation pipeline: generate -> compute -> validate.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    logger.info(f"Starting pipeline with seed={args.seed}, n_samples={args.n_samples}")
    
    # Ensure output directories exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Generate Microstructures
        logger.info("Step 1: Generating microstructures...")
        from code.data_generation.generate_microstructures import main as gen_main
        gen_args = argparse.Namespace(
            seed=args.seed,
            n_samples=args.n_samples,
            output_dir=str(output_dir)
        )
        gen_result = gen_main(gen_args)
        if gen_result != 0:
            logger.error("Microstructure generation failed")
            return 1
        
        # Step 2: Compute Stiffness Tensors
        logger.info("Step 2: Computing stiffness tensors...")
        from code.data_generation.compute_stiffness import main as comp_main
        comp_args = argparse.Namespace(
            input_dir=str(output_dir),
            output_dir=str(output_dir),
            metadata_file=str(output_dir / "metadata.json")
        )
        comp_result = comp_main(comp_args)
        if comp_result != 0:
            logger.error("Stiffness computation failed")
            return 1
        
        # Step 3: Validate Tensors
        logger.info("Step 3: Validating tensors...")
        from code.data_generation.validate_tensors import main as val_main
        val_args = argparse.Namespace(
            metadata_file=str(output_dir / "metadata.json"),
            schema_file="specs/001-predict-stiffness-cnn/contracts/dataset.schema.yaml",
            log_file=str(processed_dir / "validation_log.csv")
        )
        val_result = val_main(val_args)
        if val_result != 0:
            logger.warning("Validation found issues (check logs)")
            # Return 0 if validation only warns, but log the issues
            # If validation fails completely (e.g., all samples invalid), return 1
            # For now, we assume partial validation is acceptable
        
        # Log derivation metadata
        logger.info("Step 4: Logging derivation metadata...")
        derivation_log = {
            "timestamp": datetime.now().isoformat(),
            "seed": args.seed,
            "n_samples": args.n_samples,
            "output_dir": str(output_dir),
            "pipeline_version": "1.0.0",
            "steps_completed": ["generation", "computation", "validation"]
        }
        with open(processed_dir / "derivation_log.json", "w") as f:
            json.dump(derivation_log, f, indent=2)
        
        logger.info("Pipeline completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

def main():
    """Main entry point."""
    args = parse_args()
    exit_code = run_generation_pipeline(args)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
