"""
code/utils/state_diff.py

Implements recovery segment identification using cosine similarity of sentence embeddings.
This is a CPU-tractable proxy for attention-weighted token overlap (FR-007).
"""
import logging
import math
import os
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

# Use sentence-transformers for embeddings.
# If not installed, the import will fail loudly as per constraints.
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError(
        "Required package 'sentence-transformers' not found. "
        "Please install it via: pip install sentence-transformers"
    )

logger = logging.getLogger(__name__)

# Global model cache to avoid reloading the model on every call
_model_cache: Optional[SentenceTransformer] = None

def _get_model() -> SentenceTransformer:
    """Load or retrieve the sentence embedding model."""
    global _model_cache
    if _model_cache is None:
        # Using a small, efficient model optimized for CPU
        logger.info("Loading sentence-transformer model 'all-MiniLM-L6-v2'...")
        _model_cache = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Model loaded successfully.")
    return _model_cache

def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Args:
        vec_a: First vector (numpy array)
        vec_b: Second vector (numpy array)
    
    Returns:
        Cosine similarity score (float between -1 and 1)
    """
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

def calculate_state_diff_embedding(observations: List[str]) -> np.ndarray:
    """
    Calculate the embedding representation of the state change (diff) 
    across a sequence of observations.
    
    This function concatenates the observations into a single text block 
    to represent the "state evolution" and computes its embedding.
    
    Args:
        observations: List of observation strings from the trajectory.
    
    Returns:
        A numpy array representing the embedding of the state sequence.
    """
    if not observations:
        return np.zeros(512) # Default zero vector if empty

    model = _get_model()
    # Join observations to capture the full context of the state change
    # We use a separator to distinguish steps
    text = " | ".join(observations)
    embedding = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
    return embedding

def identify_recovery_segments(
    trajectory: List[Dict[str, Any]],
    threshold_ratio: float = 0.05
) -> List[int]:
    """
    Identify segments contributing >5% to the total state change.
    
    Definition: contribution > 0.05 * sum(abs(state_diff) for all segments).
    Since we use embeddings, we calculate the contribution of each segment
    relative to the total magnitude of state changes in the trajectory.
    
    Args:
        trajectory: List of step dictionaries, each containing 'observation'.
        threshold_ratio: The threshold ratio (default 0.05 for 5%).
    
    Returns:
        List of segment indices (0-based) that are considered recovery-critical.
    """
    if not trajectory:
        return []
    
    model = _get_model()
    
    # Extract observations
    observations = [step.get('observation', '') for step in trajectory if 'observation' in step]
    
    if len(observations) < 2:
        # Cannot compute diff if less than 2 observations
        logger.warning("Trajectory has fewer than 2 observations. No segments identified.")
        return []
    
    # Compute embeddings for each observation to measure state change
    # We compute the difference between consecutive states
    embeddings = []
    for obs in observations:
        emb = model.encode(obs, convert_to_numpy=True, show_progress_bar=False)
        embeddings.append(emb)
    
    # Calculate pairwise distances (state changes)
    # We treat the magnitude of the change between step i and i+1 as the "contribution"
    # of that transition. The segment ID corresponds to the starting step of the transition.
    contributions = []
    
    for i in range(len(embeddings) - 1):
        diff_vec = embeddings[i+1] - embeddings[i]
        # Use L2 norm of the difference as the magnitude of state change
        magnitude = np.linalg.norm(diff_vec)
        contributions.append(magnitude)
    
    if not contributions:
        return []
        
    total_change = sum(contributions)
    
    if total_change == 0:
        logger.warning("Total state change is zero. No segments identified.")
        return []
    
    threshold_value = threshold_ratio * total_change
    
    recovery_segments = []
    for idx, contribution in enumerate(contributions):
        if contribution > threshold_value:
            # The segment index corresponds to the step where the significant change started
            recovery_segments.append(idx)
    
    logger.info(f"Identified {len(recovery_segments)} recovery-critical segments out of {len(trajectory)} steps.")
    return recovery_segments

def process_baseline_logs_with_recovery_tags(
    input_path: str,
    output_path: str
) -> None:
    """
    Reads the baseline execution logs, computes recovery segments for each trajectory,
    and writes the updated CSV with a 'recovery_segment_id' column.
    
    The 'recovery_segment_id' column will contain a JSON string of the list of indices,
    or an empty string if none were found.
    
    Args:
        input_path: Path to the input CSV (data/processed/baseline_execution_logs.csv).
        output_path: Path to the output CSV.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading baseline logs from {input_path}...")
    df = pd.read_csv(input_path)
    
    # Verify required columns exist
    required_cols = ['task_id', 'trajectory']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input CSV: {missing_cols}")
    
    logger.info(f"Processing {len(df)} rows for recovery segment tagging...")
    
    recovery_ids = []
    
    for idx, row in df.iterrows():
        task_id = row['task_id']
        # The trajectory is stored as a JSON string in the CSV
        try:
            trajectory = json.loads(row['trajectory'])
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Row {idx} (Task {task_id}): Invalid trajectory JSON. Skipping.")
            recovery_ids.append("[]")
            continue
        
        if not isinstance(trajectory, list):
            logger.warning(f"Row {idx} (Task {task_id}): Trajectory is not a list. Skipping.")
            recovery_ids.append("[]")
            continue
        
        segments = identify_recovery_segments(trajectory)
        recovery_ids.append(json.dumps(segments))
        
        if idx % 100 == 0:
            logger.info(f"Processed {idx}/{len(df)} rows...")
    
    df['recovery_segment_id'] = recovery_ids
    
    logger.info(f"Writing updated logs to {output_path}...")
    df.to_csv(output_path, index=False)
    logger.info("Done.")

def main():
    """Entry point for T014 execution."""
    import json # Import here to avoid circular if needed, though not used in top level
    
    # Define paths relative to project root
    # Assuming script runs from project root or code/
    base_dir = Path(__file__).resolve().parent.parent
    input_path = base_dir / "data" / "processed" / "baseline_execution_logs.csv"
    output_path = base_dir / "data" / "processed" / "baseline_execution_logs.csv" # Overwrite or save to new? Task says "Update"
    
    # If the task implies creating a new file, we might rename, but "Update" implies in-place or overwrite.
    # To be safe, we write to the same path.
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        process_baseline_logs_with_recovery_tags(str(input_path), str(output_path))
        logger.info("T014 Execution completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during T014 execution: {e}")
        raise

if __name__ == "__main__":
    main()
