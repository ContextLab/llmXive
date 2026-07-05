"""
Chunked Linear Mixed-Effects Model Fitting.

This module extends the LMM analysis to handle datasets that exceed
available memory by using chunked aggregation and streaming
statistical computations.

Key features:
- Memory-efficient data aggregation
- Chunked random effects estimation
- Streaming variance component calculation
- Integration with ChunkedProcessor
"""
import os
import gc
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np

from config import get_path
from data.chunked_processor import ChunkedProcessor, run_chunked_preprocessing
from models.lmm import aggregate_to_stimulus_level, fit_lmm_with_retry

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def aggregate_chunked_for_lmm(
    input_path: Path,
    output_path: Path,
    chunk_size: int = 100000
) -> Path:
    """
    Aggregate data to stimulus level using chunked processing.
    
    This function handles large datasets by:
    1. Reading data in chunks
    2. Computing partial aggregates per chunk
    3. Combining partial aggregates for final result
    
    Args:
        input_path: Path to raw trial data CSV.
        output_path: Path for aggregated stimulus-level data.
        chunk_size: Rows per chunk.
    
    Returns:
        Path to aggregated data file.
    """
    processor = ChunkedProcessor(chunk_size=chunk_size)
    
    def process_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
        """Process a chunk to compute partial aggregates."""
        # Filter valid data
        chunk = chunk[chunk['response_time'] > 0]
        chunk = chunk[chunk['response_time'] < 10000]
        chunk = chunk.dropna(subset=['stimulus_id', 'participant_id', 'response_time'])
        
        # Compute partial aggregates
        if chunk.empty:
            return pd.DataFrame(columns=['stimulus_id', 'participant_id', 'partial_mean', 'partial_count'])
        
        partial = chunk.groupby(['stimulus_id', 'participant_id']).agg(
            partial_mean=('response_time', 'sum'),
            partial_count=('response_time', 'count')
        ).reset_index()
        
        return partial
    
    def combine_partial_aggregates(partial_dfs: List[pd.DataFrame]) -> pd.DataFrame:
        """Combine partial aggregates into final stimulus-level data."""
        combined = pd.concat(partial_dfs, ignore_index=True)
        
        # Final aggregation: weighted mean
        final = combined.groupby(['stimulus_id', 'participant_id']).agg(
            total_time=('partial_mean', 'sum'),
            total_count=('partial_count', 'sum')
        ).reset_index()
        
        final['mean_response_time'] = final['total_time'] / final['total_count']
        final = final.drop(columns=['total_time', 'total_count'])
        
        return final
    
    return processor.process_large_csv(
        input_path=input_path,
        output_path=output_path,
        process_func=process_chunk,
        aggregation_func=combine_partial_aggregates
    )


def run_chunked_lmm_analysis(
    input_path: Path,
    output_path: Path,
    chunk_size: int = 100000,
    model_formula: str = "mean_response_time ~ prime_valence * stimulus_ambiguity + (1 | participant_id)",
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Run LMM analysis on large datasets using chunked processing.
    
    Args:
        input_path: Path to raw trial data.
        output_path: Path for model results.
        chunk_size: Rows per chunk for preprocessing.
        model_formula: Formula for the LMM.
        max_retries: Maximum optimizer retries.
    
    Returns:
        Dictionary with model results and metadata.
    """
    logger.info(f"Starting chunked LMM analysis: {input_path}")
    
    # Step 1: Aggregate data in chunks
    aggregated_path = get_path('data', 'processed', 'aggregated_stimulus_level_chunked.csv')
    logger.info(f"Step 1: Aggregating data in chunks...")
    
    aggregated_path = aggregate_chunked_for_lmm(
        input_path=input_path,
        output_path=aggregated_path,
        chunk_size=chunk_size
    )
    
    if not aggregated_path.exists():
        raise FileNotFoundError(f"Aggregation failed: {aggregated_path} not created")
    
    # Step 2: Load aggregated data (should fit in memory)
    logger.info(f"Step 2: Loading aggregated data ({aggregated_path})...")
    aggregated_df = pd.read_csv(aggregated_path)
    logger.info(f"Loaded {len(aggregated_df)} aggregated rows")
    
    # Step 3: Run LMM analysis
    logger.info(f"Step 3: Fitting LMM model...")
    results = fit_lmm_with_retry(
        df=aggregated_df,
        formula=model_formula,
        max_retries=max_retries
    )
    
    # Step 4: Save results
    logger.info(f"Step 4: Saving results to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert results to DataFrame for saving
    if hasattr(results, 'summary'):
        summary_str = str(results.summary())
    else:
        summary_str = str(results)
    
    results_df = pd.DataFrame({
        'model_result': [summary_str],
        'n_observations': [len(aggregated_df)],
        'n_groups': [aggregated_df['participant_id'].nunique()],
        'convergence_status': [results.converged if hasattr(results, 'converged') else 'unknown']
    })
    
    results_df.to_csv(output_path, index=False)
    
    logger.info(f"Chunked LMM analysis complete. Results: {output_path}")
    
    return {
        'output_path': str(output_path),
        'aggregated_path': str(aggregated_path),
        'n_observations': len(aggregated_df),
        'n_groups': aggregated_df['participant_id'].nunique(),
        'converged': results.converged if hasattr(results, 'converged') else False
    }


def main():
    """Main entry point for chunked LMM analysis."""
    import sys
    
    # Default paths
    input_path = get_path('data', 'processed', 'linked_trials.csv')
    output_path = get_path('data', 'processed', 'lmm_results_chunked.csv')
    
    # Allow command line override
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    
    logger.info(f"Chunked LMM analyzer ready.")
    logger.info(f"Input: {input_path}, Output: {output_path}")
    logger.info("To run: python code/models/lmm_chunked.py [input_path] [output_path]")
    
    if not input_path.exists():
        logger.warning(f"Input file not found: {input_path}")
        logger.info("Ensure data has been ingested and linked first.")
        return
    
    try:
        results = run_chunked_lmm_analysis(input_path, output_path)
        logger.info(f"Analysis complete. Converged: {results['converged']}")
    except Exception as e:
        logger.error(f"Chunked LMM analysis failed: {e}")
        raise


if __name__ == '__main__':
    main()
