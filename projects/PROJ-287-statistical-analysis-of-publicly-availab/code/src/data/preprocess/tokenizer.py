"""
Tokenizer module for processing academic abstracts.

Implements NLTK/spaCy tokenization with window-specific stopword loading.
Supports the five 5-year analysis windows: 2000-2004, 2005-2009, 2010-2014, 
2015-2019, 2020-2024.
"""
import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Generator
from dataclasses import dataclass, field

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import spacy

from src.utils.logging import get_logger

# Ensure required NLTK resources are available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If model not installed, try to download it
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], 
                  capture_output=True, check=True)
    nlp = spacy.load("en_core_web_sm")

logger = get_logger(__name__)

@dataclass
class TokenizationResult:
    """Container for tokenization results."""
    original_text: str
    tokens: List[str]
    tokens_lower: List[str]
    tokens_stopped: List[str]
    window: str
    record_id: str
    token_count: int
    stopped_count: int

class WindowStopwordLoader:
    """Loads and manages window-specific stopword lists."""
    
    # Define the 5-year windows
    WINDOWS = [
        "2000-2004",
        "2005-2009", 
        "2010-2014",
        "2015-2019",
        "2020-2024"
    ]
    
    # Base stopwords (common across all windows)
    BASE_STOPWORDS = set(stopwords.words('english'))
    
    # Window-specific additions based on temporal drift in academic language
    WINDOW_SPECIFIC_STOPWORDS = {
        "2000-2004": {
            'xml', 'schema', 'dtd', 'rdf', 'owl', 'semantic', 'web',
            'grid', 'cluster', 'computing', 'distributed'
        },
        "2005-2009": {
            'semantic', 'web', 'ontology', 'rdf', 'owl', 'linked',
            'cloud', 'computing', 'virtualization', 'grid'
        },
        "2010-2014": {
            'big', 'data', 'cloud', 'computing', 'social', 'network',
            'mobile', 'app', 'smartphone', 'tablet'
        },
        "2015-2019": {
            'deep', 'learning', 'neural', 'network', 'lstm', 'cnn',
            'rnn', 'gan', 'transfer', 'learning', 'representation'
        },
        "2020-2024": {
            'transformer', 'attention', 'bert', 'gpt', 'llm', 'large',
            'language', 'model', 'foundation', 'model', 'pretrain'
        }
    }
    
    def __init__(self, stopwords_dir: Optional[Path] = None):
        """
        Initialize the stopword loader.
        
        Args:
            stopwords_dir: Optional directory containing custom stopword files.
                           If provided, these will be loaded in addition to defaults.
        """
        self.stopwords_dir = Path(stopwords_dir) if stopwords_dir else None
        self._cache: Dict[str, Set[str]] = {}
        
        if self.stopwords_dir and not self.stopwords_dir.exists():
            logger.warning(f"Stopwords directory does not exist: {self.stopwords_dir}")
            self.stopwords_dir = None
    
    def get_stopwords(self, window: str) -> Set[str]:
        """
        Get the complete set of stopwords for a given window.
        
        Args:
            window: The 5-year window string (e.g., "2000-2004")
            
        Returns:
            Set of stopwords for the specified window
            
        Raises:
            ValueError: If window is not recognized
        """
        if window not in self.WINDOWS:
            raise ValueError(f"Unknown window: {window}. Must be one of {self.WINDOWS}")
        
        if window in self._cache:
            return self._cache[window]
        
        # Start with base stopwords
        window_stopwords = self.BASE_STOPWORDS.copy()
        
        # Add window-specific stopwords
        if window in self.WINDOW_SPECIFIC_STOPWORDS:
            window_stopwords.update(self.WINDOW_SPECIFIC_STOPWORDS[window])
        
        # Add custom stopwords from file if directory exists
        if self.stopwords_dir:
            custom_file = self.stopwords_dir / f"{window.replace('-', '_')}_stopwords.txt"
            if custom_file.exists():
                with open(custom_file, 'r', encoding='utf-8') as f:
                    custom_words = set(line.strip().lower() for line in f if line.strip())
                    window_stopwords.update(custom_words)
        
        self._cache[window] = window_stopwords
        return window_stopwords

class AbstractTokenizer:
    """
    Tokenizer for academic abstracts using NLTK and spaCy.
    
    Implements a two-stage tokenization process:
    1. Basic tokenization and lowercasing
    2. Stopword removal based on publication window
    """
    
    def __init__(self, window_stopwords_loader: WindowStopwordLoader):
        """
        Initialize the tokenizer.
        
        Args:
            window_stopwords_loader: Loader instance for window-specific stopwords
        """
        self.stopword_loader = window_stopwords_loader
        self.nlp = nlp
        
        # Pattern for cleaning text
        self.clean_pattern = re.compile(r'\s+')
        self.number_pattern = re.compile(r'\b\d+(\.\d+)?\b')
        
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Raw text input
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = self.clean_pattern.sub(' ', text).strip()
        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text)
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
        
        return text
    
    def tokenize(self, text: str, window: str, record_id: str) -> TokenizationResult:
        """
        Tokenize a single abstract.
        
        Args:
            text: The abstract text
            window: The 5-year window for stopword selection
            record_id: Unique identifier for the record
            
        Returns:
            TokenizationResult containing all tokenization stages
        """
        # Clean the text
        cleaned = self.clean_text(text)
        
        # Basic tokenization with NLTK
        tokens = word_tokenize(cleaned)
        
        # Lowercase
        tokens_lower = [t.lower() for t in tokens]
        
        # Get stopwords for this window
        stopwords_set = self.stopword_loader.get_stopwords(window)
        
        # Remove stopwords and non-alphabetic tokens
        tokens_stopped = [
            t for t in tokens_lower 
            if t.isalpha() and t not in stopwords_set
        ]
        
        return TokenizationResult(
            original_text=text,
            tokens=tokens,
            tokens_lower=tokens_lower,
            tokens_stopped=tokens_stopped,
            window=window,
            record_id=record_id,
            token_count=len(tokens),
            stopped_count=len(tokens_stopped)
        )
    
    def tokenize_batch(
        self, 
        records: List[Dict[str, Any]], 
        window: str
    ) -> Generator[TokenizationResult, None, None]:
        """
        Tokenize a batch of records.
        
        Args:
            records: List of record dictionaries with 'text' and 'id' keys
            window: The 5-year window for stopword selection
            
        Yields:
            TokenizationResult for each record
        """
        for record in records:
            record_id = record.get('id', record.get('record_id', ''))
            text = record.get('text', record.get('abstract', ''))
            
            if not text or not isinstance(text, str):
                logger.warning(f"Skipping record {record_id}: invalid text")
                continue
            
            result = self.tokenize(text, window, record_id)
            yield result


def load_preprocessed_data(
    input_path: Path,
    window: str
) -> List[Dict[str, Any]]:
    """
    Load preprocessed data from a JSONL file.
    
    Args:
        input_path: Path to the JSONL file
        window: The window this data belongs to
        
    Returns:
        List of record dictionaries
        
    Raises:
        FileNotFoundError: If the input file doesn't exist
        ValueError: If the file format is invalid
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    records = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                # Ensure required fields exist
                if 'text' not in record and 'abstract' not in record:
                    logger.warning(f"Line {line_num}: Missing text/abstract field")
                    continue
                if 'id' not in record and 'record_id' not in record:
                    logger.warning(f"Line {line_num}: Missing id/record_id field")
                    continue
                
                # Normalize field names
                if 'abstract' in record:
                    record['text'] = record.pop('abstract')
                if 'record_id' in record:
                    record['id'] = record.pop('record_id')
                
                records.append(record)
            except json.JSONDecodeError as e:
                logger.error(f"Line {line_num}: Invalid JSON - {e}")
                continue
    
    logger.info(f"Loaded {len(records)} records from {input_path}")
    return records


def save_tokenized_results(
    results: List[TokenizationResult],
    output_path: Path
) -> None:
    """
    Save tokenization results to a JSONL file.
    
    Args:
        results: List of TokenizationResult objects
        output_path: Path to the output JSONL file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            record = {
                'id': result.record_id,
                'window': result.window,
                'original_text': result.original_text,
                'tokens': result.tokens,
                'tokens_lower': result.tokens_lower,
                'tokens_stopped': result.tokens_stopped,
                'token_count': result.token_count,
                'stopped_count': result.stopped_count
            }
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    logger.info(f"Saved {len(results)} tokenized results to {output_path}")


def main():
    """
    Main entry point for the tokenizer module.
    
    Processes raw abstract data from data/raw/ and saves tokenized results
    to data/processed/ partitioned by window.
    """
    import json
    from typing import Any
    
    logger.info("Starting tokenizer module")
    
    # Configuration
    raw_data_dir = Path("data/raw")
    processed_data_dir = Path("data/processed")
    stopwords_dir = Path("data/stopwords")  # Optional custom stopwords
    
    # Initialize components
    stopword_loader = WindowStopwordLoader(stopwords_dir if stopwords_dir.exists() else None)
    tokenizer = AbstractTokenizer(stopword_loader)
    
    # Process each window
    for window in WindowStopwordLoader.WINDOWS:
        logger.info(f"Processing window: {window}")
        
        # Find input files for this window
        input_files = list(raw_data_dir.glob(f"*{window.replace('-', '_')}*.jsonl"))
        
        if not input_files:
            logger.warning(f"No input files found for window {window}")
            continue
        
        for input_file in input_files:
            logger.info(f"  Processing file: {input_file}")
            
            # Load records
            try:
                records = load_preprocessed_data(input_file, window)
            except (FileNotFoundError, ValueError) as e:
                logger.error(f"  Failed to load {input_file}: {e}")
                continue
            
            # Tokenize
            tokenized_results = list(tokenizer.tokenize_batch(records, window))
            
            # Save results
            output_file = processed_data_dir / f"tokenized_{input_file.stem}.jsonl"
            save_tokenized_results(tokenized_results, output_file)
            
            # Log statistics
            total_tokens = sum(r.token_count for r in tokenized_results)
            total_stopped = sum(r.stopped_count for r in tokenized_results)
            avg_tokens = total_tokens / len(tokenized_results) if tokenized_results else 0
            avg_stopped = total_stopped / len(tokenized_results) if tokenized_results else 0
            
            logger.info(f"    Records: {len(tokenized_results)}")
            logger.info(f"    Avg tokens per record: {avg_tokens:.1f}")
            logger.info(f"    Avg tokens after stopword removal: {avg_stopped:.1f}")
    
    logger.info("Tokenizer module completed")


if __name__ == "__main__":
    main()
