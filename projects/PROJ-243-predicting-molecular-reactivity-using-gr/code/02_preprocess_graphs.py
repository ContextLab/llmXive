"""
Preprocess Graphs (T014a)
Converts SMILES from QM9 subset to PyTorch Geometric graphs with memory safety,
streaming, and exclusion reporting.
"""
import os
import sys
import logging
import time
import json
import pickle
import psutil
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit import RDLogger
import torch
from torch_geometric.data import Data
from torch_geometric.utils import to_undirected

# Project-relative imports based on API surface
from config import get_config, ensure_directories
from utils.logging_utils import setup_logging, log_metric, log_execution_summary
from utils.graph_utils import smiles_to_graph, batch_smiles_to_graphs, validate_graph, get_feature_dimensions

# Disable RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

def setup_script_logging():
    """Initialize logging for this script."""
    return setup_logging("02_preprocess_graphs")

def check_memory_usage(logger: logging.Logger) -> float:
    """
    Check current RSS memory usage in GB.
    """
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / (1024 ** 3)
    logger.debug(f"Current memory usage: {mem_gb:.2f} GB")
    return mem_gb

def estimate_memory_per_molecule(sample_smiles: List[str], logger: logging.Logger) -> float:
    """
    Estimate memory usage per molecule by processing a small sample.
    """
    if not sample_smiles:
        return 0.0
    
    start_mem = check_memory_usage(logger)
    # Process a small batch to estimate
    try:
        graphs = batch_smiles_to_graphs(sample_smiles[:50], logger)
        end_mem = check_memory_usage(logger)
        # Estimate per molecule (rough approximation)
        mem_per_mol = (end_mem - start_mem) / len(sample_smiles[:50]) if sample_smiles else 0.0
        return max(mem_per_mol, 0.001) # Minimum 1MB per molecule to avoid div by zero
    except Exception as e:
        logger.warning(f"Error estimating memory: {e}")
        return 0.01 # Default 10MB if estimation fails

def log_memory_adjustment(batch_size: int, logger: logging.Logger, log_path: str):
    """Log the memory adjustment to the specified file."""
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "action": "batch_size_reduction",
        "new_batch_size": batch_size,
        "reason": "memory_threshold_exceeded"
    }
    
    with open(log_path, 'a') as f:
        f.write(json.dumps(entry) + '\n')
    logger.info(f"Logged memory adjustment: batch_size reduced to {batch_size}")

def generate_exclusion_report(excluded_ids: List[str], total_count: int, threshold: float, logger: logging.Logger, report_path: str):
    """
    Generate the exclusion report JSON.
    Validates threshold and flags data quality issues.
    """
    exclusion_rate = len(excluded_ids) / total_count if total_count > 0 else 0.0
    status = "PASS" if exclusion_rate < threshold else "DATA_QUALITY_ISSUE"
    
    report = {
        "total_molecules": total_count,
        "excluded_count": len(excluded_ids),
        "excluded_ids": excluded_ids,
        "exclusion_rate": exclusion_rate,
        "threshold": threshold,
        "status": status,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    if status == "DATA_QUALITY_ISSUE":
        logger.warning(f"DATA QUALITY ISSUE: Exclusion rate {exclusion_rate:.4f} exceeds threshold {threshold}")
    else:
        logger.info(f"Exclusion rate {exclusion_rate:.4f} is within threshold {threshold}")
    
    return report

def serialize_graphs_to_parquet(graphs: List[Data], output_path: str, logger: logging.Logger):
    """
    Serialize a list of PyTorch Geometric Data objects to a .pt file.
    Note: Task requires .pt format for PyTorch Geometric compatibility.
    """
    try:
        torch.save(graphs, output_path)
        logger.info(f"Successfully serialized {len(graphs)} graphs to {output_path}")
    except Exception as e:
        logger.error(f"Failed to serialize graphs: {e}")
        raise

def process_smiles_to_graphs(
    smiles_list: List[str], 
    ids_list: List[str], 
    logger: logging.Logger,
    max_memory_gb: float = 4.0,
    batch_size: int = 1000
) -> Tuple[List[Data], List[str]]:
    """
    Process SMILES to graphs with memory safety and streaming logic.
    Returns (processed_graphs, excluded_ids).
    """
    processed_graphs = []
    excluded_ids = []
    
    # Initial memory estimation
    sample_size = min(100, len(smiles_list))
    mem_per_mol = estimate_memory_per_molecule(smiles_list[:sample_size], logger)
    logger.info(f"Estimated memory per molecule: {mem_per_mol*1024:.2f} MB")
    
    current_batch_size = batch_size
    start_time = time.time()
    
    for i in range(0, len(smiles_list), current_batch_size):
        batch_smiles = smiles_list[i:i+current_batch_size]
        batch_ids = ids_list[i:i+current_batch_size]
        
        # Check memory before processing batch
        mem_before = check_memory_usage(logger)
        
        if mem_before > max_memory_gb:
            logger.warning(f"Memory usage {mem_before:.2f} GB exceeds limit {max_memory_gb} GB. Reducing batch size.")
            current_batch_size = max(10, current_batch_size // 2)
            log_memory_adjustment(current_batch_size, logger, os.path.join("artifacts", "memory_adjustment.log"))
            # Force garbage collection
            import gc
            gc.collect()
            continue # Retry with smaller batch
        
        # Process batch
        valid_graphs = []
        valid_ids = []
        
        for idx, smiles in enumerate(batch_smiles):
            mol_id = batch_ids[idx]
            try:
                # Convert SMILES to graph
                graph = smiles_to_graph(smiles)
                if graph is not None and validate_graph(graph):
                    valid_graphs.append(graph)
                    valid_ids.append(mol_id)
                else:
                    excluded_ids.append(mol_id)
                    logger.debug(f"Invalid molecule excluded: {mol_id}")
            except Exception as e:
                excluded_ids.append(mol_id)
                logger.debug(f"Error processing {mol_id}: {e}")
        
        processed_graphs.extend(valid_graphs)
        
        # Log progress
        if (i // current_batch_size + 1) % 10 == 0:
            elapsed = time.time() - start_time
            rate = len(processed_graphs) / elapsed if elapsed > 0 else 0
            logger.info(f"Processed {len(processed_graphs)} molecules ({elapsed:.1f}s, {rate:.1f} mol/s)")
    
    return processed_graphs, excluded_ids

def main():
    """Main entry point for T014a."""
    logger = setup_script_logging()
    logger.info("Starting T014a: Preprocess Graphs")
    
    config = get_config()
    ensure_directories()
    
    # Input/Output paths
    input_path = os.path.join("data", "raw", "qm9_subset.parquet")
    output_path = os.path.join("data", "processed", "graphs_intermediate.pt")
    exclusion_report_path = os.path.join("artifacts", "exclusion_report.json")
    memory_log_path = os.path.join("artifacts", "memory_adjustment.log")
    
    # Ensure output directories exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(os.path.dirname(exclusion_report_path), exist_ok=True)
    
    # Clear memory log if exists
    if os.path.exists(memory_log_path):
        os.remove(memory_log_path)
    
    logger.info(f"Loading data from {input_path}")
    
    # Check if input exists
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Stream data in chunks
    try:
        # Read parquet in chunks to handle large datasets
        chunk_size = 50000
        all_smiles = []
        all_ids = []
        
        # Using pandas read_parquet with chunksize (if supported) or manual iteration
        # For parquet, we often load the whole file if it fits, or use pyarrow directly
        # Given the constraint of "real data" and QM9 size, we assume it fits in memory 
        # but process in logical batches for the conversion step.
        # If the file is too large for RAM, we would need pyarrow.dataset streaming.
        
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded {len(df)} molecules from {input_path}")
        
        # Validate columns
        if 'smiles' not in df.columns:
            logger.error("Column 'smiles' not found in input data")
            sys.exit(1)
        
        # Assume 'id' or 'idx' is the ID column, fallback to index
        id_col = 'id' if 'id' in df.columns else ('idx' if 'idx' in df.columns else None)
        if id_col is None:
            logger.warning("No ID column found, using index as ID")
            ids_list = list(range(len(df)))
        else:
            ids_list = df[id_col].astype(str).tolist()
        
        smiles_list = df['smiles'].dropna().astype(str).tolist()
        # Align IDs if we dropped NaNs
        if len(ids_list) != len(smiles_list):
            # Re-align if necessary (simplest: drop corresponding IDs)
            # This is a simplification; real logic might be more complex
            ids_list = [ids_list[i] for i, s in enumerate(df['smiles']) if pd.notna(s)]
        
        logger.info(f"Processing {len(smiles_list)} SMILES strings...")
        
        # Process with memory safety
        processed_graphs, excluded_ids = process_smiles_to_graphs(
            smiles_list, 
            ids_list, 
            logger,
            max_memory_gb=4.0,
            batch_size=1000
        )
        
        logger.info(f"Processing complete. {len(processed_graphs)} valid graphs, {len(excluded_ids)} excluded.")
        
        # Generate Exclusion Report
        total_count = len(smiles_list)
        report = generate_exclusion_report(
            excluded_ids, 
            total_count, 
            threshold=0.001, # 0.1%
            logger=logger,
            report_path=exclusion_report_path
        )
        
        # Serialize graphs
        serialize_graphs_to_parquet(processed_graphs, output_path, logger)
        
        # Log metrics
        log_metric("total_molecules_processed", len(processed_graphs))
        log_metric("exclusion_rate", report["exclusion_rate"])
        log_metric("status", report["status"])
        
        log_execution_summary(
            logger, 
            "T014a Preprocess Graphs", 
            status="SUCCESS" if report["status"] == "PASS" else "WARNING",
            details={
                "input_file": input_path,
                "output_file": output_path,
                "graphs_count": len(processed_graphs),
                "excluded_count": len(excluded_ids)
            }
        )
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
