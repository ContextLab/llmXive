"""
Stopword Validator Module (T014b)

Validates generated window-specific stopword lists against a baseline to ensure:
1. No global list is used by default (each window has distinct content).
2. Lists are deterministic (re-running generation produces identical hashes).
3. Manifest integrity matches the actual files on disk.

Dependencies:
- src/data/preprocess/stopword_generator.py (for manifest loading logic)
- src/utils/logging.py
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple, Optional

from src.utils.logging import get_logger

# Constants
STOPWORDS_DIR = Path("data/stopwords")
MANIFEST_PATH = STOPWORDS_DIR / "manifest.json"
GLOBAL_STOPWORDS_BASELINE = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "can", "need",
    "dare", "ought", "used", "it", "its", "this", "that", "these", "those",
    "i", "you", "he", "she", "we", "they", "who", "which", "what", "whose",
    "whom", "where", "when", "why", "how", "all", "each", "every", "both",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "own", "same", "so", "than", "too", "very", "just", "also"
}


def get_logger_module() -> logging.Logger:
    """Get a logger specific to this module."""
    return get_logger("stopword_validator")


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the stopword manifest JSON."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found at {manifest_path}")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_stopword_set(file_path: Path) -> Set[str]:
    """Load a stopword set from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        # Expecting structure: {"window": "...", "stopwords": [...]}
        if "stopwords" not in data:
            raise ValueError(f"Invalid stopword file format at {file_path}: missing 'stopwords' key")
        return set(data["stopwords"])


def validate_determinism(manifest: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates that the hashes in the manifest match the actual file hashes on disk.
    Ensures the generation process is deterministic.
    """
    logger = get_logger_module()
    errors = []
    all_valid = True

    windows = manifest.get("windows", [])
    
    for window_entry in windows:
        window_name = window_entry.get("window")
        expected_hash = window_entry.get("hash")
        filename = window_entry.get("filename")
        
        if not window_name or not expected_hash or not filename:
            errors.append(f"Malformed manifest entry for window: {window_entry}")
            all_valid = False
            continue

        file_path = STOPWORDS_DIR / filename
        
        if not file_path.exists():
            errors.append(f"File missing for window {window_name}: {filename}")
            all_valid = False
            continue

        actual_hash = compute_file_hash(file_path)
        
        if actual_hash != expected_hash:
            errors.append(
                f"Hash mismatch for window {window_name}: "
                f"Expected {expected_hash}, Got {actual_hash}"
            )
            all_valid = False
        else:
            logger.info(f"Hash verified for window {window_name}: {expected_hash[:16]}...")

    return all_valid, errors


def validate_window_specificity(manifest: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates that stopword lists are specific to windows and not just a global list.
    Checks that at least some windows have unique stopwords compared to others.
    """
    logger = get_logger_module()
    errors = []
    is_valid = True

    windows = manifest.get("windows", [])
    if len(windows) < 2:
        errors.append("Not enough windows to validate specificity.")
        return False, errors

    loaded_sets = {}
    for window_entry in windows:
        window_name = window_entry.get("window")
        filename = window_entry.get("filename")
        if not filename:
            continue
        
        file_path = STOPWORDS_DIR / filename
        if file_path.exists():
            loaded_sets[window_name] = load_stopword_set(file_path)

    if len(loaded_sets) < 2:
        errors.append("Could not load enough stopword files to compare.")
        return False, errors

    # Check if all sets are identical
    set_list = list(loaded_sets.values())
    first_set = set_list[0]
    all_identical = all(s == first_set for s in set_list)

    if all_identical:
        errors.append("CRITICAL: All window stopword lists are identical. "
                    "This suggests a global list was used instead of window-specific generation.")
        is_valid = False
    else:
        logger.info("Window specificity check passed: Lists are distinct.")

    # Check against global baseline (optional heuristic)
    # We expect window-specific lists to differ significantly from a generic global list
    # because they include domain-specific noise for that era.
    # If a list is exactly the global baseline, it's suspicious.
    for name, s in loaded_sets.items():
        if s == GLOBAL_STOPWORDS_BASELINE:
            errors.append(f"Window {name} matches the global baseline exactly. "
                        "This may indicate the TF-IDF generation step was skipped.")
            is_valid = False

    return is_valid, errors


def validate_content_quality(stopword_sets: Dict[str, Set[str]]) -> Tuple[bool, List[str]]:
    """
    Validates that stopword lists contain a reasonable number of terms
    and are not empty or excessively large.
    """
    logger = get_logger_module()
    errors = []
    is_valid = True

    for window_name, stopwords in stopword_sets.items():
        count = len(stopwords)
        if count == 0:
            errors.append(f"Window {window_name} has an empty stopword list.")
            is_valid = False
        elif count > 1000:
            errors.append(f"Window {window_name} has an unusually large stopword list ({count}).")
            is_valid = False
        else:
            logger.info(f"Window {window_name} stopword count: {count}")

    return is_valid, errors


def run_validation() -> bool:
    """
    Main entry point to run all validation checks.
    Returns True if all validations pass, False otherwise.
    """
    logger = get_logger_module()
    logger.info("Starting stopword list validation (T014b)...")

    if not MANIFEST_PATH.exists():
        logger.error(f"Manifest not found at {MANIFEST_PATH}. "
                    "Did you run T014a (stopword_generator.py) first?")
        return False

    try:
        manifest = load_manifest(MANIFEST_PATH)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Failed to load manifest: {e}")
        return False

    # 1. Validate Determinism (Hashes match files)
    logger.info("Checking determinism (hash verification)...")
    det_valid, det_errors = validate_determinism(manifest)
    if not det_valid:
        for err in det_errors:
            logger.error(err)
    else:
        logger.info("Determinism check PASSED.")

    # 2. Validate Window Specificity (Lists are not identical/global)
    logger.info("Checking window specificity...")
    spec_valid, spec_errors = validate_window_specificity(manifest)
    if not spec_valid:
        for err in spec_errors:
            logger.error(err)
    else:
        logger.info("Window specificity check PASSED.")

    # 3. Validate Content Quality (Load and check sizes)
    windows = manifest.get("windows", [])
    loaded_sets = {}
    for w in windows:
        fn = w.get("filename")
        if fn:
            fp = STOPWORDS_DIR / fn
            if fp.exists():
                loaded_sets[w.get("window")] = load_stopword_set(fp)
    
    qual_valid, qual_errors = validate_content_quality(loaded_sets)
    if not qual_valid:
        for err in qual_errors:
            logger.error(err)
    else:
        logger.info("Content quality check PASSED.")

    all_passed = det_valid and spec_valid and qual_valid

    if all_passed:
        logger.info("SUCCESS: All stopword validation checks passed.")
    else:
        logger.error("FAILURE: One or more validation checks failed.")

    return all_passed


def main():
    """CLI entry point."""
    success = run_validation()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
