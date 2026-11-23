"""
Benchmark script for the molecular flexibility pipeline.

Executes the full pipeline on a fixed representative subset of 100 molecules
to estimate total runtime for the complete dataset.

Traceability: T040a [US3]
"""
import time
import logging
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, setup_logging_for_script
from utils.config import get_project_root, get_data_path, get_state_path
from data.preprocessing import load_raw_data, preprocess_data
from data.conformer_gen import generate_conformers
from data.descriptors import process_molecules
from data.analysis import calculate_bivariate_correlations, run_multivariate_regression

# Setup logging
logger = setup_logging_for_script("benchmark_pipeline")

def load_sample_data(sample_size: int = 100) -> pd.DataFrame:
    """Load a fixed sample of molecules from the enriched dataset."""
    enriched_path = get_data_path() / "processed" / "enriched_data.csv"
    
    if not enriched_path.exists():
        logger.error(f"Enriched data file not found: {enriched_path}")
        raise FileNotFoundError(f"Required input file missing: {enriched_path}")
    
    df = pd.read_csv(enriched_path)
    
    # Filter for rows with valid SMILES and logPapp
    valid_df = df[df['smiles'].notna() & df['logPapp'].notna()]
    
    if len(valid_df) < sample_size:
        logger.warning(f"Only {len(valid_df)} valid molecules found, using all available")
        sample_size = len(valid_df)
    
    # Take first N rows deterministically
    sample_df = valid_df.head(sample_size).copy()
    logger.info(f"Selected {len(sample_df)} molecules for benchmark")
    
    return sample_df

def run_conformer_generation(sample_df: pd.DataFrame) -> float:
    """Run conformer generation on the sample and return time."""
    logger.info("Starting conformer generation benchmark...")
    start_time = time.time()
    
    # Generate conformers for the sample
    # Note: In a real run, this would call generate_conformers(sample_df['smiles'].tolist())
    # For benchmarking, we simulate the process with a subset
    smiles_list = sample_df['smiles'].tolist()
    
    # Call the actual function (it will handle the real computation)
    try:
        from data.conformer_gen import generate_conformers, save_conformers
        conformers = generate_conformers(smiles_list)
        # Save to a temporary benchmark file
        benchmark_conformer_path = get_data_path() / "processed" / "benchmark_conformers.pkl"
        save_conformers(conformers, benchmark_conformer_path)
    except Exception as e:
        logger.error(f"Conformer generation failed: {e}")
        raise
    
    elapsed = time.time() - start_time
    logger.info(f"Conformer generation completed in {elapsed:.2f} seconds")
    return elapsed

def run_descriptor_calculation(sample_df: pd.DataFrame) -> float:
    """Run descriptor calculation on the sample and return time."""
    logger.info("Starting descriptor calculation benchmark...")
    start_time = time.time()
    
    # Load the benchmark conformers generated above
    benchmark_conformer_path = get_data_path() / "processed" / "benchmark_conformers.pkl"
    
    try:
        from data.descriptors import load_conformers, process_molecules
        conformers = load_conformers(benchmark_conformer_path)
        
        # Process molecules to calculate descriptors
        descriptors = process_molecules(sample_df['smiles'].tolist(), conformers)
        
        # Save results
        benchmark_descriptor_path = get_data_path() / "processed" / "benchmark_descriptors.csv"
        descriptors.to_csv(benchmark_descriptor_path, index=False)
    except Exception as e:
        logger.error(f"Descriptor calculation failed: {e}")
        raise
    
    elapsed = time.time() - start_time
    logger.info(f"Descriptor calculation completed in {elapsed:.2f} seconds")
    return elapsed

def run_correlation_analysis(sample_df: pd.DataFrame) -> float:
    """Run correlation analysis on the sample and return time."""
    logger.info("Starting correlation analysis benchmark...")
    start_time = time.time()
    
    try:
        # Load the benchmark descriptors
        benchmark_descriptor_path = get_data_path() / "processed" / "benchmark_descriptors.csv"
        if not benchmark_descriptor_path.exists():
            logger.error("Benchmark descriptors not found. Run descriptor calculation first.")
            raise FileNotFoundError("Benchmark descriptors missing")
        
        descriptors = pd.read_csv(benchmark_descriptor_path)
        
        # Merge with sample data for analysis
        analysis_df = sample_df.merge(descriptors, on='smiles', how='inner')
        
        # Run bivariate correlations
        correlations = calculate_bivariate_correlations(analysis_df)
        
        # Save results
        benchmark_corr_path = get_data_path() / "processed" / "benchmark_correlations.csv"
        correlations.to_csv(benchmark_corr_path, index=False)
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        raise
    
    elapsed = time.time() - start_time
    logger.info(f"Correlation analysis completed in {elapsed:.2f} seconds")
    return elapsed

def run_regression_analysis(sample_df: pd.DataFrame) -> float:
    """Run regression analysis on the sample and return time."""
    logger.info("Starting regression analysis benchmark...")
    start_time = time.time()
    
    try:
        # Load the benchmark descriptors
        benchmark_descriptor_path = get_data_path() / "processed" / "benchmark_descriptors.csv"
        if not benchmark_descriptor_path.exists():
            logger.error("Benchmark descriptors not found. Run descriptor calculation first.")
            raise FileNotFoundError("Benchmark descriptors missing")
        
        descriptors = pd.read_csv(benchmark_descriptor_path)
        
        # Merge with sample data for analysis
        analysis_df = sample_df.merge(descriptors, on='smiles', how='inner')
        
        # Run multivariate regression
        results = run_multivariate_regression(analysis_df)
        
        # Save results
        benchmark_regression_path = get_data_path() / "processed" / "benchmark_regression_results.json"
        with open(benchmark_regression_path, 'w') as f:
            json.dump(results, f, indent=2)
    except Exception as e:
        logger.error(f"Regression analysis failed: {e}")
        raise
    
    elapsed = time.time() - start_time
    logger.info(f"Regression analysis completed in {elapsed:.2f} seconds")
    return elapsed

def main():
    """Execute the full benchmark pipeline on a representative sample."""
    logger.info("=" * 60)
    logger.info("Starting Pipeline Benchmark (T040a)")
    logger.info("=" * 60)
    
    # Configuration
    SAMPLE_SIZE = 100
    project_root = get_project_root()
    
    # Load sample data
    logger.info(f"Loading sample of {SAMPLE_SIZE} molecules...")
    try:
        sample_df = load_sample_data(SAMPLE_SIZE)
    except FileNotFoundError as e:
        logger.error(f"Failed to load sample data: {e}")
        sys.exit(1)
    
    if len(sample_df) == 0:
        logger.error("No valid molecules in sample dataset")
        sys.exit(1)
    
    # Run benchmark stages
    timings = {}
    
    try:
        # Stage 1: Conformer Generation
        timings['conformer_generation'] = run_conformer_generation(sample_df)
        
        # Stage 2: Descriptor Calculation
        timings['descriptor_calculation'] = run_descriptor_calculation(sample_df)
        
        # Stage 3: Correlation Analysis
        timings['correlation_analysis'] = run_correlation_analysis(sample_df)
        
        # Stage 4: Regression Analysis
        timings['regression_analysis'] = run_regression_analysis(sample_df)
        
    except Exception as e:
        logger.error(f"Benchmark failed at stage: {e}")
        # Write partial results before exiting
        partial_results = {
            'sample_size': len(sample_df),
            'timings': timings,
            'error': str(e),
            'status': 'failed'
        }
        output_path = project_root / "data" / "processed" / "benchmark_results.json"
        with open(output_path, 'w') as f:
            json.dump(partial_results, f, indent=2)
        sys.exit(1)
    
    # Calculate total sample time
    total_sample_time = sum(timings.values())
    logger.info(f"Total sample time: {total_sample_time:.2f} seconds")
    
    # Estimate runtime for full dataset
    # Count total valid molecules in enriched data
    enriched_path = get_data_path() / "processed" / "enriched_data.csv"
    total_df = pd.read_csv(enriched_path)
    total_valid = len(total_df[total_df['smiles'].notna() & total_df['logPapp'].notna()])
    
    estimated_runtime = total_sample_time * (total_valid / len(sample_df))
    
    # Prepare results
    results = {
        'sample_size': len(sample_df),
        'total_valid_molecules': total_valid,
        'sample_time_seconds': total_sample_time,
        'estimated_runtime_seconds': estimated_runtime,
        'estimated_runtime_hours': estimated_runtime / 3600,
        'stage_timings': timings,
        'status': 'success',
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Write results
    output_path = project_root / "data" / "processed" / "benchmark_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("=" * 60)
    logger.info("BENCHMARK RESULTS")
    logger.info("=" * 60)
    logger.info(f"Sample size: {results['sample_size']}")
    logger.info(f"Total valid molecules: {results['total_valid_molecules']}")
    logger.info(f"Sample time: {results['sample_time_seconds']:.2f}s")
    logger.info(f"Estimated full runtime: {results['estimated_runtime_seconds']:.2f}s ({results['estimated_runtime_hours']:.2f}h)")
    logger.info("=" * 60)
    
    # Print stage breakdown
    logger.info("Stage breakdown:")
    for stage, duration in timings.items():
        logger.info(f"  {stage}: {duration:.2f}s")
    
    logger.info("Benchmark completed successfully!")
    return results

if __name__ == "__main__":
    main()