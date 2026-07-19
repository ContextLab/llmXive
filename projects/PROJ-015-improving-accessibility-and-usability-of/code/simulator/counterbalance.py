"""
Counterbalancing Module.

Implements Latin Square Counterbalancing to assign interface sequences.
This module ensures that for two conditions (Traditional, Explainable),
the sequences are balanced:
1. Traditional -> Explainable
2. Explainable -> Traditional
"""

from typing import List, Dict, Any, Optional
import hashlib
from utils.seed import set_seed

class LatinSquareCounterbalancer:
    """
    Generates counterbalanced sequences for A/B testing using a deterministic
    hash-based approach to ensure reproducibility while balancing the groups.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the counterbalancer.

        Args:
            seed: Optional seed for reproducibility if needed for future
                  randomization extensions. Currently, assignment is hash-based.
        """
        if seed is not None:
            set_seed(seed)

    def get_sequence(self, participant_id: str) -> List[str]:
        """
        Determine the sequence for a participant using a hash of their ID.

        This ensures:
        1. The same participant always gets the same sequence (reproducibility).
        2. Different participants are distributed roughly 50/50 between sequences
           (balance).

        Args:
            participant_id: Unique identifier for the participant.

        Returns:
            List of interface types in the order they should be presented.
            Options are ["traditional", "explainable"] or ["explainable", "traditional"].
        """
        if not participant_id:
            raise ValueError("participant_id cannot be empty")

        # Use a hash of the participant ID to determine the sequence
        # This ensures the same participant always gets the same sequence
        # but different participants get randomized sequences
        # Using hashlib for a consistent hash across Python versions/sessions
        hash_obj = hashlib.md5(participant_id.encode('utf-8'))
        hash_int = int(hash_obj.hexdigest(), 16)
        
        # Map even/odd hash to sequence
        if hash_int % 2 == 0:
            return ["traditional", "explainable"]
        else:
            return ["explainable", "traditional"]

    def get_sequence_index(self, participant_id: str) -> int:
        """
        Get the index of the sequence for a participant (0 or 1).

        Args:
            participant_id: Unique identifier for the participant.

        Returns:
            0 for traditional->explainable, 1 for explainable->traditional.
        """
        sequence = self.get_sequence(participant_id)
        if sequence == ["traditional", "explainable"]:
            return 0
        return 1

def main():
    """Test the counterbalancer."""
    counterbalancer = LatinSquareCounterbalancer()
    
    # Test with a few participant IDs
    p_ids = ["P001", "P002", "P003", "P004", "P005", "P006"]
    print("Latin Square Counterbalancer Test Results:")
    print("-" * 50)
    for p_id in p_ids:
        seq = counterbalancer.get_sequence(p_id)
        idx = counterbalancer.get_sequence_index(p_id)
        print(f"Participant {p_id}: Sequence {idx} -> {seq}")
    
    # Verify balance
    sequences = [counterbalancer.get_sequence(p) for p in p_ids]
    traditional_first = sum(1 for s in sequences if s[0] == "traditional")
    explainable_first = sum(1 for s in sequences if s[0] == "explainable")
    print("-" * 50)
    print(f"Traditional first: {traditional_first}, Explainable first: {explainable_first}")

if __name__ == "__main__":
    main()