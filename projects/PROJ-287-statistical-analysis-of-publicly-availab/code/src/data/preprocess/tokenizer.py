import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Generator
from dataclasses import dataclass, field
import json

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import spacy

from src.utils.logging import get_logger

# Ensure required NLTK data is available
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
except LookupError:
    nltk.download('wordnet', quiet=True)
try:
    word_tokenize("test", language='english')
    nltk.download('punkt_tab', quiet=True)
except:
    pass

# Load spaCy model (small English model)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If model not found, try to download it
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
    nlp = spacy.load("en_core_web_sm")


@dataclass
class TokenizationResult:
    """Container for tokenization results of a single record."""
    record_id: str
    source: str
    original_text: str
    tokens: List[str]
    lemmatized_tokens: List[str]
    token_count: int
    window: Optional[str] = None
    is_filtered: bool = False
    filter_reason: Optional[str] = None


class WindowStopwordLoader:
    """
    Loads and manages window-specific stopword lists.
    
    Windows are defined as 5-year periods:
    - 2000-2004
    - 2005-2009
    - 2010-2014
    - 2015-2019
    - 2020-2024
    
    Each window may have custom stopwords in addition to standard English stopwords.
    """
    
    def __init__(self, custom_stopwords_dir: Optional[Path] = None):
        self.logger = get_logger(__name__)
        self.base_stopwords: Set[str] = set(stopwords.words('english'))
        self.window_stopwords: Dict[str, Set[str]] = {}
        self.custom_stopwords_dir = custom_stopwords_dir
        
        # Define standard windows
        self.windows = [
            "2000-2004",
            "2005-2009",
            "2010-2014",
            "2015-2019",
            "2020-2024"
        ]
        
        # Initialize empty sets for each window
        for window in self.windows:
            self.window_stopwords[window] = set()
        
        # Load custom stopwords if directory provided
        if custom_stopwords_dir:
            self._load_custom_stopwords(custom_stopwords_dir)
    
    def _load_custom_stopwords(self, custom_dir: Path) -> None:
        """Load custom stopwords from JSON files in the specified directory."""
        if not custom_dir.exists():
            self.logger.warning(f"Custom stopwords directory does not exist: {custom_dir}")
            return
        
        for window in self.windows:
            file_path = custom_dir / f"stopwords_{window}.json"
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        custom_words = json.load(f)
                        if isinstance(custom_words, list):
                            self.window_stopwords[window].update(
                                word.lower().strip() for word in custom_words
                            )
                            self.logger.info(
                                f"Loaded {len(custom_words)} custom stopwords for window {window}"
                            )
                        else:
                            self.logger.warning(
                                f"Invalid format in {file_path}: expected list of strings"
                            )
                except (json.JSONDecodeError, IOError) as e:
                    self.logger.error(f"Error loading {file_path}: {e}")
            else:
                self.logger.info(f"No custom stopwords file found for window {window}")
    
    def get_stopwords(self, window: str) -> Set[str]:
        """
        Get the complete stopwords set for a specific window.
        
        Args:
            window: Window identifier (e.g., "2000-2004")
        
        Returns:
            Set of stopwords for the window (base + custom)
        """
        if window not in self.window_stopwords:
            self.logger.warning(f"Unknown window: {window}, using base stopwords only")
            return self.base_stopwords.copy()
        
        # Combine base stopwords with window-specific custom stopwords
        combined = self.base_stopwords.copy()
        combined.update(self.window_stopwords[window])
        return combined
    
    def add_custom_stopwords(self, window: str, words: List[str]) -> None:
        """
        Add custom stopwords to a specific window.
        
        Args:
            window: Window identifier
            words: List of words to add as stopwords
        """
        if window not in self.window_stopwords:
            self.logger.warning(f"Unknown window: {window}, skipping addition")
            return
        
        normalized = {word.lower().strip() for word in words if word and word.strip()}
        self.window_stopwords[window].update(normalized)
        self.logger.debug(f"Added {len(normalized)} stopwords to window {window}")


class AbstractTokenizer:
    """
    Tokenizer for academic abstracts using NLTK and spaCy.
    
    Features:
    - Tokenization using NLTK
    - Lemmatization using spaCy
    - Window-specific stopword removal
    - Lowercasing and punctuation removal
    - Token counting
    """
    
    def __init__(
        self,
        stopword_loader: WindowStopwordLoader,
        remove_punctuation: bool = True,
        lowercase: bool = True,
        min_token_length: int = 2
    ):
        """
        Initialize the tokenizer.
        
        Args:
            stopword_loader: WindowStopwordLoader instance for window-specific stopwords
            remove_punctuation: Whether to remove punctuation tokens
            lowercase: Whether to lowercase all tokens
            min_token_length: Minimum length of tokens to keep
        """
        self.stopword_loader = stopword_loader
        self.remove_punctuation = remove_punctuation
        self.lowercase = lowercase
        self.min_token_length = min_token_length
        self.logger = get_logger(__name__)
        
        # Initialize spaCy pipeline
        self.nlp = nlp
        
        # Initialize NLTK lemmatizer (fallback)
        self.lemmatizer = WordNetLemmatizer()
    
    def _clean_token(self, token: str) -> str:
        """Clean a single token."""
        if self.lowercase:
            token = token.lower()
        
        if self.remove_punctuation:
            # Remove punctuation
            token = re.sub(r'[^\w\s]', '', token)
        
        return token.strip()
    
    def _is_valid_token(self, token: str) -> bool:
        """Check if a token meets filtering criteria."""
        if not token:
            return False
        
        if len(token) < self.min_token_length:
            return False
        
        # Check if token is alphanumeric (after cleaning)
        if not re.match(r'^[a-z0-9]+$', token, re.IGNORECASE):
            return False
        
        return True
    
    def _lemmatize_tokens(self, tokens: List[str], window: Optional[str] = None) -> List[str]:
        """
        Lemmatize tokens using spaCy for better accuracy.
        
        Args:
            tokens: List of tokens to lemmatize
            window: Optional window identifier for context-aware lemmatization
        
        Returns:
            List of lemmatized tokens
        """
        # Use spaCy for lemmatization (more accurate than NLTK)
        doc = self.nlp(" ".join(tokens))
        lemmatized = [token.lemma_ for token in doc]
        
        # Clean lemmatized tokens
        cleaned = []
        for lemma in lemmatized:
            cleaned_token = self._clean_token(lemma)
            if self._is_valid_token(cleaned_token):
                cleaned.append(cleaned_token)
        
        return cleaned
    
    def tokenize(
        self,
        text: str,
        record_id: str,
        source: str,
        window: Optional[str] = None
    ) -> TokenizationResult:
        """
        Tokenize and preprocess a single abstract.
        
        Args:
            text: The abstract text
            record_id: Unique identifier for the record
            source: Data source (e.g., 'arxiv', 'pubmed')
            window: Optional window identifier for stopword selection
        
        Returns:
            TokenizationResult containing all processing details
        """
        if not text or not text.strip():
            return TokenizationResult(
                record_id=record_id,
                source=source,
                original_text=text,
                tokens=[],
                lemmatized_tokens=[],
                token_count=0,
                window=window,
                is_filtered=True,
                filter_reason="Empty text"
            )
        
        # Step 1: Tokenize using NLTK
        try:
            raw_tokens = word_tokenize(text)
        except Exception as e:
            self.logger.error(f"Tokenization failed for {record_id}: {e}")
            raw_tokens = text.split()  # Fallback to simple split
        
        # Step 2: Clean and filter tokens
        cleaned_tokens = []
        for token in raw_tokens:
            cleaned = self._clean_token(token)
            if self._is_valid_token(cleaned):
                cleaned_tokens.append(cleaned)
        
        # Step 3: Remove stopwords
        if window:
            stopwords_set = self.stopword_loader.get_stopwords(window)
        else:
            stopwords_set = self.stopword_loader.get_stopwords("2000-2004")  # Default
        
        filtered_tokens = [
            token for token in cleaned_tokens
            if token.lower() not in stopwords_set
        ]
        
        # Step 4: Lemmatize
        lemmatized_tokens = self._lemmatize_tokens(filtered_tokens, window)
        
        # Determine if record should be filtered based on token count
        # (Minimum 20 tokens as per requirements)
        is_filtered = len(lemmatized_tokens) < 20
        filter_reason = "Insufficient tokens (< 20)" if is_filtered else None
        
        return TokenizationResult(
            record_id=record_id,
            source=source,
            original_text=text,
            tokens=filtered_tokens,
            lemmatized_tokens=lemmatized_tokens,
            token_count=len(lemmatized_tokens),
            window=window,
            is_filtered=is_filtered,
            filter_reason=filter_reason
        )
    
    def tokenize_batch(
        self,
        records: List[Dict[str, any]],
        window: Optional[str] = None
    ) -> Generator[TokenizationResult, None, None]:
        """
        Tokenize a batch of records.
        
        Args:
            records: List of record dictionaries with 'id', 'text', 'source' keys
            window: Optional window identifier
        
        Yields:
            TokenizationResult for each record
        """
        for record in records:
            result = self.tokenize(
                text=record.get('text', ''),
                record_id=record.get('id', 'unknown'),
                source=record.get('source', 'unknown'),
                window=window
            )
            yield result


def load_preprocessed_data(input_path: Path) -> List[Dict[str, any]]:
    """
    Load preprocessed data from a JSONL file.
    
    Args:
        input_path: Path to the JSONL file
    
    Returns:
        List of record dictionaries
    """
    records = []
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                # Validate required fields
                if 'id' not in record or 'text' not in record:
                    raise ValueError(f"Missing required fields at line {line_num}")
                records.append(record)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {line_num}: {e}")
    
    return records


def save_tokenized_results(
    results: List[TokenizationResult],
    output_path: Path,
    include_filtered: bool = True
) -> None:
    """
    Save tokenization results to a JSONL file.
    
    Args:
        results: List of TokenizationResult objects
        output_path: Output file path
        include_filtered: Whether to include filtered-out records
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            if not include_filtered and result.is_filtered:
                continue
            
            # Convert dataclass to dict
            record_dict = {
                'id': result.record_id,
                'source': result.source,
                'window': result.window,
                'original_text': result.original_text,
                'tokens': result.tokens,
                'lemmatized_tokens': result.lemmatized_tokens,
                'token_count': result.token_count,
                'is_filtered': result.is_filtered,
                'filter_reason': result.filter_reason
            }
            f.write(json.dumps(record_dict) + '\n')
    
    # Log summary
    total = len(results)
    filtered = sum(1 for r in results if r.is_filtered)
    kept = total - filtered
    
    logger = get_logger(__name__)
    logger.info(f"Saved {kept}/{total} records to {output_path}")
    if filtered > 0:
        logger.info(f"Filtered out {filtered} records ({filtered/total*100:.1f}%)")


def main():
    """Main entry point for tokenizer module."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Tokenize academic abstracts')
    parser.add_argument('--input', type=str, required=True, help='Input JSONL file path')
    parser.add_argument('--output', type=str, required=True, help='Output JSONL file path')
    parser.add_argument('--window', type=str, default='2000-2004', help='Time window for stopwords')
    parser.add_argument('--custom-stopwords-dir', type=str, default=None, help='Directory with custom stopwords')
    
    args = parser.parse_args()
    
    # Initialize components
    stopword_loader = WindowStopwordLoader(
        custom_stopwords_dir=Path(args.custom_stopwords_dir) if args.custom_stopwords_dir else None
    )
    tokenizer = AbstractTokenizer(stopword_loader=stopword_loader)
    
    # Load data
    logger = get_logger(__name__)
    logger.info(f"Loading data from {args.input}")
    records = load_preprocessed_data(Path(args.input))
    logger.info(f"Loaded {len(records)} records")
    
    # Process
    logger.info(f"Tokenizing with window: {args.window}")
    results = list(tokenizer.tokenize_batch(records, window=args.window))
    
    # Save
    logger.info(f"Saving results to {args.output}")
    save_tokenized_results(results, Path(args.output), include_filtered=True)
    
    logger.info("Tokenization complete")


if __name__ == '__main__':
    main()
