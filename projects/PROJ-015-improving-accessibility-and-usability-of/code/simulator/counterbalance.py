"""
Counterbalancing module for the usability study.
Implements Latin Square design to assign interface sequences.
"""
from typing import List, Dict, Any
import random
from utils.seed import set_seed

class LatinSquareCounterbalancer:
    """
    Assigns participants to interface sequences (Traditional->Explainable or Explainable->Traditional)
    using a 2x2 Latin Square design to control for order effects.
    """
    def __init__(self, participants: List[str], seed: int = 42):
        """
        Initialize the counterbalancer.
        
        Args:
            participants: List of participant IDs.
            seed: Random seed for reproducibility.
        """
        set_seed(seed)
        self.participants = participants
        self.assignments: Dict[str, List[str]] = {}
        self._generate_assignments()

    def _generate_assignments(self):
        """
        Generate the Latin Square assignments.
        For 2 conditions, the sequences are [A, B] and [B, A].
        """
        # Define the two possible sequences for 2 conditions
        sequences = [
            ["Traditional", "Explainable"], 
            ["Explainable", "Traditional"]
        ]
        
        # Shuffle the order of sequences to randomize which participant gets which start
        # while maintaining the balance across the group.
        # For a true Latin Square with N participants, we rotate the base sequence.
        # Here with 2 sequences, we just shuffle the list and assign round-robin.
        random.shuffle(sequences)
        
        for i, pid in enumerate(self.participants):
            # Assign sequence cyclically to ensure equal distribution
            self.assignments[pid] = sequences[i % len(sequences)]

    def get_sequence(self, participant_id: str) -> List[str]:
        """
        Retrieve the interface sequence for a specific participant.
        
        Args:
            participant_id: The ID of the participant.
            
        Returns:
            A list of interface names in the order they should be presented.
            Returns empty list if participant not found.
        """
        return self.assignments.get(participant_id, [])

    def get_all_assignments(self) -> Dict[str, List[str]]:
        """
        Return a copy of all assignments.
        
        Returns:
            Dictionary mapping participant IDs to their interface sequences.
        """
        return self.assignments.copy()

def main():
    """
    Entry point for testing the counterbalancer module.
    """
    # Example usage
    test_participants = ["P001", "P002", "P003", "P004", "P005"]
    counterbalancer = LatinSquareCounterbalancer(test_participants, seed=42)
    
    print("Latin Square Counterbalancer Results:")
    print("-" * 40)
    for pid, seq in counterbalancer.get_all_assignments().items():
        print(f"Participant {pid}: {' -> '.join(seq)}")
    
    # Verify balance
    traditional_first = sum(1 for seq in counterbalancer.get_all_assignments().values() if seq[0] == "Traditional")
    explainable_first = sum(1 for seq in counterbalancer.get_all_assignments().values() if seq[0] == "Explainable")
    print("-" * 40)
    print(f"Traditional First: {traditional_first}")
    print(f"Explainable First: {explainable_first}")

if __name__ == "__main__":
    main()