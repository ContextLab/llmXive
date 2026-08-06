import os
import sys
import logging
import time
import json
import pickle
import gc
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdchem
import psutil

# Project imports based on API surface
from config import get_config, ensure_directories
from utils.graph_utils import smiles_to_graph, batch_smiles_to_graphs, validate_graph
from utils.logging_utils import setup_logging, log_metric, log_execution_summary

# Constants
MEMORY_LIMIT_GB = 4.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024 ** 3
MIN_BATCH_SIZE = 16
INVALID_SMILES_THRESHOLD = 0.001  # 0.1%

def setup_script_logging():
    """Initialize logging for the preprocessing script."""
    logger = setup_logging("02_preprocess_graphs")
    return logger

def check_memory_usage() -> float:
    """Check current system memory usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def estimate_memory_per_molecule(sample_smiles: List[str], logger: logging.Logger) -> float:
    """
    Estimate memory usage per molecule by processing a small sample.
    Returns estimated bytes per molecule.
    """
    if not sample_smiles:
        return 0.0
    
    sample_size = min(100, len(sample_smiles))
    sample = sample_smiles[:sample_size]
    
    start_mem = check_memory_usage()
    try:
        # Process sample batch
        graphs = batch_smiles_to_graphs(sample, logger)
        valid_graphs = [g for g in graphs if g is not None]
        
        # Serialize to estimate size
        serialized = pickle.dumps(valid_graphs)
        total_bytes = len(serialized)
        
        if len(valid_graphs) > 0:
            return total_bytes / len(valid_graphs)
        else:
            return 0.0
    finally:
        # Clean up
        del graphs
        del valid_graphs
        del serialized
        gc.collect()

def log_memory_adjustment(logger: logging.Logger, action: str, details: Dict[str, Any]):
    """Log memory adjustment events to artifacts/memory_adjustment.log."""
    log_dir = "artifacts"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "memory_adjustment.log")
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {action}: {json.dumps(details)}\n"
    
    with open(log_path, "a") as f:
        f.write(entry)
    
    logger.info(f"Memory adjustment logged: {action} - {details}")

def get_murcko_scaffold(smiles: str) -> Optional[str]:
    """Extract Murcko scaffold from SMILES string."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    
    scaffold = rdchem.GetMorganFingerprintAsBitVect(mol, 2) # Simplified scaffold approach
    # Use RDKit's MurckoScaffold module if available, otherwise fallback
    try:
        from rdkit.Chem.MurckoScaffold import GetScaffoldForMol
        scaffold_mol = GetScaffoldForMol(mol)
        if scaffold_mol is not None:
            return Chem.MolToSmiles(scaffold_mol)
    except ImportError:
        pass
    
    # Fallback: return original if scaffold extraction fails
    return smiles

def murcko_scaffold_split(df: pd.DataFrame, test_frac: float = 0.2, seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split dataframe by Murcko scaffolds.
    Returns train and test splits.
    """
    import random
    random.seed(seed)
    np.random.seed(seed)
    
    # Extract scaffolds
    df['scaffold'] = df['smiles'].apply(get_murcko_scaffold)
    
    # Group by scaffold
    scaffold_counts = df['scaffold'].value_counts()
    scaffold_list = scaffold_counts.index.tolist()
    random.shuffle(scaffold_list)
    
    # Determine split point
    split_idx = int(len(scaffold_list) * (1 - test_frac))
    train_scaffolds = set(scaffold_list[:split_idx])
    test_scaffolds = set(scaffold_list[split_idx:])
    
    train_df = df[df['scaffold'].isin(train_scaffolds)].drop(columns=['scaffold'])
    test_df = df[df['scaffold'].isin(test_scaffolds)].drop(columns=['scaffold'])
    
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True)

def process_smiles_to_graphs(smiles_list: List[str], logger: logging.Logger) -> Tuple[List[Dict], List[str]]:
    """
    Convert a list of SMILES to graph objects.
    Returns tuple of (valid_graphs, excluded_smiles).
    Implements memory safety by processing in batches and adjusting batch size.
    """
    valid_graphs = []
    excluded_smiles = []
    
    current_batch_size = 1024
    
    for i in range(0, len(smiles_list), current_batch_size):
        batch = smiles_list[i : i + current_batch_size]
        current_mem = check_memory_usage()
        
        # Memory safety check: if usage > 4GB, reduce batch size
        if current_mem > MEMORY_LIMIT_GB:
            new_batch_size = max(MIN_BATCH_SIZE, current_batch_size // 2)
            if new_batch_size != current_batch_size:
                logger.warning(f"Memory usage {current_mem:.2f}GB exceeds limit. Reducing batch size from {current_batch_size} to {new_batch_size}.")
                log_memory_adjustment(logger, "BATCH_SIZE_REDUCED", {
                    "old_size": current_batch_size,
                    "new_size": new_batch_size,
                    "current_memory_gb": current_mem
                })
                current_batch_size = new_batch_size
                # Retry this batch with smaller size
                # Adjust loop index to re-process this chunk
                i -= current_batch_size
                continue
        
        try:
            # Process batch
            batch_graphs = batch_smiles_to_graphs(batch, logger)
            
            for idx, graph in enumerate(batch_graphs):
                original_smiles = batch[idx]
                if graph is not None and validate_graph(graph):
                    valid_graphs.append(graph)
                else:
                    excluded_smiles.append(original_smiles)
                    
        except Exception as e:
            logger.error(f"Error processing batch starting at index {i}: {str(e)}")
            # On error, reduce batch size and retry
            new_batch_size = max(MIN_BATCH_SIZE, current_batch_size // 2)
            if new_batch_size != current_batch_size:
                logger.warning(f"Batch processing failed. Reducing batch size to {new_batch_size}.")
                log_memory_adjustment(logger, "BATCH_SIZE_REDUCED_ON_ERROR", {
                    "old_size": current_batch_size,
                    "new_size": new_batch_size,
                    "error": str(e)
                })
                current_batch_size = new_batch_size
                i -= current_batch_size
                continue
            else:
                # Hard floor reached, skip batch
                logger.error(f"Hard floor batch size reached. Skipping batch at index {i}.")
                excluded_smiles.extend(batch)
    
    return valid_graphs, excluded_smiles

def serialize_graphs_to_parquet(graphs: List[Dict], output_path: str, logger: logging.Logger):
    """
    Serialize graph objects to a Parquet file.
    Graphs are converted to a serializable format first.
    """
    # Convert graphs to a serializable dictionary format
    serializable_data = []
    for g in graphs:
        # Assuming graph has keys: 'node_features', 'edge_features', 'edge_index', 'smiles', 'y'
        row = {
            'smiles': g.get('smiles', ''),
            'num_nodes': g.get('num_nodes', 0),
            'num_edges': g.get('num_edges', 0),
            # Store arrays as lists for parquet compatibility
            'node_features': g.get('node_features', []).tolist() if hasattr(g.get('node_features'), 'tolist') else g.get('node_features', []),
            'edge_features': g.get('edge_features', []).tolist() if hasattr(g.get('edge_features'), 'tolist') else g.get('edge_features', []),
            'edge_index': g.get('edge_index', []).tolist() if hasattr(g.get('edge_index'), 'tolist') else g.get('edge_index', []),
            'target': g.get('y', 0.0)
        }
        serializable_data.append(row)
    
    df = pd.DataFrame(serializable_data)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write to parquet with snappy compression
    df.to_parquet(output_path, compression='snappy', index=False)
    logger.info(f"Serialized {len(graphs)} graphs to {output_path}")

def generate_exclusion_report(excluded_count: int, total_count: int, logger: logging.Logger):
    """
    Generate exclusion report and validate threshold.
    Writes to artifacts/exclusion_report.json.
    """
    exclusion_pct = (excluded_count / total_count * 100) if total_count > 0 else 0.0
    
    report = {
        "total_molecules": total_count,
        "excluded_count": excluded_count,
        "exclusion_percentage": round(exclusion_pct, 4),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Validate threshold
    if exclusion_pct > (INVALID_SMILES_THRESHOLD * 100):
        logger.warning(f"Exclusion rate {exclusion_pct:.2f}% exceeds threshold {INVALID_SMILES_THRESHOLD * 100}%")
    else:
        logger.info(f"Exclusion rate {exclusion_pct:.2f}% is within threshold.")
    
    # Write report
    report_path = "artifacts/exclusion_report.json"
    os.makedirs("artifacts", exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Exclusion report written to {report_path}")
    return report

def main():
    """Main entry point for preprocessing."""
    logger = setup_script_logging()
    logger.info("Starting molecular graph preprocessing (T014b)")
    
    config = get_config()
    ensure_directories()
    
    # Load raw data from T013
    input_path = "data/raw/qm9_subset_raw.csv"
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}. Run T013 first.")
        sys.exit(1)
    
    df = pd.read_csv(input_path)
    smiles_list = df['smiles'].tolist()
    total_count = len(smiles_list)
    logger.info(f"Loaded {total_count} molecules from {input_path}")
    
    # Estimate memory per molecule (T014a logic integration)
    # Note: T014a should have already sampled if needed, but we re-check here
    # For this task, we assume T014a has prepared the data or we sample if needed
    # Since T014a is marked completed, we proceed with the list as is, 
    # but we implement the memory safety logic during processing.
    
    start_time = time.time()
    
    # Process SMILES to graphs
    valid_graphs, excluded_smiles = process_smiles_to_graphs(smiles_list, logger)
    
    elapsed = time.time() - start_time
    logger.info(f"Preprocessing completed in {elapsed:.2f}s")
    logger.info(f"Valid graphs: {len(valid_graphs)}, Excluded: {len(excluded_smiles)}")
    
    # Generate exclusion report (T014c requirement)
    generate_exclusion_report(len(excluded_smiles), total_count, logger)
    
    # Serialize to intermediate parquet (T014b deliverable)
    output_path = "data/processed/qm9_graphs_intermediate.parquet"
    serialize_graphs_to_parquet(valid_graphs, output_path, logger)
    
    log_execution_summary(logger, {
        "task": "T014b",
        "status": "completed",
        "total_molecules": total_count,
        "valid_graphs": len(valid_graphs),
        "excluded": len(excluded_smiles),
        "output_file": output_path,
        "duration_seconds": elapsed
    })
    
    logger.info("T014b Preprocessing complete.")

if __name__ == "__main__":
    main()