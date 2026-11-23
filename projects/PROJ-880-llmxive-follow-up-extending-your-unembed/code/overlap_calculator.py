"""
Overlap Calculator for Cross-Lingual Token Shift Analysis.

Implements T022: Calculate overlap ratio between English and non-English
top-ranked token lists, outputting results to data/processed/token_overlap.json.

Requires: T021 (Token Ranking) which produces token ranking files.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np

from config import load_config, get_path, get_hyperparameter, ensure_dirs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_token_rankings(
    en_ranking_path: Path,
    fr_ranking_path: Path,
    zh_ranking_path: Path,
    top_n: int
) -> Tuple[List[str], List[str], List[str]]:
    """
    Load top-ranked tokens from attribution reports for English, French, and Chinese.
    
    Args:
        en_ranking_path: Path to English token attribution report
        fr_ranking_path: Path to French token attribution report
        zh_ranking_path: Path to Chinese token attribution report
        top_n: Number of top tokens to extract from each list
        
    Returns:
        Tuple of (en_tokens, fr_tokens, zh_tokens) lists
        
    Raises:
        FileNotFoundError: If any ranking file does not exist
        ValueError: If files are malformed or missing required fields
    """
    def extract_top_tokens(file_path: Path, language: str) -> List[str]:
        if not file_path.exists():
            raise FileNotFoundError(f"Ranking file not found for {language}: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'top_tokens' not in data:
            raise ValueError(f"Missing 'top_tokens' field in {language} ranking file")
        
        tokens = [item['token'] for item in data['top_tokens']]
        
        if len(tokens) < top_n:
            logger.warning(
                f"Language {language} has only {len(tokens)} tokens, "
                f"requested top {top_n}. Using available tokens."
            )
        
        return tokens[:top_n]
    
    en_tokens = extract_top_tokens(en_ranking_path, "English")
    fr_tokens = extract_top_tokens(fr_ranking_path, "French")
    zh_tokens = extract_top_tokens(zh_ranking_path, "Chinese")
    
    return en_tokens, fr_tokens, zh_tokens


def calculate_overlap_ratio(
    base_tokens: List[str],
    comparison_tokens: List[str]
) -> float:
    """
    Calculate the overlap ratio between two token lists.
    
    Overlap ratio = |intersection| / |union|
    This is the Jaccard similarity coefficient.
    
    Args:
        base_tokens: Base token list (e.g., English)
        comparison_tokens: Comparison token list (e.g., French or Chinese)
        
    Returns:
        Float between 0.0 and 1.0 representing overlap ratio
    """
    base_set = set(base_tokens)
    comparison_set = set(comparison_tokens)
    
    if not base_set or not comparison_set:
        logger.warning("One or both token sets are empty. Returning 0.0 overlap.")
        return 0.0
    
    intersection = base_set & comparison_set
    union = base_set | comparison_set
    
    overlap_ratio = len(intersection) / len(union)
    
    logger.info(
        f"Overlap calculation: |intersection|={len(intersection)}, "
        f"|union|={len(union)}, ratio={overlap_ratio:.4f}"
    )
    
    return overlap_ratio


def generate_overlap_report(
    en_tokens: List[str],
    fr_tokens: List[str],
    zh_tokens: List[str],
    top_n: int
) -> Dict[str, Any]:
    """
    Generate the complete overlap report for all language pairs.
    
    Args:
        en_tokens: List of top English tokens
        fr_tokens: List of top French tokens
        zh_tokens: List of top Chinese tokens
        top_n: Number of tokens used for comparison
        
    Returns:
        Dictionary containing overlap ratios for all language pairs
    """
    # Calculate pairwise overlaps
    en_fr_overlap = calculate_overlap_ratio(en_tokens, fr_tokens)
    en_zh_overlap = calculate_overlap_ratio(en_tokens, zh_tokens)
    fr_zh_overlap = calculate_overlap_ratio(fr_tokens, zh_tokens)
    
    # Calculate average cross-lingual overlap (non-English vs English)
    non_en_overlaps = [en_fr_overlap, en_zh_overlap]
    avg_non_en_overlap = np.mean(non_en_overlaps)
    
    report = {
        "top_n": top_n,
        "language_pairs": {
            "en_fr": {
                "overlap_ratio": round(en_fr_overlap, 6),
                "base_tokens_count": len(en_tokens),
                "comparison_tokens_count": len(fr_tokens),
                "intersection_count": len(set(en_tokens) & set(fr_tokens)),
                "union_count": len(set(en_tokens) | set(fr_tokens))
            },
            "en_zh": {
                "overlap_ratio": round(en_zh_overlap, 6),
                "base_tokens_count": len(en_tokens),
                "comparison_tokens_count": len(zh_tokens),
                "intersection_count": len(set(en_tokens) & set(zh_tokens)),
                "union_count": len(set(en_tokens) | set(zh_tokens))
            },
            "fr_zh": {
                "overlap_ratio": round(fr_zh_overlap, 6),
                "base_tokens_count": len(fr_tokens),
                "comparison_tokens_count": len(zh_tokens),
                "intersection_count": len(set(fr_tokens) & set(zh_tokens)),
                "union_count": len(set(fr_tokens) | set(zh_tokens))
            }
        },
        "summary": {
            "avg_en_vs_non_en_overlap": round(avg_non_en_overlap, 6),
            "min_overlap": round(min(non_en_overlaps), 6),
            "max_overlap": round(max(non_en_overlaps), 6)
        },
        "top_tokens": {
            "en": en_tokens[:min(top_n, 10)],  # Preview first 10
            "fr": fr_tokens[:min(top_n, 10)],
            "zh": zh_tokens[:min(top_n, 10)]
        }
    }
    
    return report


def main():
    """
    Main entry point for T022: Overlap ratio calculation.
    
    Reads token attribution reports from T021, calculates overlap ratios
    between English and non-English token lists, and outputs results to
    data/processed/token_overlap.json.
    """
    logger.info("Starting T022: Overlap ratio calculation")
    
    # Load configuration
    config = load_config()
    
    # Get paths from config
    output_dir = get_path("processed_data_dir")
    top_n = get_hyperparameter("top_n_tokens", default=100)
    
    # Ensure output directory exists
    ensure_dirs([output_dir])
    
    # Define input paths (generated by T021)
    en_ranking_path = get_path("en_token_attribution_report")
    fr_ranking_path = get_path("fr_token_attribution_report")
    zh_ranking_path = get_path("zh_token_attribution_report")
    
    # Define output path
    output_path = output_dir / "token_overlap.json"
    
    logger.info(f"Input paths: EN={en_ranking_path}, FR={fr_ranking_path}, ZH={zh_ranking_path}")
    logger.info(f"Output path: {output_path}")
    logger.info(f"Top N tokens: {top_n}")
    
    try:
        # Load token rankings
        en_tokens, fr_tokens, zh_tokens = load_token_rankings(
            en_ranking_path, fr_ranking_path, zh_ranking_path, top_n
        )
        
        logger.info(
            f"Loaded {len(en_tokens)} EN, {len(fr_tokens)} FR, {len(zh_tokens)} ZH tokens"
        )
        
        # Generate overlap report
        report = generate_overlap_report(en_tokens, fr_tokens, zh_tokens, top_n)
        
        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully wrote overlap report to {output_path}")
        
        # Log summary
        logger.info(f"EN-FR overlap: {report['language_pairs']['en_fr']['overlap_ratio']:.4f}")
        logger.info(f"EN-ZH overlap: {report['language_pairs']['en_zh']['overlap_ratio']:.4f}")
        logger.info(f"Average EN vs Non-EN overlap: {report['summary']['avg_en_vs_non_en_overlap']:.4f}")
        
        return report
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        logger.error("Ensure T021 has completed and generated the token attribution reports.")
        raise
    except Exception as e:
        logger.error(f"Error during overlap calculation: {e}")
        raise


if __name__ == "__main__":
    main()
