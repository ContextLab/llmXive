import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Generator
from dataclasses import dataclass

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import spacy

from src.utils.logging import get_logger

# Ensure necessary NLTK resources are available
try:
    stopwords.words('english')
except LookupError:
    nltk.download('stopwords', quiet=True)
try:
    word_tokenize("test")
except LookupError:
    nltk.download('punkt', quiet=True)
try:
    WordNetLemmatizer().lemmatize("test")
    # Ensure wordnet data is present
    nltk.download('wordnet', quiet=True)
except LookupError:
    nltk.download('wordnet', quiet=True)

# Load spaCy model lazily
_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback if model not installed, though requirements.txt should handle it
            # In a real execution environment, this would raise an error if not found
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
            _nlp = spacy.load("en_core_web_sm")
    return _nlp

@dataclass
class TokenizationResult:
    """Container for tokenized and lemmatized text."""
    original_text: str
    tokens: List[str]
    lemmas: List[str]
    window: str
    source: str
    record_id: str
    token_count: int

class WindowStopwordLoader:
    """Loads window-specific stopwords from data files."""

    def __init__(self, stopword_dir: Optional[Path] = None):
        self.stopword_dir = stopword_dir or Path("data/stopwords")
        self._cache: Dict[str, Set[str]] = {}

    def _load_stopwords_from_file(self, filepath: Path) -> Set[str]:
        """Load stopwords from a text file, one word per line."""
        if not filepath.exists():
            raise FileNotFoundError(f"Stopword file not found: {filepath}")
        
        stopwords_set = set()
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().lower()
                if word:
                    stopwords_set.add(word)
        return stopwords_set

    def get_stopwords(self, window: str) -> Set[str]:
        """Get the combined stopwords for a specific window."""
        if window in self._cache:
            return self._cache[window]

        # Base English stopwords from NLTK
        base_stopwords = set(stopwords.words('english'))
        
        # Load window-specific stopwords if they exist
        window_file = self.stopword_dir / f"{window}_stopwords.txt"
        
        if window_file.exists():
            try:
                window_specific = self._load_stopwords_from_file(window_file)
                combined = base_stopwords.union(window_specific)
            except FileNotFoundError:
                logging.warning(f"Window-specific stopwords file {window_file} not found. Using base stopwords only.")
                combined = base_stopwords
        else:
            # If no specific file, just use base stopwords
            combined = base_stopwords

        self._cache[window] = combined
        return combined

class AbstractTokenizer:
    """Handles tokenization, lemmatization, and filtering for abstracts."""

    def __init__(self, stopword_loader: WindowStopwordLoader):
        self.stopword_loader = stopword_loader
        self.lemmatizer = WordNetLemmatizer()
        self.nlp = _get_nlp()

    def _clean_text(self, text: str) -> str:
        """Basic text cleaning."""
        if not text:
            return ""
        # Convert to lowercase
        text = text.lower()
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _tokenize_with_nltk(self, text: str) -> List[str]:
        """Tokenize text using NLTK."""
        return word_tokenize(text)

    def _lemmatize_tokens(self, tokens: List[str]) -> List[str]:
        """Lemmatize tokens using WordNetLemmatizer."""
        # Simple POS tagging approximation (default to noun)
        # For better accuracy, one could use spacy for POS tagging
        return [self.lemmatizer.lemmatize(token) for token in tokens]

    def _remove_stopwords(self, tokens: List[str], stopwords_set: Set[str]) -> List[str]:
        """Remove stopwords from tokens."""
        return [token for token in tokens if token not in stopwords_set]

    def _remove_short_tokens(self, tokens: List[str], min_length: int = 2) -> List[str]:
        """Remove tokens shorter than min_length."""
        return [token for token in tokens if len(token) >= min_length]

    def tokenize_record(self, record: Dict[str, any], window: str) -> Optional[TokenizationResult]:
        """
        Process a single abstract record.
        
        Args:
            record: Dictionary containing 'text', 'source', and 'id' keys.
            window: The 5-year window string (e.g., '2000-2004').
        
        Returns:
            TokenizationResult or None if text is empty.
        """
        text = record.get('text', '')
        if not text or not text.strip():
            return None

        source = record.get('source', 'unknown')
        record_id = record.get('id', 'unknown')

        # Clean text
        cleaned = self._clean_text(text)
        if not cleaned:
            return None

        # Tokenize
        tokens = self._tokenize_with_nltk(cleaned)
        
        # Get stopwords for this window
        stopwords_set = self.stopword_loader.get_stopwords(window)
        
        # Remove stopwords
        tokens_no_stop = self._remove_stopwords(tokens, stopwords_set)
        
        # Remove short tokens
        tokens_filtered = self._remove_short_tokens(tokens_no_stop)
        
        # Lemmatize
        lemmas = self._lemmatize_tokens(tokens_filtered)

        # Final filter: remove empty strings after lemmatization
        lemmas = [l for l in lemmas if l]

        return TokenizationResult(
            original_text=record['text'],
            tokens=tokens_filtered,
            lemmas=lemmas,
            window=window,
            source=source,
            record_id=record_id,
            token_count=len(lemmas)
        )

def load_preprocessed_data(input_path: Path) -> Generator[Dict[str, any], None, None]:
    """
    Load preprocessed data from a JSONL file.
    
    Args:
        input_path: Path to the JSONL file.
        
    Yields:
        Dictionary for each record.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                import json
                yield json.loads(line)
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON at line {line_num}: {e}")
                continue

def save_tokenized_results(results: List[TokenizationResult], output_path: Path):
    """
    Save tokenization results to a JSONL file.
    
    Args:
        results: List of TokenizationResult objects.
        output_path: Path to the output file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            record = {
                'original_text': result.original_text,
                'tokens': result.tokens,
                'lemmas': result.lemmas,
                'window': result.window,
                'source': result.source,
                'id': result.record_id,
                'token_count': result.token_count
            }
            f.write(json.dumps(record) + '\n')

def main():
    """
    Main entry point for the tokenizer script.
    Processes raw JSONL data from data/raw/ and saves tokenized results to data/processed/.
    """
    logger = get_logger(__name__)
    logger.info("Starting tokenizer process...")

    # Define paths
    input_dir = Path("data/raw")
    output_dir = Path("data/processed")
    stopword_dir = Path("data/stopwords")
    
    # Ensure output directories exist
    output_dir.mkdir(parents=True, exist_ok=True)
    stopword_dir.mkdir(parents=True, exist_ok=True)

    # Initialize components
    stopword_loader = WindowStopwordLoader(stopword_dir)
    tokenizer = AbstractTokenizer(stopword_loader)

    # Define windows
    windows = [
        "2000-2004",
        "2005-2009",
        "2010-2014",
        "2015-2019",
        "2020-2024"
    ]

    # Process each window
    for window in windows:
        input_file = input_dir / f"raw_{window}.jsonl"
        output_file = output_dir / f"tokenized_{window}.jsonl"

        if not input_file.exists():
            logger.warning(f"Input file not found for window {window}: {input_file}")
            continue

        logger.info(f"Processing window: {window}")
        results = []
        count = 0
        error_count = 0

        for record in load_preprocessed_data(input_file):
            try:
                result = tokenizer.tokenize_record(record, window)
                if result:
                    results.append(result)
                    count += 1
            except Exception as e:
                logger.error(f"Error processing record {record.get('id', 'unknown')}: {e}")
                error_count += 1

        if results:
            save_tokenized_results(results, output_file)
            logger.info(f"Saved {len(results)} tokenized records to {output_file}")
        else:
            logger.warning(f"No valid records found for window {window}")

        logger.info(f"Window {window}: Processed {count}, Errors {error_count}")

    logger.info("Tokenizer process completed.")

if __name__ == "__main__":
    main()
