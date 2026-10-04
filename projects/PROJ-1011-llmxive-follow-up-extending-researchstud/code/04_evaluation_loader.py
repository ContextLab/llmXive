import json
import csv
import hashlib
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
import requests

from utils.logging_config import get_logger
from utils.error_handling import DataFetchError, ValidationError

logger = get_logger("evaluation_loader")

RESULTS_DIR = Path("data/results")
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

def ensure_results_dir():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_generated_proposals(filepath: Optional[str] = None) -> List[Dict[str, Any]]:
    if filepath is None:
        filepath = str(RESULTS_DIR / "generated_proposals.jsonl")
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Generated proposals file not found: {filepath}")
    proposals = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                proposals.append(json.loads(line))
    return proposals

def strip_metadata_for_blinding(proposal: Dict[str, Any]) -> Dict[str, Any]:
    """Remove generation metadata to create a blinded proposal."""
    blinded = {
        "id": proposal.get("id"),
        "problem_statement": proposal.get("problem_statement"),
        "proposal_text": proposal.get("proposal_text"),
        "group": proposal.get("group"),
    }
    return blinded

def create_blinded_pairs(proposals: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Create blinded pairs from proposals, ensuring one from each group per pair."""
    pattern_guided = [p for p in proposals if p.get("group") == "pattern-guided"]
    baseline = [p for p in proposals if p.get("group") == "baseline"]

    if len(pattern_guided) != len(baseline):
        raise ValidationError("Mismatch in number of pattern-guided and baseline proposals.")

    pairs = []
    for pg, b in zip(pattern_guided, baseline):
        pairs.append((strip_metadata_for_blinding(pg), strip_metadata_for_blinding(b)))
    return pairs

def save_blinded_pairs(pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]], filepath: Optional[str] = None):
    if filepath is None:
        filepath = str(RESULTS_DIR / "blinded_batches.csv")
    ensure_results_dir()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["pair_id", "proposal_a_id", "proposal_a_text", "proposal_b_id", "proposal_b_text"])
        for i, (pa, pb) in enumerate(pairs):
            writer.writerow([i, pa["id"], pa["proposal_text"], pb["id"], pb["proposal_text"]])
    logger.info(f"Blinded pairs saved to {filepath}")

def generate_ratings_template(filepath: Optional[str] = None):
    if filepath is None:
        filepath = str(RESULTS_DIR / "ratings_template.csv")
    ensure_results_dir()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["pair_id", "expert_orcid", "proposal_a_score", "proposal_b_score", "comments"])
    logger.info(f"Ratings template saved to {filepath}")

def validate_ratings_schema(filepath: str) -> bool:
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Ratings file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required_fields = {"pair_id", "expert_orcid", "proposal_a_score", "proposal_b_score", "comments"}
        if not required_fields.issubset(set(reader.fieldnames or [])):
            raise ValidationError("Ratings file missing required fields.")
    return True

def verify_orcid(orcid: str, timeout: int = 5) -> bool:
    """Verify ORCID exists via public API."""
    url = f"https://api.orcid.org/v3.0/{orcid}/"
    headers = {"Accept": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            return False
        else:
            logger.warning(f"ORCID API returned unexpected status: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        logger.warning(f"ORCID verification timed out for {orcid}")
        return False
    except Exception as e:
        logger.warning(f"ORCID verification failed for {orcid}: {e}")
        return False

def load_expert_roster(filepath: str) -> List[Dict[str, Any]]:
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Expert roster not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_expert_inputs(roster: List[Dict[str, Any]]) -> List[str]:
    """Validate expert inputs, returning list of invalid ORCIDs."""
    invalid = []
    for expert in roster:
        orcid = expert.get("orcid")
        if not orcid:
            invalid.append("Missing ORCID")
            continue
        if not verify_orcid(orcid):
            invalid.append(f"Invalid ORCID: {orcid}")
    return invalid

def ingest_ratings(filepath: str) -> List[Dict[str, Any]]:
    """Load and validate ratings from CSV."""
    validate_ratings_schema(filepath)
    ratings = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ratings.append(row)
    return ratings

def recruit_experts_via_prolific(api_key: str, task_description: str):
    """Simulate recruitment via Prolific API (placeholder for real integration)."""
    logger.info(f"Recruiting experts for task: {task_description}")
    # Real implementation would call Prolific API here
    pass

def generate_mock_ratings_for_testing(num_pairs: int = 10, num_experts: int = 3, filepath: Optional[str] = None):
    """Generate deterministic mock ratings for testing T030 ingestion logic."""
    if filepath is None:
        filepath = str(RESULTS_DIR / "ratings_filled.csv")
    ensure_results_dir()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["pair_id", "expert_orcid", "proposal_a_score", "proposal_b_score", "comments"])
        for pair_id in range(num_pairs):
            for expert_idx in range(num_experts):
                orcid = f"0000-0000-0000-{expert_idx:04d}"
                score_a = 5  # Deterministic mock score
                score_b = 5
                comment = "Mock rating for testing."
                writer.writerow([pair_id, orcid, score_a, score_b, comment])
    logger.info(f"Mock ratings generated at {filepath}")

def main():
    """Main entry point for evaluation loader workflow."""
    ensure_results_dir()
    proposals = load_generated_proposals()
    pairs = create_blinded_pairs(proposals)
    save_blinded_pairs(pairs)
    generate_ratings_template()
    generate_mock_ratings_for_testing()
    logger.info("Evaluation workflow completed successfully.")

if __name__ == "__main__":
    main()
