"""
Utility functions for the ConstraintResolver to reduce cyclomatic complexity.
Extracted from resolver.py to improve maintainability and testability.
"""
import re
from typing import Dict, Any, Optional, Tuple
from agent.constraint_store import Constraint


def parse_intent(intent_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse an intent string into structured components.
    
    Extracts:
    - action: the verb or action being performed
    - object: the target object
    - location: the target location (if present)
    - modifiers: list of adjectives or qualifiers
    
    Args:
        intent_text: The raw intent string from the generator.
        
    Returns:
        A dictionary with parsed components, or None if parsing fails.
    """
    if not intent_text or not isinstance(intent_text, str):
        return None
        
    intent_text = intent_text.strip().lower()
    if not intent_text:
        return None

    # Simple heuristic parser for demonstration
    # In a real system, this would use a proper NLP model
    parsed = {
        "original": intent_text,
        "action": None,
        "object": None,
        "location": None,
        "modifiers": [],
        "is_negation": False
    }

    # Check for negation patterns
    negation_patterns = [
        r"\bdo\s*not\b", r"\bdon't\b", r"\bnever\b", 
        r"\bwithout\b", r"\bavoid\b", r"\bnegate\b"
    ]
    for pattern in negation_patterns:
        if re.search(pattern, intent_text):
            parsed["is_negation"] = True
            break

    # Split into words for simple parsing
    words = intent_text.split()
    if len(words) < 2:
        return None  # Too short to parse meaningfully

    # Heuristic: first word is likely action
    if words:
        parsed["action"] = words[0]
    
    # Look for "on", "at", "in" to identify location
    prepositions = ["on", "at", "in", "under", "over", "beside", "next to"]
    for i, word in enumerate(words):
        if word in prepositions:
            # Rest of sentence is location
            parsed["location"] = " ".join(words[i+1:]) if i+1 < len(words) else None
            # Object is everything between action and preposition
            if i > 1:
                parsed["object"] = " ".join(words[1:i])
            break
    
    # If no location found, last word might be object
    if not parsed["object"] and not parsed["location"]:
        if len(words) > 1:
            parsed["object"] = " ".join(words[1:])

    # Extract modifiers (adjectives before object)
    if parsed["object"]:
        obj_words = parsed["object"].split()
        if len(obj_words) > 1:
            # Assume first few words are modifiers
            parsed["modifiers"] = obj_words[:-1]
            parsed["object"] = obj_words[-1]

    return parsed


def match_constraint(parsed_intent: Dict[str, Any], constraint: Constraint) -> Dict[str, Any]:
    """
    Match a parsed intent against a constraint.
    
    Implements three matching strategies:
    1. Exact string matching (case-insensitive)
    2. Case-insensitive substring matching
    3. Explicit negation pattern matching
    
    Args:
        parsed_intent: The parsed intent dictionary from parse_intent().
        constraint: The Constraint object to match against.
        
    Returns:
        A dictionary with match results:
        - matched: bool
        - is_violation: bool
        - match_type: str ("exact", "substring", "negation", "miss")
        - confidence: float
    """
    if not parsed_intent or not constraint:
        return {
            "matched": False,
            "is_violation": False,
            "match_type": "miss",
            "confidence": 0.0
        }

    intent_text = parsed_intent.get("original", "").lower()
    constraint_text = constraint.text.lower()
    
    # Strategy 1: Exact match (case-insensitive)
    if intent_text == constraint_text:
        return {
            "matched": True,
            "is_violation": not parsed_intent.get("is_negation", False),
            "match_type": "exact",
            "confidence": 1.0
        }

    # Strategy 2: Substring match
    if constraint_text in intent_text or intent_text in constraint_text:
        # Higher confidence if longer overlap
        overlap_ratio = len(constraint_text) / max(len(intent_text), len(constraint_text))
        return {
            "matched": True,
            "is_violation": not parsed_intent.get("is_negation", False),
            "match_type": "substring",
            "confidence": min(0.9, overlap_ratio)
        }

    # Strategy 3: Negation pattern matching
    # If the constraint is a prohibition (e.g., "Do not X") and the intent
    # attempts to do X (without negation), it's a violation.
    negation_keywords = ["do not", "don't", "never", "avoid", "without"]
    constraint_is_negation = any(kw in constraint_text for kw in negation_keywords)
    
    if constraint_is_negation:
        # Extract the prohibited action from the constraint
        for kw in negation_keywords:
            if kw in constraint_text:
                prohibited_action = constraint_text.split(kw, 1)[1].strip()
                break
        else:
            prohibited_action = constraint_text

        # Check if intent attempts the prohibited action
        if prohibited_action in intent_text:
            # Intent matches prohibited action without negation
            if not parsed_intent.get("is_negation", False):
                return {
                    "matched": True,
                    "is_violation": True,
                    "match_type": "negation",
                    "confidence": 0.85
                }
            else:
                # Intent also has negation, so it's compliant
                return {
                    "matched": True,
                    "is_violation": False,
                    "match_type": "negation",
                    "confidence": 0.75
                }

    # No match found
    return {
        "matched": False,
        "is_violation": False,
        "match_type": "miss",
        "confidence": 0.0
    }
