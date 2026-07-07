"""
Pronoun extraction module for US1.
Calculates the rate of first-person pronouns relative to total words using spaCy.
"""
import logging
import re
from typing import List, Optional, Tuple

import pandas as pd
import spacy
from spacy.language import Language

# Configure logging
logger = logging.getLogger(__name__)

# Load spaCy model (cached globally to avoid reloading on every call)
_nlp: Optional[Language] = None

def _get_nlp() -> Language:
    """Lazy load the spaCy English model."""
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model 'en_core_web_sm'")
        except OSError:
            raise RuntimeError(
                "spaCy model 'en_core_web_sm' not found. "
                "Please run: python -m spacy download en_core_web_sm"
            )
    return _nlp

# First-person pronouns (singular and plural)
FIRST_PERSON_PRONOUNS = {
    "i", "me", "my", "mine", "myself",
    "we", "us", "our", "ours", "ourselves"
}

def calculate_pronoun_rate(text: str) -> float:
    """
    Calculate the rate of first-person pronouns in the given text.
    
    Args:
        text: The input text string.
        
    Returns:
        A float representing the ratio of first-person pronouns to total words.
        Returns 0.0 if the text has no words or is empty.
    """
    if not text or not isinstance(text, str):
        return 0.0
        
    doc = _get_nlp()(text)
    
    # Count total words (tokens that are alphabetic or alphanumeric, excluding punctuation/symbols for "word" count)
    # Using is_alpha to ensure we count actual words, not punctuation
    words = [token.text for token in doc if token.is_alpha]
    total_words = len(words)
    
    if total_words == 0:
        return 0.0
        
    # Count first-person pronouns (case-insensitive)
    first_person_count = sum(
        1 for token in doc 
        if token.pos_ == "PRON" and token.text.lower() in FIRST_PERSON_PRONOUNS
    )
    
    return first_person_count / total_words

def extract_pronoun_features(df: pd.DataFrame, text_column: str = "text", output_column: str = "pronoun_rate") -> pd.DataFrame:
    """
    Apply pronoun rate extraction to a DataFrame of conversations.
    
    Args:
        df: DataFrame containing the text data.
        text_column: Name of the column containing text.
        output_column: Name of the new column to store the pronoun rate.
        
    Returns:
        The DataFrame with the new 'pronoun_rate' column added.
        
    Raises:
        ValueError: If the text column is missing.
    """
    if text_column not in df.columns:
        raise ValueError(f"Column '{text_column}' not found in DataFrame. Available: {list(df.columns)}")
        
    logger.info(f"Calculating pronoun rate for column '{text_column}'...")
    
    # Apply the calculation row by row
    df[output_column] = df[text_column].apply(calculate_pronoun_rate)
    
    logger.info(f"Added column '{output_column}' with {df[output_column].notna().sum()} valid values.")
    return df

def main():
    """
    Standalone runner for testing the pronoun extractor.
    Expects a CSV file at data/raw/sample_conversations.csv with a 'text' column.
    Outputs to data/processed/pronoun_features.csv.
    """
    import sys
    from pathlib import Path
    
    # Set up paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "data" / "raw" / "sample_conversations.csv"
    output_path = project_root / "data" / "processed" / "pronoun_features.csv"
    
    if not input_path.exists():
        print(f"Error: Input file not found at {input_path}")
        print("Please ensure 'data/raw/sample_conversations.csv' exists.")
        sys.exit(1)
        
    try:
        # Load data
        df = pd.read_csv(input_path)
        print(f"Loaded {len(df)} conversations from {input_path}")
        
        # Extract features
        result_df = extract_pronoun_features(df)
        
        # Save results
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(output_path, index=False)
        print(f"Successfully wrote results to {output_path}")
        print(f"Sample output:\n{result_df[['text', 'pronoun_rate']].head()}")
        
    except Exception as e:
        logger.exception("An error occurred during extraction.")
        sys.exit(1)

if __name__ == "__main__":
    main()
