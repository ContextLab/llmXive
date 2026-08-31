"""
NLP Logic for Qualitative Extraction (Task T012 dependency).

Implements regex patterns to search for tract names (from the lexicon)
in proximity (≤5 words) to directional verbs.
"""
import re
from typing import Dict, List, Optional, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)

def extract_tract_descriptors(text: str, lexicon: Dict, scheme: Dict) -> Optional[Dict[str, Any]]:
    """
    Extract qualitative descriptors from text based on the lexicon and scheme.
    
    Args:
        text: The input text to process.
        lexicon: Dictionary containing 'tracts' and 'verbs' lists.
        scheme: Dictionary containing 'keywords', 'sentiment_rules', etc.
    
    Returns:
        A dictionary with 'description', 'detected_tract', 'detected_verb', and 'confidence',
        or None if no match is found.
    """
    if not text or not isinstance(text, str):
        return None

    text_lower = text.lower()
    words = text_lower.split()
    
    detected_tract = None
    detected_verb = None
    description = ""
    
    # Normalize tracts for regex (escape special chars)
    tract_patterns = []
    for tract in lexicon.get("tracts", []):
        # Create a pattern that matches the tract name as a whole word or phrase
        pattern = r'\b' + re.escape(tract.lower()) + r'\b'
        tract_patterns.append((pattern, tract))
    
    # Normalize verbs
    verb_patterns = []
    for verb in lexicon.get("verbs", []):
        pattern = r'\b' + re.escape(verb.lower()) + r'\b'
        verb_patterns.append((pattern, verb))
    
    # Search for tracts
    tract_matches = []
    for pattern, tract_name in tract_patterns:
        matches = list(re.finditer(pattern, text_lower))
        if matches:
            tract_matches.append((matches[0].start(), tract_name))
    
    # Search for verbs
    verb_matches = []
    for pattern, verb_name in verb_patterns:
        matches = list(re.finditer(pattern, text_lower))
        if matches:
            verb_matches.append((matches[0].start(), verb_name))
    
    # Check proximity: tract and verb within 5 words
    for t_start, t_name in tract_matches:
        # Find the word index of the tract
        t_word_idx = len(text_lower[:t_start].split())
        
        for v_start, v_name in verb_matches:
            v_word_idx = len(text_lower[:v_start].split())
            
            # Check if within 5 words
            if abs(t_word_idx - v_word_idx) <= 5:
                detected_tract = t_name
                detected_verb = v_name
                # Construct a simple description
                description = f"{t_name} {v_name}"
                break
        if detected_tract:
            break
    
    if detected_tract and detected_verb:
        # Determine confidence based on proximity
        # Closer proximity = higher confidence
        proximity = abs(len(text_lower[:tract_matches[0][0]].split()) - len(text_lower[:verb_matches[0][0]].split()))
        confidence = max(0.5, 1.0 - (proximity * 0.1))
        
        return {
            "description": description,
            "detected_tract": detected_tract,
            "detected_verb": detected_verb,
            "confidence": round(confidence, 2)
        }
    
    return None
