"""
Evaluation Loader Module for llmXive Research Pipeline.

This module handles the loading, validation, and blinding of expert ratings
from the CSV file generated after the evaluation phase (T059).
"""
import json
import csv
import hashlib
import logging
import sys
import os
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Importing from existing API surface
from utils.error_handling import VerificationError, IRRGateFailError
from utils.logging_config import get_logger
from utils.data_manifest import register_new_file

# Configuration paths
RESULTS_DIR = Path("data/results")
RATINGS_FILE = RESULTS_DIR / "ratings_filled.csv"
PROPOSALS_FILE = RESULTS_DIR / "generated_proposals.jsonl"
BLINDING_FILE = RESULTS_DIR / "blinded_pairs.jsonl"
ORCID_API_BASE = "https://pub.orcid.org/v3.0"

logger = get_logger(__name__)

# --- Error Definitions (as per API surface) ---
# These are re-defined here for clarity if not imported, but we rely on utils.error_handling
# VerificationError and IRRGateFailError are imported above.

def ensure_results_dir():
    """Ensure the results directory exists."""
    if not RESULTS_DIR.exists():
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created results directory: {RESULTS_DIR}")

def load_generated_proposals() -> List[Dict[str, Any]]:
    """
    Load the generated proposals from the JSONL file.
    """
    if not PROPOSALS_FILE.exists():
        raise FileNotFoundError(f"Generated proposals file not found: {PROPOSALS_FILE}")

    proposals = []
    with open(PROPOSALS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                proposals.append(json.loads(line))
    logger.info(f"Loaded {len(proposals)} proposals from {PROPOSALS_FILE}")
    return proposals

def strip_metadata_for_blinding(proposal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Strip all generation metadata from a proposal to ensure blinding.
    Keeps only: problem_statement, proposal_text, group_id (A/B).
    """
    blinded = {
        "problem_statement": proposal.get("problem_statement"),
        "proposal_text": proposal.get("proposal_text"),
        "group_id": proposal.get("group_id"), # A or B
        "proposal_id": proposal.get("proposal_id")
    }
    # Remove any internal IDs, timestamps, model names, etc.
    return blinded

def create_blinded_pairs(proposals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create blinded pairs from the loaded proposals.
    Assumes proposals are already paired or can be paired by problem_statement hash.
    """
    # Group by problem_statement
    grouped = {}
    for p in proposals:
        ps = p.get("problem_statement")
        if not ps:
            continue
        # Use SHA256 of problem statement as key for pairing
        key = hashlib.sha256(ps.encode('utf-8')).hexdigest()[:16]
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(strip_metadata_for_blinding(p))

    pairs = []
    for key, group in grouped.items():
        if len(group) >= 2:
            # Take first two as the pair
            pairs.append({
                "pair_id": key,
                "proposal_a": group[0],
                "proposal_b": group[1]
            })
    logger.info(f"Created {len(pairs)} blinded pairs.")
    return pairs

def save_blinded_pairs(pairs: List[Dict[str, Any]], output_path: Path = BLINDING_FILE):
    """Save blinded pairs to JSONL."""
    ensure_results_dir()
    with open(output_path, 'w', encoding='utf-8') as f:
        for pair in pairs:
            f.write(json.dumps(pair) + '\n')
    logger.info(f"Saved {len(pairs)} blinded pairs to {output_path}")
    register_new_file(str(output_path), "blinded_pairs")

def generate_ratings_template(pairs: List[Dict[str, Any]], output_path: Path = RATINGS_FILE):
    """
    Generate a CSV template for expert ratings.
    Columns: pair_id, expert_orcid, proposal_a_score, proposal_b_score, contextual_alignment_a, contextual_alignment_b, notes
    """
    ensure_results_dir()
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "pair_id", "expert_orcid",
            "proposal_a_score", "proposal_b_score",
            "contextual_alignment_a", "contextual_alignment_b",
            "notes"
        ])
        # Write empty rows for experts to fill
        for pair in pairs:
            writer.writerow([
                pair["pair_id"], "", "", "", "", "", ""
            ])
    logger.info(f"Generated ratings template at {output_path} for {len(pairs)} pairs.")
    register_new_file(str(output_path), "ratings_template")

def validate_ratings_schema(row: Dict[str, Any]) -> bool:
    """
    Validate that a row in the ratings CSV matches the expected schema.
    """
    required_fields = ["pair_id", "expert_orcid", "proposal_a_score", "proposal_b_score",
                       "contextual_alignment_a", "contextual_alignment_b"]
    for field in required_fields:
        if field not in row or row[field] is None or row[field] == "":
            return False
    # Check numeric fields
    try:
        float(row["proposal_a_score"])
        float(row["proposal_b_score"])
        float(row["contextual_alignment_a"])
        float(row["contextual_alignment_b"])
    except ValueError:
        return False
    return True

def verify_orcid(orcid: str) -> bool:
    """
    Verify ORCID existence and domain affiliation via public API.
    Returns True if valid and domain matches 'public health' or 'climate adaptation'.
    Raises VerificationError if invalid.
    """
    if not orcid or not orcid.startswith("0000-"):
        raise VerificationError(f"Invalid ORCID format: {orcid}")

    try:
        # Query ORCID API
        url = f"{ORCID_API_BASE}/{orcid}/person"
        # Note: We use a specific header for read-public
        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer PUBLIC_ACCESS_TOKEN" # In real scenario, this would be handled by OAuth flow
            # For this script, we assume a mock or public endpoint check if token is missing.
            # However, the spec requires a real API call.
            # We will attempt a fetch. If the API requires OAuth, we simulate the check logic.
        }
        
        # Since we cannot generate a valid OAuth token in this script without user interaction,
        # we will perform a structural check on the public endpoint if accessible,
        # or raise an error if the API requires auth that we don't have.
        # The spec says: "Query the public ORCID API...".
        
        # Attempting a fetch to the public profile endpoint
        # If the ORCID is valid, the profile exists.
        # We check for 'researcher-activities' or 'keywords' in the response.
        
        # NOTE: In a real execution, the OAuth token must be provided.
        # If we cannot get a token, we fail loudly as per "Fail loudly, never silently".
        # However, for the purpose of this task, we assume the environment has a way to auth
        # or we are checking the existence of the ID format and a mock response.
        
        # Let's assume we have a way to get the data (e.g., via a pre-verified list or token).
        # If the API strictly requires OAuth, this script would fail without it.
        # We will implement the logic to check the response structure.
        
        # Simulating the API call logic for the task implementation:
        # In a real run, we would use `requests.get` with a valid token.
        # If the token is missing, we raise a specific error.
        
        # For the sake of the task, we will assume the token is available in an env var
        # ORCID_API_TOKEN. If not present, we raise an error.
        token = os.environ.get("ORCID_API_TOKEN")
        if not token:
            # If we cannot auth, we cannot verify domain.
            # But we can at least check the ORCID format.
            # The spec says: "Query the public ORCID API...".
            # If we can't query, we fail.
            raise VerificationError(f"ORCID API token not found. Cannot verify {orcid}.")
        
        headers["Authorization"] = f"Bearer {token}"
        headers["Content-Type"] = "application/json"
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            raise VerificationError(f"ORCID {orcid} not found.")
        
        if response.status_code != 200:
            raise VerificationError(f"ORCID API error for {orcid}: {response.status_code}")
        
        data = response.json()
        
        # Check for researcher activities or keywords
        activities = data.get("activities", {})
        keywords = data.get("keywords", [])
        
        # Check if domain matches
        domain_keywords = ["public health", "climate adaptation", "climate change", "health"]
        found_domain = False
        
        # Check keywords
        for kw in keywords:
            if isinstance(kw, str) and any(k in kw.lower() for k in domain_keywords):
                found_domain = True
                break
        
        # Check activities (summary)
        if not found_domain and "activities" in activities:
            # Check summary or other fields
            summary = activities.get("summary", "")
            if any(k in summary.lower() for k in domain_keywords):
                found_domain = True

        if not found_domain:
            raise VerificationError(
                f"ORCID {orcid} is valid but domain affiliation does not match 'public health' or 'climate adaptation'. "
                "Please check the expert's profile."
            )
        
        logger.info(f"ORCID {orcid} verified successfully.")
        return True

    except requests.RequestException as e:
        raise VerificationError(f"Network error verifying ORCID {orcid}: {e}")
    except json.JSONDecodeError:
        raise VerificationError(f"Invalid JSON response from ORCID API for {orcid}.")
    except VerificationError:
        raise
    except Exception as e:
        raise VerificationError(f"Unexpected error verifying ORCID {orcid}: {e}")

def ingest_ratings(ratings_file: Path = RATINGS_FILE) -> List[Dict[str, Any]]:
    """
    Load and validate expert ratings from the CSV file.
    Performs ORCID verification for each entry.
    """
    if not ratings_file.exists():
        raise FileNotFoundError(f"Ratings file not found: {ratings_file}")

    ratings = []
    with open(ratings_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not validate_ratings_schema(row):
                logger.warning(f"Skipping invalid row in ratings: {row}")
                continue

            # Verify ORCID
            orcid = row.get("expert_orcid")
            try:
                verify_orcid(orcid)
            except VerificationError as e:
                logger.error(f"ORCID verification failed for {orcid}: {e}")
                # Fail loudly: stop the pipeline
                raise e

            # Parse scores
            rating_entry = {
                "pair_id": row["pair_id"],
                "expert_orcid": orcid,
                "proposal_a_score": float(row["proposal_a_score"]),
                "proposal_b_score": float(row["proposal_b_score"]),
                "contextual_alignment_a": float(row["contextual_alignment_a"]),
                "contextual_alignment_b": float(row["contextual_alignment_b"]),
                "notes": row.get("notes", "")
            }
            ratings.append(rating_entry)

    logger.info(f"Successfully ingested {len(ratings)} valid ratings.")
    return ratings

def main():
    """
    Main entry point for T030.
    1. Ensure results dir.
    2. Load generated proposals.
    3. Create blinded pairs (if not already done).
    4. Generate ratings template (if not already done).
    5. Ingest ratings (load, verify ORCID, validate schema).
    6. Save validated ratings to a processed file (optional, or just return).
    """
    ensure_results_dir()
    
    # Check if ratings file exists (T059 output)
    if not RATINGS_FILE.exists():
        logger.error("Ratings file not found. Did you run T059?")
        logger.info("Generating a template for T059 to populate.")
        proposals = load_generated_proposals()
        pairs = create_blinded_pairs(proposals)
        save_blinded_pairs(pairs)
        generate_ratings_template(pairs)
        logger.info("Template generated. Please fill it and run again.")
        return

    # Ingest and verify
    try:
        validated_ratings = ingest_ratings(RATINGS_FILE)
        # Save the validated ratings to a processed file
        processed_ratings_path = RESULTS_DIR / "ratings_validated.json"
        with open(processed_ratings_path, 'w', encoding='utf-8') as f:
            json.dump(validated_ratings, f, indent=2)
        logger.info(f"Saved validated ratings to {processed_ratings_path}")
        register_new_file(str(processed_ratings_path), "validated_ratings")
    except VerificationError as e:
        logger.critical(f"Pipeline halted due to ORCID verification failure: {e}")
        raise e
    except FileNotFoundError as e:
        logger.critical(f"Pipeline halted due to missing file: {e}")
        raise e

if __name__ == "__main__":
    main()
