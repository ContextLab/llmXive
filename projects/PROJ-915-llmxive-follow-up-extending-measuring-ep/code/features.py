import os
import re
import csv
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_config

def count_sentences(text: str) -> int:
    """Count sentences in text."""
    if not text:
        return 0
    return len(re.findall(r'[.!?]+', text))

def count_modal_verbs(text: str) -> int:
    """Count modal verbs in text."""
    if not text:
        return 0
    text_lower = text.lower()
    modal_verbs = ['can', 'could', 'may', 'might', 'must', 'shall', 'should', 'will', 'would']
    count = 0
    for verb in modal_verbs:
        # Use word boundaries to avoid partial matches
        count += len(re.findall(r'\b' + verb + r'\b', text_lower))
    return count

def count_imperative_sentences(text: str) -> int:
    """Count imperative sentences (typically start with a verb)."""
    if not text:
        return 0
    sentences = re.split(r'[.!?]+', text)
    count = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        # Simple heuristic: starts with a common verb or imperative structure
        if re.match(r'^(do|please|make|let|take|get|put|come|go|see|know|think|want|need|have|be|can|could|may|might|must|shall|should|will|would)', sentence.lower()):
            count += 1
    return count

def count_declarative_sentences(text: str) -> int:
    """Count declarative sentences."""
    total = count_sentences(text)
    imperative = count_imperative_sentences(text)
    return max(0, total - imperative)

def count_citations(text: str) -> int:
    """Count citation patterns in text (e.g., [1], (Author, Year))."""
    if not text:
        return 0
    # Match patterns like [1], [1, 2], (Author, 2020), etc.
    bracket_count = len(re.findall(r'\[\d+(?:,\s*\d+)*\]', text))
    paren_count = len(re.findall(r'\([A-Za-z]+\s*,\s*\d{4}\)', text))
    return bracket_count + paren_count

def extract_features(row: Dict[str, Any]) -> Dict[str, Any]:
    """Extract linguistic features from a single row."""
    text = row.get("prompt", "") or row.get("text", "")
    if not text:
        text = ""
    
    features = {
        "prompt_id": row.get("prompt_id", row.get("id", "")),
        "sentence_count": count_sentences(text),
        "modal_verb_count": count_modal_verbs(text),
        "imperative_count": count_imperative_sentences(text),
        "declarative_count": count_declarative_sentences(text),
        "citation_count": count_citations(text),
    }
    
    # Handle division by zero for ratios
    if features["declarative_count"] == 0:
        features["imperative_declarative_ratio"] = float('nan')
        features["is_undefined_ratio"] = True
    else:
        features["imperative_declarative_ratio"] = features["imperative_count"] / features["declarative_count"]
        features["is_undefined_ratio"] = False
    
    return features

def flag_undefined_imperative_ratio(features_list: List[Dict]) -> List[Dict]:
    """Ensure undefined ratios are flagged."""
    for f in features_list:
        if f.get("declarative_count", 0) == 0:
            f["is_undefined_ratio"] = True
            if "imperative_declarative_ratio" not in f:
                f["imperative_declarative_ratio"] = float('nan')
    return features_list

def run_feature_extraction_pipeline() -> None:
    """Main feature extraction pipeline."""
    raw_file = Path("data/raw/medmis_subset.csv")
    output_file = Path("data/processed/features.csv")
    
    if not raw_file.exists():
        raise FileNotFoundError(f"Input file not found: {raw_file}")
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    features_list = []
    
    with open(raw_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            features = extract_features(row)
            features_list.append(features)
    
    # Flag undefined ratios
    features_list = flag_undefined_imperative_ratio(features_list)
    
    # Save to CSV
    if features_list:
        fieldnames = features_list[0].keys()
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(features_list)
    
    logging.info(f"Extracted {len(features_list)} feature rows to {output_file}")

def main():
    """Entry point for feature extraction script."""
    run_feature_extraction_pipeline()

if __name__ == "__main__":
    main()