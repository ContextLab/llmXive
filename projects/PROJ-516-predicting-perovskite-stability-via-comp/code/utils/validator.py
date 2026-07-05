"""
Validator module for data quality checks.

Implements 'title-token-overlap' validation to ensure data citations
meet a minimum relevance threshold before processing.
"""
import re
import logging
from typing import List, Dict, Any, Optional, Set

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when data validation fails."""
    pass


def _normalize_text(text: str) -> Set[str]:
    """
    Normalize a string into a set of lowercase alphanumeric tokens.
    
    Removes punctuation, converts to lowercase, and splits on whitespace.
    """
    if not text:
        return set()
    # Convert to lowercase and replace non-alphanumeric chars with space
    normalized = re.sub(r'[^a-z0-9\s]', ' ', text.lower())
    # Split into tokens and filter out empty strings
    tokens = {t for t in normalized.split() if len(t) > 1}
    return tokens


def calculate_title_token_overlap(
    title_tokens: Set[str],
    citation_tokens: Set[str]
) -> float:
    """
    Calculate the Jaccard similarity (overlap) between two sets of tokens.
    
    Args:
        title_tokens: Set of tokens from the primary source title.
        citation_tokens: Set of tokens from the citation or metadata.
        
    Returns:
        Float between 0.0 and 1.0 representing the overlap ratio.
        Returns 0.0 if either set is empty to avoid division by zero.
    """
    if not title_tokens or not citation_tokens:
        return 0.0
    
    intersection = len(title_tokens.intersection(citation_tokens))
    union = len(title_tokens.union(citation_tokens))
    
    if union == 0:
        return 0.0
        
    return intersection / union


def validate_title_token_overlap(
    entry: Dict[str, Any],
    threshold: float = 0.7
) -> bool:
    """
    Validate that the title and citation of a data entry have sufficient overlap.
    
    This function compares the title of the primary source against the citation
    metadata (or secondary title) to ensure they refer to the same work.
    A Jaccard similarity score >= threshold is required.
    
    Args:
        entry: Dictionary containing 'title' and 'citation' (or 'source_title') keys.
        threshold: Minimum required overlap score (default 0.7).
        
    Returns:
        True if the overlap meets the threshold.
        
    Raises:
        ValidationError: If the overlap is below the threshold or required fields are missing.
    """
    title = entry.get('title')
    # Try common citation field names
    citation_text = entry.get('citation') or entry.get('source_title') or entry.get('reference')
    
    if not title:
        raise ValidationError(
            f"Missing 'title' field in entry: {entry.get('id', 'unknown')}"
        )
    
    if not citation_text:
        # If no citation text is provided, we cannot validate overlap.
        # Depending on strictness, this might be a hard failure or a warning.
        # For this implementation, we require the citation to exist for validation.
        raise ValidationError(
            f"Missing citation/reference field in entry: {entry.get('id', 'unknown')}. "
            "Cannot perform title-token-overlap validation."
        )
    
    title_tokens = _normalize_text(title)
    citation_tokens = _normalize_text(citation_text)
    
    overlap_score = calculate_title_token_overlap(title_tokens, citation_tokens)
    
    if overlap_score < threshold:
        raise ValidationError(
            f"Title-token-overlap validation failed for entry {entry.get('id', 'unknown')}: "
            f"Overlap score {overlap_score:.2f} is below threshold {threshold}. "
            f"Title: '{title[:50]}...', Citation: '{citation_text[:50]}...'"
        )
    
    logger.debug(
        f"Title-token-overlap validation passed for entry {entry.get('id', 'unknown')}: "
        f"Score {overlap_score:.2f}"
    )
    return True


def validate_data_entries(
    entries: List[Dict[str, Any]],
    threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Validate a list of data entries for title-token overlap.
    
    Args:
        entries: List of dictionaries, each representing a data entry.
        threshold: Minimum required overlap score.
        
    Returns:
        List of entries that passed validation.
        
    Raises:
        ValidationError: If any entry fails validation.
    """
    valid_entries = []
    for entry in entries:
        try:
            if validate_title_token_overlap(entry, threshold):
                valid_entries.append(entry)
        except ValidationError as e:
            # Log the specific error and re-raise to stop processing
            logger.error(str(e))
            raise
    
    return valid_entries
