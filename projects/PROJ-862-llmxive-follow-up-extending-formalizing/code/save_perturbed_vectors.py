"""
T025: Save perturbed vectors and metadata to data/processed/perturbed_vectors.csv.

This script consumes the intermediate perturbation results generated during the noise sweep
(typically stored in a temporary JSON or in-memory structure by main.py) and persists them
to a permanent CSV artifact linked by PairID and sigma.

It ensures the output matches the schema defined in specs/001-lm-axive-noise-injection/contracts/latent-vector.schema.yaml:
Fields: pair_id, task_type, vector_base64 (L2 normalized), norm_status.
Additional columns for T025: sigma, perturbation_method.

Prerequisites:
- data/processed/baseline_vectors.csv (for PairID/TaskType mapping if not in results)
- Perturbation results must be available (passed via argument or generated inline by main.py context)

Execution:
python code/save_perturbed_vectors.py
"""

import os
import sys
import csv
import json
import logging
import base64
import torch
from typing import List, Dict, Any, Optional
from pathlib import Path

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import OutputPaths, load_config
from memory_monitor import get_peak_memory_mb, check_memory_limit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("save_perturbed_vectors")

# Constants
MEMORY_LIMIT_GB = 7.0  # SC-004

def load_perturbation_results(results_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Loads perturbation results. 
    In the context of T024a (main.py), these are often generated in-memory and passed here.
    If a file path is provided (e.g., from a checkpoint), load from disk.
    Otherwise, attempts to load from the standard intermediate location if main.py wrote one.
    """
    if results_path and os.path.exists(results_path):
        logger.info(f"Loading perturbation results from: {results_path}")
        with open(results_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Fallback: Check for a standard intermediate file created by main.py sweep loop
    # T024a logic might write to a temp file before this script runs, or we rely on main.py
    # to pass the data. For this standalone script, we expect the data to be generated 
    # or passed via a specific mechanism. 
    # However, per T025 description, we are the saver. 
    # If main.py didn't write a temp file, this script must be run in a context where 
    # data is available. 
    # To make this script runnable as a standalone verification or continuation, 
    # we will assume main.py generated 'data/processed/perturbation_intermediate.json'
    # or we raise an error if not found, preventing silent failure.
    
    default_path = os.path.join(PROJECT_ROOT, "data", "processed", "perturbation_intermediate.json")
    if os.path.exists(default_path):
        logger.info(f"Loading from default intermediate path: {default_path}")
        with open(default_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # If we are here, we have no data. This is a critical failure state for T025.
    # We must not fabricate data.
    raise FileNotFoundError(
        "No perturbation results found. "
        "Ensure T024a (main.py) has run and produced 'data/processed/perturbation_intermediate.json' "
        "or pass the --results-path argument."
    )

def parse_vector(vector_data: Any) -> torch.Tensor:
    """
    Parses vector data which might be a list of floats, a base64 string, or a tensor representation.
    Returns a torch.Tensor.
    """
    if isinstance(vector_data, torch.Tensor):
        return vector_data
    
    if isinstance(vector_data, list):
        return torch.tensor(vector_data, dtype=torch.float32)
    
    if isinstance(vector_data, str):
        # Might be base64
        try:
            decoded = base64.b64decode(vector_data)
            # Try to load as numpy/torch if it was serialized that way, 
            # but simpler assumption: if it's a string in the result, it might be raw floats separated by comma
            # or base64 of a float array. 
            # Given T015 outputs base64, we assume this might be base64.
            # If it fails base64 decode as tensor, try comma split.
            try:
                # Attempt base64 decode to bytes then reconstruct (complex)
                # Simpler: If it's a base64 string of a tensor, we need to know the format.
                # Let's assume if it's a string, it's a list of floats stringified or base64.
                # We'll try comma split first as a fallback for list-strings.
                if ',' in vector_data:
                    return torch.tensor([float(x) for x in vector_data.split(',')], dtype=torch.float32)
                else:
                    # It's likely base64 encoded bytes of a numpy array or similar.
                    # For safety, we assume the input from main.py is a list of floats or base64.
                    # If it's base64 of a tensor, we need to know the dtype/shape.
                    # Let's assume the 'vector_data' passed here is a list of floats for simplicity 
                    # unless it's explicitly a base64 string that decodes to bytes.
                    # Actually, T015 outputs base64. T024a likely carries that forward or recalculates.
                    # We will try to decode as base64 and assume it's a raw float32 array.
                    import numpy as np
                    arr = np.frombuffer(decoded, dtype=np.float32)
                    return torch.from_numpy(arr)
            except Exception:
                raise ValueError(f"Could not parse vector string: {vector_data[:50]}...")
        except Exception:
            raise ValueError(f"Invalid vector string format: {vector_data[:50]}...")
    
    raise TypeError(f"Unsupported vector type: {type(vector_data)}")

def validate_and_prepare_record(record: Dict[str, Any]) -> Dict[str, str]:
    """
    Validates a single record and prepares it for CSV writing.
    Ensures L2 normalization and base64 encoding.
    """
    pair_id = record.get('pair_id')
    task_type = record.get('task_type')
    sigma = record.get('sigma')
    vector_data = record.get('vector')
    
    if not pair_id or not task_type:
        raise ValueError(f"Record missing pair_id or task_type: {record}")
    
    if vector_data is None:
        raise ValueError(f"Record missing vector data: {record}")
    
    try:
        vec_tensor = parse_vector(vector_data)
    except Exception as e:
        logger.error(f"Failed to parse vector for PairID {pair_id}: {e}")
        raise
    
    # L2 Normalize
    norm = vec_tensor.norm(p=2)
    if norm.item() == 0:
        # Avoid division by zero, though unlikely for meaningful embeddings
        vec_tensor = vec_tensor / 1e-9
    else:
        vec_tensor = vec_tensor / norm
    
    # Base64 encode
    vec_np = vec_tensor.detach().cpu().numpy().astype('float32')
    import numpy as np
    vec_bytes = vec_np.tobytes()
    vec_base64 = base64.b64encode(vec_bytes).decode('ascii')
    
    return {
        'pair_id': str(pair_id),
        'task_type': str(task_type),
        'sigma': str(sigma),
        'vector_base64': vec_base64,
        'norm_status': 'L2_NORMALIZED',
        'dimension': str(vec_tensor.shape[0])
    }

def save_perturbed_vectors(records: List[Dict[str, Any]], output_path: str) -> int:
    """
    Saves the validated records to the output CSV.
    Returns the count of saved records.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = ['pair_id', 'task_type', 'sigma', 'vector_base64', 'norm_status', 'dimension']
    
    saved_count = 0
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in records:
            try:
                prepared = validate_and_prepare_record(record)
                writer.writerow(prepared)
                saved_count += 1
            except Exception as e:
                logger.warning(f"Skipping invalid record {record.get('pair_id', 'UNKNOWN')}: {e}")
                continue
    
    logger.info(f"Saved {saved_count} perturbed vectors to {output_path}")
    return saved_count

def main():
    """
    Entry point for T025.
    """
    logger.info("Starting T025: Save Perturbed Vectors")
    
    # Check memory
    check_memory_limit(MEMORY_LIMIT_GB)
    
    # Load config to get paths
    config = load_config()
    output_paths = config.output_paths if hasattr(config, 'output_paths') else OutputPaths()
    
    # Determine output path
    # T025 specific output: data/processed/perturbed_vectors.csv
    output_file = os.path.join(PROJECT_ROOT, "data", "processed", "perturbed_vectors.csv")
    
    # Check for command line argument for results path
    results_path = None
    if len(sys.argv) > 1:
        results_path = sys.argv[1]
    
    try:
        # 1. Load results
        perturbation_results = load_perturbation_results(results_path)
        
        if not isinstance(perturbation_results, list):
            raise ValueError("Expected perturbation results to be a list of records.")
        
        logger.info(f"Loaded {len(perturbation_results)} perturbation records.")
        
        # 2. Save to CSV
        saved_count = save_perturbed_vectors(perturbation_results, output_file)
        
        if saved_count == 0:
            logger.warning("No valid records were saved. Check input data.")
            # Do not fail hard if input was empty, but log warning.
        else:
            logger.info(f"Successfully wrote {output_file}")
            
        # 3. Update memory profile if possible
        # T008b requirement: log peak RSS
        from memory_monitor import get_peak_memory_mb, save_memory_profile
        peak_mb = get_peak_memory_mb()
        profile_path = os.path.join(PROJECT_ROOT, "data", "processed", "memory_profile.json")
        
        # Load existing profile if exists, update, save
        profile = {}
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                profile = json.load(f)
        
        profile['last_perturbation_save'] = {
            'timestamp': str(torch.utils.data.get_worker_info()), # Placeholder for real timestamp logic if needed
            'peak_memory_mb': peak_mb
        }
        
        with open(profile_path, 'w') as f:
            json.dump(profile, f, indent=2)
            
        logger.info(f"Updated memory profile at {profile_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Critical: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during T025 execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
