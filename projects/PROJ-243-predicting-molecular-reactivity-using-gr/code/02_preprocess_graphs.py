import os
import sys
import logging
import time
import json
import pickle
import traceback
from typing import List, Dict, Any, Optional, Tuple, Generator
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from datasets import load_dataset

# Local imports from project API surface
from config import get_config, ensure_directories
from utils.graph_utils import smiles_to_graph, batch_smiles_to_graphs, validate_graph
from utils.logging_utils import setup_logging, get_logger, log_metric

# Constants for memory safety
MEMORY_LIMIT_GB = 4.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024**3
MIN_BATCH_SIZE = 16
MAX_BATCH_SIZE = 1024

def setup_script_logging():
    """Initialize logging for the preprocessing script."""
    return setup_logging("02_preprocess_graphs")

def check_memory_usage() -> float:
    """
    Check current system memory usage in GB.
    Returns the usage in GB.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return mem_info.rss / (1024 ** 3)
    except ImportError:
        # Fallback to a simple estimation if psutil is not available
        # This is less accurate but prevents immediate crash
        logging.warning("psutil not found. Memory usage estimation disabled.")
        return 0.0
    except Exception as e:
        logging.warning(f"Could not check memory usage: {e}")
        return 0.0

def log_memory_adjustment(batch_size: int, reason: str, log_path: str):
    """
    Log memory adjustments to a specific log file.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] Memory Adjustment: Batch size set to {batch_size}. Reason: {reason}\n"
    
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'a') as f:
        f.write(log_entry)
    
    logging.info(log_entry.strip())

def get_murcko_scaffold(smiles: str) -> Optional[str]:
    """
    Extract the Murcko scaffold from a SMILES string.
    Returns the scaffold SMILES or None if extraction fails.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    try:
        scaffold = rdMolDescriptors.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaffold)
    except Exception:
        return None

def murcko_scaffold_split(
    smiles_list: List[str], 
    test_frac: float = 0.1, 
    val_frac: float = 0.1, 
    seed: int = 42
) -> Dict[str, List[str]]:
    """
    Split molecules into train/val/test sets based on Murcko scaffolds.
    """
    np.random.seed(seed)
    
    # Map scaffold to list of smiles
    scaffold_to_smiles = {}
    valid_smiles = []
    
    for smi in smiles_list:
        scaffold = get_murcko_scaffold(smi)
        if scaffold:
            if scaffold not in scaffold_to_smiles:
                scaffold_to_smiles[scaffold] = []
            scaffold_to_smiles[scaffold].append(smi)
            valid_smiles.append(smi)
        else:
            # Invalid molecules are excluded from split logic
            pass
    
    # Shuffle scaffolds
    scaffolds = list(scaffold_to_smiles.keys())
    np.random.shuffle(scaffolds)
    
    n_scaffolds = len(scaffolds)
    n_test = int(n_scaffolds * test_frac)
    n_val = int(n_scaffolds * val_frac)
    
    test_scaffolds = set(scaffolds[:n_test])
    val_scaffolds = set(scaffolds[n_test:n_test+n_val])
    
    train_split = []
    val_split = []
    test_split = []
    
    for smi in valid_smiles:
        scaffold = get_murcko_scaffold(smi)
        if scaffold in test_scaffolds:
            test_split.append(smi)
        elif scaffold in val_scaffolds:
            val_split.append(smi)
        else:
            train_split.append(smi)
    
    return {
        'train': train_split,
        'val': val_split,
        'test': test_split
    }

def process_smiles_to_graphs(
    smiles_list: List[str],
    logger: logging.Logger
) -> Tuple[List[Dict[str, Any]], List[str], int]:
    """
    Convert a list of SMILES strings to graph representations.
    Handles invalid SMILES and logs exclusions.
    
    Returns:
        Tuple of (valid_graphs, excluded_smiles, total_processed)
    """
    valid_graphs = []
    excluded_smiles = []
    total_processed = 0
    
    for smi in smiles_list:
        total_processed += 1
        try:
            graph = smiles_to_graph(smi)
            if validate_graph(graph):
                valid_graphs.append(graph)
            else:
                excluded_smiles.append(smi)
                logger.debug(f"Invalid graph structure for SMILES: {smi}")
        except Exception as e:
            excluded_smiles.append(smi)
            logger.debug(f"Error processing SMILES {smi}: {e}")
            
    return valid_graphs, excluded_smiles, total_processed

def serialize_graphs_to_parquet(
    graphs: List[Dict[str, Any]],
    split_name: str,
    output_dir: str,
    logger: logging.Logger
):
    """
    Serialize a list of graph dictionaries to a Parquet file.
    Graphs are converted to a tabular format suitable for Parquet.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"qm9_processed_{split_name}.parquet")
    
    # Flatten graph data for Parquet
    # Assuming graph structure: {'nodes': [...], 'edges': [...], 'features': {...}}
    # We will serialize the node/edge lists as JSON strings for Parquet compatibility
    data_rows = []
    for i, graph in enumerate(graphs):
        row = {
            'graph_id': i,
            'num_nodes': len(graph.get('nodes', [])),
            'num_edges': len(graph.get('edges', [])),
            'node_features': json.dumps(graph.get('nodes', [])),
            'edge_features': json.dumps(graph.get('edges', [])),
            'properties': json.dumps(graph.get('properties', {}))
        }
        data_rows.append(row)
    
    df = pd.DataFrame(data_rows)
    df.to_parquet(output_path, compression='snappy')
    logger.info(f"Serialized {len(graphs)} graphs to {output_path}")

def generate_exclusion_report(
    total_molecules: int,
    excluded_count: int,
    output_path: str,
    logger: logging.Logger
):
    """
    Generate a JSON report of exclusion statistics.
    """
    exclusion_percentage = (excluded_count / total_molecules * 100) if total_molecules > 0 else 0.0
    
    report = {
        "total_molecules": total_molecules,
        "excluded_count": excluded_count,
        "exclusion_percentage": exclusion_percentage,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Exclusion report generated: {output_path}")
    return report

def main():
    """
    Main entry point for the preprocessing script.
    Implements memory safety logic and Murcko scaffold splitting.
    """
    logger = setup_script_logging()
    config = get_config()
    ensure_directories()
    
    logger.info("Starting QM9 data preprocessing...")
    
    # 1. Load Dataset
    logger.info("Loading QM9 dataset...")
    try:
        # Using streaming to estimate size without loading everything into memory initially
        dataset = load_dataset("qm9", split='train', streaming=True)
        # Consume a small sample to estimate memory requirements
        sample_size = 1000
        sample_data = list(dataset.take(sample_size))
        avg_mem_per_mol = check_memory_usage() / sample_size if sample_size > 0 else 0.0
        
        # Estimate total size
        # QM9 has ~130k molecules. We will process a subset if memory is tight.
        # For this implementation, we will process the first N molecules that fit in 4GB
        # based on the sample estimate.
        
        # Reset dataset to start
        dataset = load_dataset("qm9", split='train', streaming=True)
        
        # Calculate max molecules to process
        # We need to account for graph construction overhead, which is roughly 5x raw data
        estimated_overhead_factor = 5.0
        safe_limit_per_mol = avg_mem_per_mol * estimated_overhead_factor
        
        if safe_limit_per_mol <= 0:
            # Fallback if estimation failed
            max_molecules = 50000 
            logger.warning("Memory estimation failed. Using conservative default: 50,000 molecules.")
        else:
            max_molecules = int(MEMORY_LIMIT_BYTES / safe_limit_per_mol)
            logger.info(f"Estimated max molecules for {MEMORY_LIMIT_GB}GB limit: {max_molecules}")
        
        # Enforce a hard cap to prevent runaway memory if estimation is wrong
        if max_molecules > 100000:
            max_molecules = 100000
            logger.info(f"Capped max molecules to {max_molecules} to prevent excessive runtime.")
        
        # Sample N molecules (fixed seed)
        np.random.seed(config['seed'])
        # Since streaming doesn't support random sampling easily without full iteration,
        # we will iterate and select with a reservoir or just take the first N if we assume order is fine.
        # For reproducibility and simplicity in this MVP, we take the first N molecules.
        # In a more advanced version, we would shuffle indices first.
        
        logger.info(f"Processing first {max_molecules} molecules from QM9 train split.")
        
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

    # 2. Pre-Load Subset Sampling Logic
    # We have determined max_molecules. We will process them in batches.
    # If memory usage spikes during processing, we will reduce batch size.
    
    all_graphs = []
    all_excluded = []
    total_processed = 0
    
    current_batch_size = MAX_BATCH_SIZE
    batch = []
    
    # Log path for memory adjustments
    memory_log_path = os.path.join(config['artifacts_dir'], 'memory_adjustment.log')
    
    # Iterate through the dataset
    # Note: load_dataset with streaming returns an iterator
    iterator = dataset.take(max_molecules)
    
    start_time = time.time()
    
    for idx, item in enumerate(iterator):
        smi = item.get('smiles')
        if not smi:
            continue
        
        batch.append(smi)
        
        # Check memory before processing a full batch
        current_mem = check_memory_usage()
        if current_mem > (MEMORY_LIMIT_GB * 0.9): # Trigger at 90% to be safe
            logger.warning(f"Memory usage high ({current_mem:.2f}GB). Reducing batch size.")
            current_batch_size = max(MIN_BATCH_SIZE, current_batch_size // 2)
            log_memory_adjustment(current_batch_size, "Memory pressure > 90%", memory_log_path)
            # Process the current batch immediately and clear it
            if batch:
                graphs, excluded, count = process_smiles_to_graphs(batch, logger)
                all_graphs.extend(graphs)
                all_excluded.extend(excluded)
                total_processed += count
                batch = []
            continue
        
        # If batch is full, process it
        if len(batch) >= current_batch_size:
            graphs, excluded, count = process_smiles_to_graphs(batch, logger)
            all_graphs.extend(graphs)
            all_excluded.extend(excluded)
            total_processed += count
            batch = []
            
            # Check memory after processing a batch
            current_mem = check_memory_usage()
            if current_mem > (MEMORY_LIMIT_GB * 0.8):
                # Proactively reduce batch size for next iteration
                if current_batch_size > MIN_BATCH_SIZE:
                    current_batch_size = max(MIN_BATCH_SIZE, current_batch_size // 2)
                    log_memory_adjustment(current_batch_size, "Memory usage > 80% after batch", memory_log_path)

    # Process remaining batch
    if batch:
        graphs, excluded, count = process_smiles_to_graphs(batch, logger)
        all_graphs.extend(graphs)
        all_excluded.extend(excluded)
        total_processed += count

    end_time = time.time()
    logger.info(f"Preprocessing completed in {end_time - start_time:.2f} seconds.")
    logger.info(f"Total processed: {total_processed}, Excluded: {len(all_excluded)}")
    
    # 3. Murcko Scaffold Split
    logger.info("Performing Murcko scaffold split...")
    # We split the *original* SMILES list to ensure the split is based on the input
    # Since we only have the processed SMILES in all_graphs (or we can re-iterate the dataset)
    # To be precise, we should split the original SMILES. 
    # For this implementation, we will split the SMILES that were successfully processed.
    # Note: This is a slight approximation as we excluded invalid SMILES.
    
    processed_smiles = [g.get('smiles') for g in all_graphs if g.get('smiles')]
    splits = murcko_scaffold_split(processed_smiles)
    
    # 4. Serialize Graphs by Split
    processed_dir = config['processed_dir']
    
    for split_name, split_smiles in splits.items():
        # Filter graphs for this split
        # Since we have the graph objects, we need to map them back.
        # A simpler approach for this MVP: Re-process the split_smiles to get graphs.
        # This ensures the split SMILES match the graphs exactly.
        # However, to save time, we assume the order in `all_graphs` corresponds to `processed_smiles`.
        # Let's create a map for safety.
        
        smi_to_graph = {g['smiles']: g for g in all_graphs if 'smiles' in g}
        split_graphs = [smi_to_graph[smi] for smi in split_smiles if smi in smi_to_graph]
        
        if split_graphs:
            serialize_graphs_to_parquet(split_graphs, split_name, processed_dir, logger)
        else:
            logger.warning(f"No graphs found for split {split_name}")

    # 5. Generate Exclusion Report
    exclusion_report_path = os.path.join(config['artifacts_dir'], 'exclusion_report.json')
    report = generate_exclusion_report(total_processed, len(all_excluded), exclusion_report_path, logger)
    
    # Log metrics
    log_metric("preprocessing_total_molecules", total_processed)
    log_metric("preprocessing_excluded_count", len(all_excluded))
    log_metric("preprocessing_exclusion_percentage", report['exclusion_percentage'])
    
    logger.info("Preprocessing pipeline finished successfully.")

if __name__ == "__main__":
    main()
