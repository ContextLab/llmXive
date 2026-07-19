import re
from typing import Dict, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

def extract_tract_descriptors(text: str, target_tract: str, lexicon: Dict[str, List[str]]) -> List[str]:
    """
    Extract qualitative descriptors for a specific tract from text using the lexicon.
    
    Args:
        text: The raw text (notes/description) to search.
        target_tract: The specific tract name to look for (e.g., "arcuate").
        lexicon: Dictionary of categories to lists of terms (from tract_lexicon.yaml).
    
    Returns:
        List of strings formatted as "category: term".
    """
    if not text or not target_tract:
        return []
    
    text_lower = text.lower()
    target_lower = target_tract.lower()
    
    # Normalize tract name for search (simple substring match for now)
    # In a more complex scenario, we might use word boundaries or stemming.
    if target_lower not in text_lower:
        # If the specific tract isn't mentioned, return empty
        # Or we could search for any tract in the lexicon? 
        # The task implies searching for the tract found in the row.
        return []
    
    descriptors = []
    
    # We need to find directional verbs or adjectives near the tract name.
    # Strategy: Find the index of the tract, then look at surrounding words.
    # For simplicity with the lexicon structure (categories -> terms),
    # we will check if any lexicon terms appear in the text, and if they are contextually relevant.
    # A simple heuristic: if the term appears in the text, and the tract appears in the text.
    # A better heuristic: check proximity.
    
    tract_matches = list(re.finditer(re.escape(target_lower), text_lower))
    
    if not tract_matches:
        return []
    
    # Define a window size (characters or words)
    window_size = 100
    
    for match in tract_matches:
        start = max(0, match.start() - window_size)
        end = min(len(text), match.end() + window_size)
        context_window = text[start:end]
        context_lower = context_window.lower()
        
        for category, terms in lexicon.items():
            for term in terms:
                term_lower = term.lower()
                if term_lower in context_lower:
                    descriptors.append(f"{category}: {term}")
    
    return list(set(descriptors)) # Remove duplicates

def main() -> None:
    """Main entry point for NLP logic (for testing)."""
    import argparse
    import yaml
    
    parser = argparse.ArgumentParser(description="NLP Logic Test")
    parser.add_argument("--text", type=str, required=True)
    parser.add_argument("--tract", type=str, required=True)
    parser.add_argument("--lexicon", type=str, required=True)
    args = parser.parse_args()
    
    with open(args.lexicon, 'r') as f:
        lexicon = yaml.safe_load(f)
    
    results = extract_tract_descriptors(args.text, args.tract, lexicon)
    print(f"Descriptors: {results}")

if __name__ == "__main__":
    main()