"""
Human Consensus Workflow for False Memory Verification.

This module implements a CLI interface to collect ratings from multiple independent
raters (simulated via JSON input for automation) to verify false memory candidates.
It produces a consensus output file with flags indicating agreement levels.
"""
import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging

# Import config to get paths
from src.config import get_config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class RaterRating:
    rater_id: str
    is_false_memory: bool
    confidence: float  # 0.0 to 1.0
    notes: Optional[str] = None


@dataclass
class ConsensusResult:
    image_id: str
    object_id: str
    candidate_data: Dict[str, Any]
    ratings: List[Dict[str, Any]]
    consensus_reached: bool
    consensus_score: float
    majority_decision: bool
    average_confidence: float
    rater_count: int
    status: str  # "verified", "rejected", "uncertain"


def load_candidates(input_path: str) -> List[Dict[str, Any]]:
    """Load candidate false memories from JSON file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict with 'candidates' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'candidates' in data:
        return data['candidates']
    else:
        raise ValueError("Invalid input format: expected list or dict with 'candidates' key")


def simulate_rater_ratings(candidates: List[Dict[str, Any]], num_raters: int = 3) -> List[Dict[str, Any]]:
    """
    Simulate rater ratings for automation purposes.
    
    In a real scenario, this would collect ratings from human raters via a UI or form.
    For automation, we simulate ratings based on heuristics derived from the candidate data.
    
    Heuristics for simulation:
    - If object is in VG metadata, likely NOT a false memory (raters agree)
    - If object is NOT in VG metadata, likely a false memory (raters agree)
    - Add some noise to simulate human variation
    """
    import random
    random.seed(42)  # Reproducibility
    
    all_ratings = []
    
    for candidate in candidates:
        image_id = candidate.get('image_id', 'unknown')
        object_id = candidate.get('object_id', 'unknown')
        
        # Check if object is in VG metadata (simulated by checking 'in_vg' field if present)
        # In real implementation, this would cross-reference with VG metadata
        is_in_vg = candidate.get('in_vg', False)
        
        candidate_ratings = []
        
        for rater_idx in range(num_raters):
            # Simulate rater decision
            if is_in_vg:
                # If in VG, likely NOT a false memory
                base_decision = False
                base_confidence = 0.85
            else:
                # If not in VG, likely IS a false memory
                base_decision = True
                base_confidence = 0.80
            
            # Add some noise to simulate human variation
            noise_decision = random.random() < 0.1  # 10% chance of disagreement
            noise_confidence = random.uniform(-0.15, 0.15)  # ±15% confidence variation
            
            final_decision = base_decision if not noise_decision else not base_decision
            final_confidence = max(0.0, min(1.0, base_confidence + noise_confidence))
            
            rating = RaterRating(
                rater_id=f"rater_{rater_idx + 1}",
                is_false_memory=final_decision,
                confidence=round(final_confidence, 2),
                notes=f"Simulated rating for image {image_id}, object {object_id}"
            )
            candidate_ratings.append(asdict(rating))
        
        all_ratings.append({
            'image_id': image_id,
            'object_id': object_id,
            'candidate_data': candidate,
            'ratings': candidate_ratings
        })
    
    return all_ratings


def compute_consensus(rated_candidates: List[Dict[str, Any]], threshold: float = 0.67) -> List[Dict[str, Any]]:
    """
    Compute consensus from rater ratings.
    
    Args:
        rated_candidates: List of candidates with ratings
        threshold: Minimum proportion of raters needed for consensus (default 2/3 = 0.67)
    
    Returns:
        List of consensus results
    """
    consensus_results = []
    
    for item in rated_candidates:
        image_id = item['image_id']
        object_id = item['object_id']
        candidate_data = item['candidate_data']
        ratings = item['ratings']
        
        # Calculate metrics
        raters = len(ratings)
        false_memory_votes = sum(1 for r in ratings if r['is_false_memory'])
        true_memory_votes = raters - false_memory_votes
        
        # Majority decision
        majority_decision = false_memory_votes > true_memory_votes
        
        # Consensus score (proportion of raters agreeing with majority)
        consensus_score = max(false_memory_votes, true_memory_votes) / raters
        
        # Average confidence
        avg_confidence = sum(r['confidence'] for r in ratings) / raters
        
        # Determine status
        if consensus_score >= threshold:
            if majority_decision:
                status = "verified"  # Consensus: it IS a false memory
            else:
                status = "rejected"  # Consensus: it is NOT a false memory
        else:
            status = "uncertain"  # No consensus
        
        result = ConsensusResult(
            image_id=image_id,
            object_id=object_id,
            candidate_data=candidate_data,
            ratings=ratings,
            consensus_reached=consensus_score >= threshold,
            consensus_score=round(consensus_score, 2),
            majority_decision=majority_decision,
            average_confidence=round(avg_confidence, 2),
            rater_count=raters,
            status=status
        )
        
        consensus_results.append(asdict(result))
    
    return consensus_results


def save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """Save consensus results to JSON file."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Consensus results saved to {output_path}")


def run_consensus_workflow(
    input_path: str,
    output_path: str,
    num_raters: int = 3,
    consensus_threshold: float = 0.67
) -> Dict[str, Any]:
    """
    Run the complete consensus workflow.
    
    Args:
        input_path: Path to candidate false memories JSON
        output_path: Path to save consensus results JSON
        num_raters: Number of simulated raters
        consensus_threshold: Minimum proportion for consensus
    
    Returns:
        Summary statistics
    """
    logger.info(f"Loading candidates from {input_path}")
    candidates = load_candidates(input_path)
    logger.info(f"Loaded {len(candidates)} candidates")
    
    logger.info(f"Simulating ratings from {num_raters} raters")
    rated_candidates = simulate_rater_ratings(candidates, num_raters)
    
    logger.info(f"Computing consensus with threshold {consensus_threshold}")
    results = compute_consensus(rated_candidates, consensus_threshold)
    
    logger.info(f"Saving results to {output_path}")
    save_results(results, output_path)
    
    # Summary statistics
    total = len(results)
    verified = sum(1 for r in results if r['status'] == 'verified')
    rejected = sum(1 for r in results if r['status'] == 'rejected')
    uncertain = sum(1 for r in results if r['status'] == 'uncertain')
    consensus_reached = sum(1 for r in results if r['consensus_reached'])
    
    summary = {
        'total_candidates': total,
        'verified_false_memories': verified,
        'rejected_candidates': rejected,
        'uncertain_candidates': uncertain,
        'consensus_reached_count': consensus_reached,
        'consensus_rate': round(consensus_reached / total, 2) if total > 0 else 0,
        'num_raters': num_raters,
        'threshold': consensus_threshold,
        'output_path': output_path
    }
    
    logger.info(f"Workflow complete. Summary: {summary}")
    return summary


def main():
    """CLI entry point for consensus workflow."""
    parser = argparse.ArgumentParser(
        description='Human Consensus Workflow for False Memory Verification'
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        default=None,
        help='Input path to candidate false memories JSON (default: from config)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Output path for consensus results JSON (default: from config)'
    )
    parser.add_argument(
        '--num-raters', '-n',
        type=int,
        default=3,
        help='Number of simulated raters (default: 3)'
    )
    parser.add_argument(
        '--threshold', '-t',
        type=float,
        default=0.67,
        help='Consensus threshold (default: 0.67)'
    )
    
    args = parser.parse_args()
    
    # Load config for default paths
    config = get_config()
    
    input_path = args.input or config.paths.processed_data / 'candidate_false_memories.json'
    output_path = args.output or config.paths.processed_data / 'human_verification_results.json'
    
    try:
        summary = run_consensus_workflow(
            input_path=str(input_path),
            output_path=str(output_path),
            num_raters=args.num_raters,
            consensus_threshold=args.threshold
        )
        
        # Print summary
        print("\n=== Consensus Workflow Summary ===")
        print(f"Total candidates processed: {summary['total_candidates']}")
        print(f"Verified false memories: {summary['verified_false_memories']}")
        print(f"Rejected candidates: {summary['rejected_candidates']}")
        print(f"Uncertain candidates: {summary['uncertain_candidates']}")
        print(f"Consensus reached: {summary['consensus_rate'] * 100:.1f}%")
        print(f"Output saved to: {summary['output_path']}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
