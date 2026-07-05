"""
Tokenizer module for preprocessing academic abstracts.

Implements tokenization using NLTK and spaCy with window-specific
stopword loading for the topic drift analysis pipeline.
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Generator
from dataclasses import dataclass

import nltk
import spacy
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import pandas as pd

from src.utils.logging import get_logger
from src.utils.config import get_config_dict

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

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If model not found, try downloading it
    import subprocess
    subprocess.check_call(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

logger = get_logger(__name__)

@dataclass
class TokenizationResult:
    """Result of tokenizing a single abstract."""
    original_text: str
    tokens: List[str]
    lemmatized_tokens: List[str]
    filtered_tokens: List[str]
    token_count: int
    window_id: Optional[str]

class WindowStopwordLoader:
    """Manages window-specific stopword lists."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the stopword loader.
        
        Args:
            config_path: Path to the configuration file containing
                        window-specific stopword definitions.
        """
        self.window_stopwords: Dict[str, Set[str]] = {}
        self.base_stopwords: Set[str] = set(stopwords.words('english'))
        self.config = get_config_dict()
        
        if config_path and config_path.exists():
            self._load_window_config(config_path)
        else:
            # Define default window-specific stopword additions
            self._init_default_window_stopwords()
    
    def _init_default_window_stopwords(self) -> None:
        """Initialize default window-specific stopword sets."""
        # Define 5-year windows as specified in the project
        windows = [
            "2000-2004", "2005-2009", "2010-2014", 
            "2015-2019", "2020-2024"
        ]
        
        # Base stopwords are common to all windows
        for window in windows:
            self.window_stopwords[window] = self.base_stopwords.copy()
        
        # Add window-specific terms based on temporal context
        # Early 2000s: terms related to emerging web technologies
        self.window_stopwords["2000-2004"].update({
            'web', 'internet', 'online', 'digital', 'computer',
            'software', 'hardware', 'algorithm', 'database'
        })
        
        # Mid 2000s: social media emergence
        self.window_stopwords["2005-2009"].update({
            'social', 'media', 'blog', 'user', 'content',
            'platform', 'network', 'share', 'post'
        })
        
        # Early 2010s: mobile and cloud computing
        self.window_stopwords["2010-2014"].update({
            'mobile', 'cloud', 'app', 'smartphone', 'tablet',
            'service', 'platform', 'mobile', 'device'
        })
        
        # Late 2010s: AI and big data
        self.window_stopwords["2015-2019"].update({
            'deep', 'learning', 'neural', 'network', 'big',
            'data', 'ai', 'machine', 'model', 'algorithm'
        })
        
        # Early 2020s: pandemic and remote work
        self.window_stopwords["2020-2024"].update({
            'pandemic', 'covid', 'remote', 'work', 'online',
            'virtual', 'hybrid', 'lockdown', 'vaccine'
        })
        
        logger.info(f"Initialized default stopwords for {len(windows)} windows")
    
    def _load_window_config(self, config_path: Path) -> None:
        """Load window-specific stopwords from configuration file."""
        import yaml
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if 'window_stopwords' in config:
            for window, terms in config['window_stopwords'].items():
                if isinstance(terms, list):
                    self.window_stopwords[window] = set(terms)
                else:
                    logger.warning(f"Invalid stopwords format for window {window}")
        
        logger.info(f"Loaded window-specific stopwords from {config_path}")
    
    def get_stopwords(self, window_id: str) -> Set[str]:
        """
        Get stopwords for a specific window.
        
        Args:
            window_id: The window identifier (e.g., "2000-2004")
        
        Returns:
            Set of stopwords for the specified window
        """
        if window_id not in self.window_stopwords:
            logger.warning(f"Window {window_id} not found, using default stopwords")
            return self.base_stopwords
        
        return self.window_stopwords[window_id]

class AbstractTokenizer:
    """Tokenizer for academic abstracts with window-specific processing."""
    
    def __init__(self, window_stopword_loader: Optional[WindowStopwordLoader] = None):
        """
        Initialize the tokenizer.
        
        Args:
            window_stopword_loader: Optional loader for window-specific stopwords.
                                   If None, uses default initialization.
        """
        self.stopword_loader = window_stopword_loader or WindowStopwordLoader()
        self.lemmatizer = WordNetLemmatizer()
        self.nlp = nlp
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text using spaCy.
        
        Args:
            text: Input text to tokenize
        
        Returns:
            List of tokens
        """
        doc = self.nlp(text.lower())
        tokens = [token.text for token in doc if not token.is_space]
        return tokens
    
    def lemmatize(self, tokens: List[str]) -> List[str]:
        """
        Lemmatize tokens using NLTK WordNetLemmatizer.
        
        Args:
            tokens: List of tokens to lemmatize
        
        Returns:
            List of lemmatized tokens
        """
        lemmatized = []
        for token in tokens:
            # Determine POS tag for better lemmatization
            pos = 'n'  # Default to noun
            lemmatized.append(self.lemmatizer.lemmatize(token, pos))
        return lemmatized
    
    def filter_stopwords(self, tokens: List[str], window_id: str) -> List[str]:
        """
        Filter stopwords from tokens based on window-specific list.
        
        Args:
            tokens: List of tokens to filter
            window_id: Window identifier for selecting stopwords
        
        Returns:
            List of tokens with stopwords removed
        """
        stopwords_set = self.stopword_loader.get_stopwords(window_id)
        return [token for token in tokens if token not in stopwords_set]
    
    def filter_special_tokens(self, tokens: List[str]) -> List[str]:
        """
        Remove special tokens (punctuation, numbers, short tokens).
        
        Args:
            tokens: List of tokens to filter
        
        Returns:
            List of cleaned tokens
        """
        filtered = []
        for token in tokens:
            # Remove tokens that are purely punctuation or numbers
            if token.isalnum() and len(token) > 1:
                filtered.append(token)
        return filtered
    
    def process_abstract(self, text: str, window_id: str) -> TokenizationResult:
        """
        Process a single abstract through the full tokenization pipeline.
        
        Args:
            text: Original abstract text
            window_id: Window identifier for stopword filtering
        
        Returns:
            TokenizationResult containing all processing stages
        """
        # Step 1: Tokenize
        tokens = self.tokenize(text)
        
        # Step 2: Lemmatize
        lemmatized_tokens = self.lemmatize(tokens)
        
        # Step 3: Filter stopwords (window-specific)
        filtered_tokens = self.filter_stopwords(lemmatized_tokens, window_id)
        
        # Step 4: Filter special tokens
        final_tokens = self.filter_special_tokens(filtered_tokens)
        
        return TokenizationResult(
            original_text=text,
            tokens=tokens,
            lemmatized_tokens=lemmatized_tokens,
            filtered_tokens=final_tokens,
            token_count=len(final_tokens),
            window_id=window_id
        )
    
    def process_dataframe(self, df: pd.DataFrame, window_id_col: str, 
                         text_col: str = 'abstract') -> Generator[TokenizationResult, None, None]:
        """
        Process a DataFrame of abstracts.
        
        Args:
            df: DataFrame containing abstracts
            window_id_col: Column name containing window identifiers
            text_col: Column name containing abstract text
        
        Yields:
            TokenizationResult for each abstract
        """
        for idx, row in df.iterrows():
            text = str(row[text_col])
            window_id = row[window_id_col]
            
            if pd.isna(text) or len(text.strip()) == 0:
                logger.warning(f"Skipping empty abstract at index {idx}")
                continue
            
            result = self.process_abstract(text, str(window_id))
            yield result

def load_preprocessed_data(data_path: Path) -> pd.DataFrame:
    """
    Load preprocessed data from CSV.
    
    Args:
        data_path: Path to the CSV file containing raw abstracts
    
    Returns:
        DataFrame with abstracts
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} records from {data_path}")
    return df

def save_tokenized_results(results: List[TokenizationResult], output_path: Path) -> None:
    """
    Save tokenization results to a CSV file.
    
    Args:
        results: List of TokenizationResult objects
        output_path: Path to save the CSV file
    """
    data = []
    for result in results:
        data.append({
            'original_text': result.original_text,
            'tokens': ' '.join(result.tokens),
            'lemmatized_tokens': ' '.join(result.lemmatized_tokens),
            'filtered_tokens': ' '.join(result.filtered_tokens),
            'token_count': result.token_count,
            'window_id': result.window_id
        })
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(results)} tokenized results to {output_path}")

def main():
    """
    Main function to run the tokenizer on raw data.
    
    This function:
    1. Loads raw abstracts from data/raw/
    2. Assigns window IDs based on publication year
    3. Tokenizes and filters each abstract
    4. Saves processed results to data/processed/
    """
    logger.info("Starting tokenizer pipeline")
    
    # Initialize tokenizer
    tokenizer = AbstractTokenizer()
    
    # Load raw data
    raw_data_path = Path("data/raw/abstracts_raw.csv")
    if not raw_data_path.exists():
        # Try JSONL format
        raw_data_path = Path("data/raw/abstracts_raw.jsonl")
        if not raw_data_path.exists():
            logger.error("No raw data found. Please run fetchers first.")
            return
    
    if raw_data_path.suffix == '.csv':
        df = load_preprocessed_data(raw_data_path)
    else:
        # Load JSONL
        df = pd.read_json(raw_data_path, lines=True)
    
    # Assign window IDs based on publication year
    def assign_window(year):
        year = int(year)
        if 2000 <= year <= 2004:
            return "2000-2004"
        elif 2005 <= year <= 2009:
            return "2005-2009"
        elif 2010 <= year <= 2014:
            return "2010-2014"
        elif 2015 <= year <= 2019:
            return "2015-2019"
        elif 2020 <= year <= 2024:
            return "2020-2024"
        else:
            return None
    
    if 'year' in df.columns:
        df['window_id'] = df['year'].apply(assign_window)
        df = df[df['window_id'].notna()]  # Filter out invalid years
        logger.info(f"Assigned windows to {len(df)} records")
    else:
        logger.error("Missing 'year' column in raw data. Cannot assign windows.")
        return
    
    # Process abstracts
    results = []
    for result in tokenizer.process_dataframe(df, 'window_id', 'abstract'):
        results.append(result)
    
    # Save results
    output_path = Path("data/processed/tokenized_abstracts.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_tokenized_results(results, output_path)
    
    # Log statistics
    total_tokens = sum(r.token_count for r in results)
    avg_tokens = total_tokens / len(results) if results else 0
    logger.info(f"Processed {len(results)} abstracts")
    logger.info(f"Total tokens: {total_tokens}, Average tokens per abstract: {avg_tokens:.2f}")
    
    # Count tokens per window
    window_counts = {}
    for result in results:
        if result.window_id:
            window_counts[result.window_id] = window_counts.get(result.window_id, 0) + 1
    
    for window, count in window_counts.items():
        logger.info(f"Window {window}: {count} abstracts")

if __name__ == "__main__":
    main()