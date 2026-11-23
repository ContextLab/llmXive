"""
Evaluation Recruitment and Validation Module.

Handles:
- Generating blinded rating templates for expert distribution.
- Stripping metadata from generated proposals.
- Validating expert inputs against a verified roster (T030b).
- Ingesting filled ratings after validation (T030c).
"""
import json
import csv
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime

# Local imports from project structure
from utils.logging_config import get_logger
from utils.error_handling import ValidationError

logger = get_logger(__name__)

# Constants for file paths (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

GENERATED_PROPOSALS_PATH = DATA_RESULTS_DIR / "generated_proposals.jsonl"
RATINGS_TEMPLATE_PATH = DATA_RESULTS_DIR / "ratings_template.csv"
RATINGS_FILLED_PATH = DATA_RESULTS_DIR / "ratings_filled.csv"
EXPERT_ROSTER_PATH = PROJECT_ROOT / "data" / "raw" / "expert_roster.csv"

# Validation constants
MIN_EXPERIENCE_YEARS = 5
REQUIRED_ROSTER_COLUMNS = {"orcid", "verified", "years_experience"}
REQUIRED_RATING_COLUMNS = {"proposal_id", "metric", "score", "rater_orcid"}


def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error at line {line_num} in {file_path}: {e}")
                raise
    return data


def save_jsonl(data: List[Dict[str, Any]], file_path: Path) -> None:
    """Save a list of dictionaries to a JSONL file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')


def strip_metadata_for_evaluation(proposals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Strip sensitive metadata from proposals for blinded evaluation.
    Keeps: proposal_id, problem_statement, group_type (pattern-guided/baseline), text
    Removes: author, timestamp, model_version, internal_ids, etc.
    """
    kept_keys = {"proposal_id", "problem_statement", "group_type", "text", "title"}
    stripped = []
    
    for p in proposals:
        clean_p = {k: v for k, v in p.items() if k in kept_keys}
        # Ensure mandatory fields exist for evaluation
        if "proposal_id" not in clean_p:
            # Fallback if ID is missing, though it should be generated upstream
            clean_p["proposal_id"] = f"prop_{hash(p.get('text', '')) % 100000}"
        stripped.append(clean_p)
    
    return stripped


def generate_ratings_template(output_path: Path) -> None:
    """
    Generate the CSV template for experts to fill out ratings.
    Columns: proposal_id, metric, score, rater_orcid
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fields = ["proposal_id", "metric", "score", "rater_orcid"]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        # Add a few example rows (commented out or with placeholder values)
        # to guide the user, but the file is essentially empty for data entry
        # except for the header.
    
    logger.info(f"Generated ratings template at {output_path}")


def load_expert_roster(roster_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Load the expert roster CSV and return a dictionary keyed by ORCID.
    Validates that required columns exist.
    """
    if not roster_path.exists():
        raise FileNotFoundError(f"Expert roster not found at {roster_path}")
    
    roster_data = {}
    with open(roster_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Validate headers
        if not REQUIRED_ROSTER_COLUMNS.issubset(set(reader.fieldnames or [])):
            missing = REQUIRED_ROSTER_COLUMNS - set(reader.fieldnames or [])
            raise ValidationError(f"Expert roster missing required columns: {missing}")
        
        for row in reader:
            orcid = row.get("orcid", "").strip()
            if not orcid:
                logger.warning("Skipping roster row with empty ORCID")
                continue
            
            # Validate 'verified' field (expecting 'true' or 'True' or '1')
            verified_val = str(row.get("verified", "")).lower().strip()
            is_verified = verified_val in ("true", "1", "yes")
            
            # Validate years_experience
            try:
                years = int(row.get("years_experience", 0))
            except ValueError:
                logger.warning(f"Invalid years_experience for ORCID {orcid}, skipping")
                continue
            
            roster_data[orcid] = {
                "verified": is_verified,
                "years_experience": years,
                "raw_row": row
            }
    
    return roster_data


def validate_expert_inputs(
    ratings_path: Path,
    roster_path: Path = EXPERT_ROSTER_PATH
) -> Tuple[List[str], List[str]]:
    """
    Validate a filled ratings file against the expert roster.
    
    Constraints:
    1. Every rating must correspond to an ORCID in the roster.
    2. The ORCID must have verified=true.
    3. The ORCID must have years_experience >= 5.
    
    Returns:
    Tuple of (valid_ratings, error_messages)
    """
    if not ratings_path.exists():
        raise FileNotFoundError(f"Ratings file not found: {ratings_path}")
    
    # Load roster first
    logger.info(f"Loading expert roster from {roster_path}")
    try:
        roster = load_expert_roster(roster_path)
    except (FileNotFoundError, ValidationError) as e:
        logger.error(f"Failed to load expert roster: {e}")
        raise
    
    valid_ratings = []
    errors = []
    
    with open(ratings_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Validate headers
        if not REQUIRED_RATING_COLUMNS.issubset(set(reader.fieldnames or [])):
            missing = REQUIRED_RATING_COLUMNS - set(reader.fieldnames or [])
            raise ValidationError(f"Ratings file missing required columns: {missing}")
        
        for line_num, row in enumerate(reader, 2): # Start at 2 because 1 is header
            orcid = row.get("rater_orcid", "").strip()
            proposal_id = row.get("proposal_id", "").strip()
            metric = row.get("metric", "").strip()
            score_str = row.get("score", "").strip()
            
            # 1. Check if ORCID exists in roster
            if orcid not in roster:
                errors.append(f"Line {line_num}: ORCID '{orcid}' not found in expert roster.")
                continue
            
            expert_info = roster[orcid]
            
            # 2. Check verified status
            if not expert_info["verified"]:
                errors.append(f"Line {line_num}: ORCID '{orcid}' is not marked as verified in roster.")
                continue
            
            # 3. Check years of experience
            if expert_info["years_experience"] < MIN_EXPERIENCE_YEARS:
                errors.append(
                    f"Line {line_num}: ORCID '{orcid}' has {expert_info['years_experience']} years experience "
                    f"(minimum required: {MIN_EXPERIENCE_YEARS})."
                )
                continue
            
            # If we reach here, the rater is valid.
            # We could also validate score range here if needed, but task focuses on rater validation.
            valid_ratings.append(row)
    
    if errors:
        logger.warning(f"Validation found {len(errors)} errors in ratings file.")
        for err in errors[:5]: # Log first 5
            logger.warning(err)
        if len(errors) > 5:
            logger.warning(f"... and {len(errors) - 5} more errors.")
    else:
        logger.info(f"Validation passed for {len(valid_ratings)} ratings.")
    
    return valid_ratings, errors


def ingest_ratings(ratings_path: Path, roster_path: Path = EXPERT_ROSTER_PATH) -> List[Dict[str, Any]]:
    """
    Ingest ratings only after validation passes.
    Raises ValidationError if validation fails.
    """
    valid_ratings, errors = validate_expert_inputs(ratings_path, roster_path)
    
    if errors:
        error_msg = f"Validation failed for {ratings_path}. {len(errors)} invalid entries found."
        logger.error(error_msg)
        raise ValidationError(error_msg)
    
    logger.info(f"Successfully ingested {len(valid_ratings)} valid ratings.")
    return valid_ratings


def main():
    """
    Main entry point for evaluation recruitment tasks.
    Supports subcommands or automatic flow based on file existence.
    """
    # Ensure output directory exists
    DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Generate template if it doesn't exist
    if not RATINGS_TEMPLATE_PATH.exists():
        logger.info("Generating ratings template...")
        generate_ratings_template(RATINGS_TEMPLATE_PATH)
    else:
        logger.info(f"Template already exists at {RATINGS_TEMPLATE_PATH}")
    
    # 2. If ratings_filled.csv exists, validate and ingest
    if RATINGS_FILLED_PATH.exists():
        logger.info(f"Found filled ratings at {RATINGS_FILLED_PATH}. Validating...")
        try:
            # This will raise ValidationError if validation fails
            valid_data = ingest_ratings(RATINGS_FILLED_PATH, EXPERT_ROSTER_PATH)
            logger.info("Validation successful. Ratings are ready for statistical analysis.")
            # Optionally save a cleaned/validated version
            # clean_path = RATINGS_FILLED_PATH.with_name("ratings_validated.csv")
            # with open(clean_path, 'w', newline='') as f: ...
        except (FileNotFoundError, ValidationError) as e:
            logger.critical(f"Validation failed: {e}")
            sys.exit(1)
    else:
        logger.info(f"No filled ratings found at {RATINGS_FILLED_PATH}. "
                    f"Please distribute {RATINGS_TEMPLATE_PATH} to experts and save results as {RATINGS_FILLED_PATH}.")
    
    # 3. If proposals exist, strip metadata (for T030a flow, though T030b is the focus)
    if GENERATED_PROPOSALS_PATH.exists():
        logger.info(f"Stripping metadata from {GENERATED_PROPOSALS_PATH}...")
        proposals = load_jsonl(GENERATED_PROPOSALS_PATH)
        stripped = strip_metadata_for_evaluation(proposals)
        # Save to a separate file to avoid overwriting original if needed, 
        # or update the original if the pipeline design requires it.
        # Based on T030a description, we might save to a specific output.
        stripped_path = DATA_RESULTS_DIR / "proposals_blinded.jsonl"
        save_jsonl(stripped, stripped_path)
        logger.info(f"Saved blinded proposals to {stripped_path}")
    else:
        logger.warning(f"Generated proposals not found at {GENERATED_PROPOSALS_PATH}. "
                       f"Skipping metadata stripping.")


if __name__ == "__main__":
    # Setup basic logging for command line execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
