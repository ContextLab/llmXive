"""
Hedge feature extraction module.

Extracts hedge counts and hedge ratios from conversation text using a predefined
lexicon of 15 hedge words.
"""
import argparse
import logging
import json
from pathlib import Path
from typing import Set, Optional, Dict, Any
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Ensure required NLTK data is available
try:
    stopwords.words('english')
except LookupError:
    nltk.download('stopwords', quiet=True)
try:
    word_tokenize("test")
except LookupError:
    nltk.download('punkt', quiet=True)

# Predefined 15-word hedge lexicon as per task specification
HEDGE_LEXICON: Set[str] = {
    "maybe", "perhaps", "possibly", "probably", "likely", "unlikely",
    "seem", "seems", "appear", "appears", "believe", "think",
    "guess", "suppose", "assume"
}

logger = logging.getLogger(__name__)

def calculate_hedge_density(text: str, lexicon: Optional[Set[str]] = None) -> int:
    """
    Count the number of hedge words in a given text.
    
    Args:
        text: Input text string to analyze.
        lexicon: Optional set of hedge words. Defaults to HEDGE_LEXICON.
    
    Returns:
        int: Count of hedge words found in the text.
    """
    if lexicon is None:
        lexicon = HEDGE_LEXICON
    
    if not text or not isinstance(text, str):
        return 0
    
    # Tokenize and lowercase
    try:
        tokens = word_tokenize(text.lower())
    except Exception as e:
        logger.warning(f"Tokenization failed for text of length {len(text)}: {e}")
        return 0
    
    # Count matches
    count = sum(1 for token in tokens if token in lexicon)
    return count

def extract_hedge_features(
    df: pd.DataFrame,
    text_column: str = "text_content",
    id_column: str = "conversation_id",
    lexicon: Optional[Set[str]] = None
) -> pd.DataFrame:
    """
    Extract hedge features (count and ratio) from a DataFrame of conversations.
    
    Args:
        df: DataFrame containing conversation text and IDs.
        text_column: Name of the column containing text content.
        id_column: Name of the column containing conversation IDs.
        lexicon: Optional set of hedge words.
    
    Returns:
        DataFrame with added columns: 'hedge_count', 'hedge_ratio'.
        - hedge_count: Number of hedge words found.
        - hedge_ratio: hedge_count / total_word_count.
    
    Raises:
        ValueError: If required columns are missing.
    """
    if lexicon is None:
        lexicon = HEDGE_LEXICON
    
    if text_column not in df.columns:
        raise ValueError(f"Missing required column: {text_column}")
    if id_column not in df.columns:
        raise ValueError(f"Missing required column: {id_column}")
    
    logger.info(f"Extracting hedge features from column '{text_column}' using lexicon of size {len(lexicon)}")
    
    hedge_counts = []
    word_counts = []
    
    for idx, row in df.iterrows():
        text = row[text_column]
        if not text or not isinstance(text, str):
            hedge_counts.append(0)
            word_counts.append(0)
            continue
        
        try:
            tokens = word_tokenize(text.lower())
            total_words = len(tokens)
            hedge_count = sum(1 for token in tokens if token in lexicon)
        except Exception as e:
            logger.warning(f"Processing failed for row {idx}: {e}")
            hedge_count = 0
            total_words = 0
        
        hedge_counts.append(hedge_count)
        word_counts.append(total_words)
    
    result_df = df.copy()
    result_df['hedge_count'] = hedge_counts
    
    # Calculate ratio (avoid division by zero)
    result_df['hedge_ratio'] = result_df.apply(
        lambda row: row['hedge_count'] / row['hedge_count'] if row['hedge_count'] > 0 and row['hedge_count'] == row['hedge_count'] else (row['hedge_count'] / max(1, word_counts[result_df.index.get_loc(row.name)])) if max(1, word_counts[result_df.index.get_loc(row.name)]) > 0 else 0.0,
        axis=1
    )
    
    # Recalculate ratio correctly using the stored word_counts list
    # The previous apply logic was complex; let's do it cleanly
    ratio_list = []
    for i, h_count in enumerate(hedge_counts):
        w_count = word_counts[i]
        if w_count > 0:
            ratio_list.append(h_count / w_count)
        else:
            ratio_list.append(0.0)
    
    result_df['hedge_ratio'] = ratio_list
    
    logger.info(f"Extraction complete. Processed {len(df)} rows. Max hedge count: {max(hedge_counts) if hedge_counts else 0}")
    
    return result_df

def main():
    """
    CLI entry point for hedge extraction.
    Reads from data/raw/conversations.jsonl and writes to data/processed/hedge_features.csv.
    """
    parser = argparse.ArgumentParser(description="Extract hedge features from conversations.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw/conversations.jsonl",
        help="Path to input JSONL file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/hedge_features.csv",
        help="Path to output CSV file."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level."
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info(f"Loading conversations from {input_path}")
    records = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                records.append(record)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
    
    if not records:
        logger.error("No valid records found in input file.")
        raise ValueError("No valid records found in input file.")
    
    df = pd.DataFrame(records)
    
    # Determine column names dynamically or use defaults
    # Assuming standard schema: 'conversation_id', 'text_content'
    # If 'text_content' is missing, try 'text' or 'content'
    text_col = "text_content"
    if text_col not in df.columns:
        if "text" in df.columns:
            text_col = "text"
        elif "content" in df.columns:
            text_col = "content"
        else:
            available_cols = ", ".join(df.columns)
            logger.error(f"Could not find text column. Available columns: {available_cols}")
            raise ValueError(f"Could not find text column. Available: {available_cols}")
    
    id_col = "conversation_id"
    if id_col not in df.columns:
        if "id" in df.columns:
            id_col = "id"
        else:
            available_cols = ", ".join(df.columns)
            logger.error(f"Could not find ID column. Available columns: {available_cols}")
            raise ValueError(f"Could not find ID column. Available: {available_cols}")
    
    logger.info(f"Using text column: '{text_col}', ID column: '{id_col}'")
    
    # Extract features
    result_df = extract_hedge_features(df, text_column=text_col, id_column=id_col)
    
    # Select and order columns for output
    output_cols = [id_col, text_col, "hedge_count", "hedge_ratio"]
    # Only include columns that exist
    final_cols = [c for c in output_cols if c in result_df.columns]
    result_df = result_df[final_cols]
    
    # Save to CSV
    result_df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote hedge features to {output_path}")
    logger.info(f"Output shape: {result_df.shape}")
    logger.info(f"Columns: {list(result_df.columns)}")

if __name__ == "__main__":
    main()