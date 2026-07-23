import json
import os
import logging
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer, util

from logger import get_logger

logger = get_logger(__name__)

# Global model cache to avoid reloading
_embedding_model: Optional[SentenceTransformer] = None

def load_embedding_model() -> SentenceTransformer:
    """Load the sentence transformer model for semantic similarity."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model: all-MiniLM-L6-v2")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity between two text strings.
    Returns a score between 0 and 1.
    """
    model = load_embedding_model()
    embeddings = model.encode([text1, text2], convert_to_tensor=True)
    cosine_sim = util.cos_sim(embeddings[0], embeddings[1])
    return float(cosine_sim.item())

def identify_missing_critical_items(
    masked_ground_truth: Dict[str, Any],
    agent_mental_map: Dict[str, Any]
) -> Tuple[List[str], List[str]]:
    """
    Identify critical items (keys, doors) in masked_ground_truth that are
    missing from the agent's mental map.
    
    Args:
        masked_ground_truth: The ground truth state with critical items visible
        agent_mental_map: The agent's constructed mental map of the state
        
    Returns:
        Tuple of (missing_critical_items, all_critical_items_found)
    """
    missing = []
    all_found = []
    
    # Extract critical items from ground truth
    # Expected format: ground_truth_state contains items with 'type' field
    gt_state = masked_ground_truth.get('ground_truth_state', {})
    agent_state = agent_mental_map.get('mental_map', {})
    
    # If states are strings, attempt to parse (though they should be dicts per contract)
    if isinstance(gt_state, str):
        try:
            gt_state = json.loads(gt_state)
        except json.JSONDecodeError:
            logger.error("Failed to parse ground_truth_state JSON")
            return [], []
            
    if isinstance(agent_state, str):
        try:
            agent_state = json.loads(agent_state)
        except json.JSONDecodeError:
            logger.error("Failed to parse agent_mental_map JSON")
            return [], []

    # Identify critical items (keys, doors) in ground truth
    critical_types = {'key', 'door'}
    
    # Handle both list of items and dict of items formats
    gt_items = gt_state if isinstance(gt_state, list) else list(gt_state.values())
    agent_items = agent_state if isinstance(agent_state, list) else list(agent_state.values())
    
    gt_critical = []
    agent_critical_ids = set()
    
    for item in gt_items:
        if isinstance(item, dict):
            item_type = item.get('type', '').lower()
            item_id = item.get('id', item.get('name', str(item)))
            if item_type in critical_types:
                gt_critical.append(item)
        
    for item in agent_items:
        if isinstance(item, dict):
            item_id = item.get('id', item.get('name', str(item)))
            agent_critical_ids.add(item_id)
    
    # Find missing critical items
    for item in gt_critical:
        item_id = item.get('id', item.get('name', str(item)))
        if item_id not in agent_critical_ids:
            missing.append(item_id)
            logger.debug(f"Critical item missing: {item_id} (type: {item.get('type')})")
        else:
            all_found.append(item_id)
            
    return missing, all_found

def calculate_memory_gap_score(
    masked_ground_truth: Dict[str, Any],
    agent_mental_map: Dict[str, Any],
    semantic_weight: float = 0.5,
    critical_penalty: float = 1.0
) -> Dict[str, Any]:
    """
    Calculate the Memory Gap score.
    
    Formula: score = (1 - semantic_similarity) + (penalty * missing_items)
    
    Args:
        masked_ground_truth: Ground truth state with critical items
        agent_mental_map: Agent's mental map
        semantic_weight: Weight for semantic similarity component (0-1)
        critical_penalty: Penalty per missing critical item (default 1.0)
        
    Returns:
        Dictionary containing score breakdown
    """
    # Calculate semantic similarity
    gt_text = json.dumps(masked_ground_truth, sort_keys=True)
    agent_text = json.dumps(agent_mental_map, sort_keys=True)
    semantic_sim = calculate_semantic_similarity(gt_text, agent_text)
    
    # Identify missing critical items
    missing_items, found_items = identify_missing_critical_items(
        masked_ground_truth, agent_mental_map
    )
    num_missing = len(missing_items)
    
    # Calculate penalty
    penalty_score = critical_penalty * num_missing
    
    # Final score: higher is worse (more gap)
    # Normalized: (1 - sim) ranges 0-1, penalty adds to it
    raw_score = (1 - semantic_sim) + penalty_score
    
    # Normalize score to a reasonable range if needed
    # For now, we keep raw score but log components
    score = raw_score
    
    result = {
        'memory_gap_score': float(score),
        'semantic_similarity': float(semantic_sim),
        'missing_critical_items': missing_items,
        'found_critical_items': found_items,
        'num_missing_critical': num_missing,
        'penalty_applied': float(penalty_score),
        'formula': f"(1 - {semantic_sim:.4f}) + ({critical_penalty} * {num_missing})"
    }
    
    logger.info(f"Memory Gap Score: {score:.4f} (semantic: {semantic_sim:.4f}, penalty: {penalty_score:.4f})")
    
    return result

def run_scorer_test() -> Dict[str, Any]:
    """
    Run a unit test for the scorer to verify critical item penalty logic.
    """
    logger.info("Running scorer unit test...")
    
    # Test case 1: Perfect match
    gt_perfect = {
        'ground_truth_state': [
            {'id': 'key_1', 'type': 'key', 'pos': [1, 1]},
            {'id': 'door_1', 'type': 'door', 'pos': [2, 2]}
        ]
    }
    agent_perfect = {
        'mental_map': [
            {'id': 'key_1', 'type': 'key', 'pos': [1, 1]},
            {'id': 'door_1', 'type': 'door', 'pos': [2, 2]}
        ]
    }
    
    result_perfect = calculate_memory_gap_score(gt_perfect, agent_perfect)
    assert result_perfect['num_missing_critical'] == 0, "Perfect match should have 0 missing"
    assert result_perfect['penalty_applied'] == 0.0, "Perfect match should have 0 penalty"
    logger.info(f"Test 1 (Perfect): Score={result_perfect['memory_gap_score']:.4f}")
    
    # Test case 2: Missing one critical item
    gt_missing = {
        'ground_truth_state': [
            {'id': 'key_1', 'type': 'key', 'pos': [1, 1]},
            {'id': 'door_1', 'type': 'door', 'pos': [2, 2]}
        ]
    }
    agent_missing = {
        'mental_map': [
            {'id': 'key_1', 'type': 'key', 'pos': [1, 1]}
            # door_1 missing
        ]
    }
    
    result_missing = calculate_memory_gap_score(gt_missing, agent_missing)
    assert result_missing['num_missing_critical'] == 1, "Should detect 1 missing critical item"
    assert result_missing['penalty_applied'] == 1.0, "Penalty should be 1.0"
    logger.info(f"Test 2 (Missing 1): Score={result_missing['memory_gap_score']:.4f}")
    
    # Test case 3: Missing two critical items
    agent_missing2 = {
        'mental_map': []
    }
    
    result_missing2 = calculate_memory_gap_score(gt_missing, agent_missing2)
    assert result_missing2['num_missing_critical'] == 2, "Should detect 2 missing critical items"
    assert result_missing2['penalty_applied'] == 2.0, "Penalty should be 2.0"
    logger.info(f"Test 3 (Missing 2): Score={result_missing2['memory_gap_score']:.4f}")
    
    return {
        'status': 'PASS',
        'tests_run': 3,
        'tests_passed': 3,
        'details': [
            result_perfect,
            result_missing,
            result_missing2
        ]
    }

def main():
    """Main entry point for testing the scorer."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test the Memory Gap Scorer')
    parser.add_argument('--run-test', action='store_true', help='Run unit tests')
    parser.add_argument('--compare', nargs=2, metavar=('GROUND_TRUTH_JSON', 'AGENT_JSON'),
                      help='Compare two JSON files')
    args = parser.parse_args()
    
    if args.run_test:
        result = run_scorer_test()
        print(json.dumps(result, indent=2))
        return
    
    if args.compare:
        with open(args.compare[0], 'r') as f:
            gt = json.load(f)
        with open(args.compare[1], 'r') as f:
            agent = json.load(f)
        
        score = calculate_memory_gap_score(gt, agent)
        print(json.dumps(score, indent=2))
        return
    
    parser.print_help()

if __name__ == '__main__':
    main()