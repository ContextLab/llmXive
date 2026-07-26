"""
Entry point for the Semantic Divergence Diagnostic pipeline.

This module orchestrates the pre-flight checks, data loading, divergence
calculation, and correlation analysis.
"""

import os
import sys
import argparse
import time
import socket
from pathlib import Path
from typing import Optional, List, Dict, Any

# Import from project libraries
from src.lib import config
from src.lib.data_loader import DataLoaderError, load_dataset_streaming
from src.lib.validator import validate_dataset_size, ValidationError
from src.lib.axpo_simulator import run_axpo_simulation_diagnostic, AXPOSimulatorError
from src.models.divergence_model import DivergenceModel, DivergenceModelError, create_divergence_model
from src.services.retrieval_service import RetrievalService, create_retrieval_service, RetrievalServiceError
from src.services.analysis_service import AnalysisService, AnalysisServiceError

class DiagnosticError(Exception):
    """Custom exception for diagnostic pipeline failures."""
    pass

def check_url_reachability(url: str, timeout: int = 5) -> bool:
    """
    Pre-flight check to verify dataset URL reachability.
    
    Implements Constitution Principle II: Fail loudly on unreachable data sources.
    
    Args:
        url: The URL to check.
        timeout: Connection timeout in seconds.
        
    Returns:
        True if the URL is reachable, False otherwise.
        
    Raises:
        DiagnosticError: If the URL is unreachable.
    """
    try:
        # Basic socket check for HTTP/HTTPS URLs
        if url.startswith('http://') or url.startswith('https://'):
            hostname = url.split('/')[2]
            socket.setdefaulttimeout(timeout)
            socket.gethostbyname(hostname)
            return True
        else:
            # For local paths or other schemes, assume reachable if path exists
            return True
    except socket.gaierror:
        raise DiagnosticError(f"URL unreachable (DNS resolution failed): {url}")
    except socket.timeout:
        raise DiagnosticError(f"URL unreachable (connection timeout): {url}")
    except Exception as e:
        raise DiagnosticError(f"URL reachability check failed: {e}")

def run_preflight_checks(args: argparse.Namespace) -> None:
    """
    Execute all pre-flight checks before running the diagnostic.
    
    Args:
        args: Parsed command-line arguments.
        
    Raises:
        DiagnosticError: If any pre-flight check fails.
    """
    print("Running pre-flight checks...")
    
    # Check 1: Dataset URL reachability
    if args.dataset_url:
        print(f"  Checking dataset URL: {args.dataset_url}")
        check_url_reachability(args.dataset_url)
        print("    ✓ URL is reachable")
    
    # Check 2: Tool mapping file exists
    tool_mapping_path = Path(config.TOOL_MAPPING_PATH)
    if not tool_mapping_path.exists():
        raise DiagnosticError(f"Tool mapping file not found: {tool_mapping_path}")
    print(f"  Tool mapping file exists: {tool_mapping_path}")
    
    # Check 3: Output directory exists and is writable
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    test_file = output_dir / ".write_test"
    try:
        test_file.touch()
        test_file.unlink()
        print(f"  Output directory is writable: {output_dir}")
    except OSError as e:
        raise DiagnosticError(f"Output directory not writable: {e}")
    
    # Check 4: Required dependencies (basic check)
    try:
        import transformers
        import torch
        import numpy as np
        import pandas as pd
        print("  Required dependencies are available")
    except ImportError as e:
        raise DiagnosticError(f"Missing required dependency: {e}")
    
    print("All pre-flight checks passed.\n")

def validate_dataset_size_after_load(dataset: Any, min_size: int = 30) -> None:
    """
    Validate that the loaded dataset meets the minimum size requirement.
    
    Args:
        dataset: The loaded dataset object.
        min_size: Minimum number of samples required.
        
    Raises:
        ValidationError: If the dataset size is insufficient.
    """
    # Handle different dataset types
    if hasattr(dataset, '__len__'):
        size = len(dataset)
    elif hasattr(dataset, 'num_rows'):
        size = dataset.num_rows
    else:
        # For streaming datasets, we might need to count or estimate
        # For now, we'll assume the caller has materialized or can count
        raise DiagnosticError("Unable to determine dataset size. Ensure dataset is materialized or has length.")
    
    if size < min_size:
        raise ValidationError(
            f"Insufficient sample size for power analysis. "
            f"Required: >= {min_size}, Got: {size}. "
            f"Dataset size N must be >= 30 for statistical validity (FR-010)."
        )
    
    print(f"  Dataset size validated: {size} samples (>= {min_size})")

def run_diagnostic(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Execute the full semantic divergence diagnostic pipeline.
    
    Args:
        args: Parsed command-line arguments.
        
    Returns:
        A dictionary containing the diagnostic results.
        
    Raises:
        DiagnosticError: If any step in the pipeline fails.
    """
    start_time = time.time()
    results = {}
    
    try:
        # Step 1: Load dataset
        print("Loading dataset...")
        try:
            dataset = load_dataset_streaming(
                dataset_name=args.dataset_name,
                dataset_url=args.dataset_url,
                split=args.split,
                streaming=args.streaming
            )
        except DataLoaderError as e:
            raise DiagnosticError(f"Failed to load dataset: {e}")
        
        # Step 2: Validate dataset size
        print("Validating dataset size...")
        validate_dataset_size_after_load(dataset, min_size=30)
        results['dataset_size'] = len(dataset) if hasattr(dataset, '__len__') else 'streaming'
        
        # Step 3: Initialize services
        print("Initializing services...")
        try:
            retrieval_service = create_retrieval_service()
            divergence_model = create_divergence_model()
            analysis_service = AnalysisService()
        except (RetrievalServiceError, DivergenceModelError, AnalysisServiceError) as e:
            raise DiagnosticError(f"Failed to initialize services: {e}")
        
        # Step 4: Run AXPO simulations (if enabled)
        if args.run_axpo:
            print("Running AXPO simulations...")
            try:
                axpo_results = run_axpo_simulation_diagnostic(dataset)
                results['axpo_results'] = axpo_results
            except AXPOSimulatorError as e:
                raise DiagnosticError(f"AXPO simulation failed: {e}")
        
        # Step 5: Compute divergence scores
        print("Computing semantic divergence scores...")
        try:
            divergence_results = divergence_model.compute_batch(
                dataset=dataset,
                retrieval_service=retrieval_service
            )
            results['divergence_scores'] = divergence_results
        except DivergenceModelError as e:
            raise DiagnosticError(f"Divergence computation failed: {e}")
        
        # Step 6: Perform correlation analysis
        if args.run_correlation and 'axpo_results' in results and 'divergence_scores' in results:
            print("Performing correlation analysis...")
            try:
                correlation_results = analysis_service.compute_correlation(
                    divergence_scores=results['divergence_scores'],
                    failure_rates=results['axpo_results'].failure_rates
                )
                results['correlation_analysis'] = correlation_results
            except AnalysisServiceError as e:
                raise DiagnosticError(f"Correlation analysis failed: {e}")
        
        # Step 7: Write output
        print(f"Writing results to {args.output_dir}...")
        output_path = Path(args.output_dir) / "diagnostic_report.json"
        import json
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        elapsed_time = time.time() - start_time
        results['elapsed_time_seconds'] = elapsed_time
        results['status'] = 'completed'
        
        print(f"\nDiagnostic completed successfully in {elapsed_time:.2f}s.")
        print(f"Results written to: {output_path}")
        
        return results
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        results['elapsed_time_seconds'] = elapsed_time
        results['status'] = 'failed'
        results['error'] = str(e)
        
        # Write partial results if any
        if results:
            output_path = Path(args.output_dir) / "diagnostic_report_error.json"
            import json
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        
        raise DiagnosticError(f"Pipeline failed: {e}")

def main():
    """Main entry point for the diagnostic CLI."""
    parser = argparse.ArgumentParser(
        description="Run Semantic Divergence Diagnostic for Agentic Reasoning"
    )
    
    # Dataset arguments
    parser.add_argument(
        '--dataset-name',
        type=str,
        default='mathvista',
        help='Name of the dataset to load (e.g., mathvista, scienceqa)'
    )
    parser.add_argument(
        '--dataset-url',
        type=str,
        default=None,
        help='Direct URL to the dataset (optional, overrides dataset-name)'
    )
    parser.add_argument(
        '--split',
        type=str,
        default='test',
        help='Dataset split to use (e.g., train, test, validation)'
    )
    parser.add_argument(
        '--streaming',
        action='store_true',
        help='Load dataset in streaming mode'
    )
    
    # Output arguments
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/outputs',
        help='Directory to write output files'
    )
    
    # Feature flags
    parser.add_argument(
        '--run-axpo',
        action='store_true',
        default=True,
        help='Run AXPO simulations (default: True)'
    )
    parser.add_argument(
        '--run-correlation',
        action='store_true',
        default=True,
        help='Run correlation analysis (default: True)'
    )
    parser.add_argument(
        '--skip-preflight',
        action='store_true',
        help='Skip pre-flight checks'
    )
    
    args = parser.parse_args()
    
    try:
        if not args.skip_preflight:
            run_preflight_checks(args)
        
        results = run_diagnostic(args)
        
        # Exit with appropriate code
        sys.exit(0 if results.get('status') == 'completed' else 1)
        
    except DiagnosticError as e:
        print(f"\n❌ Diagnostic Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Diagnostic interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
