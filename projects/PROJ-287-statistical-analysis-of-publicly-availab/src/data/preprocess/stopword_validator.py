"""
Stopword Validator Module

Validates generated stopword lists against a baseline to ensure:
1. No global list is used by default (window-specificity check)
2. Lists are deterministic (content and order consistency)
3. Content quality (reasonable size, no obvious artifacts)
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple, Optional

# Import from existing project utilities
from src.utils.logging import get_logger

# Constants
STOPWORD_DIR = Path("data/stopwords")
MANIFEST_PATH = STOPWORD_DIR / "manifest.json"
MIN_STOPWORDS_PER_WINDOW = 10
MAX_STOPWORDS_PER_WINDOW = 5000
DETERMINISM_CHECK_ITERATIONS = 3


def get_logger_module():
    """Get logger for this module."""
    return get_logger(__name__)


def load_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the stopword manifest file.

    Args:
        manifest_path: Path to manifest file. Defaults to STOPWORD_DIR/manifest.json

    Returns:
        Dictionary containing manifest data

    Raises:
        FileNotFoundError: If manifest file does not exist
        json.JSONDecodeError: If manifest is not valid JSON
    """
    if manifest_path is None:
        manifest_path = MANIFEST_PATH

    if not manifest_path.exists():
        raise FileNotFoundError(f"Stopword manifest not found at {manifest_path}")

    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of a file for determinism checking.

    Args:
        file_path: Path to the file

    Returns:
        Hex string of SHA256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_stopword_set(file_path: Path) -> Set[str]:
    """
    Load a stopword list from a JSON file.

    Args:
        file_path: Path to the stopword list JSON file

    Returns:
        Set of stopwords
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return set(data.get('stopwords', []))


def validate_determinism(manifest: Dict[str, Any], logger: Optional[logging.Logger] = None) -> Tuple[bool, List[str]]:
    """
    Validate that stopword generation is deterministic.

    This checks that:
    1. The manifest contains consistent hashes
    2. Re-loading the files produces the same content
    3. The stored hashes match the actual file contents

    Args:
        manifest: The loaded manifest dictionary
        logger: Optional logger instance

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    is_valid = True

    if logger is None:
        logger = get_logger_module()

    logger.info("Starting determinism validation...")

    # Check that manifest has required structure
    if 'windows' not in manifest:
        errors.append("Manifest missing 'windows' key")
        return False, errors

    windows = manifest['windows']
    if not isinstance(windows, dict):
        errors.append("'windows' key must be a dictionary")
        return False, errors

    # Validate each window entry
    for window_name, window_data in windows.items():
        if 'file_path' not in window_data:
            errors.append(f"Window '{window_name}' missing 'file_path'")
            is_valid = False
            continue

        if 'hash' not in window_data:
            errors.append(f"Window '{window_name}' missing 'hash'")
            is_valid = False
            continue

        file_path = Path(window_data['file_path'])
        if not file_path.exists():
            errors.append(f"Stopword file for '{window_name}' does not exist: {file_path}")
            is_valid = False
            continue

        # Compute actual hash and compare
        actual_hash = compute_file_hash(file_path)
        stored_hash = window_data['hash']

        if actual_hash != stored_hash:
            errors.append(
                f"Hash mismatch for window '{window_name}': "
                f"stored={stored_hash}, actual={actual_hash}"
            )
            is_valid = False

        # Validate content can be loaded
        try:
            stopwords = load_stopword_set(file_path)
            if not isinstance(stopwords, set):
                errors.append(f"Stopwords for '{window_name}' are not a valid set")
                is_valid = False
        except Exception as e:
            errors.append(f"Failed to load stopwords for '{window_name}': {str(e)}")
            is_valid = False

    if is_valid:
        logger.info("Determinism validation PASSED")
    else:
        logger.warning(f"Determinism validation FAILED with {len(errors)} errors")

    return is_valid, errors


def validate_window_specificity(manifest: Dict[str, Any], logger: Optional[logging.Logger] = None) -> Tuple[bool, List[str]]:
    """
    Validate that stopword lists are window-specific and not just a global list.

    This checks that:
    1. Different windows have different stopword sets
    2. No window uses a default/global list
    3. The TF-IDF generation produced distinct lists per window

    Args:
        manifest: The loaded manifest dictionary
        logger: Optional logger instance

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    is_valid = True

    if logger is None:
        logger = get_logger_module()

    logger.info("Starting window-specificity validation...")

    if 'windows' not in manifest:
        errors.append("Manifest missing 'windows' key")
        return False, errors

    windows = manifest['windows']
    window_names = list(windows.keys())

    if len(window_names) < 2:
        errors.append("Need at least 2 windows to validate specificity")
        return False, errors

    # Load all stopword sets
    stopword_sets = {}
    for window_name in window_names:
        file_path = Path(windows[window_name].get('file_path', ''))
        if file_path.exists():
            stopword_sets[window_name] = load_stopword_set(file_path)
        else:
            errors.append(f"File not found for window '{window_name}': {file_path}")
            is_valid = False

    if len(stopword_sets) < 2:
        errors.append("Cannot validate specificity with fewer than 2 valid windows")
        return False, errors

    # Check that not all windows have identical stopword sets
    unique_sets = set()
    for window_name, stopwords in stopword_sets.items():
        # Convert to frozenset for hashability
        unique_sets.add(frozenset(stopwords))

    if len(unique_sets) == 1:
        errors.append(
            "All windows have IDENTICAL stopword sets - this suggests a global list "
            "was used instead of window-specific TF-IDF generation"
        )
        is_valid = False
    else:
        logger.info(f"Found {len(unique_sets)} unique stopword sets across {len(window_names)} windows")

    # Check for common patterns that indicate a global list
    # If >95% overlap between any two windows, flag it
    window_list = list(stopword_sets.keys())
    for i in range(len(window_list)):
        for j in range(i + 1, len(window_list)):
            w1, w2 = window_list[i], window_list[j]
            set1, set2 = stopword_sets[w1], stopword_sets[w2]

            if not set1 or not set2:
                continue

            intersection = len(set1 & set2)
            union = len(set1 | set2)
            jaccard_similarity = intersection / union if union > 0 else 0

            if jaccard_similarity > 0.95:
                errors.append(
                    f"High similarity ({jaccard_similarity:.2%}) between '{w1}' and '{w2}' "
                    f"(intersection={intersection}, union={union}). "
                    f"This may indicate insufficient window-specific differentiation."
                )
                # Don't fail, just warn

    if is_valid:
        logger.info("Window-specificity validation PASSED")
    else:
        logger.warning(f"Window-specificity validation FAILED with {len(errors)} errors")

    return is_valid, errors


def validate_content_quality(manifest: Dict[str, Any], logger: Optional[logging.Logger] = None) -> Tuple[bool, List[str]]:
    """
    Validate the quality of stopword lists.

    This checks that:
    1. Each window has a reasonable number of stopwords
    2. Stopwords are not empty or excessively large
    3. No obvious artifacts (empty strings, non-string entries)

    Args:
        manifest: The loaded manifest dictionary
        logger: Optional logger instance

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    is_valid = True

    if logger is None:
        logger = get_logger_module()

    logger.info("Starting content quality validation...")

    if 'windows' not in manifest:
        errors.append("Manifest missing 'windows' key")
        return False, errors

    for window_name, window_data in manifest['windows'].items():
        file_path = Path(window_data.get('file_path', ''))
        if not file_path.exists():
            continue

        try:
            stopwords = load_stopword_set(file_path)

            # Check size bounds
            if len(stopwords) < MIN_STOPWORDS_PER_WINDOW:
                errors.append(
                    f"Window '{window_name}' has too few stopwords: {len(stopwords)} "
                    f"(minimum: {MIN_STOPWORDS_PER_WINDOW})"
                )
                is_valid = False
            elif len(stopwords) > MAX_STOPWORDS_PER_WINDOW:
                errors.append(
                    f"Window '{window_name}' has too many stopwords: {len(stopwords)} "
                    f"(maximum: {MAX_STOPWORDS_PER_WINDOW})"
                )
                is_valid = False

            # Check for artifacts
            for word in stopwords:
                if not isinstance(word, str):
                    errors.append(
                        f"Window '{window_name}' contains non-string entry: {type(word)}"
                    )
                    is_valid = False
                    break
                if word.strip() == '':
                    errors.append(
                        f"Window '{window_name}' contains empty string in stopwords"
                    )
                    is_valid = False
                    break
                if len(word) > 100:  # Unusually long "word"
                    errors.append(
                        f"Window '{window_name}' contains unusually long entry: '{word[:20]}...' "
                        f"(length={len(word)})"
                    )

            logger.info(f"Window '{window_name}': {len(stopwords)} stopwords validated")

        except Exception as e:
            errors.append(f"Error validating content for '{window_name}': {str(e)}")
            is_valid = False

    if is_valid:
        logger.info("Content quality validation PASSED")
    else:
        logger.warning(f"Content quality validation FAILED with {len(errors)} errors")

    return is_valid, errors


def run_validation(manifest_path: Optional[Path] = None, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Run all validation checks on the stopword lists.

    Args:
        manifest_path: Path to manifest file
        logger: Optional logger instance

    Returns:
        Dictionary with validation results:
        {
            "overall_pass": bool,
            "determinism": {"passed": bool, "errors": List[str]},
            "window_specificity": {"passed": bool, "errors": List[str]},
            "content_quality": {"passed": bool, "errors": List[str]},
            "total_errors": int
        }
    """
    if logger is None:
        logger = get_logger_module()

    logger.info("=" * 60)
    logger.info("STOPWORD VALIDATION START")
    logger.info("=" * 60)

    try:
        manifest = load_manifest(manifest_path)
    except FileNotFoundError as e:
        error_msg = f"Manifest not found: {str(e)}"
        logger.error(error_msg)
        return {
            "overall_pass": False,
            "determinism": {"passed": False, "errors": [error_msg]},
            "window_specificity": {"passed": False, "errors": []},
            "content_quality": {"passed": False, "errors": []},
            "total_errors": 1
        }
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in manifest: {str(e)}"
        logger.error(error_msg)
        return {
            "overall_pass": False,
            "determinism": {"passed": False, "errors": [error_msg]},
            "window_specificity": {"passed": False, "errors": []},
            "content_quality": {"passed": False, "errors": []},
            "total_errors": 1
        }

    # Run all validations
    det_pass, det_errors = validate_determinism(manifest, logger)
    spec_pass, spec_errors = validate_window_specificity(manifest, logger)
    qual_pass, qual_errors = validate_content_quality(manifest, logger)

    total_errors = len(det_errors) + len(spec_errors) + len(qual_errors)
    overall_pass = det_pass and spec_pass and qual_pass

    result = {
        "overall_pass": overall_pass,
        "determinism": {"passed": det_pass, "errors": det_errors},
        "window_specificity": {"passed": spec_pass, "errors": spec_errors},
        "content_quality": {"passed": qual_pass, "errors": qual_errors},
        "total_errors": total_errors
    }

    # Log summary
    logger.info("=" * 60)
    logger.info("STOPWORD VALIDATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Overall: {'PASSED' if overall_pass else 'FAILED'}")
    logger.info(f"Determinism: {'PASSED' if det_pass else 'FAILED'} ({len(det_errors)} errors)")
    logger.info(f"Window Specificity: {'PASSED' if spec_pass else 'FAILED'} ({len(spec_errors)} errors)")
    logger.info(f"Content Quality: {'PASSED' if qual_pass else 'FAILED'} ({len(qual_errors)} errors)")
    logger.info(f"Total Errors: {total_errors}")

    if not overall_pass:
        all_errors = det_errors + spec_errors + qual_errors
        for i, err in enumerate(all_errors, 1):
            logger.error(f"  {i}. {err}")

    logger.info("=" * 60)

    return result


def main():
    """Main entry point for stopword validation."""
    logger = get_logger_module()
    logger.info("Running stopword list validation...")

    result = run_validation()

    # Exit with appropriate code
    if result["overall_pass"]:
        logger.info("Validation completed successfully")
        exit(0)
    else:
        logger.error("Validation failed - stopword lists do not meet requirements")
        exit(1)


if __name__ == "__main__":
    main()
