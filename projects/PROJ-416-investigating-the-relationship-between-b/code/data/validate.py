"""
Validation module for fMRI data metadata.

Ensures required clinical scores, paired data presence, and validated anxiety
instruments are present before processing. Enforces FR-011 and FR-009.
"""
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

# Configure logging for this module
logger = logging.getLogger(__name__)

# Validated anxiety scales with citation info (FR-009)
VALIDATED_ANXIETY_SCALES = {
    "GAD-7": {
        "full_name": "Generalized Anxiety Disorder 7-item scale",
        "citation": "Spitzer RL, Kroenke K, Williams JB, Löwe B. A brief measure for assessing generalized anxiety disorder: the GAD-7. Arch Intern Med. 2006;166(10):1092-1097.",
        "url": "https://www.gad-7.org/"
    },
    "HAM-A": {
        "full_name": "Hamilton Anxiety Rating Scale",
        "citation": "Hamilton M. The assessment of anxiety states by rating. Br J Med Psychol. 1959;32(1):50-55.",
        "url": "https://www.psychiatry.org/Psychiatrists/Practice/Standards-and-Ethics/Practice-Guidelines"
    },
    "STAI": {
        "full_name": "State-Trait Anxiety Inventory",
        "citation": "Spielberger CD, Gorsuch RL, Lushene R, Vagg PR, Jacobs GA. Manual for the State-Trait Anxiety Inventory. Palo Alto, CA: Consulting Psychologists Press; 1983.",
        "url": "https://www.pearsonclinical.com/"
    },
    "BAI": {
        "full_name": "Beck Anxiety Inventory",
        "citation": "Beck AT, Epstein N, Brown G, Steer RA. An inventory for measuring clinical anxiety: psychometric properties. J Consult Clin Psychol. 1988;56(6):893-897.",
        "url": "https://www.pearsonclinical.com/"
    }
}

def validate_metadata(metadata: Dict[str, Any]) -> bool:
    """
    Validate that the metadata dictionary contains required treatment scores
    and a validated anxiety instrument (FR-011, FR-009).

    This function checks for:
    1. Presence of 'pre_treatment_score' and 'post_treatment_score'
    2. Numeric validity of scores
    3. Presence of 'anxiety_scale' or 'instrument' field
    4. Validation that the instrument is a recognized anxiety scale

    Args:
        metadata: Dictionary containing subject/session metadata.

    Returns:
        bool: True if validation passes, False otherwise.

    Raises:
        SystemExit: If critical validation fails (per FR-011).
    """
    required_keys = ['pre_treatment_score', 'post_treatment_score']
    missing_keys = [key for key in required_keys if key not in metadata]

    if missing_keys:
        error_msg = f"CRITICAL: Missing required metadata fields: {missing_keys}. " \
                    f"Pipeline halted per FR-011 (missing variable check)."
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        return False

    # Validate that scores are numeric
    for key in required_keys:
        try:
            score = metadata[key]
            if score is None:
                logger.error(f"CRITICAL: Field '{key}' is None. Pipeline halted.")
                print(f"CRITICAL: Field '{key}' is None. Pipeline halted.", file=sys.stderr)
                return False
            float(score)  # Attempt conversion to ensure numeric
        except (ValueError, TypeError):
            error_msg = f"CRITICAL: Field '{key}' must be numeric. Value: {metadata[key]}"
            logger.error(error_msg)
            print(error_msg, file=sys.stderr)
            return False

    # Validate anxiety instrument (FR-009)
    instrument_key = None
    for key in ['anxiety_scale', 'instrument', 'scale_name', 'clinical_scale']:
        if key in metadata:
            instrument_key = key
            break

    if instrument_key is None:
        error_msg = "CRITICAL: No anxiety instrument field found in metadata. " \
                    "Required fields: 'anxiety_scale', 'instrument', 'scale_name', or 'clinical_scale'. " \
                    "Pipeline halted per FR-009."
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        return False

    instrument_name = metadata[instrument_key]
    if instrument_name not in VALIDATED_ANXIETY_SCALES:
        error_msg = (
            f"CRITICAL: Anxiety instrument '{instrument_name}' is not a validated scale. "
            f"Per FR-009, only the following validated scales are accepted: "
            f"{list(VALIDATED_ANXIETY_SCALES.keys())}. "
            f"Pipeline halted."
        )
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        return False

    # Log citation for the validated scale
    scale_info = VALIDATED_ANXIETY_SCALES[instrument_name]
    logger.info(f"Validated instrument confirmed: {instrument_name} ({scale_info['full_name']})")
    logger.info(f"Citation: {scale_info['citation']}")

    # Check for paired data (pre and post must both be present and non-None)
    pre_score = metadata['pre_treatment_score']
    post_score = metadata['post_treatment_score']

    if pre_score is None or post_score is None:
        error_msg = "CRITICAL: Paired data incomplete. Both pre_treatment_score and post_treatment_score " \
                    "must be present and non-None for valid analysis."
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        return False

    logger.info("Metadata validation passed: pre/post scores present, numeric, and paired.")
    logger.info(f"Anxiety instrument '{instrument_name}' validated against FR-009 requirements.")
    return True


def validate_subject_metadata_path(path: Path) -> bool:
    """
    Validate a specific subject's metadata file.

    Args:
        path: Path to the subject's metadata JSON file.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not path.exists():
        logger.error(f"Metadata file not found: {path}")
        return False

    try:
        import json
        with open(path, 'r') as f:
            metadata = json.load(f)
        return validate_metadata(metadata)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in metadata file {path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error validating metadata file {path}: {e}")
        return False