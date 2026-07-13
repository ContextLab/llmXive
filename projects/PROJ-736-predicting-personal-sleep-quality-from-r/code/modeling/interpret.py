"""
Model interpretation script.
"""
import os
import sys
import json
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any
from scipy import sparse
from config import get_paths
from utils.logging import setup_logging, log_stage_complete

def load_model_coefficients():
    paths = get_paths()
    path = os.path.join(paths['results'], 'model_coefs.npy')
    if os.path.exists(path):
        return np.load(path)
    return None

def extract_nonzero_edges(coefs: np.ndarray, threshold=0.0):
    """Extract edges with non-zero coefficients."""
    indices = np.where(np.abs(coefs) > threshold)[0]
    return indices, coefs[indices]

def run_interpretation():
    """Run interpretation logic."""
    log_stage_start("Interpretation", "Extracting non-zero coefficients")
    coefs = load_model_coefficients()
    
    if coefs is None:
        log_stage_complete("Interpretation", "No coefficients found.")
        return
    
    indices, values = extract_nonzero_edges(coefs)
    
    # Save interpreted edges
    paths = get_paths()
    out_path = os.path.join(paths['results'], 'interpreted_edges.json')
    
    edges = [
        {"index": int(i), "coefficient": float(v)}
        for i, v in zip(indices, values)
    ]
    
    with open(out_path, 'w') as f:
        json.dump({"edges": edges}, f, indent=2)
    
    log_stage_complete("Interpretation", f"Found {len(edges)} non-zero edges.")

def main():
    run_interpretation()

if __name__ == "__main__":
    main()
