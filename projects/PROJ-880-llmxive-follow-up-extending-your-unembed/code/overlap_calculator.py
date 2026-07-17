"""
Overlap Calculator for User Story 2.

Implements overlap ratio calculation between English and non-English
top-ranked token lists as specified in T022.
"""
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from config import load_config, get_path, get_hyperparameter, ensure_dirs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_token_rankings(config: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Load token rankings from the token attribution report.

    Args:
        config: Configuration dictionary containing paths.

    Returns:
        Dictionary mapping language codes to lists of top-ranked tokens.

    Raises:
        FileNotFoundError: If the token attribution report does not exist.
        ValueError: If the report format is invalid.
    """
    report_path = get_path(config, "processed_token_attribution_report")
    logger.info(f"Loading token rankings from: {report_path}")

    if not Path(report_path).exists():
        raise FileNotFoundError(
            f"Token attribution report not found at {report_path}. "
            "Run the token attribution pipeline (T023) first."
        )

    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)

    if 'token_rankings' not in report:
        raise ValueError(
            f"Invalid token attribution report format. "
            "Expected 'token_rankings' key, got: {list(report.keys())}"
        )

    rankings = report['token_rankings']
    logger.info(f"Loaded rankings for languages: {list(rankings.keys())}")

    return rankings


def calculate_overlap_ratio(
    list_a: List[str],
    list_b: List[str],
    k: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calculate the overlap ratio between two lists of top-ranked tokens.

    The overlap ratio is defined as:
        overlap_ratio = |A ∩ B| / min(|A|, |B|)

    where A and B are the sets of top-k tokens from each list.

    Args:
        list_a: First list of tokens (e.g., English).
        list_b: Second list of tokens (e.g., French or Chinese).
        k: Number of top tokens to consider. If None, uses the full list.

    Returns:
        Dictionary containing:
            - 'overlap_count': Number of overlapping tokens
            - 'ratio': Overlap ratio (float between 0 and 1)
            - 'size_a': Size of list A (after truncation if k provided)
            - 'size_b': Size of list B (after truncation if k provided)
            - 'overlap_tokens': List of tokens present in both lists
    """
    if k is not None:
        list_a = list_a[:k]
        list_b = list_b[:k]

    set_a = set(list_a)
    set_b = set(list_b)

    intersection = set_a.intersection(set_b)
    union = set_a.union(set_b)

    overlap_count = len(intersection)
    min_size = min(len(list_a), len(list_b))
    max_size = max(len(list_a), len(list_b))

    # Handle edge case of empty lists
    if min_size == 0:
        ratio = 0.0
    else:
        ratio = overlap_count / min_size

    return {
        'overlap_count': overlap_count,
        'ratio': ratio,
        'size_a': len(list_a),
        'size_b': len(list_b),
        'overlap_tokens': sorted(list(intersection)),
        'jaccard_index': overlap_count / len(union) if union else 0.0
    }


def generate_overlap_report(
    config: Dict[str, Any],
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive overlap report comparing English
    and non-English token rankings.

    Args:
        config: Configuration dictionary containing paths and hyperparameters.
        output_path: Optional path to write the report. If None, uses config.

    Returns:
        Dictionary containing overlap metrics for all language pairs.
    """
    rankings = load_token_rankings(config)
    k = get_hyperparameter(config, "top_k_tokens")

    logger.info(f"Calculating overlap ratios for top {k} tokens")

    # Identify English and non-English languages
    # Assuming 'en' is the English baseline
    languages = list(rankings.keys())
    if 'en' not in languages:
        raise ValueError(
            f"English ('en') not found in token rankings. "
            f"Available languages: {languages}. "
            "The token attribution pipeline must include English baseline."
        )

    en_rankings = rankings['en']
    non_en_languages = [lang for lang in languages if lang != 'en']

    if not non_en_languages:
        logger.warning("No non-English languages found in token rankings.")
        return {
            'baseline_language': 'en',
            'comparisons': {},
            'k': k,
            'message': 'No non-English languages to compare.'
        }

    comparisons = {}

    for lang in non_en_languages:
        logger.info(f"Comparing English vs {lang}")
        lang_rankings = rankings[lang]

        overlap_result = calculate_overlap_ratio(
            en_rankings,
            lang_rankings,
            k=k
        )

        comparisons[lang] = {
            'overlap_ratio': overlap_result['ratio'],
            'overlap_count': overlap_result['overlap_count'],
            'jaccard_index': overlap_result['jaccard_index'],
            'top_k': k,
            'shared_tokens_sample': overlap_result['overlap_tokens'][:10]
        }

        logger.info(
            f"  Overlap ratio (en vs {lang}): {overlap_result['ratio']:.4f} "
            f"({overlap_result['overlap_count']} shared tokens)"
        )

    # Calculate aggregate statistics
    if comparisons:
        overlap_ratios = [c['overlap_ratio'] for c in comparisons.values()]
        avg_overlap = np.mean(overlap_ratios)
        std_overlap = np.std(overlap_ratios)
        min_overlap = np.min(overlap_ratios)
        max_overlap = np.max(overlap_ratios)

        aggregate = {
            'average_overlap_ratio': avg_overlap,
            'std_overlap_ratio': std_overlap,
            'min_overlap_ratio': min_overlap,
            'max_overlap_ratio': max_overlap,
            'languages_compared': len(comparisons)
        }
    else:
        aggregate = {
            'average_overlap_ratio': 0.0,
            'std_overlap_ratio': 0.0,
            'min_overlap_ratio': 0.0,
            'max_overlap_ratio': 0.0,
            'languages_compared': 0
        }

    report = {
        'baseline_language': 'en',
        'comparisons': comparisons,
        'aggregate_statistics': aggregate,
        'k': k,
        'timestamp': config.get('timestamp', 'unknown')
    }

    # Write report to disk
    if output_path is None:
        output_path = get_path(config, "overlap_report")

    ensure_dirs(config)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"Overlap report written to: {output_path}")

    return report


def main():
    """Main entry point for the overlap calculator."""
    config = load_config()
    logger.info("Starting overlap ratio calculation")

    try:
        report = generate_overlap_report(config)

        # Print summary to stdout
        print("\n" + "="*60)
        print("OVERLAP RATIO SUMMARY")
        print("="*60)
        print(f"Baseline language: {report['baseline_language']}")
        print(f"Top K tokens: {report['k']}")
        print(f"Languages compared: {report['aggregate_statistics']['languages_compared']}")
        print("-"*60)

        for lang, metrics in report['comparisons'].items():
            print(f"{lang}:")
            print(f"  Overlap Ratio: {metrics['overlap_ratio']:.4f}")
            print(f"  Shared Tokens: {metrics['overlap_count']}")
            print(f"  Jaccard Index: {metrics['jaccard_index']:.4f}")
            if metrics['shared_tokens_sample']:
                print(f"  Sample Shared: {', '.join(metrics['shared_tokens_sample'][:5])}")

        print("-"*60)
        print(f"Average Overlap: {report['aggregate_statistics']['average_overlap_ratio']:.4f}")
        print(f"Std Overlap: {report['aggregate_statistics']['std_overlap_ratio']:.4f}")
        print("="*60 + "\n")

        return 0

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid data format: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())
