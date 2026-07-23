import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import csv
import re

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.constants import RETRACTION_LABELS
from utils.logging_config import setup_logger

logger = setup_logger(__name__)

# --- Helper Functions ---

def normalize_text(text: str) -> str:
    """Normalize text for matching: lower case, strip whitespace, remove punctuation."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text

def levenshtein_ratio(s1: str, s2: str) -> float:
    """
    Calculate Levenshtein ratio between two strings.
    Uses the python-Levenshtein library if available, else a fallback implementation.
    """
    try:
        import Levenshtein
        return Levenshtein.ratio(s1, s2)
    except ImportError:
        # Fallback implementation if library not installed
        if not s1 or not s2:
            return 0.0
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    cost = 0
                else:
                    cost = 1
                dp[i][j] = min(dp[i - 1][j] + 1,      # deletion
                               dp[i][j - 1] + 1,      # insertion
                               dp[i - 1][j - 1] + cost) # substitution
        max_len = max(m, n)
        return 1.0 - (dp[m][n] / max_len)

def load_nodes_from_csv(filepath: str) -> List[Dict[str, Any]]:
    """Load nodes from a CSV file."""
    nodes = []
    if not os.path.exists(filepath):
        logger.error(f"Nodes file not found: {filepath}")
        return nodes
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            nodes.append(row)
    return nodes

def load_retractions_from_csv(filepath: str) -> List[Dict[str, Any]]:
    """Load retraction records from a CSV file."""
    retractions = []
    if not os.path.exists(filepath):
        logger.error(f"Retractions file not found: {filepath}")
        return retractions
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            retractions.append(row)
    return retractions

def match_doi(node: Dict[str, Any], retraction: Dict[str, Any]) -> bool:
    """Check for exact DOI match between node and retraction."""
    node_doi = normalize_text(node.get('doi', ''))
    ret_doi = normalize_text(retraction.get('doi', ''))
    return node_doi == ret_doi and node_doi != ""

def match_fuzzy(node: Dict[str, Any], retraction: Dict[str, Any], threshold: float = 0.85) -> bool:
    """
    Check for fuzzy match based on title and authors.
    Returns True if ratio >= threshold.
    """
    node_title = normalize_text(node.get('title', ''))
    ret_title = normalize_text(retraction.get('title', ''))
    node_authors = normalize_text(node.get('authors', ''))
    ret_authors = normalize_text(retraction.get('authors', ''))

    if not node_title or not ret_title:
        return False

    title_ratio = levenshtein_ratio(node_title, ret_title)
    # If title match is strong, check authors loosely or return true
    if title_ratio >= threshold:
        # Optional: check author overlap if needed, but title is primary for papers
        return True

    return False

def resolve_duplicates(matches: List[Tuple[Dict, Dict]]) -> Optional[Dict]:
    """
    Resolve duplicate matches by picking the earliest date, then alphabetical journal.
    Returns the best retraction record or None if no matches.
    """
    if not matches:
        return None

    def sort_key(item):
        node, retraction = item
        date_str = retraction.get('date', '9999-99-99')
        journal = retraction.get('journal', 'zzz')
        # Try to parse date simply as string comparison for ISO format
        return (date_str, journal)

    matches.sort(key=sort_key)
    return matches[0][1]

def map_retraction_status(reason: str) -> int:
    """
    Map retraction reason to status label based on RETRACTION_LABELS constant.
    
    Mapping:
    - 0 = Robust (Default/Unknown/Other)
    - 1 = Fragile (Methodological error, Irreproducibility)
    - 2 = Retraction-Only (Fraud)
    
    Args:
        reason: The retraction reason string.
        
    Returns:
        int: The status label (0, 1, or 2).
    """
    if not reason:
        return 0
    
    # Normalize reason for lookup
    normalized_reason = reason.lower().strip()
    
    # Direct lookup in constants
    if normalized_reason in RETRACTION_LABELS:
        return RETRACTION_LABELS[normalized_reason]
    
    # Fallback logic if exact match fails but substrings match (optional safety)
    # This ensures robustness if constants are slightly off in casing
    if "methodological" in normalized_reason or "error" in normalized_reason:
        return 1
    if "irreproducibility" in normalized_reason or "reproducibility" in normalized_reason:
        return 1
    if "fraud" in normalized_reason or "plagiarism" in normalized_reason:
        return 2
        
    # Default to Robust (0) for unknown reasons
    return 0

def convert_to_binary(status: int) -> int:
    """
    Convert 3-state retraction status to binary for modeling.
    
    Mapping:
    - 0 (Robust) -> 0
    - 1 (Fragile) -> 1
    - 2 (Retraction-Only) -> 0
    
    Args:
        status: The 3-state status label.
        
    Returns:
        int: Binary label (0 or 1).
    """
    return 1 if status == 1 else 0

def save_merged_data(nodes: List[Dict], output_path: str):
    """Save the merged nodes with labels to a CSV file."""
    if not nodes:
        logger.warning("No nodes to save.")
        return

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = list(nodes[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(nodes)
    logger.info(f"Saved merged data to {output_path}")

def main():
    """Main entry point for merging retractions with nodes."""
    # Example paths - these would typically come from args or config
    nodes_path = "data/processed/nodes_2010_2018.csv"
    retractions_path = "data/raw/retractions.csv"
    output_path = "data/processed/features_2010_2018.csv"

    if not os.path.exists(nodes_path):
        logger.error(f"Input nodes file not found: {nodes_path}")
        return

    logger.info(f"Loading nodes from {nodes_path}...")
    nodes = load_nodes_from_csv(nodes_path)
    
    logger.info(f"Loading retractions from {retractions_path}...")
    retractions = load_retractions_from_csv(retractions_path)

    logger.info(f"Matching {len(nodes)} nodes with {len(retractions)} retractions...")
    
    matched_count = 0
    for node in nodes:
        best_match = None
        potential_matches = []
        
        # Try exact DOI match first
        for ret in retractions:
            if match_doi(node, ret):
                best_match = ret
                break
        
        # If no DOI match, try fuzzy
        if not best_match:
            for ret in retractions:
                if match_fuzzy(node, ret):
                    potential_matches.append((node, ret))
            
            if potential_matches:
                best_match = resolve_duplicates(potential_matches)

        if best_match:
            matched_count += 1
            reason = best_match.get('reason', '')
            
            # T016: Apply label mapping
            status = map_retraction_status(reason)
            node['retraction_status'] = status
            node['retraction_reason'] = reason
            
            # T016b: Apply binary conversion
            node['retraction_status_binary'] = convert_to_binary(status)
        else:
            # No match found, default to Robust (0)
            node['retraction_status'] = 0
            node['retraction_reason'] = ''
            node['retraction_status_binary'] = 0

    logger.info(f"Matched {matched_count} nodes.")
    save_merged_data(nodes, output_path)
    logger.info("Merge complete.")

if __name__ == "__main__":
    main()
