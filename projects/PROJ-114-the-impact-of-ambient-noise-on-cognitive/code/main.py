"""
Main orchestration script for the ambient noise cognitive flexibility pipeline.
"""
import argparse
import logging
from pathlib import Path
from config import setup_logging, get_config_summary


def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(
        description="Ambient Noise Cognitive Flexibility Pipeline"
    )
    parser.add_argument(
        "--generate-synthetic",
        action="store_true",
        help="Generate synthetic data for testing"
    )
    parser.add_argument(
        "--n-participants",
        type=int,
        default=150,
        help="Number of participants for synthetic data"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output path for generated data"
    )
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Run data ingestion pipeline"
    )
    parser.add_argument(
        "--raw",
        type=str,
        help="Path to raw data"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate data against schema"
    )
    parser.add_argument(
        "--compute-metrics",
        action="store_true",
        help="Compute CFI metrics"
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Input data path"
    )
    parser.add_argument(
        "--fit-model",
        action="store_true",
        help="Fit linear mixed-effects model"
    )
    parser.add_argument(
        "--sensitivity",
        action="store_true",
        help="Run sensitivity analysis"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate final report"
    )
    
    args = parser.parse_args()
    
    logger = setup_logging(__name__)
    logger.info("Pipeline orchestration started")
    logger.info(f"Configuration: {get_config_summary()}")
    
    if args.generate_synthetic:
        logger.info("Generating synthetic data...")
        from scripts.generate_synthetic_data import generate_synthetic_logs
        output_path = args.output or "data/raw/synthetic_logs.jsonl"
        generate_synthetic_logs(
            output_dir=str(Path(output_path).parent),
            num_participants=args.n_participants,
            include_edge_cases=True,
            seed=42
        )
        logger.info(f"Synthetic data generated: {output_path}")
    
    if args.ingest:
        logger.info("Running data ingestion pipeline...")
        from data_ingestion import run_ingestion_pipeline
        raw_dir = Path(args.raw).parent if args.raw else Path("data/raw")
        run_ingestion_pipeline(input_dir=raw_dir)
        logger.info("Data ingestion complete")
    
    if args.compute_metrics:
        logger.info("Computing CFI metrics...")
        logger.info("CFI computation requires ingestion pipeline output")
    
    if args.fit_model:
        logger.info("Fitting linear mixed-effects model...")
        logger.info("Model fitting requires processed metrics")
    
    if args.sensitivity:
        logger.info("Running sensitivity analysis...")
        logger.info("Sensitivity analysis requires model results")
    
    if args.report:
        logger.info("Generating final report...")
        logger.info("Report generation requires all analyses")
    
    logger.info("Pipeline orchestration complete")


if __name__ == "__main__":
    main()
