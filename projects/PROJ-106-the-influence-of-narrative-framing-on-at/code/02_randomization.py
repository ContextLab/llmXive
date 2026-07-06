import argparse
import json
import os
import sys
import random
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.random_utils import set_global_seed, ensure_seed_set
from utils.logger import log_script_start, log_script_end, log_data_operation, setup_logger

def generate_participant_id() -> str:
    """Generate a unique participant ID."""
    return str(uuid.uuid4())

def assign_condition(seed: int) -> str:
    """
    Assign a participant to a condition (Partner or Tool) with 50/50 probability.
    
    Args:
        seed: Random seed for reproducibility
        
    Returns:
        Condition string: 'Partner' or 'Tool'
    """
    random.seed(seed)
    return 'Partner' if random.random() < 0.5 else 'Tool'

def run_randomization(n_participants: int, seed: int = None) -> List[Dict[str, Any]]:
    """
    Run randomization for a batch of participants.
    
    Args:
        n_participants: Number of participants to randomize
        seed: Random seed for reproducibility (optional)
        
    Returns:
        List of dictionaries containing participant_id, condition, and timestamp
    """
    if seed is not None:
        set_global_seed(seed)
    else:
        ensure_seed_set()
    
    randomizations = []
    for _ in range(n_participants):
        participant_id = generate_participant_id()
        condition = assign_condition(random.randint(0, 2**32 - 1))
        timestamp = datetime.utcnow().isoformat()
        
        randomizations.append({
            'participant_id': participant_id,
            'condition': condition,
            'timestamp': timestamp
        })
    
    return randomizations

def validate_balance(randomizations: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, int]]:
    """
    Validate that the randomization is balanced (approximately 50/50).
    
    Args:
        randomizations: List of randomization records
        
    Returns:
        Tuple of (is_balanced, counts) where counts is {'Partner': n, 'Tool': n}
    """
    counts = {'Partner': 0, 'Tool': 0}
    for record in randomizations:
        counts[record['condition']] += 1
    
    total = len(randomizations)
    if total == 0:
        return True, counts
    
    partner_ratio = counts['Partner'] / total
    is_balanced = 0.4 <= partner_ratio <= 0.6  # Allow 10% tolerance
    
    return is_balanced, counts

def save_randomization_log(randomizations: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save randomization metadata to a JSON file.
    
    This function writes the log BEFORE survey display to prevent drift,
    as required by Constitution III and US-1.
    
    Args:
        randomizations: List of randomization records
        output_path: Path to the output JSON file
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log_data = {
        'metadata': {
            'generated_at': datetime.utcnow().isoformat(),
            'total_participants': len(randomizations),
            'source': 'code/02_randomization.py'
        },
        'records': randomizations
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)
    
    log_data_operation(f"Randomization log written to {output_path}", len(randomizations))

def main():
    """Main entry point for the randomization script."""
    logger = setup_logger('randomization')
    log_script_start(logger, '02_randomization')
    
    parser = argparse.ArgumentParser(description='Randomize participants to conditions')
    parser.add_argument('--n', type=int, default=100, help='Number of participants to randomize')
    parser.add_argument('--seed', type=int, default=None, help='Random seed for reproducibility')
    parser.add_argument('--output', type=str, default='data/processed/randomization_log.json',
                      help='Output path for the randomization log')
    args = parser.parse_args()
    
    try:
        randomizations = run_randomization(args.n, args.seed)
        is_balanced, counts = validate_balance(randomizations)
        
        if not is_balanced:
            logger.warning(f"Randomization imbalance detected: {counts}")
        else:
            logger.info(f"Randomization balanced: {counts}")
        
        save_randomization_log(randomizations, args.output)
        
        log_script_end(logger, '02_randomization', success=True)
        return 0
        
    except Exception as e:
        logger.error(f"Randomization failed: {e}")
        log_script_end(logger, '02_randomization', success=False)
        return 1

if __name__ == '__main__':
    sys.exit(main())
