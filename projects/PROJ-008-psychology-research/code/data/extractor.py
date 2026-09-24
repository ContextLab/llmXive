"""
Data extraction module for US1.
Implements extraction of intervention components, delivery formats, blinding status,
and social skill domains from registry metadata.
"""

import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from code.utils.logging import get_logger

logger = get_logger(__name__)

# Constants for extraction patterns
MINDFULNESS_COMPONENTS = {
    'breathing': r'\bbreathing\b',
    'body scan': r'\bbody\s+scan\b',
    'mindful movement': r'\bmindful\s+movement\b',
    'mindful eating': r'\bmindful\s+eating\b'
}

SOCIAL_SKILL_DOMAINS = {
    'communication': [r'\bspeech\b', r'\blanguage\b', r'\bverbal\b', r'\bnon-verbal\b'],
    'peer interaction': [r'\bpeer\b', r'\bsocial\b', r'\bgroup\b', r'\bplay\b'],
    'emotional regulation': [r'\bemotion\b', r'\baffect\b', r'\bregulation\b', r'\btantrum\b']
}

DELIVERY_FORMATS = ['caregiver-mediated', 'child-led', 'mixed', 'not-reported']

BLINDING_STATUSES = ['blinded', 'unblinded', 'mixed', 'unknown']


def extract_intervention_components(text: Optional[str]) -> List[str]:
    """
    Extract mindfulness intervention components from text.
    Uses case-insensitive, whole-word regex patterns.

    Args:
        text: Text to search (description or abstract)

    Returns:
        List of detected components
    """
    if not text:
        return []

    text_lower = text.lower()
    detected = []

    for component, pattern in MINDFULNESS_COMPONENTS.items():
        if re.search(pattern, text_lower):
            detected.append(component)

    return detected


def extract_social_skill_domain(text: Optional[str]) -> str:
    """
    Extract social skill domain from text.
    Assigns first matching domain; if multiple, assigns 'mixed'.

    Args:
        text: Text to search (description or abstract)

    Returns:
        One of: communication, peer interaction, emotional regulation, mixed
    """
    if not text:
        return 'not-reported'

    text_lower = text.lower()
    matched_domains = []

    for domain, patterns in SOCIAL_SKILL_DOMAINS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                if domain not in matched_domains:
                    matched_domains.append(domain)
                break

    if len(matched_domains) == 0:
        return 'not-reported'
    elif len(matched_domains) == 1:
        return matched_domains[0]
    else:
        return 'mixed'


def extract_delivery_format(text: Optional[str]) -> str:
    """
    Extract delivery format from text.
    Looks for keywords indicating caregiver-mediated or child-led.

    Args:
        text: Text to search (description or abstract)

    Returns:
        One of: caregiver-mediated, child-led, mixed, not-reported
    """
    if not text:
        return 'not-reported'

    text_lower = text.lower()

    caregiver_keywords = ['caregiver', 'parent', 'family-mediated', 'adult-led']
    child_keywords = ['child-led', 'self-directed', 'peer-led']

    has_caregiver = any(kw in text_lower for kw in caregiver_keywords)
    has_child = any(kw in text_lower for kw in child_keywords)

    if has_caregiver and has_child:
        return 'mixed'
    elif has_caregiver:
        return 'caregiver-mediated'
    elif has_child:
        return 'child-led'
    else:
        return 'not-reported'


def extract_blinding_status(record: Dict[str, Any]) -> tuple:
    """
    Extract rater blinding status from registry metadata.

    Logic:
    - Check for explicit 'rater_type' field: values 'blinded', 'unblinded', 'mixed'
    - Check for 'blinded_assessment_flag': boolean
    - If both primary (unblinded) and secondary (blinded) outcomes exist, flag as 'mixed'
    - Default to 'unknown' if no information found

    Args:
        record: Registry metadata dictionary

    Returns:
        Tuple of (rater_type, blinded_assessment_flag)
    """
    rater_type = 'unknown'
    blinded_flag = None

    # Check explicit rater_type field
    if 'rater_type' in record:
        rater_val = record['rater_type'].lower()
        if rater_val in ['blinded', 'unblinded', 'mixed']:
            rater_type = rater_val

    # Check blinded_assessment_flag
    if 'blinded_assessment_flag' in record:
        blinded_flag = bool(record['blinded_assessment_flag'])

    # If we have both fields, reconcile
    if rater_type != 'unknown' and blinded_flag is not None:
        if rater_type == 'mixed':
            pass  # Already mixed
        elif rater_type == 'blinded' and not blinded_flag:
            rater_type = 'mixed'
        elif rater_type == 'unblinded' and blinded_flag:
            rater_type = 'mixed'
    elif rater_type == 'unknown' and blinded_flag is not None:
        rater_type = 'blinded' if blinded_flag else 'unblinded'

    return rater_type, blinded_flag


def extract_study_metadata(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract all metadata fields for a study record.

    Args:
        record: Raw registry record

    Returns:
        Dictionary with extracted fields
    """
    # Combine description and abstract for text extraction
    text_content = ''
    if 'description' in record:
        text_content += ' ' + str(record['description'])
    if 'abstract' in record:
        text_content += ' ' + str(record['abstract'])

    return {
        'intervention_components': extract_intervention_components(text_content),
        'social_skill_domain': extract_social_skill_domain(text_content),
        'delivery_format': extract_delivery_format(text_content),
        'abstract_text': record.get('abstract', None)
    }


def extract_blinding_status_from_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract blinding-specific fields from a record.

    Args:
        record: Raw registry record

    Returns:
        Dictionary with rater_type and blinded_assessment_flag
    """
    rater_type, blinded_flag = extract_blinding_status(record)
    return {
        'rater_type': rater_type,
        'blinded_assessment_flag': blinded_flag
    }


def process_studies_with_fallback(studies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a list of study records, extracting all metadata and blinding status.

    Args:
        studies: List of raw registry records

    Returns:
        List of enriched study dictionaries
    """
    processed = []
    for study in studies:
        enriched = dict(study)
        metadata = extract_study_metadata(study)
        blinding = extract_blinding_status_from_record(study)
        enriched.update(metadata)
        enriched.update(blinding)
        processed.append(enriched)

    return processed


def log_excluded_study(study_id: str, reason: str, log_path: str):
    """
    Log an excluded study to the excluded_studies.log file.

    Args:
        study_id: The study identifier
        reason: Reason for exclusion
        log_path: Path to the log file
    """
    log_entry = {
        'study_id': study_id,
        'reason': reason,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

    log_path_obj = Path(log_path)
    log_path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"{log_entry}\n")

    logger.info(f"Excluded study {study_id}: {reason}")


def main():
    """Main entry point for extraction module (testing/debugging)."""
    logger.info("Extraction module loaded successfully")
    # Example usage would be in the pipeline context
    pass


if __name__ == '__main__':
    main()
