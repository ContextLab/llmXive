"""
Main orchestration script for llmXive EVA-Bench extension.

Handles argument parsing for perturbation types and orchestrates
the pipeline execution.
"""
import argparse
import sys
import logging
from pathlib import Path

# Import project utilities
from config import ensure_directories
from logging_config import setup_logging
from synthetic.tts_engine import TTSEngine
from utils.checksum_manager import init_checksums, add_file_checksum, save_checksums

def parse_args():
    """Parse command line arguments for perturbation configuration."""
    parser = argparse.ArgumentParser(
        description="Orchestrate EVA-Bench perturbation pipeline"
    )
    
    # Perturbation type selection
    parser.add_argument(
        "--perturbation-types",
        type=str,
        nargs="+",
        choices=["latency", "acoustic", "all"],
        default=["all"],
        help="Types of perturbations to apply (latency, acoustic, or all)"
    )
    
    # Configuration parameters
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/raw",
        help="Directory containing input EVA-Bench audio files"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory for perturbed output files"
    )
    
    parser.add_argument(
        "--latency-min",
        type=float,
        default=200.0,
        help="Minimum latency in milliseconds (default: 200ms)"
    )
    
    parser.add_argument(
        "--latency-max",
        type=float,
        default=2000.0,
        help="Maximum latency in milliseconds (default: 2000ms)"
    )
    
    parser.add_argument(
        "--jitter-enabled",
        action="store_true",
        default=False,
        help="Enable jitter in latency injection"
    )
    
    parser.add_argument(
        "--noise-snr",
        type=float,
        default=20.0,
        help="Signal-to-noise ratio for acoustic perturbation (default: 20dB)"
    )
    
    parser.add_argument(
        "--reverb-enabled",
        action="store_true",
        default=False,
        help="Enable reverberation in acoustic perturbation"
    )
    
    # Execution control
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Validate configuration without executing pipeline"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def validate_perturbation_types(types):
    """Validate perturbation type configuration."""
    if not types:
        return False, "At least one perturbation type must be specified"
    
    if "all" in types:
        return True, ["latency", "acoustic"]
    
    return True, types

def main():
    """Main entry point for orchestration."""
    args = parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(
        level=log_level,
        log_file="data/processed/pipeline.log" if not args.dry_run else None
    )
    
    logger.info("Starting llmXive EVA-Bench perturbation pipeline")
    logger.info(f"Configuration: {vars(args)}")
    
    # Validate directories
    try:
        ensure_directories(args.input_dir, args.output_dir)
        logger.info("Directory structure validated")
    except Exception as e:
        logger.error(f"Directory validation failed: {e}")
        sys.exit(1)
    
    # Initialize checksum tracking
    if not args.dry_run:
        init_checksums("data/checksums.json")
    
    # Validate perturbation types
    valid, result = validate_perturbation_types(args.perturbation_types)
    if not valid:
        logger.error(result)
        sys.exit(1)
    
    perturbation_types = result
    logger.info(f"Perturbation types enabled: {perturbation_types}")
    
    if args.dry_run:
        logger.info("Dry run completed successfully")
        logger.info("Configuration validated. Ready to execute pipeline.")
        return 0
    
    # Pipeline execution would continue here with:
    # 1. Load input audio files
    # 2. Apply selected perturbations (latency/acoustic)
    # 3. Save perturbed audio to output directory
    # 4. Update checksums
    # 5. Generate summary report
    
    # Placeholder for future implementation
    logger.info("Pipeline skeleton ready. Implementation of perturbation engines pending.")
    
    # Update checksums for this run configuration
    try:
        # In a full implementation, we would checksum actual output files
        # For now, we acknowledge the pipeline ran
        logger.info("Pipeline execution completed (skeleton mode)")
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())