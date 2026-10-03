"""
Feature Extraction Module: Extracts linguistic features from prompts.
Implements T014, T015.
"""
import os
import re
import csv
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_config
from ingestion_utils import ensure_dir

logger = logging.getLogger(__name__)

def count_sentences(text: str) -> int:
    """Count sentences in text."""
    if not text:
        return 0
    # Simple regex for sentence boundaries
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])

def count_modal_verbs(text: str) -> int:
    """Count modal verbs (can, could, may, might, shall, should, will, would, must)."""
    if not text:
        return 0
    modals = r'\b(can|could|may|might|shall|should|will|would|must)\b'
    matches = re.findall(modals, text, re.IGNORECASE)
    return len(matches)

def count_imperative_sentences(text: str) -> int:
    """Count imperative sentences (starting with a verb)."""
    if not text:
        return 0
    sentences = re.split(r'[.!?]+', text)
    count = 0
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        # Imperative often starts with a verb (simple heuristic)
        # Check if first word is a verb-like token (starts with lowercase, common verbs)
        words = s.split()
        if words:
            first = words[0].lower()
            # Heuristic: imperative often starts with base verb
            common_verbs = {'get', 'take', 'do', 'make', 'see', 'know', 'think', 'look', 'give', 'use', 'find', 'tell', 'ask', 'work', 'seem', 'feel', 'try', 'leave', 'call', 'keep', 'let', 'begin', 'seem', 'help', 'talk', 'turn', 'start', 'show', 'hear', 'play', 'run', 'move', 'live', 'believe', 'hold', 'bring', 'happen', 'write', 'provide', 'sit', 'stand', 'lose', 'pay', 'meet', 'include', 'continue', 'set', 'learn', 'change', 'lead', 'understand', 'watch', 'follow', 'stop', 'create', 'speak', 'read', 'allow', 'add', 'spend', 'grow', 'open', 'walk', 'win', 'offer', 'remember', 'love', 'consider', 'appear', 'buy', 'wait', 'serve', 'die', 'send', 'expect', 'build', 'stay', 'fall', 'cut', 'reach', 'kill', 'remain', 'suggest', 'raise', 'pass', 'sell', 'require', 'report', 'decide', 'pull'}
            if first in common_verbs or (len(words) > 1 and words[1].endswith('ing')):
                count += 1
    return count

def count_declarative_sentences(text: str) -> int:
    """Count declarative sentences."""
    total = count_sentences(text)
    imperative = count_imperative_sentences(text)
    # Simplistic: Declarative = Total - Imperative (ignoring interrogative for now)
    return max(0, total - imperative)

def count_citations(text: str) -> int:
    """Count citation-like patterns (e.g., [1], (Author, Year))."""
    if not text:
        return 0
    patterns = [
        r'\[\d+\]',  # [1]
        r'\(\s*[A-Z][a-z]+,\s*\d{4}\s*\)', # (Author, 2020)
        r'\d{4}', # Years (heuristic, might be noisy)
    ]
    count = 0
    for p in patterns:
        count += len(re.findall(p, text))
    return count

def extract_features(prompt_text: str) -> Dict[str, Any]:
    """Extract all features for a single prompt."""
    total_sentences = count_sentences(prompt_text)
    modal_count = count_modal_verbs(prompt_text)
    imperative_count = count_imperative_sentences(prompt_text)
    declarative_count = count_declarative_sentences(prompt_text)
    citation_count = count_citations(prompt_text)

    modal_freq = modal_count / total_sentences if total_sentences > 0 else 0.0
    citation_density = citation_count / total_sentences if total_sentences > 0 else 0.0

    return {
        'modal_freq': modal_freq,
        'imperative_count': imperative_count,
        'declarative_count': declarative_count,
        'citation_density': citation_density,
        'total_sentences': total_sentences
    }

def flag_undefined_imperative_ratio(features: Dict[str, Any]) -> Tuple[bool, float]:
    """
    Detect if imperative ratio is undefined (zero total sentences).
    Returns (is_undefined, safe_value).
    """
    total = features.get('total_sentences', 0)
    if total == 0:
        return True, 0.0
    return False, features.get('imperative_count', 0) / total

def run_feature_extraction_pipeline():
    """
    Main pipeline to load ingestion data, extract features, and save.
    """
    config = get_config()
    input_path = Path(config.data_raw_dir) / "medmis_subset.csv"
    output_path = Path(config.data_processed_dir) / "features.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. Run ingestion first.")

    ensure_dir(output_path.parent)

    with open(input_path, 'r', encoding='utf-8') as f_in:
        reader = csv.DictReader(f_in)
        rows = list(reader)

    output_rows = []
    for row in rows:
        prompt = row.get('prompt', '')
        features = extract_features(prompt)
        
        is_undef, safe_val = flag_undefined_imperative_ratio(features)
        
        output_row = {
            'prompt_id': row.get('id', row.get('prompt_id', '')),
            'prompt_text': prompt,
            'modal_freq': features['modal_freq'],
            'imperative_ratio': safe_val,
            'citation_density': features['citation_density'],
            'is_ratio_undefined': is_undef,
            'ratio_safe_value': safe_val
        }
        output_rows.append(output_row)

    fieldnames = ['prompt_id', 'prompt_text', 'modal_freq', 'imperative_ratio', 'citation_density', 'is_ratio_undefined', 'ratio_safe_value']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    logger.info(f"Feature extraction complete. Saved to {output_path}")
    return output_rows

def main():
    run_feature_extraction_pipeline()

if __name__ == "__main__":
    main()
