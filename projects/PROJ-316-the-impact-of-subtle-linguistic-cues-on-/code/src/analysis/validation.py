"""
Lexicon Validation Module.

Implements pragmatic validation logic for the hedge lexicon by comparing
automated lexicon matches against human-annotated hedge flags.
"""
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional

import pandas as pd

# The predefined 15-word hedge lexicon as defined in T010
HEDGE_LEXICON: Set[str] = {
    "maybe", "perhaps", "possibly", "probably", "likely", "unlikely",
    "seem", "seems", "appear", "appears", "believe", "think",
    "guess", "suppose", "assume"
}

logger = logging.getLogger(__name__)


def tokenize_text(text: str) -> List[str]:
    """
    Tokenize text into a list of words (lowercased, stripped of punctuation).
    
    Args:
        text: Raw text string.
        
    Returns:
        List of tokenized words.
    """
    if not text or not isinstance(text, str):
        return []
    
    # Simple tokenization: lowercase and split on non-alphanumeric
    # This matches the simple lexicon matching approach
    tokens = re.findall(r'\b\w+\b', text.lower())
    return tokens


def find_lexicon_matches(tokens: List[str]) -> Set[int]:
    """
    Find indices of tokens that match the hedge lexicon.
    
    Args:
        tokens: List of tokenized words.
        
    Returns:
        Set of indices where hedge words were found.
    """
    matches = set()
    for idx, token in enumerate(tokens):
        if token in HEDGE_LEXICON:
            matches.add(idx)
    return matches


def parse_human_hedge_flags(flags_str: str) -> Set[int]:
    """
    Parse the human hedge flags from the CSV column.
    
    The column contains a JSON-formatted string of word indices.
    
    Args:
        flags_str: String like "[2, 5]" or "[]".
        
    Returns:
        Set of integer indices.
    """
    if not flags_str or flags_str.strip() == "":
        return set()
    
    try:
        # Handle potential string formatting issues
        flags_str = flags_str.strip()
        if not flags_str.startswith("["):
            flags_str = f"[{flags_str}]"
        
        indices = json.loads(flags_str)
        if isinstance(indices, list):
            return set(int(i) for i in indices)
        elif isinstance(indices, int):
            return {indices}
        else:
            logger.warning(f"Unexpected hedge flag format: {flags_str}")
            return set()
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse hedge flags '{flags_str}': {e}")
        return set()


def validate_lexicon_precision(
    ratings_path: str,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate the precision of the hedge lexicon against human annotations.
    
    Precision = (Lexicon Matches ∩ Human Matches) / Lexicon Matches
    
    This function loads the human-annotated hedge flags from the gold standard
    dataset, compares them against automated lexicon matches, and calculates
    the precision metric.
    
    Args:
        ratings_path: Path to `data/processed/hedge_gold_standard.csv`.
        output_path: Optional path to write results YAML. If None, results are
                    returned as a dict only.
                    
    Returns:
        Dictionary containing validation metrics:
        - precision: float (0.0 to 1.0)
        - total_lexicon_matches: int
        - total_human_matches: int
        - true_positives: int
        - false_positives: int
        - false_negatives: int
        - sample_size: int
        - details: List of per-sample results
        
    Raises:
        FileNotFoundError: If the ratings file does not exist.
        ValueError: If required columns are missing.
    """
    ratings_path = Path(ratings_path)
    if not ratings_path.exists():
        raise FileNotFoundError(f"Hedge gold standard file not found: {ratings_path}")
    
    logger.info(f"Loading hedge gold standard from {ratings_path}")
    df = pd.read_csv(ratings_path)
    
    # Validate required columns
    required_cols = {"conversation_id", "text_content", "hedge_flags"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns in {ratings_path}: {missing_cols}")
    
    if df.empty:
        logger.warning("Hedge gold standard file is empty")
        return {
            "precision": 0.0,
            "total_lexicon_matches": 0,
            "total_human_matches": 0,
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "sample_size": 0,
            "details": []
        }
    
    logger.info(f"Processing {len(df)} samples for lexicon validation")
    
    total_lexicon_matches = 0
    total_human_matches = 0
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    
    details = []
    
    for idx, row in df.iterrows():
        text = row["text_content"]
        human_flags_str = str(row["hedge_flags"])
        
        # Tokenize text
        tokens = tokenize_text(text)
        
        # Find lexicon matches
        lexicon_matches = find_lexicon_matches(tokens)
        
        # Parse human matches
        human_matches = parse_human_hedge_flags(human_flags_str)
        
        # Calculate metrics for this sample
        intersection = lexicon_matches & human_matches
        union = lexicon_matches | human_matches
        
        tp = len(intersection)
        fp = len(lexicon_matches - human_matches)
        fn = len(human_matches - lexicon_matches)
        
        total_lexicon_matches += len(lexicon_matches)
        total_human_matches += len(human_matches)
        true_positives += tp
        false_positives += fp
        false_negatives += fn
        
        # Record details
        details.append({
            "conversation_id": row["conversation_id"],
            "lexicon_count": len(lexicon_matches),
            "human_count": len(human_matches),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn
        })
    
    # Calculate overall precision
    if total_lexicon_matches > 0:
        precision = true_positives / total_lexicon_matches
    else:
        precision = 0.0
    
    # Calculate recall for additional context
    if total_human_matches > 0:
        recall = true_positives / total_human_matches
    else:
        recall = 0.0
    
    results = {
        "precision": precision,
        "recall": recall,
        "total_lexicon_matches": total_lexicon_matches,
        "total_human_matches": total_human_matches,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "sample_size": len(df),
        "details": details
    }
    
    logger.info(f"Lexicon validation complete: Precision={precision:.4f}, Recall={recall:.4f}")
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write results as YAML-like text (simple key-value format)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Lexicon Validation Results\n")
            f.write(f"precision: {precision:.4f}\n")
            f.write(f"recall: {recall:.4f}\n")
            f.write(f"total_lexicon_matches: {total_lexicon_matches}\n")
            f.write(f"total_human_matches: {total_human_matches}\n")
            f.write(f"true_positives: {true_positives}\n")
            f.write(f"false_positives: {false_positives}\n")
            f.write(f"false_negatives: {false_negatives}\n")
            f.write(f"sample_size: {len(df)}\n")
            f.write("\n# Per-sample details\n")
            for d in details:
                f.write(f"- conversation_id: {d['conversation_id']}\n")
                f.write(f"  lexicon_count: {d['lexicon_count']}\n")
                f.write(f"  human_count: {d['human_count']}\n")
                f.write(f"  true_positives: {d['true_positives']}\n")
                f.write(f"  false_positives: {d['false_positives']}\n")
                f.write(f"  false_negatives: {d['false_negatives']}\n")
    
    return results


def main():
    """
    Main entry point for running lexicon validation.
    
    Usage: python -m src.analysis.validation --input data/processed/hedge_gold_standard.csv
    """
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Validate hedge lexicon precision")
    parser.add_argument(
        "--input", 
        type=str, 
        required=True,
        help="Path to hedge_gold_standard.csv"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/results/lexicon_validation_results.yaml",
        help="Path to output results file"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    try:
        results = validate_lexicon_precision(args.input, args.output)
        
        print(f"\nValidation Results:")
        print(f"  Precision: {results['precision']:.4f}")
        print(f"  Recall: {results['recall']:.4f}")
        print(f"  True Positives: {results['true_positives']}")
        print(f"  False Positives: {results['false_positives']}")
        print(f"  False Negatives: {results['false_negatives']}")
        print(f"  Sample Size: {results['sample_size']}")
        print(f"\nResults written to: {args.output}")
        
        # Exit with error if precision is below threshold (0.8)
        if results['precision'] < 0.8:
            print(f"\n⚠️  WARNING: Precision ({results['precision']:.4f}) is below threshold (0.8)")
            print("Proceeding to T001e (Remediation) may be required.")
            sys.exit(1)
        else:
            print(f"\n✓ Lexicon validation PASSED (precision >= 0.8)")
            sys.exit(0)
            
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
    except ValueError as e:
        print(f"VALIDATION ERROR: {e}", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        logging.exception("Unexpected error during validation")
        sys.exit(4)


if __name__ == "__main__":
    main()
