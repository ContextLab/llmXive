"""
Command-line interface for the DomainShuttle compression pipeline.

This module orchestrates the various stages of the pipeline,
including data loading, complexity scoring, embedding extraction,
training sweeps, and validation.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

from src.config.settings import get_config
from src.utils.logging import get_logger
from src.data.loaders import load_webvid_subset
from src.data.complexity import compute_complexity_scores
from src.data.embeddings import extract_domainshuttle_embeddings
from src.models.training import train_autoencoder
from src.analysis.validation import validate_and_update_failed_subjects


logger = get_logger(__name__)


def setup_parser() -> argparse.ArgumentParser:
    """Setup the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description='DomainShuttle Compression Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Data acquisition
    data_parser = subparsers.add_parser('data', help='Load and process data')
    data_parser.add_argument('--output-dir', default='data/processed',
                            help='Output directory for processed data')
    data_parser.add_argument('--num-subjects', type=int, default=100,
                            help='Number of subjects to load')
    
    # Training sweep
    train_parser = subparsers.add_parser('train', help='Run training sweep')
    train_parser.add_argument('--input-dir', default='data/processed',
                             help='Input directory with embeddings')
    train_parser.add_argument('--output-dir', default='data/processed',
                             help='Output directory for models and logs')
    train_parser.add_argument('--dimensions', type=int, nargs='+',
                             default=[16, 32, 64, 128, 256],
                             help='Target dimensions to sweep')
    
    # Validation
    validate_parser = subparsers.add_parser('validate', help='Validate training convergence')
    validate_parser.add_argument('--input-dir', default='data/processed',
                                help='Directory containing sweep_logs.json')
    validate_parser.add_argument('--output-log', default='data/processed/failed_subjects.log',
                                help='Path to failed subjects log')
    
    # Full pipeline
    pipeline_parser = subparsers.add_parser('pipeline', help='Run full pipeline')
    pipeline_parser.add_argument('--output-dir', default='data/processed',
                                help='Output directory for all artifacts')
    pipeline_parser.add_argument('--timeout', type=int, default=21600,
                                help='Pipeline timeout in seconds (default: 6 hours)')
    
    return parser


def run_data_acquisition(args: argparse.Namespace) -> None:
    """Run the data acquisition stage."""
    logger.info("Starting data acquisition...")
    start_time = time.time()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info(f"Loading {args.num_subjects} subjects from WebVid-10M")
    subjects = load_webvid_subset(num_subjects=args.num_subjects)
    
    # Compute complexity scores
    logger.info("Computing visual complexity scores")
    complexity_scores = compute_complexity_scores(subjects)
    
    # Extract embeddings
    logger.info("Extracting DomainShuttle embeddings")
    embeddings = extract_domainshuttle_embeddings(subjects)
    
    # Save results
    complexity_path = output_dir / 'complexity_scores.csv'
    embeddings_dir = output_dir / 'embeddings'
    embeddings_dir.mkdir(exist_ok=True)
    
    # Save complexity scores
    complexity_scores.to_csv(complexity_path, index=False)
    logger.info(f"Saved complexity scores to {complexity_path}")
    
    # Save embeddings
    for subject_id, embedding in embeddings.items():
        emb_path = embeddings_dir / f'{subject_id}.pt'
        torch.save(embedding, emb_path)
        
    elapsed = time.time() - start_time
    logger.info(f"Data acquisition completed in {elapsed:.2f} seconds")


def run_training_sweep(args: argparse.Namespace) -> None:
    """Run the training sweep across multiple dimensions."""
    logger.info("Starting training sweep...")
    start_time = time.time()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    dimensions = args.dimensions
    logger.info(f"Training dimensions: {dimensions}")
    
    # Load embeddings
    embeddings_dir = input_dir / 'embeddings'
    if not embeddings_dir.exists():
        raise FileNotFoundError(f"Embeddings directory not found: {embeddings_dir}")
        
    embeddings = {}
    for emb_file in embeddings_dir.glob('*.pt'):
        subject_id = emb_file.stem
        embeddings[subject_id] = torch.load(emb_file)
        
    logger.info(f"Loaded {len(embeddings)} embeddings")
    
    # Train for each dimension
    all_results = {'subjects': {}}
    
    for dim in dimensions:
        logger.info(f"Training dimension {dim}")
        dim_results = {}
        
        for subject_id, embedding in embeddings.items():
            try:
                # Train model
                model_path = output_dir / f'model_{dim}_{subject_id}.pt'
                log = train_autoencoder(
                    embedding,
                    target_dim=dim,
                    model_path=str(model_path)
                )
                dim_results[subject_id] = log
                
            except Exception as e:
                logger.error(f"Failed to train {subject_id} at dim {dim}: {e}")
                dim_results[subject_id] = {
                    'error': str(e),
                    'loss_history': []
                }
        
        all_results['subjects'][dim] = dim_results
        
        # Save intermediate results
        sweep_logs_path = output_dir / 'sweep_logs.json'
        with open(sweep_logs_path, 'w') as f:
            json.dump(all_results, f, indent=2)
    
    elapsed = time.time() - start_time
    logger.info(f"Training sweep completed in {elapsed:.2f} seconds")


def run_validation(args: argparse.Namespace) -> None:
    """Run validation to identify failed subjects."""
    logger.info("Starting validation...")
    start_time = time.time()
    
    summary = validate_and_update_failed_subjects(
        args.input_dir,
        args.output_log
    )
    
    elapsed = time.time() - start_time
    logger.info(f"Validation completed in {elapsed:.2f} seconds")
    logger.info(f"Found {summary['failed_count']} failures out of {summary['total_subjects']}")


def run_full_pipeline(args: argparse.Namespace) -> None:
    """Run the full pipeline with timeout monitoring."""
    logger.info("Starting full pipeline...")
    start_time = time.time()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Stage 1: Data acquisition
        logger.info("=== Stage 1: Data Acquisition ===")
        data_args = argparse.Namespace(
            output_dir=str(output_dir),
            num_subjects=100
        )
        run_data_acquisition(data_args)
        
        # Check timeout
        if time.time() - start_time > args.timeout:
            timeout_log = output_dir / 'pipeline_timeout.json'
            with open(timeout_log, 'w') as f:
                json.dump({'status': 'timeout', 'stage': 'data_acquisition'}, f)
            raise TimeoutError("Pipeline timed out during data acquisition")
        
        # Stage 2: Training sweep
        logger.info("=== Stage 2: Training Sweep ===")
        train_args = argparse.Namespace(
            input_dir=str(output_dir),
            output_dir=str(output_dir),
            dimensions=[16, 32, 64, 128, 256]
        )
        run_training_sweep(train_args)
        
        # Check timeout
        if time.time() - start_time > args.timeout:
            timeout_log = output_dir / 'pipeline_timeout.json'
            with open(timeout_log, 'w') as f:
                json.dump({'status': 'timeout', 'stage': 'training_sweep'}, f)
            raise TimeoutError("Pipeline timed out during training sweep")
        
        # Stage 3: Validation
        logger.info("=== Stage 3: Validation ===")
        validate_args = argparse.Namespace(
            input_dir=str(output_dir),
            output_log=str(output_dir / 'failed_subjects.log')
        )
        run_validation(validate_args)
        
        # Check timeout
        if time.time() - start_time > args.timeout:
            timeout_log = output_dir / 'pipeline_timeout.json'
            with open(timeout_log, 'w') as f:
                json.dump({'status': 'timeout', 'stage': 'validation'}, f)
            raise TimeoutError("Pipeline timed out during validation")
        
        elapsed = time.time() - start_time
        logger.info(f"Full pipeline completed successfully in {elapsed:.2f} seconds")
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Pipeline failed after {elapsed:.2f} seconds: {e}")
        raise


def main():
    """Main entry point for the CLI."""
    parser = setup_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    if args.command == 'data':
        run_data_acquisition(args)
    elif args.command == 'train':
        run_training_sweep(args)
    elif args.command == 'validate':
        run_validation(args)
    elif args.command == 'pipeline':
        run_full_pipeline(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()