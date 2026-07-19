import argparse
import logging
import os
import random
import re
from pathlib import Path
from typing import List, Set, Tuple
import pandas as pd
import yaml

# Define the 15-word hedge lexicon as per task description
HEDGE_LEXICON = {
    "maybe", "perhaps", "possibly", "probably", "likely", "unlikely",
    "seem", "seems", "appear", "appears", "believe", "think",
    "guess", "suppose", "assume"
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_conversations(file_path: Path) -> pd.DataFrame:
    """Load conversations from a JSONL or CSV file.
    
    Args:
        file_path: Path to the input file.
        
    Returns:
        DataFrame with 'conversation_id' and 'text_content' columns.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
        
    if file_path.suffix.lower() == '.jsonl':
        df = pd.read_json(file_path, lines=True)
    elif file_path.suffix.lower() == '.csv':
        df = pd.read_csv(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
    # Ensure required columns exist
    required_cols = ['conversation_id', 'text_content']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
        
    return df

def load_ratings(file_path: Path) -> pd.DataFrame:
    """Load ratings from a CSV file.
    
    Args:
        file_path: Path to the ratings CSV file.
        
    Returns:
        DataFrame with rating information including 'gold_labels'.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Ratings file not found: {file_path}")
        
    df = pd.read_csv(file_path)
    
    # The task specifies 'gold_labels' as the source of human matches
    # If the file uses 'authenticity_score' or similar, we map it
    if 'gold_labels' not in df.columns:
        if 'authenticity_score' in df.columns:
            logger.warning("Column 'gold_labels' not found. Using 'authenticity_score' as gold_labels.")
            df['gold_labels'] = df['authenticity_score']
        else:
            raise ValueError("Ratings file must contain 'gold_labels' or 'authenticity_score' column.")
            
    return df

def tokenize_text(text: str) -> List[str]:
    """Tokenize text into lowercase words.
    
    Args:
        text: Input text string.
        
    Returns:
        List of lowercase tokens.
    """
    if not isinstance(text, str):
        return []
    # Simple regex tokenization: split on non-alphanumeric
    tokens = re.findall(r'\b\w+\b', text.lower())
    return tokens

def find_lexicon_matches(tokens: List[str], lexicon: Set[str] = None) -> Set[str]:
    """Find which lexicon words appear in the token list.
    
    Args:
        tokens: List of tokens from text.
        lexicon: Set of words to match against (defaults to HEDGE_LEXICON).
        
    Returns:
        Set of matched words found in the text.
    """
    if lexicon is None:
        lexicon = HEDGE_LEXICON
    return set(tokens).intersection(lexicon)

def sample_turns(df: pd.DataFrame, n: int = 50) -> pd.DataFrame:
    """Sample a subset of turns from the DataFrame.
    
    Args:
        df: Input DataFrame.
        n: Number of samples to return.
        
    Returns:
        DataFrame with n randomly sampled rows.
    """
    if len(df) <= n:
        return df.reset_index(drop=True)
    return df.sample(n=n, random_state=42).reset_index(drop=True)

def validate_lexicon_precision(gold_df: pd.DataFrame, lexicon: Set[str] = None) -> Tuple[float, dict]:
    """Calculate precision of the lexicon against human gold labels.
    
    Precision = (Lexicon Matches ∩ Human Matches) / Lexicon Matches
    
    For this validation:
    - 'Lexicon Matches' are words found in text using the hedge lexicon.
    - 'Human Matches' are derived from 'gold_labels' column.
      * We assume if a row has a high authenticity score (e.g., >= 4), 
        it implies the presence of specific linguistic cues (hedges) 
        that the human raters associated with authenticity.
      * Alternatively, if 'gold_labels' contains the actual words, 
        we intersect. Given the schema 'gold_labels' usually implies a score 
        in this context unless specified as 'annotated_words', 
        we interpret the task's "Human Matches" as:
        Rows where the human rated the text as containing the cue (e.g. score >= 4).
        
    However, the task says: "Input: 'Human Matches' are derived from the `gold_labels` column".
    If `gold_labels` is a numeric score (as in T001c), we need a threshold to define "Human Match".
    Let's assume a high authenticity score (>= 4.0) indicates the presence of the cue 
    (since the study is about cues affecting authenticity).
    
    Logic:
    1. For each row in gold_df:
       - Extract text tokens.
       - Find Lexicon Matches (words from HEDGE_LEXICON in text).
       - Determine Human Match: If gold_labels >= 4.0 (or if gold_labels is a list of words, check intersection).
         * Assumption based on T001c: gold_labels is likely a numeric score.
         * Interpretation: If a human rated it high, they perceived the cue.
         * Strictly speaking, "Human Matches" in the formula usually refers to the set of true positives.
         * Let's assume the "Human Match" for a specific turn is a binary flag: Did the human see the hedge?
         * If the column is numeric, we treat score >= 4 as "Human identified hedge".
    
    2. Precision = (Count of rows where Lexicon found hedge AND Human flagged hedge) 
                   / (Count of rows where Lexicon found hedge).
    
    Args:
        gold_df: DataFrame with 'text_content' and 'gold_labels'.
        lexicon: Set of hedge words.
        
    Returns:
        Tuple of (precision, detailed_stats_dict).
    """
    if lexicon is None:
        lexicon = HEDGE_LEXICON
        
    if gold_df.empty:
        return 0.0, {"error": "Empty dataframe"}
        
    lexicon_match_count = 0
    true_positive_count = 0
    stats = []
    
    for idx, row in gold_df.iterrows():
        text = str(row.get('text_content', ''))
        tokens = tokenize_text(text)
        found_lexicon_words = find_lexicon_matches(tokens, lexicon)
        
        has_lexicon_match = len(found_lexicon_words) > 0
        if has_lexicon_match:
            lexicon_match_count += 1
            
            # Determine Human Match
            # Assuming gold_labels is numeric. Threshold >= 4.0 for "Human detected cue"
            # If gold_labels is a string/list, we would need different logic, but T001c implies score.
            gold_val = row.get('gold_labels')
            if isinstance(gold_val, (int, float)) and not pd.isna(gold_val):
                is_human_match = gold_val >= 4.0
            else:
                # Fallback: if not numeric, assume no match or log warning
                is_human_match = False
                logger.warning(f"Non-numeric gold_labels at row {idx}: {gold_val}")
                
            if is_human_match:
                true_positive_count += 1
                
            stats.append({
                "row_id": idx,
                "text_preview": text[:50],
                "lexicon_found": list(found_lexicon_words),
                "human_score": gold_val,
                "is_tp": is_human_match
            })
    
    if lexicon_match_count == 0:
        precision = 0.0
    else:
        precision = true_positive_count / lexicon_match_count
        
    result = {
        "precision": precision,
        "lexicon_match_count": lexicon_match_count,
        "true_positive_count": true_positive_count,
        "sample_size": len(gold_df),
        "details": stats
    }
    
    return precision, result

def write_validation_results(results: dict, output_path: Path, precision_threshold: float = 0.8):
    """Write validation results to a YAML file.
    
    Args:
        results: Dictionary containing validation stats.
        output_path: Path to the output YAML file.
        precision_threshold: Threshold for passing validation.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    status = "PASSED" if results["precision"] >= precision_threshold else "FAILED"
    
    output_data = {
        "validation_status": status,
        "precision_threshold": precision_threshold,
        "results": results
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(output_data, f, default_flow_style=False)
        
    logger.info(f"Validation results written to {output_path}")
    logger.info(f"Status: {status} (Precision: {results['precision']:.4f})")

def main():
    """Main entry point for lexicon validation."""
    parser = argparse.ArgumentParser(description="Validate hedge lexicon precision on gold standard data.")
    parser.add_argument("--gold-standard", type=str, required=True, 
                        help="Path to the gold standard CSV file (e.g., data/processed/gold_standard_50.csv)")
    parser.add_argument("--output", type=str, required=True, 
                        help="Path to output results YAML file (e.g., data/results/lexicon_validation_results.yaml)")
    parser.add_argument("--threshold", type=float, default=0.8, 
                        help="Precision threshold for passing validation (default: 0.8)")
    
    args = parser.parse_args()
    
    gold_path = Path(args.gold_standard)
    output_path = Path(args.output)
    
    try:
        logger.info(f"Loading gold standard data from {gold_path}...")
        gold_df = load_ratings(gold_path) # Reusing load_ratings as it handles the CSV structure
        
        logger.info(f"Validating lexicon precision...")
        precision, stats = validate_lexicon_precision(gold_df)
        
        logger.info(f"Calculated Precision: {precision:.4f}")
        
        write_validation_results(stats, output_path, args.threshold)
        
        if precision < args.threshold:
            logger.warning(f"Precision {precision:.4f} is below threshold {args.threshold}. Dataset flagged for review.")
            return 1
        else:
            logger.info("Validation passed.")
            return 0
            
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        raise

if __name__ == "__main__":
    main()
