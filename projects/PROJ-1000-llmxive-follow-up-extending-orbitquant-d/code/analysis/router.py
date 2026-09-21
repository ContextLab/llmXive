"""
EntropyRouter module for mapping semantic entropy to rotation matrix indices.
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
        # The clustering report structure from T022 is expected to have:
        # { "layers": ..., "subsets": ..., "boundaries": [list of floats], "matrices": [...] }
        # If the structure is nested, adjust accordingly.
        
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
        - If entropy > max_boundary -> Index N-1
        - Otherwise -> Find the interval containing the score.
        
        Args:
            entropy_score: The computed semantic entropy.
            
        Returns:
            The index of the rotation matrix to use.
        """
        if not self.boundaries:
            # Fallback to median/first if no boundaries (should not happen)
            return 0
        
        # Clamp to range
        min_ent = self.boundaries[0]
        max_ent = self.boundaries[-1]
        
        if entropy_score <= min_ent:
            return 0
        if entropy_score >= max_ent:
            return len(self.boundaries) - 1
        
        # Binary search for the interval
        # boundaries = [b0, b1, b2, ...]
        # Interval 0: (-inf, b0] -> Matrix 0
        # Interval 1: (b0, b1] -> Matrix 1
        # ...
        # Interval N: (bN-1, inf) -> Matrix N
        
        # Using np.searchsorted:
        # indices = np.searchsorted(boundaries, score, side='right')
        # If score is 0.5 and boundaries=[0.4, 0.6], searchsorted returns 1 (index 1)
        # We want matrix index = index - 1? No.
        # Let's define:
        # boundaries = [b1, b2, ..., bk] (k boundaries) -> k+1 regions
        # Region 0: score <= b1 -> Matrix 0
        # Region 1: b1 < score <= b2 -> Matrix 1
        # ...
        # Region k: score > bk -> Matrix k
        
        idx = np.searchsorted(self.boundaries, entropy_score, side='right')
        
        # Ensure index is within valid matrix range
        # If we have k boundaries, we have k+1 matrices (0 to k)
        max_idx = len(self.boundaries) # This is the count of matrices if we have k boundaries?
        # Wait, if boundaries = [b1, b2], we have 3 regions: <=b1, (b1,b2], >b2.
        # So indices 0, 1, 2.
        # searchsorted returns 0, 1, 2.
        # So the index returned IS the matrix index.
        
        # Clamp to number of matrices available
        num_matrices = len(self.matrices)
        # If num_matrices != len(boundaries) + 1, we have a mismatch.
        # We assume the clustering report is consistent.
        
        if idx >= num_matrices:
            idx = num_matrices - 1
        
        return int(idx)

    def get_matrix(self, index: int):
        """Retrieves the rotation matrix by index."""
        if 0 <= index < len(self.matrices):
            return self.matrices[index]
        raise IndexError(f"Matrix index {index} out of range [0, {len(self.matrices)-1}]")

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