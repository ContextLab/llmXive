import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from code.utils.logging import get_logger

logger = get_logger(__name__)

def log_excluded_study(study_id: str, reason: str, output_dir: Path) -> None:
    """Log excluded study to JSONL file."""
    log_file = output_dir / "excluded_studies.log"
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "study_id": study_id,
        "reason": reason,
        "timestamp": timestamp
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def extract_study_metadata(study: Dict[str, Any]) -> Dict[str, Any]:
    """Extract core metadata from study record."""
    return {
        "id": study.get("id"),
        "title": study.get("title"),
        "registry": study.get("registry"),
        "age_range": study.get("age_range"),
        "diagnosis": study.get("diagnosis"),
        "outcomes": study.get("outcomes"),
        "abstract_text": study.get("abstract"),
        "follow_up": study.get("follow_up"),
        "rater_type": study.get("rater_type"),
        "blinded_assessment_flag": study.get("blinded_assessment_flag")
    }

def extract_intervention_components(study: Dict[str, Any]) -> List[str]:
    """Extract mindfulness intervention components from description/abstract."""
    text = ""
    if "description" in study:
        text += study["description"] + " "
    if "abstract" in study and study["abstract"]:
        text += study["abstract"] + " "
    
    text_lower = text.lower()
    
    components = []
    component_map = {
        "breathing": r"\bbreathing\b",
        "body scan": r"\bbody\s+scan\b",
        "mindful movement": r"\bmindful\s+movement\b",
        "mindful eating": r"\bmindful\s+eating\b"
    }
    
    for component, pattern in component_map.items():
        if re.search(pattern, text_lower):
            components.append(component)
    
    return components if components else ["none"]

def extract_social_skill_domain(study: Dict[str, Any]) -> tuple:
    """Extract social skill domain and notes from description/abstract."""
    text = ""
    if "description" in study:
        text += study["description"] + " "
    if "abstract" in study and study["abstract"]:
        text += study["abstract"] + " "
    
    text_lower = text.lower()
    
    domain_keywords = {
        "communication": ["speech", "language", "verbal", "non-verbal"],
        "peer interaction": ["peer", "social", "group", "play"],
        "emotional regulation": ["emotion", "affect", "regulation", "tantrum"]
    }
    
    found_domains = []
    for domain, keywords in domain_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                found_domains.append(domain)
                break
    
    if len(found_domains) == 0:
        # Check if there's a description that suggests a domain but doesn't match keywords
        if text and "social" in text_lower or "skill" in text_lower:
            return "other", text[:200]  # Return first 200 chars as note
        return "other", None
    elif len(found_domains) == 1:
        return found_domains[0], None
    else:
        return "mixed", None

def extract_delivery_format(study: Dict[str, Any]) -> str:
    """Extract delivery format from metadata."""
    format_val = study.get("delivery_format")
    if format_val in ["caregiver-mediated", "child-led", "mixed", "not-reported"]:
        return format_val
    return "not-reported"

def extract_blinding_status(study: Dict[str, Any]) -> tuple:
    """
    Extract blinding status from metadata.
    Returns (rater_type, blinded_assessment_flag)
    
    Logic:
    - If both fields present: use them directly
    - If rater_type present but flag missing: infer flag from type
    - If flag present but type missing: infer type from flag
    - If both missing: flag as 'unknown'
    - If both present but conflicting: flag as 'mixed'
    """
    rater_type = study.get("rater_type")
    blinded_flag = study.get("blinded_assessment_flag")
    
    # Case 1: Both present
    if rater_type is not None and blinded_flag is not None:
        # Check for consistency
        if rater_type == "blinded" and not blinded_flag:
            return "mixed", None  # Conflicting
        if rater_type == "unblinded" and blinded_flag:
            return "mixed", None  # Conflicting
        return rater_type, blinded_flag
    
    # Case 2: Only rater_type present
    if rater_type is not None:
        if rater_type == "blinded":
            return rater_type, True
        elif rater_type == "unblinded":
            return rater_type, False
        elif rater_type == "mixed":
            return rater_type, None  # Mixed implies both exist
        else:
            return "unknown", None
    
    # Case 3: Only flag present
    if blinded_flag is not None:
        if blinded_flag:
            return "blinded", blinded_flag
        else:
            return "unblinded", blinded_flag
    
    # Case 4: Both missing
    return "unknown", None

def process_studies_with_fallback(studies: List[Dict[str, Any]], output_dir: Path) -> List[Dict[str, Any]]:
    """Process all studies, extracting metadata and handling missing fields."""
    processed = []
    
    for study in studies:
        study_id = study.get("id", "unknown")
        
        # Check for insufficient metadata (age_range, diagnosis, or outcomes missing)
        if not study.get("age_range") or not study.get("diagnosis") or not study.get("outcomes"):
            # Check if abstract exists for fallback
            if not study.get("abstract"):
                log_excluded_study(study_id, "INSUFFICIENT_METADATA_NO_ABSTRACT", output_dir)
                continue
            else:
                # Per T020: DO NOT attempt extraction from abstract for inclusion criteria
                # Just exclude
                log_excluded_study(study_id, "MISSING_PRIMARY_FIELD", output_dir)
                continue
        
        # Extract core metadata
        meta = extract_study_metadata(study)
        
        # Extract intervention components
        meta["intervention_components"] = extract_intervention_components(study)
        
        # Extract social skill domain
        domain, notes = extract_social_skill_domain(study)
        meta["social_skill_domain"] = domain
        meta["domain_notes"] = notes
        
        # Extract delivery format
        meta["delivery_format"] = extract_delivery_format(study)
        
        # Extract blinding status (T022)
        rater_type, blinded_flag = extract_blinding_status(study)
        meta["rater_type"] = rater_type
        meta["blinded_assessment_flag"] = blinded_flag
        
        processed.append(meta)
    
    return processed

def main():
    """Entry point for extractor script."""
    import argparse
    from code.utils.config import get_data_path

    parser = argparse.ArgumentParser(description="Extract study metadata")
    parser.add_argument("--input", type=str, required=True, help="Input directory containing raw JSON files")
    parser.add_argument("--output", type=str, required=True, help="Output directory for extracted data")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading studies from {input_dir}")
    
    # Load all JSON files from input directory
    studies = []
    for json_file in input_dir.glob("*.json"):
        if "mock" not in str(json_file):  # Skip mock data in production
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    studies.extend(data)
                elif isinstance(data, dict):
                    studies.append(data)
    
    logger.info(f"Loaded {len(studies)} studies")
    
    if not studies:
        logger.warning("No studies found to extract")
        return

    # Process studies
    processed_studies = process_studies_with_fallback(studies, output_dir)
    
    logger.info(f"Extracted metadata for {len(processed_studies)} studies")
    
    # Save to JSON
    output_file = output_dir / "extracted_studies.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(processed_studies, f, indent=2)
    logger.info(f"Saved extracted studies to {output_file}")

if __name__ == "__main__":
    main()
