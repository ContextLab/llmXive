"""
Merge retraction data with method nodes.
Implements fuzzy matching, duplicate resolution, and label mapping logic.
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import csv
import re

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.constants import RETRACTION_LABELS
from code.utils.logging_config import setup_logger

logger = setup_logger(__name__)

# --- Text Normalization ---
def normalize_text(text: str) -> str:
    """Normalize text for fuzzy matching: lowercase, remove punctuation, collapse spaces."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# --- Levenshtein Distance ---
def levenshtein_ratio(s1: str, s2: str) -> float:
    """Calculate normalized Levenshtein similarity ratio between two strings."""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    
    len_s1, len_s2 = len(s1), len(s2)
    # Create a matrix of size (len_s1+1) x (len_s2+1)
    matrix = [[0] * (len_s2 + 1) for _ in range(len_s1 + 1)]

    for i in range(len_s1 + 1):
        matrix[i][0] = i
    for j in range(len_s2 + 1):
        matrix[0][j] = j

    for i in range(1, len_s1 + 1):
        for j in range(1, len_s2 + 1):
            if s1[i-1] == s2[j-1]:
                cost = 0
            else:
                cost = 1
            matrix[i][j] = min(
                matrix[i-1][j] + 1,      # deletion
                matrix[i][j-1] + 1,      # insertion
                matrix[i-1][j-1] + cost  # substitution
            )

    max_len = max(len_s1, len_s2)
    if max_len == 0:
        return 1.0
    return 1.0 - (matrix[len_s1][len_s2] / max_len)

# --- Data Loading ---
def load_nodes_from_csv(filepath: Path) -> List[Dict[str, Any]]:
    """Load method nodes from a CSV file."""
    nodes = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            nodes.append(row)
    return nodes

def load_retractions_from_csv(filepath: Path) -> List[Dict[str, Any]]:
    """Load retraction records from a CSV file."""
    retractions = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            retractions.append(row)
    return retractions

# --- Matching Logic ---
def match_doi(node: Dict[str, Any], retraction: Dict[str, Any]) -> bool:
    """Check for exact DOI match."""
    node_doi = normalize_text(node.get('doi', ''))
    ret_doi = normalize_text(retraction.get('doi', ''))
    return node_doi == ret_doi and node_doi != ""

def match_fuzzy(node: Dict[str, Any], retraction: Dict[str, Any], threshold: float = 0.85) -> bool:
    """Check for fuzzy match on title/author with Levenshtein ratio >= threshold."""
    node_title = normalize_text(node.get('title', ''))
    ret_title = normalize_text(retraction.get('title', ''))
    
    if not node_title or not ret_title:
        return False

    ratio = levenshtein_ratio(node_title, ret_title)
    return ratio >= threshold

def resolve_duplicates(matches: List[Tuple[Dict, Dict]]) -> List[Tuple[Dict, Dict]]:
    """
    Resolve duplicate matches for a single node.
    Strategy: Earliest date, then alphabetical journal.
    """
    if not matches:
        return []
    
    def sort_key(match_tuple):
        node, ret = match_tuple
        date_str = ret.get('date', '9999-99-99')
        journal = ret.get('journal', '')
        return (date_str, journal)

    # Sort by date (asc), then journal (asc)
    sorted_matches = sorted(matches, key=sort_key)
    
    # Return the best match (first one)
    # In a real scenario, we might keep top N, but for this task we pick the best
    return [sorted_matches[0]]

# --- Label Mapping Logic (T016) ---
def map_retraction_status(reason: str) -> int:
    """
    Map retraction reason to status label based on FR-004.
    Returns:
      0 = Robust (default for 'other' or unknown)
      1 = Fragile (methodological error, irreproducibility)
      2 = Retraction-Only (fraud)
    """
    if not reason:
        return 0
    
    reason_lower = reason.lower().strip()
    
    # Check for Fraud (Retraction-Only)
    if 'fraud' in reason_lower or 'plagiarism' in reason_lower:
        return 2
    
    # Check for Methodological Error or Irreproducibility (Fragile)
    if 'methodological' in reason_lower or 'error' in reason_lower:
        return 1
    if 'irreproducibility' in reason_lower or 'irreproducible' in reason_lower:
        return 1
    
    # Default to Robust for other/unknown reasons
    return 0

def convert_to_binary(status: int) -> int:
    """
    Convert 3-state retraction status to binary for modeling.
    Mapping:
      0 (Robust) -> 0
      1 (Fragile) -> 1
      2 (Retraction-Only) -> 0 (treated as non-Fragile)
    """
    if status == 1:
        return 1
    return 0

# --- Data Merging & Saving ---
def save_merged_data(nodes: List[Dict], output_path: Path):
    """Save merged data to CSV, preserving all three states."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = nodes[0].keys() if nodes else []
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(nodes)

def main():
    """Main entry point for retraction merging."""
    # Example usage paths (would be configured via env or args in full pipeline)
    nodes_path = Path("data/processed/nodes_2010_2018.csv")
    retractions_path = Path("data/raw/retractions.csv")
    output_path = Path("data/processed/features_2010_2018.csv")

    if not nodes_path.exists():
        logger.error(f"Nodes file not found: {nodes_path}")
        return
    if not retractions_path.exists():
        logger.error(f"Retractions file not found: {retractions_path}")
        return

    nodes = load_nodes_from_csv(nodes_path)
    retractions = load_retractions_from_csv(retractions_path)

    logger.info(f"Loaded {len(nodes)} nodes and {len(retractions)} retractions.")

    # Match and merge
    for node in nodes:
        best_match = None
        
        # 1. Try exact DOI match
        for ret in retractions:
            if match_doi(node, ret):
                best_match = ret
                break
        
        # 2. If no DOI match, try fuzzy match
        if not best_match:
            fuzzy_matches = []
            for ret in retractions:
                if match_fuzzy(node, ret):
                    fuzzy_matches.append((node, ret))
            
            if fuzzy_matches:
                resolved = resolve_duplicates(fuzzy_matches)
                if resolved:
                    best_match = resolved[0][1]

        # Apply labels if match found
        if best_match:
            reason = best_match.get('reason', 'unknown')
            status = map_retraction_status(reason)
            binary_status = convert_to_binary(status)
            
            node['retraction_reason'] = reason
            node['retraction_status'] = status
            node['retraction_status_binary'] = binary_status
        else:
            node['retraction_reason'] = ''
            node['retraction_status'] = 0
            node['retraction_status_binary'] = 0

    save_merged_data(nodes, output_path)
    logger.info(f"Merged data saved to {output_path}")

if __name__ == "__main__":
    main()
