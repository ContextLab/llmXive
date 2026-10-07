import os
import sys
import time
import json
import logging
import signal
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any, Iterator

# Import existing project modules
from config import get_project_root, get_metrics_path, get_stats_path, get_figures_dir
from download import fetch_molecules, load_and_sample_dataset
from metrics import (
    calculate_shannon_entropy,
    calculate_lzma_length,
    calculate_sa_score,
    calculate_qed_score,
    calculate_molecular_weight,
    calculate_atom_count,
    TimeoutError,
    timeout
)
from logging_setup import setup_logging, get_logger, log_skipped_molecule, log_timeout_event
from analysis import calculate_pearson_correlations, apply_multiple_comparison_correction, bootstrap_correlations
from report import generate_initial_report
from viz import plot_correlation_scatter

logger = logging.getLogger(__name__)

# Configuration (inlined from config.py for standalone execution context if needed, 
# but primarily relying on config.py constants if they were defined there. 
# Assuming config.py has SEED, CHUNK_SIZE, etc. as per T004)
try:
    from config import SEED, CHUNK_SIZE, TIMEOUT_SECONDS
except ImportError:
    # Fallback defaults if config.py is not fully populated yet, though T004 should exist
    SEED = 42
    CHUNK_SIZE = 500
    TIMEOUT_SECONDS = 60

def ensure_directories():
    """Create necessary directories if they don't exist."""
    root = get_project_root()
    dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "processed" / "plots",
        root / "figures"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def setup_skipped_molecule_logging():
    """Configure specific logging for skipped molecules."""
    # This is handled by logging_setup module in T008
    pass

def process_molecule(molecule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single molecule: calculate metrics.
    Returns a dict with results or None if skipped.
    """
    cid = molecule.get('cid')
    smiles = molecule.get('smiles')
    
    if not smiles or not isinstance(smiles, str):
        log_skipped_molecule(cid, "invalid_smiles")
        return None

    try:
        with timeout(TIMEOUT_SECONDS):
            entropy = calculate_shannon_entropy(smiles)
            lz_length = calculate_lzma_length(smiles)
            sa_score = calculate_sa_score(smiles)
            qed_score = calculate_qed_score(smiles)
            mw = calculate_molecular_weight(smiles)
            atom_count = calculate_atom_count(smiles)
        
        return {
            'cid': cid,
            'smiles': smiles,
            'entropy': entropy,
            'lz': lz_length,
            'sa': sa_score,
            'qed': qed_score,
            'mw': mw,
            'atom_count': atom_count
        }
    except TimeoutError:
        log_timeout_event(cid)
        return None
    except Exception as e:
        logger.warning(f"Error processing molecule {cid}: {e}")
        log_skipped_molecule(cid, "processing_error")
        return None

def process_chunk(chunk: List[Dict[str, Any]], output_file: Path):
    """
    Process a chunk of molecules and append results to CSV.
    """
    results = []
    for mol in chunk:
        res = process_molecule(mol)
        if res:
            results.append(res)
    
    if results:
        df_chunk = pd.DataFrame(results)
        # Check if file exists to decide header
        write_header = not output_file.exists()
        df_chunk.to_csv(output_file, mode='a', header=write_header, index=False)
        logger.info(f"Appended {len(results)} molecules to {output_file}")

def run_download_step() -> Iterator[Dict[str, Any]]:
    """
    Fetch molecules from the dataset.
    Returns an iterator of molecule dicts.
    """
    logger.info("Starting download step...")
    # Using the dataset ID from config (T004)
    # Assuming config.py has DATASET_ID
    try:
        from config import DATASET_ID
    except ImportError:
        DATASET_ID = "sagawa/pubchem-10m-canonicalized"
    
    # Fetch molecules using streaming
    return fetch_molecules(DATASET_ID)

def run_metrics_step():
    """
    Iterate over downloaded molecules, compute metrics, and write to CSV.
    """
    logger.info("Starting metrics computation step...")
    metrics_path = get_metrics_path()
    ensure_directories()
    
    # Remove existing file to start fresh if needed, or append? 
    # Task T015 says "write results incrementally", usually implies fresh run or append.
    # We will ensure it's a fresh run for the pipeline unless specified otherwise.
    if metrics_path.exists():
        metrics_path.unlink()
    
    molecule_iterator = run_download_step()
    
    # Process in chunks
    chunk = []
    for mol in molecule_iterator:
        chunk.append(mol)
        if len(chunk) >= CHUNK_SIZE:
            process_chunk(chunk, metrics_path)
            chunk = []
    
    # Process remaining
    if chunk:
        process_chunk(chunk, metrics_path)
    
    logger.info(f"Metrics computation complete. Output: {metrics_path}")

def run_analysis_step():
    """
    Load the computed metrics from CSV and perform statistical analysis.
    Implements T040: Load data for analysis.
    """
    logger.info("Starting analysis step...")
    metrics_path = get_metrics_path()
    
    if not metrics_path.exists():
        logger.error(f"Metrics file not found: {metrics_path}. Cannot proceed with analysis.")
        # Handle FileNotFoundError gracefully as per T040
        # In a real pipeline, we might raise an error or return early.
        # Here we log and return, assuming the caller handles the state.
        return None

    try:
        # T040 Implementation: Load data into pandas DataFrame
        df_full = pd.read_csv(metrics_path)
        logger.info(f"Loaded {len(df_full)} molecules from {metrics_path}")
        
        # Perform analysis
        correlations = calculate_pearson_correlations(df_full)
        
        # Apply corrections
        adjusted_p = apply_multiple_comparison_correction(correlations)
        
        # Bootstrap stats (if implemented and needed)
        # bootstrap_results = bootstrap_correlations(df_full) 
        
        # Generate report
        report_data = {
            'correlations': correlations,
            'adjusted_p_values': adjusted_p,
            'n_samples': len(df_full)
        }
        
        generate_initial_report(report_data)
        
        return df_full
        
    except FileNotFoundError as e:
        logger.error(f"File not found during analysis: {e}")
        return None
    except Exception as e:
        logger.error(f"Error during analysis step: {e}")
        raise

def run_viz_step(df: Optional[pd.DataFrame] = None):
    """
    Generate visualizations based on the loaded data.
    """
    if df is None:
        logger.warning("No data provided for visualization. Skipping.")
        return

    logger.info("Starting visualization step...")
    ensure_directories()
    figures_dir = get_figures_dir()
    
    pairs = [
        ('entropy', 'sa'),
        ('entropy', 'qed'),
        ('lz', 'sa'),
        ('lz', 'qed')
    ]
    
    for x, y in pairs:
        if x in df.columns and y in df.columns:
            plot_correlation_scatter(x, y, df, figures_dir / f"{x}_{y}.png")
        else:
            logger.warning(f"Columns {x} or {y} not found in dataframe. Skipping plot.")

def main():
    """
    Main orchestration function.
    """
    setup_logging()
    ensure_directories()
    
    try:
        # Step 1: Download (if needed, or just fetch iterator)
        # For this pipeline, we run the full download/metrics loop
        run_metrics_step()
        
        # Step 2: Analysis (T040 loads data here)
        df = run_analysis_step()
        
        # Step 3: Visualization
        if df is not None:
            run_viz_step(df)
            
        logger.info("Pipeline completed successfully.")
        
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()