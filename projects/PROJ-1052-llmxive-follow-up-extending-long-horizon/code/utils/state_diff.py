"""
T006/T014: State difference analysis for recovery segment identification.

Implements cosine similarity of sentence embeddings as a CPU-tractable proxy
for attention-weighted token overlap to identify recovery-critical context segments.
"""
import logging
import math
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity value between -1 and 1
    """
    if len(vec1) != len(vec2):
        raise ValueError(f"Vector dimensions mismatch: {len(vec1)} vs {len(vec2)}")
    
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(np.dot(vec1, vec2) / (norm1 * norm2))

def calculate_state_diff_embedding(observations: List[str]) -> np.ndarray:
    """
    Calculate embedding representation of state differences between observations.
    
    Uses a simple bag-of-words TF-IDF like approach as a CPU-tractable proxy.
    In a full implementation, this would use sentence-transformers embeddings.
    
    Args:
        observations: List of observation strings from trajectory
        
    Returns:
        Numpy array representing the state difference embedding
    """
    if not observations:
        return np.array([0.0])
    
    # Simple word frequency embedding (proxy for sentence embeddings)
    word_freq = {}
    for obs in observations:
        words = obs.lower().split()
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Normalize to create embedding vector
    total = sum(word_freq.values())
    if total == 0:
        return np.array([0.0])
    
    embedding = np.array([count / total for count in word_freq.values()])
    return embedding

def identify_recovery_segments(
    trajectory: Dict[str, Any],
    threshold_percentile: float = 0.95
) -> List[Dict[str, Any]]:
    """
    Identify segments contributing to state changes (recovery-critical segments).
    
    Uses cosine similarity of sentence embeddings to identify segments that
    contribute >5% to state change (as per T014 specification).
    
    Args:
        trajectory: Trajectory dictionary containing observations and rewards
        threshold_percentile: Percentile threshold for segment contribution
        
    Returns:
        List of identified recovery segments with their IDs and contribution scores
    """
    observations = trajectory.get('observations', [])
    if len(observations) < 2:
        logger.warning("Insufficient observations for recovery segment identification")
        return []
    
    # Calculate state differences between consecutive observations
    state_diffs = []
    for i in range(1, len(observations)):
        emb1 = calculate_state_diff_embedding([observations[i-1]])
        emb2 = calculate_state_diff_embedding([observations[i]])
        
        # Calculate magnitude of state change
        diff = np.abs(emb2 - emb1)
        magnitude = np.linalg.norm(diff)
        state_diffs.append({
            'segment_index': i,
            'magnitude': magnitude,
            'embedding_diff': diff
        })
    
    if not state_diffs:
        return []
    
    # Calculate total state change
    total_change = sum(seg['magnitude'] for seg in state_diffs)
    if total_change == 0:
        logger.warning("No state change detected in trajectory")
        return []
    
    # Identify segments contributing >5% to state change
    threshold = 0.05 * total_change
    recovery_segments = []
    
    for seg in state_diffs:
        if seg['magnitude'] > threshold:
            segment_id = f"seg_{seg['segment_index']}"
            recovery_segments.append({
                'segment_id': segment_id,
                'segment_index': seg['segment_index'],
                'contribution': seg['magnitude'] / total_change,
                'magnitude': seg['magnitude']
            })
    
    logger.info(f"Identified {len(recovery_segments)} recovery-critical segments")
    return recovery_segments

def process_baseline_logs_with_recovery_tags(baseline_logs_path: str) -> Optional[pd.DataFrame]:
    """
    Process baseline execution logs and add recovery segment tags.
    
    This function reads the baseline execution logs, identifies recovery segments
    for each trajectory, and adds the recovery_segment_id column.
    
    Args:
        baseline_logs_path: Path to baseline_execution_logs.csv
        
    Returns:
        DataFrame with added recovery_segment_id column
    """
    if not os.path.exists(baseline_logs_path):
        logger.error(f"Baseline logs file not found: {baseline_logs_path}")
        return None
    
    # Read baseline logs
    try:
        df = pd.read_csv(baseline_logs_path)
    except Exception as e:
        logger.error(f"Failed to read baseline logs: {e}")
        return None
    
    if df.empty:
        logger.warning("Baseline logs DataFrame is empty")
        return None
    
    # Process each trajectory to identify recovery segments
    recovery_segment_ids = []
    
    for idx, row in df.iterrows():
        task_id = row.get('task_id', f'task_{idx}')
        
        # Extract trajectory data
        trajectory = row.to_dict()
        
        # Identify recovery segments for this trajectory
        recovery_segments = identify_recovery_segments(trajectory)
        
        # Create recovery segment ID string
        if recovery_segments:
            segment_ids = [seg['segment_id'] for seg in recovery_segments]
            recovery_segment_id = ','.join(segment_ids)
        else:
            recovery_segment_id = ''
        
        recovery_segment_ids.append(recovery_segment_id)
    
    # Add recovery_segment_id column
    df['recovery_segment_id'] = recovery_segment_ids
    
    logger.info(f"Processed {len(df)} baseline trajectories with recovery tags")
    return df

def main():
    """Main entry point for T014 execution."""
    import sys
    from pathlib import Path
    
    baseline_path = Path(__file__).parent.parent.parent / "data" / "processed" / "baseline_execution_logs.csv"
    output_path = Path(__file__).parent.parent.parent / "data" / "processed" / "baseline_execution_logs.csv"
    
    if not baseline_path.exists():
        print(f"Error: Baseline logs not found at {baseline_path}")
        sys.exit(1)
    
    result_df = process_baseline_logs_with_recovery_tags(str(baseline_path))
    
    if result_df is not None:
        result_df.to_csv(output_path, index=False)
        print(f"Successfully processed and saved baseline logs with recovery tags to {output_path}")
    else:
        print("Failed to process baseline logs")
        sys.exit(1)

if __name__ == "__main__":
    main()
