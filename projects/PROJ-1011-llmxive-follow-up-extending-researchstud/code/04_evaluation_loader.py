import json
import csv
import hashlib
import logging
import sys
import os
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import existing utilities from the project API surface
from utils.logging_config import get_logger

# Ensure we can find utils if running as a script
if 'code' not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logger = get_logger(__name__)

RESULTS_DIR = Path("data/results")
GENERATED_PROPOSALS_PATH = RESULTS_DIR / "generated_proposals.jsonl"
BLINDED_BATCHES_PATH = RESULTS_DIR / "blinded_batches.csv"
RATINGS_FILLED_PATH = RESULTS_DIR / "ratings_filled.csv"

def ensure_results_dir():
    """Ensure the results directory exists."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_generated_proposals() -> List[Dict[str, Any]]:
    """Load generated proposals from the JSONL file."""
    if not GENERATED_PROPOSALS_PATH.exists():
        raise FileNotFoundError(f"Generated proposals file not found: {GENERATED_PROPOSALS_PATH}")
    
    proposals = []
    with open(GENERATED_PROPOSALS_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                proposals.append(json.loads(line))
    return proposals

def strip_metadata_for_blinding(proposal: Dict[str, Any]) -> Dict[str, Any]:
    """Strip generation metadata to create a blinded proposal."""
    blinded = {
        "proposal_id": proposal.get("proposal_id", ""),
        "problem_statement": proposal.get("problem_statement", ""),
        "domain": proposal.get("domain", ""),
        "group": proposal.get("group", ""),
        "proposal_text": proposal.get("proposal_text", ""),
    }
    # Explicitly remove any sensitive fields
    for key in ['pattern_confidence_scores', 'pattern_ids', 'generation_timestamp', 'model_version']:
        blinded.pop(key, None)
    return blinded

def create_blinded_pairs(proposals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create blinded pairs for evaluation."""
    blinded_pairs = []
    
    # Group by problem_id to pair pattern-guided and baseline
    problem_groups = {}
    for p in proposals:
        pid = p.get("problem_id")
        if pid not in problem_groups:
            problem_groups[pid] = []
        problem_groups[pid].append(p)
    
    for pid, group in problem_groups.items():
        if len(group) != 2:
            logger.warning(f"Problem ID {pid} does not have exactly 2 proposals. Skipping.")
            continue
        
        # Sort to ensure deterministic pairing (pattern-guided first, then baseline)
        group.sort(key=lambda x: x.get("group", ""))
        
        blinded = []
        for i, p in enumerate(group):
            b = strip_metadata_for_blinding(p)
            # Create a unique blinded ID for this specific entry
            raw_id = f"{pid}_{i}_{b['group']}"
            b["blinded_id"] = hashlib.sha256(raw_id.encode()).hexdigest()[:16]
            b["instructions"] = "Rate the quality and contextual alignment of this proposal."
            blinded.append(b)
        
        blinded_pairs.extend(blinded)
    
    return blinded_pairs

def save_blinded_pairs(blinded_pairs: List[Dict[str, Any]]):
    """Save blinded pairs to CSV."""
    ensure_results_dir()
    
    fieldnames = ["proposal_id", "problem_statement", "domain", "group", "blinded_id", "instructions"]
    
    with open(BLINDED_BATCHES_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(blinded_pairs)
    
    logger.info(f"Saved {len(blinded_pairs)} blinded pairs to {BLINDED_BATCHES_PATH}")

def generate_ratings_template() -> Dict[str, Any]:
    """Generate a template for rating data."""
    return {
        "blinded_id": str,
        "expert_id": str,
        "contextual_alignment": int,  # 1-5 scale
        "novelty": int,  # 1-5 scale
        "feasibility": int,  # 1-5 scale
        "comments": str
    }

def validate_ratings_schema(row: Dict[str, Any]) -> bool:
    """Validate that a rating row matches the expected schema."""
    required_fields = ["blinded_id", "expert_id", "contextual_alignment", "novelty", "feasibility"]
    return all(field in row for field in required_fields)

def verify_orcid(orcid: str) -> bool:
    """Verify an ORCID ID (placeholder for real API check)."""
    # In a real implementation, this would query api.orcid.org
    # For now, we do basic format validation
    if not orcid or not isinstance(orcid, str):
        return False
    parts = orcid.split('-')
    if len(parts) != 4:
        return False
    return True

def load_expert_roster() -> List[Dict[str, Any]]:
    """Load the expert roster from a configuration file."""
    # Placeholder: In a real system, this would load from a config or DB
    return []

def validate_expert_inputs(experts: List[Dict[str, Any]]) -> bool:
    """Validate expert inputs before rating ingestion."""
    for expert in experts:
        if not verify_orcid(expert.get("orcid", "")):
            return False
    return True

def ingest_ratings(ratings_path: Path) -> List[Dict[str, Any]]:
    """Ingest ratings from a CSV file."""
    if not ratings_path.exists():
        raise FileNotFoundError(f"Ratings file not found: {ratings_path}")
    
    ratings = []
    with open(ratings_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if validate_ratings_schema(row):
                ratings.append(row)
    
    return ratings

def recruit_experts_via_prolific():
    """Recruit experts via Prolific API (placeholder)."""
    logger.info("Prolific recruitment not implemented in this task.")

def generate_mock_ratings_for_testing(seed: int = 42, num_ratings: int = 100):
    """
    Generate deterministic, seeded mock ratings for testing the ingestion pipeline.
    
    CONSTRAINT: This is FOR TESTING ONLY. Do NOT generate mock ratings for the final analysis.
    Do NOT use this path in CI or production.
    
    Output: Writes data/results/ratings_filled.csv with schema matching T030-test.
    """
    ensure_results_dir()
    random.seed(seed)
    
    # Load existing blinded pairs to generate realistic ratings
    if not BLINDED_BATCHES_PATH.exists():
        logger.warning("Blinded batches not found. Generating generic mock ratings.")
        blinded_ids = [f"mock_blinded_{i:04d}" for i in range(num_ratings)]
    else:
        with open(BLINDED_BATCHES_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            blinded_ids = [row['blinded_id'] for row in reader]
    
    if not blinded_ids:
        blinded_ids = [f"mock_blinded_{i:04d}" for i in range(num_ratings)]
    
    ratings = []
    expert_ids = ["expert_001", "expert_002", "expert_003", "expert_004", "expert_005"]
    
    for i, bid in enumerate(blinded_ids[:num_ratings]):
        expert_id = random.choice(expert_ids)
        ratings.append({
            "blinded_id": bid,
            "expert_id": expert_id,
            "contextual_alignment": random.randint(1, 5),
            "novelty": random.randint(1, 5),
            "feasibility": random.randint(1, 5),
            "comments": f"Mock rating for testing purposes only (ID: {bid})."
        })
    
    fieldnames = ["blinded_id", "expert_id", "contextual_alignment", "novelty", "feasibility", "comments"]
    
    with open(RATINGS_FILLED_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ratings)
    
    logger.info(f"Generated {len(ratings)} mock ratings to {RATINGS_FILLED_PATH}")
    logger.warning("WARNING: This file contains MOCK data for testing ONLY. Do not use in production.")

def main():
    """Main entry point for the evaluation loader."""
    import argparse
    parser = argparse.ArgumentParser(description="Evaluation Loader Utility")
    parser.add_argument("--generate-mock", action="store_true", help="Generate mock ratings for testing")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for mock generation")
    parser.add_argument("--num-ratings", type=int, default=100, help="Number of mock ratings to generate")
    args = parser.parse_args()
    
    if args.generate_mock:
        logger.info("Generating mock ratings for testing...")
        generate_mock_ratings_for_testing(seed=args.seed, num_ratings=args.num_ratings)
    else:
        # Default behavior: run the blinding pipeline
        logger.info("Loading generated proposals...")
        proposals = load_generated_proposals()
        logger.info("Creating blinded pairs...")
        blinded_pairs = create_blinded_pairs(proposals)
        logger.info("Saving blinded pairs...")
        save_blinded_pairs(blinded_pairs)
        logger.info("Evaluation loader completed successfully.")

if __name__ == "__main__":
    main()
