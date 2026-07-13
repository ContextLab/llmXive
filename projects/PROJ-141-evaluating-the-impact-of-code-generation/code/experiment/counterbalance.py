"""
Counterbalancing implementation for carryover effect mitigation.

Implements Latin Square design and random order swapping to ensure
that the order of conditions (LLM-assisted vs baseline) is balanced
across participants.
"""
import os
import sys
import json
import logging
import random
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

# Import existing utilities
from experiment.randomization import pin_random_seed, generate_participant_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CounterbalanceError(Exception):
    """Custom exception for counterbalancing errors."""
    pass

class LatinSquare:
    """
    Implements a Latin Square design for counterbalancing.
    
    For a 2-condition experiment (A=LLM-assisted, B=baseline),
    generates two orders: [A, B] and [B, A].
    """
    
    def __init__(self, conditions: List[str]):
        """
        Initialize Latin Square with given conditions.
        
        Args:
            conditions: List of condition identifiers (e.g., ['llm', 'baseline'])
        """
        if len(conditions) < 2:
            raise CounterbalanceError("Latin Square requires at least 2 conditions")
        
        self.conditions = conditions
        self.n_conditions = len(conditions)
        
    def _generate_square(self) -> List[List[str]]:
        """
        Generate a Latin Square matrix.
        
        For 2 conditions, returns:
            [[A, B],
             [B, A]]
        """
        n = self.n_conditions
        square = []
        
        # Generate rows by cyclically shifting the base order
        for i in range(n):
            row = []
            for j in range(n):
                # Cyclic shift: row i, column j -> condition (j + i) % n
                idx = (j + i) % n
                row.append(self.conditions[idx])
            square.append(row)
        
        return square
    
    def get_order_for_participant(self, participant_id: str, seed: int) -> List[str]:
        """
        Determine the condition order for a specific participant.
        
        Uses the participant_id and seed to select a row from the Latin Square
        in a reproducible manner.
        
        Args:
            participant_id: Unique participant identifier
            seed: Random seed for reproducibility
            
        Returns:
            List of conditions in the order they should be presented
        """
        # Create a deterministic hash from participant_id and seed
        hash_input = f"{participant_id}_{seed}".encode('utf-8')
        hash_val = int(hashlib.sha256(hash_input).hexdigest(), 16)
        
        # Select row index based on hash
        row_index = hash_val % self.n_conditions
        
        # Generate the square and return the selected row
        square = self._generate_square()
        return square[row_index]

class CounterbalanceManager:
    """
    Manages counterbalancing for the experiment.
    
    Handles both Latin Square and random order swapping strategies
    to mitigate carryover effects.
    """
    
    def __init__(self, strategy: str = 'latin_square', seed: Optional[int] = None):
        """
        Initialize the counterbalance manager.
        
        Args:
            strategy: Counterbalancing strategy ('latin_square' or 'random_swap')
            seed: Random seed for reproducibility (if None, generates one)
        """
        self.strategy = strategy
        self.conditions = ['llm_assisted', 'baseline']
        self.seed = seed if seed is not None else random.randint(0, 2**31 - 1)
        self.latin_square = LatinSquare(self.conditions)
        
        logger.info(f"CounterbalanceManager initialized with strategy: {strategy}, seed: {self.seed}")
    
    def get_condition_order(self, participant_id: str) -> List[str]:
        """
        Get the condition order for a participant.
        
        Args:
            participant_id: Unique participant identifier
            
        Returns:
            List of conditions in presentation order
        """
        if self.strategy == 'latin_square':
            return self.latin_square.get_order_for_participant(participant_id, self.seed)
        
        elif self.strategy == 'random_swap':
            return self._get_random_order(participant_id)
        
        else:
            raise CounterbalanceError(f"Unknown strategy: {self.strategy}")
    
    def _get_random_order(self, participant_id: str) -> List[str]:
        """
        Generate a random order with equal probability for each permutation.
        
        Uses a seeded random generator based on participant_id for reproducibility.
        """
        # Create a deterministic seed from participant_id and base seed
        hash_input = f"{participant_id}_{self.seed}".encode('utf-8')
        local_seed = int(hashlib.sha256(hash_input).hexdigest(), 16) % (2**31 - 1)
        
        # Initialize local random generator
        local_random = random.Random(local_seed)
        
        # Create a copy of conditions and shuffle
        order = self.conditions.copy()
        local_random.shuffle(order)
        
        return order
    
    def verify_balance(self, participant_ids: List[str]) -> Dict[str, Any]:
        """
        Verify that the counterbalancing is balanced across participants.
        
        Args:
            participant_ids: List of participant identifiers
            
        Returns:
            Dictionary with balance statistics
        """
        orders = [self.get_condition_order(pid) for pid in participant_ids]
        
        # Count occurrences of each order
        order_counts = {}
        for order in orders:
            order_str = ','.join(order)
            order_counts[order_str] = order_counts.get(order_str, 0) + 1
        
        total = len(orders)
        balance_ratio = max(order_counts.values()) / total if total > 0 else 0
        
        result = {
            'total_participants': total,
            'order_counts': order_counts,
            'balance_ratio': balance_ratio,
            'is_balanced': balance_ratio <= 0.6  # Allow some tolerance
        }
        
        logger.info(f"Balance verification: {result}")
        return result
    
    def create_record(self, participant_id: str) -> Dict[str, Any]:
        """
        Create a counterbalancing record for a participant.
        
        Args:
            participant_id: Unique participant identifier
            
        Returns:
            Dictionary containing the counterbalancing record
        """
        order = self.get_condition_order(participant_id)
        
        record = {
            'participant_id': participant_id,
            'strategy': self.strategy,
            'seed': self.seed,
            'condition_order': order,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'hash': hashlib.sha256(
                f"{participant_id}_{self.seed}_{self.strategy}".encode('utf-8')
            ).hexdigest()
        }
        
        logger.info(f"Counterbalance record created for {participant_id}: {order}")
        return record

def apply_counterbalancing(participant_id: str, strategy: str = 'latin_square') -> List[str]:
    """
    Convenience function to get condition order for a participant.
    
    Args:
        participant_id: Unique participant identifier
        strategy: Counterbalancing strategy to use
        
    Returns:
        List of conditions in presentation order
    """
    manager = CounterbalanceManager(strategy=strategy)
    return manager.get_condition_order(participant_id)

def main():
    """
    Main function to demonstrate counterbalancing functionality.
    
    Runs a test with multiple participants and verifies balance.
    """
    logger.info("Starting counterbalance demonstration...")
    
    # Test with Latin Square strategy
    manager = CounterbalanceManager(strategy='latin_square', seed=42)
    
    # Generate orders for 10 participants
    test_participants = [f"participant_{i:03d}" for i in range(1, 11)]
    
    print("\n=== Counterbalancing Test Results ===")
    print(f"Strategy: {manager.strategy}")
    print(f"Seed: {manager.seed}")
    print(f"Conditions: {manager.conditions}")
    print("\nParticipant Condition Orders:")
    print("-" * 50)
    
    for pid in test_participants:
        order = manager.get_condition_order(pid)
        print(f"{pid}: {order}")
    
    # Verify balance
    print("\n=== Balance Verification ===")
    balance_result = manager.verify_balance(test_participants)
    print(f"Total participants: {balance_result['total_participants']}")
    print(f"Order distribution: {balance_result['order_counts']}")
    print(f"Balance ratio: {balance_result['balance_ratio']:.2f}")
    print(f"Is balanced: {balance_result['is_balanced']}")
    
    # Test random swap strategy
    print("\n=== Random Swap Strategy Test ===")
    random_manager = CounterbalanceManager(strategy='random_swap', seed=123)
    
    print(f"Strategy: {random_manager.strategy}")
    print(f"Seed: {random_manager.seed}")
    print("\nParticipant Condition Orders (Random Swap):")
    print("-" * 50)
    
    for pid in test_participants[:5]:  # Show first 5
        order = random_manager.get_condition_order(pid)
        print(f"{pid}: {order}")
    
    random_balance = random_manager.verify_balance(test_participants)
    print(f"\nRandom Swap Balance: {random_balance['order_counts']}")
    
    # Create a record example
    print("\n=== Sample Counterbalance Record ===")
    sample_record = manager.create_record("participant_001")
    print(json.dumps(sample_record, indent=2))
    
    logger.info("Counterbalance demonstration completed successfully.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
