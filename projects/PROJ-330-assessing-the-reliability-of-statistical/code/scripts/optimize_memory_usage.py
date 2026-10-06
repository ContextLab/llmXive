"""
Memory optimization script for the genomic analysis pipeline.

This script analyzes memory usage patterns in the main pipeline components
and provides recommendations for optimization to ensure memory usage stays
below 6GB.
"""
import os
import sys
import logging
import argparse
import gc
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import PROJECT_ROOT as CONFIG_ROOT
from src.memory_monitor import (
    get_current_memory_mb,
    force_gc,
    check_memory_usage,
    optimize_dataframe_dtypes,
    stream_dataframe,
    get_memory_profile,
    MEMORY_LIMIT_MB,
    MEMORY_WARNING_THRESHOLD_MB
)
from src.data_loader import fetch_dataset, load_manifest
from src.preprocessing import preprocess_dataset
from src.metrics import calculate_stability_metrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_memory_usage_of_dataset(dataset_path: str) -> Dict[str, Any]:
    """
    Analyze memory usage of loading and processing a dataset.
    
    Args:
        dataset_path: Path to the dataset file.
        
    Returns:
        Dictionary with memory usage statistics.
    """
    logger.info(f"Analyzing memory usage for dataset: {dataset_path}")
    
    # Initial memory
    initial_memory = get_current_memory_mb()
    logger.info(f"Initial memory: {initial_memory:.2f} MB")
    
    # Load dataset
    df = pd.read_csv(dataset_path)
    after_load_memory = get_current_memory_mb()
    logger.info(f"Memory after loading: {after_load_memory:.2f} MB")
    
    # Optimize dtypes
    df_optimized = optimize_dataframe_dtypes(df)
    after_optimize_memory = get_current_memory_mb()
    logger.info(f"Memory after optimization: {after_optimize_memory:.2f} MB")
    
    # Process in chunks
    chunk_memory_usages = []
    for i, chunk in enumerate(stream_dataframe(df_optimized, chunk_size=10000)):
        chunk_memory = get_current_memory_mb()
        chunk_memory_usages.append(chunk_memory)
        if i % 10 == 0:
            logger.info(f"Processed chunk {i}, current memory: {chunk_memory:.2f} MB")
    
    # Final cleanup
    del df, df_optimized
    final_memory = force_gc()
    
    return {
        'initial_memory_mb': initial_memory,
        'after_load_mb': after_load_memory,
        'after_optimize_mb': after_optimize_memory,
        'peak_chunk_memory_mb': max(chunk_memory_usages) if chunk_memory_usages else 0,
        'final_memory_mb': final_memory,
        'total_chunks': len(chunk_memory_usages)
    }

def generate_optimization_report(dataset_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a comprehensive memory optimization report.
    
    Args:
        dataset_path: Optional path to a dataset for specific analysis.
        
    Returns:
        Dictionary with optimization recommendations.
    """
    report = {
        'memory_limit_mb': MEMORY_LIMIT_MB,
        'warning_threshold_mb': MEMORY_WARNING_THRESHOLD_MB,
        'current_memory_profile': get_memory_profile(),
        'recommendations': []
    }
    
    current_memory = get_current_memory_mb()
    if current_memory > MEMORY_WARNING_THRESHOLD_MB:
        report['recommendations'].append(
            f"Current memory ({current_memory:.2f} MB) is above warning threshold. "
            "Consider reducing chunk sizes or processing datasets sequentially."
        )
    
    if dataset_path and os.path.exists(dataset_path):
        dataset_analysis = analyze_memory_usage_of_dataset(dataset_path)
        report['dataset_analysis'] = dataset_analysis
        
        if dataset_analysis['after_load_mb'] > MEMORY_LIMIT_MB * 0.8:
            report['recommendations'].append(
                "Dataset loading exceeds 80% of memory limit. "
                "Implement streaming/chunked processing for this dataset."
            )
    
    return report

def main():
    """Main entry point for the memory optimization script."""
    parser = argparse.ArgumentParser(description='Memory optimization analysis for genomic pipeline')
    parser.add_argument('--dataset', type=str, help='Path to dataset for analysis')
    parser.add_argument('--output', type=str, help='Output file for report (JSON)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting memory optimization analysis")
    
    report = generate_optimization_report(args.dataset)
    
    if args.output:
        import json
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved to {args.output}")
    else:
        import json
        print(json.dumps(report, indent=2))
    
    # Final memory check
    final_memory = get_current_memory_mb()
    logger.info(f"Final memory usage: {final_memory:.2f} MB")
    
    if final_memory > MEMORY_LIMIT_MB:
        logger.error(f"Memory usage ({final_memory:.2f} MB) exceeds limit ({MEMORY_LIMIT_MB} MB)")
        sys.exit(1)
    
    logger.info("Memory optimization analysis completed successfully")

if __name__ == '__main__':
    main()