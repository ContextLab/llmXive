"""
Helper script to generate a dummy skill_index.npz for testing T030.
This script creates the required dependency file with dummy data.
"""
import os
import sys
from pathlib import Path
import numpy as np

def main():
    project_root = Path(__file__).resolve().parent.parent
    index_path = project_root / "data" / "processed" / "skill_index.npz"
    
    index_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create dummy normalized vectors (L2 normalized)
    # Simulating flattened A/B matrices
    # Shape: 4096 x 1024 -> flattened 4,194,304. Too big for dummy.
    # We use a smaller dimension for the dummy file to keep it small, 
    # but the code in T030 handles any dimension.
    dim = 100 
    
    vectors = {
        "alfworld_task_1_vector": np.random.randn(dim),
        "alfworld_task_2_vector": np.random.randn(dim),
        "alfworld_task_3_vector": np.random.randn(dim),
    }
    
    # Normalize
    for key in vectors:
        vec = vectors[key]
        vectors[key] = vec / np.linalg.norm(vec)
    
    np.savez(index_path, **vectors)
    print(f"Generated dummy index at {index_path}")

if __name__ == "__main__":
    main()
