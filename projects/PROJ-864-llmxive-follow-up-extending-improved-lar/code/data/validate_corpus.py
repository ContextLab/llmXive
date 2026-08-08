"""
Corpus Validation Module for llmXive Follow-up Project.

This module validates the processed micro-corpus by checking:
1. Token count bounds (target ± 10,000)
2. HumanEval exclusion verification
3. Data integrity checks

Outputs a validation report to data/artifacts/corpus_validation.json
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import (
    get_project_root,
    get_processed_dir,
    get_artifacts_dir,
    get_token_limit,
    get_config,
    ConfigError
)
from utils.logging import get_logger, info, error, warning, debug
from utils.monitor import get_ram_usage_gb
from tests.test_human_eval_exclusion import load_human_eval_samples, compute_text_fingerprint, load_corpus_samples, check_exclusion

logger = get_logger(__name__)

def load_processed_corpus(corpus_path: str = None) -> List[Dict[str, Any]]:
    """
    Load the processed corpus from JSONL file.

    Args:
        corpus_path: Path to the JSONL file. If None, uses default from config.

    Returns:
        List of dictionaries containing corpus entries.

    Raises:
        FileNotFoundError: If the corpus file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if corpus_path is None:
        processed_dir = get_processed_dir()
        corpus_path = str(processed_dir / "micro_corpus.jsonl")

    if not os.path.exists(corpus_path):
        error(f"Corpus file not found: {corpus_path}")
        raise FileNotFoundError(f"Corpus file not found: {corpus_path}")

    logger.info(f"Loading processed corpus from: {corpus_path}")
    corpus = []

    with open(corpus_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                corpus.append(entry)
            except json.JSONDecodeError as e:
                error(f"Invalid JSON at line {line_num}: {e}")
                raise

    logger.info(f"Loaded {len(corpus)} entries from corpus")
    return corpus

def verify_token_bounds(corpus: List[Dict[str, Any]], tolerance: int = 10000) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify that the total token count is within the target ± tolerance.

    Args:
        corpus: List of corpus entries.
        tolerance: Acceptable deviation from target (default 10,000).

    Returns:
        Tuple of (passed, details_dict)
    """
    logger.info("Verifying token bounds...")

    target_tokens = get_token_limit()
    total_tokens = 0
    entry_counts = []

    for i, entry in enumerate(corpus):
        if 'token_count' in entry:
            count = entry['token_count']
        elif 'tokens' in entry:
            # Count tokens if stored as list
            count = len(entry['tokens']) if isinstance(entry['tokens'], list) else 0
        else:
            # Fallback: estimate based on text length (approximate)
            text = entry.get('text', '')
            count = len(text.split())  # Rough word count approximation

        total_tokens += count
        entry_counts.append(count)

        # Log progress for large datasets
        if (i + 1) % 10000 == 0:
            debug(f"Processed {i + 1} entries, cumulative tokens: {total_tokens}")

    min_bound = target_tokens - tolerance
    max_bound = target_tokens + tolerance
    passed = min_bound <= total_tokens <= max_bound

    details = {
        "target_tokens": target_tokens,
        "actual_tokens": total_tokens,
        "tolerance": tolerance,
        "min_bound": min_bound,
        "max_bound": max_bound,
        "passed": passed,
        "entry_count": len(corpus),
        "avg_tokens_per_entry": total_tokens / len(corpus) if corpus else 0,
        "min_tokens_in_entry": min(entry_counts) if entry_counts else 0,
        "max_tokens_in_entry": max(entry_counts) if entry_counts else 0
    }

    if passed:
        info(f"Token count validation PASSED: {total_tokens} tokens (target: {target_tokens} ± {tolerance})")
    else:
        error(f"Token count validation FAILED: {total_tokens} tokens (target: {target_tokens} ± {tolerance})")

    return passed, details

def verify_human_eval_exclusion(corpus: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify that HumanEval data is excluded from the corpus.

    Args:
        corpus: List of corpus entries.

    Returns:
        Tuple of (passed, details_dict)
    """
    logger.info("Verifying HumanEval exclusion...")

    # Load HumanEval samples
    human_eval_samples = load_human_eval_samples()
    if not human_eval_samples:
        error("Failed to load HumanEval samples for exclusion check")
        return False, {
            "passed": False,
            "error": "Failed to load HumanEval samples",
            "human_eval_count": 0,
            "corpus_count": len(corpus),
            "overlaps_found": 0
        }

    # Load corpus samples for fingerprinting
    corpus_samples = load_corpus_samples(corpus, sample_size=min(1000, len(corpus)))

    # Check for exclusions
    overlaps_found, overlap_details = check_exclusion(human_eval_samples, corpus_samples)

    passed = overlaps_found == 0

    details = {
        "passed": passed,
        "human_eval_count": len(human_eval_samples),
        "corpus_count": len(corpus),
        "corpus_samples_checked": len(corpus_samples),
        "overlaps_found": overlaps_found,
        "overlap_details": overlap_details[:10] if overlap_details else []  # Limit detail size
    }

    if passed:
        info("HumanEval exclusion validation PASSED: No overlaps found")
    else:
        error(f"HumanEval exclusion validation FAILED: {overlaps_found} overlaps found")

    return passed, details

def generate_validation_report(token_check: Dict[str, Any], human_eval_check: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a comprehensive validation report.

    Args:
        token_check: Results from token bounds verification.
        human_eval_check: Results from HumanEval exclusion verification.

    Returns:
        Complete validation report dictionary.
    """
    overall_passed = token_check["passed"] and human_eval_check["passed"]

    report = {
        "validation_timestamp": str(Path(__file__).parent.parent / "data" / "artifacts"),  # Will be replaced with actual timestamp
        "project_root": str(get_project_root()),
        "overall_status": "PASSED" if overall_passed else "FAILED",
        "overall_passed": overall_passed,
        "checks": {
            "token_bounds": token_check,
            "human_eval_exclusion": human_eval_check
        },
        "summary": {
            "total_entries": token_check.get("entry_count", 0),
            "total_tokens": token_check.get("actual_tokens", 0),
            "human_eval_overlaps": human_eval_check.get("overlaps_found", 0),
            "ram_usage_gb": get_ram_usage_gb()
        }
    }

    # Add timestamp
    from datetime import datetime
    report["validation_timestamp"] = datetime.now().isoformat()

    return report

def save_validation_report(report: Dict[str, Any], output_path: str = None) -> str:
    """
    Save the validation report to a JSON file.

    Args:
        report: The validation report dictionary.
        output_path: Path for the output file. If None, uses default.

    Returns:
        Path to the saved file.
    """
    if output_path is None:
        artifacts_dir = get_artifacts_dir()
        output_path = str(artifacts_dir / "corpus_validation.json")

    # Ensure directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving validation report to: {output_path}")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Validation report saved successfully")
    return output_path

def main():
    """
    Main entry point for corpus validation.
    """
    logger.info("Starting corpus validation...")

    try:
        # Load corpus
        corpus = load_processed_corpus()
        if not corpus:
            error("Corpus is empty. Validation cannot proceed.")
            return 1

        # Verify token bounds
        token_passed, token_details = verify_token_bounds(corpus)

        # Verify HumanEval exclusion
        human_eval_passed, human_eval_details = verify_human_eval_exclusion(corpus)

        # Generate report
        report = generate_validation_report(token_details, human_eval_details)

        # Save report
        output_path = save_validation_report(report)

        # Print summary
        print("\n" + "="*60)
        print("CORPUS VALIDATION SUMMARY")
        print("="*60)
        print(f"Overall Status: {report['overall_status']}")
        print(f"Token Bounds Check: {'PASSED' if token_passed else 'FAILED'}")
        print(f"  - Target: {token_details['target_tokens']} ± {token_details['tolerance']}")
        print(f"  - Actual: {token_details['actual_tokens']}")
        print(f"HumanEval Exclusion Check: {'PASSED' if human_eval_passed else 'FAILED'}")
        print(f"  - Overlaps found: {human_eval_details['overlaps_found']}")
        print(f"Report saved to: {output_path}")
        print("="*60 + "\n")

        return 0 if report['overall_passed'] else 1

    except FileNotFoundError as e:
        error(f"File not found: {e}")
        return 1
    except Exception as e:
        error(f"Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
