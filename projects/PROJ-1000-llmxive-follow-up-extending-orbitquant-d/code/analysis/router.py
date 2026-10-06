"""
EntropyRouter module for mapping semantic entropy to rotation matrix indices.
Implements robust clamping and outlier handling as per US2 requirements.
"""
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from config import Config

logger = logging.getLogger(__name__)

class EntropyRouter:
    """
    Maps prompt semantic entropy scores to pre-optimized rotation matrix indices.
    Uses boundaries derived from clustering to determine the optimal matrix.
    Handles out-of-range values via clamping and proxy failures via static fallback.
    """
    
    def __init__(self, clustering_report_path: str, config: Optional[Config] = None):
        """
        Initializes the router by loading the clustering report.
        
        Args:
            clustering_report_path: Path to the clustering_report.json file.
            config: Optional Config instance for fallback parameters.
        """
        self.config = config or Config()
        self.report = self._load_report(clustering_report_path)
        self.boundaries = self._extract_boundaries()
        self.matrices = self.report.get('matrices', [])
        
        if not self.boundaries:
            raise ValueError("No valid boundaries found in clustering report. Router cannot function.")
        
        # Ensure we have matrices for every boundary interval
        # If boundaries has N items, we expect N+1 matrices (regions)
        # If the report has exactly N matrices for N boundaries, we adjust logic to N-1 or pad.
        # Standard clustering output: N boundaries define N+1 clusters.
        # We assume the clustering report is consistent: len(matrices) == len(boundaries) + 1
        
        if len(self.matrices) != len(self.boundaries) + 1:
            logger.warning(f"Matrix count ({len(self.matrices)}) does not match boundary intervals ({len(self.boundaries) + 1}). "
                         f"Truncating or padding to match. Using {min(len(self.matrices), len(self.boundaries) + 1)} matrices.")
            # Clamp matrices to expected count
            expected = len(self.boundaries) + 1
            if len(self.matrices) > expected:
                self.matrices = self.matrices[:expected]
            else:
                # Pad with the last matrix if we have too few
                last_matrix = self.matrices[-1]
                while len(self.matrices) < expected:
                    self.matrices.append(last_matrix)
        
        logger.info(f"EntropyRouter initialized with {len(self.boundaries)} boundaries and {len(self.matrices)} matrices.")

    def _load_report(self, path: str) -> Dict[str, Any]:
        """Loads the clustering report JSON."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Clustering report not found: {path}")
        
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data

    def _extract_boundaries(self) -> List[float]:
        """
        Extracts the sorted entropy boundaries from the report.
        Assumes the report contains a 'boundaries' key or similar structure.
        """
        raw_boundaries = self.report.get('boundaries', [])
        
        # Filter and sort
        valid_boundaries = [float(b) for b in raw_boundaries if isinstance(b, (int, float))]
        valid_boundaries = sorted(list(set(valid_boundaries)))
        
        return valid_boundaries

    def route(self, entropy_score: float) -> int:
        """
        Maps an entropy score to a matrix index.
        
        Logic:
        - If entropy < min_boundary -> Index 0
        - If entropy > max_boundary -> Index N-1 (last matrix)
        - Otherwise -> Find the interval containing the score.
        
        Handles outliers by clamping to the nearest valid index.
        
        Args:
            entropy_score: The computed semantic entropy.
            
        Returns:
            The index of the rotation matrix to use.
        """
        if not self.boundaries:
            # Fallback to first matrix if no boundaries (should not happen due to init check)
            return 0
        
        min_ent = self.boundaries[0]
        max_ent = self.boundaries[-1]
        
        # Clamp out-of-range values
        if entropy_score <= min_ent:
            return 0
        if entropy_score >= max_ent:
            return len(self.boundaries) # Index corresponding to the last interval
        
        # Binary search for the interval
        # boundaries = [b0, b1, b2, ...]
        # Region 0: score <= b0 -> Matrix 0
        # Region 1: b0 < score <= b1 -> Matrix 1
        # ...
        # Region N: score > bN-1 -> Matrix N
        
        # np.searchsorted returns the index where the element would be inserted to maintain order.
        # side='right' means if the element is equal to an existing value, it goes after.
        # Example: boundaries = [1.0, 2.0, 3.0]
        # score = 0.5 -> idx=0 (Matrix 0)
        # score = 1.0 -> idx=1 (Matrix 1)  <-- Boundary case: score == b0 goes to next region?
        # Let's verify the logic:
        # If boundaries are split points, usually:
        # Interval 0: (-inf, b0]
        # Interval 1: (b0, b1]
        # ...
        # If score == b0, it falls in Interval 1? Or Interval 0?
        # The previous implementation used 'right', meaning score <= b0 -> idx=1? No.
        # searchsorted([1, 2], 0.5) -> 0.
        # searchsorted([1, 2], 1.0) -> 1 (because side='right', 1.0 is after 1? No, 1.0 == 1, right means after).
        # So if score == b0, it returns 1.
        # This implies:
        # score <= b0 -> 0? No, 0.5 < 1.0 -> 0.
        # 1.0 == 1.0 -> 1.
        # So the region (b_{i-1}, b_i] maps to index i.
        # Region 0: (-inf, b0] -> Index 0?
        # If score = 0.5 ( < 1.0), returns 0. Correct.
        # If score = 1.0 (== 1.0), returns 1. Correct (Region 1).
        # So the index returned by searchsorted IS the matrix index.
        
        idx = np.searchsorted(self.boundaries, entropy_score, side='right')
        
        # Ensure index is within valid matrix range
        # We have len(boundaries) + 1 matrices.
        # Max valid index is len(boundaries).
        # searchsorted returns values in [0, len(boundaries)].
        # So no need to clamp if logic holds, but safe to clamp.
        
        max_idx = len(self.boundaries)
        if idx > max_idx:
            idx = max_idx
        
        return int(idx)

    def get_matrix(self, index: int):
        """Retrieves the rotation matrix by index."""
        if 0 <= index < len(self.matrices):
            return self.matrices[index]
        raise IndexError(f"Matrix index {index} out of range [0, {len(self.matrices)-1}]")

    def route_with_fallback(self, entropy_score: float) -> Tuple[int, bool]:
        """
        Routes with a fallback mechanism for invalid scores or errors.
        
        Args:
            entropy_score: The computed semantic entropy.
            
        Returns:
            Tuple of (matrix_index, was_fallback_used)
        """
        try:
            idx = self.route(entropy_score)
            return idx, False
        except Exception as e:
            logger.warning(f"Router failed for entropy {entropy_score}: {e}. Using fallback index 0.")
            return 0, True

def main():
    """Entry point for testing the router."""
    import sys
    from config import Config
    
    config = Config()
    report_path = config.data_path / "processed" / "clustering_report.json"
    
    if not report_path.exists():
        print(f"Error: {report_path} not found. Run T022 first.")
        sys.exit(1)
    
    router = EntropyRouter(str(report_path), config)
    
    # Test cases
    test_scores = [0.1, 0.5, 1.0, 10.0]
    for score in test_scores:
        idx = router.route(score)
        print(f"Entropy {score:.2f} -> Matrix Index {idx}")

if __name__ == "__main__":
    main()