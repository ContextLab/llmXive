import os
import sys
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import re

# Local imports based on provided API surface
from utils.matching import match_papers, find_best_match, calculate_title_similarity
from utils.pdf_parser import extract_p_values, extract_effect_sizes

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for filtering
SAMPLE_SIZE_THRESHOLD = 0.20  # 20% change allowed
MIN_SIMILARITY_SCORE = 0.85   # Minimum fuzzy match score for title/author

def fetch_arxiv_metadata() -> List[Dict[str, Any]]:
    """
    Fetches metadata from arXiv.
    Note: In a real implementation, this would use the arXiv API.
    For this task, we assume the data is fetched and returned as a list of dicts.
    """
    # Placeholder for actual API call logic
    # This function is expected to be implemented fully in T013 context,
    # but we ensure the signature matches the API surface.
    logger.info("Fetching arXiv metadata...")
    return []

def fetch_biorxiv_metadata() -> List[Dict[str, Any]]:
    """
    Fetches metadata from bioRxiv.
    """
    logger.info("Fetching bioRxiv metadata...")
    return []

def fetch_journal_metadata_from_openalex() -> List[Dict[str, Any]]:
    """
    Fetches journal metadata from OpenAlex.
    """
    logger.info("Fetching journal metadata from OpenAlex...")
    return []

def match_preprints_to_journals(preprints: List[Dict], journals: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Matches preprints to journals using fuzzy matching logic.
    Returns a tuple of (matched_pairs, unmatched_preprints).
    """
    matched_pairs = []
    unmatched_preprints = []

    logger.info(f"Matching {len(preprints)} preprints to {len(journals)} journals...")

    for preprint in preprints:
        best_match = find_best_match(preprint, journals)
        if best_match and best_match['score'] >= MIN_SIMILARITY_SCORE:
            matched_pairs.append({
                'preprint': preprint,
                'journal': best_match['match'],
                'score': best_match['score']
            })
        else:
            unmatched_preprints.append(preprint)

    return matched_pairs, unmatched_preprints

def calculate_sample_size_change(preprint_data: Dict, journal_data: Dict) -> float:
    """
    Calculates the percentage change in sample size (N) between preprint and journal versions.
    Returns the absolute percentage change.
    """
    n_preprint = preprint_data.get('sample_size')
    n_journal = journal_data.get('sample_size')

    if n_preprint is None or n_journal is None:
        return float('inf')  # Cannot calculate, treat as large change

    if n_preprint == 0:
        return float('inf')

    change = abs(n_journal - n_preprint) / n_preprint
    return change

def is_theoretical_paper(text_content: str) -> bool:
    """
    Heuristic to detect if a paper is theoretical based on content.
    Checks for absence of empirical data indicators.
    """
    # Simple heuristics: look for absence of 'results', 'methods', 'participants', 'data'
    # or presence of 'theorem', 'proof', 'conjecture' in title/abstract
    text_lower = text_content.lower()
    theoretical_indicators = ['theorem', 'proof', 'conjecture', 'model', 'simulation']
    empirical_indicators = ['experiment', 'study', 'participants', 'data', 'results', 'methods']

    has_theoretical = any(ind in text_lower for ind in theoretical_indicators)
    has_empirical = any(ind in text_lower for ind in empirical_indicators)

    # If it has theoretical indicators and NO empirical indicators, likely theoretical
    if has_theoretical and not has_empirical:
        return True
    return False

def is_case_study(title: str, abstract: str) -> bool:
    """
    Heuristic to detect if a paper is a case study.
    """
    text = (title + " " + abstract).lower()
    case_indicators = ['case study', 'case report', 'single subject', 'n=1']
    return any(ind in text for ind in case_indicators)

def filter_matched_pairs(pairs: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Filters matched pairs based on FR-003 and FR-006:
    1. Exclude case studies.
    2. Exclude theoretical papers.
    3. Exclude pairs with >20% sample size (N) change.

    Returns (included_pairs, excluded_pairs) where excluded_pairs have a 'reason' field.
    """
    included = []
    excluded = []

    for pair in pairs:
        preprint = pair['preprint']
        journal = pair['journal']

        preprint_title = preprint.get('title', '')
        preprint_abstract = preprint.get('abstract', '')
        journal_title = journal.get('title', '')
        journal_abstract = journal.get('abstract', '')

        # Check for case study
        if is_case_study(preprint_title, preprint_abstract) or is_case_study(journal_title, journal_abstract):
            excluded.append({**pair, 'reason': 'methodological shift (case study)'})
            continue

        # Check for theoretical paper
        # We use a combination of title and abstract for the check
        combined_text = f"{preprint_title} {preprint_abstract} {journal_title} {journal_abstract}"
        if is_theoretical_paper(combined_text):
            excluded.append({**pair, 'reason': 'methodological shift (theoretical)'})
            continue

        # Check sample size change
        n_change = calculate_sample_size_change(preprint, journal)
        if n_change > SAMPLE_SIZE_THRESHOLD:
            excluded.append({
                **pair,
                'reason': f'N_change ({n_change:.2%})'
            })
            continue

        included.append(pair)

    return included, excluded

def write_matched_pairs_csv(pairs: List[Dict], output_path: str):
    """
    Writes the included matched pairs to a CSV file.
    Includes an 'exclusion_reason' column (empty for included pairs).
    """
    if not pairs:
        logger.warning("No pairs to write to CSV.")
        return

    # Determine fields
    fieldnames = [
        'preprint_id', 'preprint_title', 'journal_id', 'journal_title',
        'match_score', 'sample_size_preprint', 'sample_size_journal',
        'exclusion_reason'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for pair in pairs:
            preprint = pair['preprint']
            journal = pair['journal']
            row = {
                'preprint_id': preprint.get('id', ''),
                'preprint_title': preprint.get('title', ''),
                'journal_id': journal.get('id', ''),
                'journal_title': journal.get('title', ''),
                'match_score': pair.get('score', 0.0),
                'sample_size_preprint': preprint.get('sample_size', ''),
                'sample_size_journal': journal.get('sample_size', ''),
                'exclusion_reason': pair.get('reason', '')
            }
            writer.writerow(row)

    logger.info(f"Wrote {len(pairs)} pairs to {output_path}")

def write_exclusion_log(excluded_pairs: List[Dict], log_path: str):
    """
    Writes a dedicated log file for excluded pairs.
    Columns: preprint_id, journal_id, reason, timestamp
    """
    if not excluded_pairs:
        logger.info("No excluded pairs to log.")
        return

    timestamp = datetime.now().isoformat()

    with open(log_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['preprint_id', 'journal_id', 'reason', 'timestamp'])
        writer.writeheader()

        for pair in excluded_pairs:
            preprint = pair['preprint']
            journal = pair['journal']
            row = {
                'preprint_id': preprint.get('id', ''),
                'journal_id': journal.get('id', ''),
                'reason': pair.get('reason', 'unknown'),
                'timestamp': timestamp
            }
            writer.writerow(row)

    logger.info(f"Wrote {len(excluded_pairs)} exclusion entries to {log_path}")

def main():
    """
    Main orchestration function for fetching, matching, and filtering.
    """
    logger.info("Starting fetch and match pipeline (T014)...")

    # 1. Fetch Data (Mocked for this task context, but structure is ready)
    # In a real run, these would call the API functions
    preprints = fetch_arxiv_metadata() + fetch_biorxiv_metadata()
    journals = fetch_journal_metadata_from_openalex()

    if not preprints or not journals:
        logger.warning("No data fetched. Exiting.")
        return

    # 2. Match
    matched_pairs, unmatched = match_preprints_to_journals(preprints, journals)
    logger.info(f"Found {len(matched_pairs)} initial matches. {len(unmatched)} unmatched.")

    # 3. Filter (T014 Implementation)
    included_pairs, excluded_pairs = filter_matched_pairs(matched_pairs)
    logger.info(f"Filtered: {len(included_pairs)} included, {len(excluded_pairs)} excluded.")

    # 4. Write Outputs
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "matched_pairs.csv"
    write_matched_pairs_csv(included_pairs, str(csv_path))

    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    log_path = raw_dir / "exclusion_log.csv"
    write_exclusion_log(excluded_pairs, str(log_path))

    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()