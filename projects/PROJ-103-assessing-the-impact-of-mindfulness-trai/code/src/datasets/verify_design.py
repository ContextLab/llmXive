"""
Design verification logic for mindfulness intervention metadata.

This module checks dataset metadata for mindfulness-related interventions,
handling various synonyms and naming conventions without rigid regex patterns.
"""
import os
import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field

# Configure logging
logger = logging.getLogger(__name__)


class DesignVerificationError(Exception):
    """Raised when design verification fails."""
    pass


class InterventionType(Enum):
    """Enum representing known intervention types."""
    MINDFULNESS = "mindfulness"
    MBSR = "MBSR"
    MBCT = "MBCT"
    MEDITATION = "meditation"
    OTHER = "other"
    UNKNOWN = "unknown"


@dataclass
class DesignMetadata:
    """Container for dataset design metadata."""
    intervention_type: Optional[str] = None
    pre_scan_count: Optional[int] = None
    post_scan_count: Optional[int] = None
    study_design: Optional[str] = None
    population: Optional[str] = None
    notes: Optional[str] = None


# Synonym mapping for mindfulness interventions
# This is a flexible mapping that can be extended without regex
MINDFULNESS_SYNONYMS = {
    "mindfulness": ["mindfulness", "mindful", "mindfulness-based"],
    "mbsr": ["mbsr", "mindfulness-based stress reduction", "mindfulness based stress reduction"],
    "mbct": ["mbct", "mindfulness-based cognitive therapy", "mindfulness based cognitive therapy"],
    "meditation": ["meditation", "meditative", "meditative practice", "vipassana", "zen", "samatha"],
    "march": ["march", "mindfulness and resilience training"],
    "mbsr-variant": ["mbsr", "mindfulness based stress reduction"],
}

# Keywords that suggest a mindfulness intervention
MINDFULNESS_KEYWORDS = {
    "mindfulness", "mbsr", "mbct", "meditation", "mindful", "vipassana",
    "zen", "samatha", "loving-kindness", "metta", "body scan", "breath awareness",
    "mindfulness-based stress reduction", "mindfulness based stress reduction",
    "mindfulness-based cognitive therapy", "mindfulness based cognitive therapy",
    "march", "mindfulness and resilience", "mindfulness training",
    "mindfulness intervention", "mindfulness program"
}


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.
    
    Args:
        text: Input text string
        
    Returns:
        Normalized lowercase text with extra whitespace removed
    """
    if not text:
        return ""
    # Convert to lowercase and collapse whitespace
    normalized = " ".join(text.lower().split())
    return normalized


def match_intervention_type(intervention_text: str) -> InterventionType:
    """
    Match intervention text to a known mindfulness intervention type.
    
    This function uses a flexible, non-regex approach to identify
    mindfulness-related interventions by checking against known synonyms
    and keywords.
    
    Args:
        intervention_text: The intervention description text
        
    Returns:
        InterventionType enum value
    """
    if not intervention_text:
        return InterventionType.UNKNOWN
    
    normalized = normalize_text(intervention_text)
    
    # Direct matches for specific programs
    if "mbsr" in normalized:
        return InterventionType.MBSR
    if "mbct" in normalized:
        return InterventionType.MBCT
    if "mindfulness" in normalized:
        return InterventionType.MINDFULNESS
    
    # Check for meditation-related terms
    if "meditation" in normalized or "meditative" in normalized:
        return InterventionType.MEDITATION
    
    # Check for other mindfulness-related terms
    mindfulness_terms = ["vipassana", "zen", "samatha", "loving-kindness", "metta"]
    for term in mindfulness_terms:
        if term in normalized:
            return InterventionType.MEDITATION
    
    # Check for mindfulness-based programs
    if "mindfulness-based" in normalized or "mindfulness based" in normalized:
        return InterventionType.MINDFULNESS
    
    # Check for resilience training programs that include mindfulness
    if "march" in normalized or "mindfulness and resilience" in normalized:
        return InterventionType.MINDFULNESS
    
    return InterventionType.OTHER


def validate_metadata_fields(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that required metadata fields are present and have valid values.
    
    Args:
        metadata: Dictionary containing dataset metadata
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check for intervention type field
    if "intervention_type" not in metadata:
        errors.append("Missing required field: intervention_type")
    elif not isinstance(metadata.get("intervention_type"), str):
        errors.append("intervention_type must be a string")
    
    # Check for scan counts (optional but recommended)
    for field_name in ["pre_scan_count", "post_scan_count"]:
        if field_name in metadata:
            if not isinstance(metadata[field_name], int) or metadata[field_name] < 0:
                errors.append(f"{field_name} must be a non-negative integer")
    
    return len(errors) == 0, errors


def validate_design_logic(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate logical consistency of design metadata.
    
    Args:
        metadata: Dictionary containing dataset metadata
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    intervention_type = metadata.get("intervention_type", "")
    if not intervention_type:
        return True, []  # No intervention type specified, skip logic validation
    
    intervention_match = match_intervention_type(intervention_type)
    
    # If it's a mindfulness intervention, check for required design elements
    if intervention_match in [InterventionType.MINDFULNESS, InterventionType.MBSR, 
                             InterventionType.MBCT, InterventionType.MEDITATION]:
        # Check for pre/post design
        if "pre_scan_count" not in metadata or "post_scan_count" not in metadata:
            logger.warning(
                f"Mindfulness intervention detected but pre/post scan counts not specified. "
                f"This may limit analysis capabilities."
            )
        elif metadata["pre_scan_count"] == 0 or metadata["post_scan_count"] == 0:
            errors.append(
                "Both pre_scan_count and post_scan_count must be non-zero for "
                "a valid pre-post mindfulness intervention design"
            )
    
    return len(errors) == 0, errors


def verify_dataset_design(metadata: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify that a dataset's design metadata indicates a mindfulness intervention.
    
    This function performs comprehensive verification including:
    - Field validation
    - Logical consistency checks
    - Intervention type matching
    
    Args:
        metadata: Dictionary containing dataset metadata
        
    Returns:
        Tuple of (is_valid, verification_details)
    """
    details = {
        "intervention_type": None,
        "intervention_match": None,
        "is_mindfulness": False,
        "field_validation": {},
        "logic_validation": {},
        "warnings": []
    }
    
    # Validate required fields
    field_valid, field_errors = validate_metadata_fields(metadata)
    details["field_validation"] = {
        "is_valid": field_valid,
        "errors": field_errors
    }
    
    if not field_valid:
        return False, details
    
    # Validate design logic
    logic_valid, logic_errors = validate_design_logic(metadata)
    details["logic_validation"] = {
        "is_valid": logic_valid,
        "errors": logic_errors
    }
    
    # Match intervention type
    intervention_text = metadata.get("intervention_type", "")
    intervention_match = match_intervention_type(intervention_text)
    details["intervention_type"] = intervention_text
    details["intervention_match"] = intervention_match.value
    
    # Determine if it's a mindfulness intervention
    is_mindfulness = intervention_match in [
        InterventionType.MINDFULNESS,
        InterventionType.MBSR,
        InterventionType.MBCT,
        InterventionType.MEDITATION
    ]
    details["is_mindfulness"] = is_mindfulness
    
    # Add warnings if applicable
    if not is_mindfulness and intervention_text:
        details["warnings"].append(
            f"Intervention '{intervention_text}' does not match known mindfulness patterns"
        )
    
    # Overall validity
    is_valid = field_valid and logic_valid and is_mindfulness
    
    return is_valid, details


def verify_all_datasets(datasets_dir: Path) -> Dict[str, Dict[str, Any]]:
    """
    Verify design metadata for all datasets in a directory.
    
    Args:
        datasets_dir: Path to directory containing dataset metadata JSON files
        
    Returns:
        Dictionary mapping dataset IDs to verification results
    """
    results = {}
    
    if not datasets_dir.exists():
        raise DesignVerificationError(f"Datasets directory not found: {datasets_dir}")
    
    # Find all JSON files
    json_files = list(datasets_dir.glob("*.json"))
    
    if not json_files:
        logger.warning(f"No JSON files found in {datasets_dir}")
        return results
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                metadata = json.load(f)
            
            dataset_id = json_file.stem
            is_valid, details = verify_dataset_design(metadata)
            results[dataset_id] = {
                "is_valid": is_valid,
                "details": details,
                "file_path": str(json_file)
            }
            
            if is_valid:
                logger.info(f"✓ Dataset '{dataset_id}' verified as mindfulness intervention")
            else:
                logger.warning(f"✗ Dataset '{dataset_id}' verification failed: {details}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {json_file}: {e}")
            results[str(json_file)] = {
                "is_valid": False,
                "error": f"JSON decode error: {e}"
            }
        except Exception as e:
            logger.error(f"Error processing {json_file}: {e}")
            results[str(json_file)] = {
                "is_valid": False,
                "error": str(e)
            }
    
    return results


def main():
    """Main entry point for design verification."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Verify dataset design metadata for mindfulness interventions"
    )
    parser.add_argument(
        "--datasets-dir",
        type=str,
        required=True,
        help="Path to directory containing dataset metadata JSON files"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output JSON file with verification results"
    )
    
    args = parser.parse_args()
    
    datasets_dir = Path(args.datasets_dir)
    
    try:
        results = verify_all_datasets(datasets_dir)
        
        # Count results
        total = len(results)
        valid = sum(1 for r in results.values() if r.get("is_valid", False))
        invalid = total - valid
        
        print(f"\nDesign Verification Results:")
        print(f"  Total datasets: {total}")
        print(f"  Valid mindfulness interventions: {valid}")
        print(f"  Invalid/Non-mindfulness: {invalid}")
        
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nResults written to: {output_path}")
        
        # Return exit code based on validity
        if invalid > 0:
            return 1
        return 0
        
    except DesignVerificationError as e:
        print(f"Design verification error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    import sys
    sys.exit(main())
