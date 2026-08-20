import os
import re
import json
import hashlib
import requests
import pandas as pd
from typing import List, Optional, Dict, Any
from pathlib import Path

# Ensure standard library List is available for type hints if Python < 3.9
# The API surface shows 'List' is expected in the signature.
# We import from typing to ensure compatibility.

# --- T007.1 Implementation (referenced by execution failures) ---
# Although T007.1 is a separate task, the execution log shows `fetch_gutenberg_stories`
# failing due to `List` not being defined. We fix the import and signature here.
# The API surface expects: def fetch_gutenberg_stories(output_dir: str, authors: List[str] = None) -> List[str]:

def fetch_gutenberg_stories(output_dir: str, authors: List[str] = None) -> List[str]:
    """
    Fetches stories from Project Gutenberg for specified authors.
    Returns a list of paths to the downloaded story files.
    """
    if authors is None:
        authors = ["O. Henry", "Guy de Maupassant", "Anton Chekhov", "Jack London", "Mark Twain"]
    
    os.makedirs(output_dir, exist_ok=True)
    downloaded_files = []
    
    # Fallback list if initial authors don't yield enough stories
    fallback_authors = ["Edgar Allan Poe", "H.G. Wells", "Arthur Conan Doyle", "Nathaniel Hawthorne", "Kate Chopin"]
    
    # Note: This is a simplified fetcher. In a real production environment, 
    # one would use the `gutenberg` library or the `datasets` library with 
    # a specific Project Gutenberg dataset. Since `gutenberg` library is 
    # in requirements, we assume it's available or use a direct HTTP approach 
    # if the library is not strictly installed in the runner environment.
    # However, to strictly follow "Real data only" and "Fail loudly", 
    # we attempt to use the `gutenberg` package if available, otherwise 
    # we raise an error rather than faking data.
    
    try:
        from gutenberg import cleanup, loadtxt
        from gutenberg.query import get_titles, get_files
        
        for author in authors:
            # Get files for the author
            try:
                files = get_files(author=author)
                for file_id in files:
                    text = loadtxt(file_id)
                    text = cleanup.strip_headers(text)
                    
                    # Split by common story separators or just save as one file per work
                    # For simplicity, we save the whole work as a story if length > 50 words
                    words = text.split()
                    if len(words) > 50:
                        safe_name = re.sub(r'[^\w\-_\. ]', '_', author)
                        filename = f"{safe_name}_file_{file_id}.txt"
                        filepath = os.path.join(output_dir, filename)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(text)
                        downloaded_files.append(filepath)
            except Exception as e:
                print(f"Error fetching for author {author}: {e}")
                continue
        
        # If we have fewer than 50 stories, try fallback authors
        if len(downloaded_files) < 50:
            print(f"Only {len(downloaded_files)} stories found. Trying fallback authors...")
            for author in fallback_authors:
                if len(downloaded_files) >= 50:
                    break
                try:
                    files = get_files(author=author)
                    for file_id in files:
                        text = loadtxt(file_id)
                        text = cleanup.strip_headers(text)
                        words = text.split()
                        if len(words) > 50:
                            safe_name = re.sub(r'[^\w\-_\. ]', '_', author)
                            filename = f"{safe_name}_file_{file_id}.txt"
                            filepath = os.path.join(output_dir, filename)
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(text)
                            downloaded_files.append(filepath)
                except Exception as e:
                    continue
                    
        if len(downloaded_files) < 50:
            raise RuntimeError(f"Failed to extract 50 stories. Only found {len(downloaded_files)}.")
            
    except ImportError:
        raise ImportError("The 'gutenberg' package is required to fetch stories. Install it via requirements.txt.")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch Gutenberg stories: {e}")
        
    return downloaded_files

def fetch_external_moral_dataset(output_path: str) -> None:
    """
    Fetches an external moral judgement dataset.
    For this implementation, we attempt to fetch from a known HuggingFace dataset.
    If not available, we raise an error (Fail Loudly).
    """
    try:
        from datasets import load_dataset
        # Attempt to load a known moral foundations dataset
        # Note: The specific dataset ID might vary; using a generic placeholder logic 
        # that fails loudly if the dataset doesn't exist.
        # A real verified source would be specified in config or a verified URL.
        # Using 'moral_foundations' as a placeholder for the real dataset name.
        # If this specific dataset is not available, the code must fail.
        dataset = load_dataset("moral_foundations", split="train")
        
        # Ensure required columns exist
        if 'text' not in dataset.column_names or 'moral_judgement_score' not in dataset.column_names:
            raise ValueError("Dataset does not contain required columns: 'text', 'moral_judgement_score'")
        
        df = dataset.to_pandas()
        df.to_csv(output_path, index=False)
        print(f"Saved moral judgement dataset to {output_path}")
        
    except ImportError:
        raise ImportError("The 'datasets' package is required to fetch external data.")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch external moral dataset: {e}")

# --- T024 Implementation ---

def prepare_sensitivity_thresholds() -> List[float]:
    """
    Generates a list of threshold values for sensitivity analysis.
    Returns a list of floats: [0.25, 0.30, 0.35, 0.40]
    """
    return [0.25, 0.30, 0.35, 0.40]

def save_thresholds_to_file(output_path: str) -> None:
    """
    Saves the sensitivity thresholds to a JSON file.
    Output format: {"thresholds": [0.25, 0.30, 0.35, 0.40]}
    """
    thresholds = prepare_sensitivity_thresholds()
    data = {"thresholds": thresholds}
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved thresholds to {output_path}")

# Note: The execution log indicated a NameError for 'List' in data_loader.py.
# The fix is ensuring 'List' is imported from typing at the top of the file.
# The code above includes 'from typing import List'.