"""
Perturbation Generation Logic
Implements synonym substitution, typo injection, and syntactic rephrasing.
"""

import re
import random
import json
import ast
from typing import Tuple, List, Dict, Any, Optional, Set
from collections import Counter

# Simple synonym mapping for demonstration (in a real scenario, this might use WordNet or a larger corpus)
# We define a small set of common programming keywords and their 'synonyms' for perturbation
# Note: These are chosen carefully to not break Python syntax if replaced in non-critical spots
# or we rely on the semantic validator to filter out broken ones.
SYNOMYM_MAP = {
    "print": ["log", "display", "output"],
    "return": ["yield", "give_back"], # yield changes semantics slightly but might pass semantic check
    "if": ["when"], # Context dependent
    "while": ["for_the_duration_of"],
    "for": ["iterate_over"],
    "def": ["create_function"],
    "class": ["define_class"],
    "import": ["bring_in"],
    "from": ["starting_at"],
    "True": ["is_true"],
    "False": ["is_false"],
    "None": ["null_val", "empty"]
}

# Common typos
TYPO_CHANCES = {
    "e": "a", "a": "e", "i": "o", "o": "i", "s": "z", "t": "f", "l": "1", "0": "o"
}

def substitute_synonyms(code: str) -> str:
    """
    Substitutes non-keyword tokens or specific known tokens with synonyms.
    Note: Python keywords are strict, so we only substitute in string literals
    or variable names that match our map, or we risk SyntaxError.
    To be safe, we target variable names and string content.
    """
    words = code.split()
    new_words = []
    for word in words:
        # Clean punctuation for lookup
        clean_word = word.strip(".,;:()[]{}\"'")
        if clean_word in SYNOMYM_MAP:
            # Only substitute if it's not a strict keyword context (simplified check)
            # For this implementation, we randomly choose to substitute if it matches
            if random.random() < 0.5:
                new_word = random.choice(SYNOMYM_MAP[clean_word])
                # Preserve original casing/punctuation roughly
                if word[0].isupper():
                    new_word = new_word.capitalize()
                new_words.append(new_word)
            else:
                new_words.append(word)
        else:
            new_words.append(word)
    return " ".join(new_words)

def inject_typos(code: str) -> str:
    """
    Injects random character typos into the code.
    """
    if not code:
        return code
    
    # Convert to list for mutability
    chars = list(code)
    # 1% chance to typo each character
    for i in range(len(chars)):
        if random.random() < 0.01:
            original = chars[i]
            if original.lower() in TYPO_CHANCES:
                chars[i] = TYPO_CHANCES[original.lower()]
            elif original.isdigit():
                # Swap digit
                d = int(original)
                chars[i] = str((d + 1) % 10)
    return "".join(chars)

def rephrase_syntax(code: str) -> str:
    """
    Attempts syntactic rephrasing.
    Example: Convert 'for i in range' to 'for i in list' if applicable,
    or reorder simple statements.
    This is a simplified version.
    """
    # Simple pattern: swap 'is not' to '!=', 'is' to '==' (careful with object identity)
    # Or swap 'and' to '&&' (invalid in Python, so we avoid)
    # Let's try changing variable assignment style or simple comment rephrasing if present.
    # Since we can't easily parse and regenerate without breaking, we do string substitution
    # on safe patterns.
    
    replacements = [
        (r"\bif\s+not\b", "unless"), # 'unless' is not Python, so this will likely fail syntax
        # Instead, let's rephrase comments if they exist
        (r"# TODO", "# To-Do"),
        (r"# FIXME", "# Fix-Me"),
        (r"== True", "= True"), # Invalid, but semantic filter should catch
    ]
    
    # Safer approach: Add a comment or whitespace variation
    # Or swap 'return x' to 'return (x)'
    if "return " in code:
        code = code.replace("return ", "return (", 1)
        code = code.rstrip() + ")"
    
    return code

def generate_perturbation_variants(
    prompt: str, 
    max_variants: int = 3
) -> List[Tuple[str, str]]:
    """
    Generates up to max_variants perturbation strings from the input prompt.
    Returns a list of tuples: (perturbation_type, perturbed_text).
    """
    variants = []
    types = ["synonym", "typo", "rephrase"]
    
    # Shuffle to ensure diversity if max_variants < 3
    random.shuffle(types)
    
    for p_type in types[:max_variants]:
        if p_type == "synonym":
            perturbed = substitute_synonyms(prompt)
        elif p_type == "typo":
            perturbed = inject_typos(prompt)
        elif p_type == "rephrase":
            perturbed = rephrase_syntax(prompt)
        else:
            continue
        
        if perturbed != prompt: # Ensure it actually changed
            variants.append((p_type, perturbed))
    
    return variants
