import hashlib
import os
from pathlib import Path
from typing import Generator, Dict, Any, Optional
import datasets
from code.config import DATASET_BOOK_CORPUS, DATASET_BEIR, DATA_RAW_DIR

# Ensure directories exist before loading
from code.config import ensure_directories
ensure_directories()

def load_dataset_with_checksum(
    dataset_name: str,
    split: str = "train",
    streaming: bool = False
) -> datasets.Dataset:
    """
    Load a dataset from HuggingFace.
    If streaming is False, returns the full dataset.
    If streaming is True, returns a streaming dataset.
    """
    try:
        ds = datasets.load_dataset(dataset_name, split=split, streaming=streaming)
        return ds
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset {dataset_name}: {e}")

def load_book_corpus() -> datasets.Dataset:
    """Load the Book Corpus dataset."""
    return load_dataset_with_checksum(DATASET_BOOK_CORPUS)

def load_beir() -> datasets.Dataset:
    """Load the BEIR dataset."""
    return load_dataset_with_checksum(DATASET_BEIR)

def main() -> None:
    """Test loading datasets."""
    print("Loading Book Corpus...")
    bc = load_book_corpus()
    print(f"Book Corpus loaded. Num rows: {len(bc)}")
    
    print("Loading BEIR...")
    beir = load_beir()
    print(f"BEIR loaded. Num rows: {len(beir)}")

if __name__ == "__main__":
    main()
