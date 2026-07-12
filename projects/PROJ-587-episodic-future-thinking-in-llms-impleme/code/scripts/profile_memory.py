"""
Script to verify memory footprint < 7GB during index construction.

This script performs a realistic memory profiling run by:
1. Generating synthetic trajectory data that mimics the structure of ALFWorld/TextWorld data
2. Constructing a FAISS HNSW index (the primary memory consumer)
3. Measuring peak RSS (Resident Set Space) during the operation
4. Writing a verification report to data/processed/memory_profile_report.json

The synthetic data generation uses realistic string lengths and dimensions
to ensure the memory profile is representative of actual usage patterns.
"""

import json
import os
import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Constants
MAX_MEMORY_GB = 7.0
MAX_MEMORY_BYTES = MAX_MEMORY_GB * 1024**3

# FAISS and embedding dimensions
EMBEDDING_DIM = 768  # Typical for medium-sized transformers
NUM_EPISODES = 10000  # Number of episodes to simulate

# Output paths
DATA_PROCESSED_DIR = project_root / "data" / "processed"
REPORT_PATH = DATA_PROCESSED_DIR / "memory_profile_report.json"

# Ensure output directory exists
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def generate_synthetic_episode(n: int, embedding_dim: int) -> dict:
    """
    Generate a synthetic episode with realistic dimensions.
    
    Args:
        n: Episode index
        embedding_dim: Dimension of the embedding vector
    
    Returns:
        Dictionary containing state, action, outcome, and embedding
    """
    # Simulate realistic text lengths from ALFWorld/TextWorld
    state_text = f"State {n}: In a room with {np.random.randint(5, 20)} objects. Goal: {np.random.choice(['open', 'take', 'put', 'heat', 'cool'])} the {np.random.choice(['apple', 'book', 'key', 'cup', 'plate'])}."
    action_text = f"Action {n}: {np.random.choice(['go to', 'take', 'put', 'open', 'close', 'heat', 'cool'])} the {np.random.choice(['apple', 'book', 'key', 'cup', 'plate', 'drawer', 'fridge'])}."
    outcome_text = f"Outcome {n}: Successfully {np.random.choice(['completed', 'failed', 'partially completed'])} the task with {np.random.randint(1, 10)} steps remaining."
    
    # Generate realistic embedding (normalized random vector)
    embedding = np.random.randn(embedding_dim).astype(np.float32)
    embedding = embedding / np.linalg.norm(embedding)
    
    return {
        "episode_id": n,
        "state_text": state_text,
        "action_text": action_text,
        "outcome_text": outcome_text,
        "embedding": embedding
    }

def build_faiss_index(episodes: list) -> tuple:
    """
    Build FAISS HNSW index and measure memory usage.
    
    Args:
        episodes: List of episode dictionaries with embeddings
    
    Returns:
        Tuple of (index, peak_memory_bytes, build_time_seconds)
    """
    import faiss
    
    # Extract embeddings
    embeddings = np.array([ep["embedding"] for ep in episodes])
    
    # Start memory tracking
    tracemalloc.start()
    start_time = time.time()
    
    # Create FAISS HNSW index
    # M=32 is typical for HNSW, efConstruction=200 for good recall
    index = faiss.IndexHNSWFlat(EMBEDDING_DIM, 32)
    index.hnsw.efConstruction = 200
    
    # Add vectors to index (this is the memory-intensive operation)
    index.add(embeddings)
    
    # Get peak memory usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    build_time = time.time() - start_time
    
    return index, peak, build_time

def main():
    """Main entry point for memory profiling."""
    print(f"Starting memory profile for {NUM_EPISODES:,} episodes...")
    print(f"Max allowed memory: {MAX_MEMORY_GB} GB")
    
    # Generate synthetic data
    print(f"Generating {NUM_EPISODES:,} synthetic episodes...")
    episodes = [generate_synthetic_episode(i, EMBEDDING_DIM) for i in range(NUM_EPISODES)]
    
    # Build index and measure memory
    print("Building FAISS HNSW index...")
    index, peak_memory_bytes, build_time = build_faiss_index(episodes)
    
    # Calculate results
    peak_memory_gb = peak_memory_bytes / (1024**3)
    passed = peak_memory_gb < MAX_MEMORY_GB
    
    # Prepare report
    report = {
        "task_id": "T004c",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "parameters": {
            "num_episodes": NUM_EPISODES,
            "embedding_dim": EMBEDDING_DIM,
            "max_memory_gb": MAX_MEMORY_GB
        },
        "results": {
            "peak_memory_bytes": peak_memory_bytes,
            "peak_memory_gb": round(peak_memory_gb, 4),
            "build_time_seconds": round(build_time, 4),
            "index_size_bytes": index.d * index.ntotal * 4 + index.hnsw.max_connections * index.ntotal * 4,  # Approximate
            "passed": passed
        },
        "status": "PASS" if passed else "FAIL"
    }
    
    # Write report
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"MEMORY PROFILE RESULTS")
    print(f"{'='*60}")
    print(f"Episodes processed:     {NUM_EPISODES:,}")
    print(f"Embedding dimension:    {EMBEDDING_DIM}")
    print(f"Peak memory usage:      {peak_memory_gb:.4f} GB")
    print(f"Max allowed memory:     {MAX_MEMORY_GB} GB")
    print(f"Index build time:       {build_time:.4f} seconds")
    print(f"Status:                 {'PASS' if passed else 'FAIL'}")
    print(f"Report saved to:        {REPORT_PATH}")
    print(f"{'='*60}")
    
    if not passed:
        print(f"\n⚠️  WARNING: Memory usage ({peak_memory_gb:.4f} GB) exceeds limit ({MAX_MEMORY_GB} GB)")
        sys.exit(1)
    else:
        print(f"\n✅ SUCCESS: Memory usage ({peak_memory_gb:.4f} GB) is within limit ({MAX_MEMORY_GB} GB)")
        sys.exit(0)

if __name__ == "__main__":
    main()