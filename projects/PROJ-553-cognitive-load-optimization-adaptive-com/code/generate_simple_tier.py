import os
import sys
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import textstat

# Import from sibling module as per API surface
from utils import calculate_flesch_kincaid, calculate_jaccard_similarity

logger = logging.getLogger(__name__)

# Constants for constraints
MIN_FK_DIFF = 5.0
MIN_JACCARD = 0.85
MAX_ITERATIONS = 5

def load_moderate_tiers(path: str = "data/explanation_tiers/moderate_tiers.csv") -> pd.DataFrame:
    """Load the moderate tiers CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Moderate tiers file not found at {path}. Run T022b first.")
    df = pd.read_csv(path)
    required_cols = ['instructional_unit_id', 'text']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Moderate tiers CSV missing required columns: {required_cols}")
    return df

def simplify_text(text: str, aggression: int) -> str:
    """
    Simplify text based on aggression level (1-3).
    Aggression 1: Simple sentence splitting, basic vocabulary.
    Aggression 2: Aggressive sentence splitting, replace complex words.
    Aggression 3: Very aggressive simplification, short sentences, simple words.
    """
    if not text:
        return text

    # Aggression 1: Basic simplification
    if aggression == 1:
        # Split long sentences (heuristic: split at conjunctions or long pauses)
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        simplified_parts = []
        for s in sentences:
            if len(s) > 100:
                # Split long sentences
                chunks = re.split(r'\s+(?:and|or|but|however|therefore)\s+', s, flags=re.IGNORECASE)
                simplified_parts.extend(chunks)
            else:
                simplified_parts.append(s)
        return ' '.join(simplified_parts)

    # Aggression 2: Moderate simplification
    elif aggression == 2:
        # Split sentences more aggressively
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        simplified_parts = []
        complex_words = {
            'utilize': 'use', 'demonstrate': 'show', 'approximately': 'about',
            'subsequently': 'later', 'consequently': 'so', 'furthermore': 'also',
            'nevertheless': 'still', 'moreover': 'plus', 'therefore': 'so',
            'however': 'but', 'although': 'though', 'because': 'since'
        }
        for s in sentences:
            s_lower = s.lower()
            for complex, simple in complex_words.items():
                s = re.sub(r'\b' + complex + r'\b', simple, s, flags=re.IGNORECASE)
            
            if len(s) > 80:
                chunks = re.split(r'\s+(?:and|or|but|however|therefore|since)\s+', s, flags=re.IGNORECASE)
                simplified_parts.extend(chunks)
            else:
                simplified_parts.append(s)
        return ' '.join(simplified_parts)

    # Aggression 3: High simplification
    elif aggression == 3:
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        simplified_parts = []
        complex_words = {
            'utilize': 'use', 'demonstrate': 'show', 'approximately': 'about',
            'subsequently': 'later', 'consequently': 'so', 'furthermore': 'also',
            'nevertheless': 'still', 'moreover': 'plus', 'therefore': 'so',
            'however': 'but', 'although': 'though', 'because': 'since',
            'significant': 'big', 'essential': 'key', 'facilitate': 'help',
            'implement': 'do', 'individual': 'person', 'obtain': 'get',
            'indicate': 'show', 'conclude': 'end', 'initiate': 'start'
        }
        for s in sentences:
            s_lower = s.lower()
            for complex, simple in complex_words.items():
                s = re.sub(r'\b' + complex + r'\b', simple, s, flags=re.IGNORECASE)
            
            # Split very aggressively
            if len(s) > 60:
                chunks = re.split(r'\s+(?:and|or|but|however|therefore|since|while|if|when)\s+', s, flags=re.IGNORECASE)
                simplified_parts.extend(chunks)
            else:
                simplified_parts.append(s)
        return ' '.join(simplified_parts)

    return text

def iterative_simplify(original_text: str, moderate_text: str) -> Tuple[str, bool]:
    """
    Iteratively simplify text until constraints are met or max iterations reached.
    Returns (simplified_text, success).
    """
    current_text = moderate_text
    
    for i in range(1, MAX_ITERATIONS + 1):
        # Calculate current metrics
        fk_moderate = calculate_flesch_kincaid(moderate_text)
        fk_current = calculate_flesch_kincaid(current_text)
        jaccard = calculate_jaccard_similarity(current_text, moderate_text)
        
        fk_diff = fk_moderate - fk_current
        
        logger.debug(f"Iteration {i}: FK_diff={fk_diff:.2f}, Jaccard={jaccard:.2f}")
        
        # Check constraints
        if fk_diff >= MIN_FK_DIFF and jaccard >= MIN_JACCARD:
            logger.info(f"Constraints met at iteration {i}")
            return current_text, True
        
        # If we can't improve further or constraints are violated badly
        if i == MAX_ITERATIONS:
            logger.warning(f"Max iterations reached. Final FK_diff={fk_diff:.2f}, Jaccard={jaccard:.2f}")
            return current_text, False
        
        # Increase aggression for next iteration
        current_text = simplify_text(moderate_text, aggression=i)
    
    return current_text, False

def generate_simple_tiers(moderate_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Generate simple tiers for all rows in the moderate dataframe."""
    results = []
    
    for idx, row in moderate_df.iterrows():
        unit_id = row['instructional_unit_id']
        moderate_text = row['text']
        
        logger.info(f"Processing unit {unit_id}")
        
        simplified_text, success = iterative_simplify(moderate_text, moderate_text)
        
        # Calculate final metrics for logging
        fk_moderate = calculate_flesch_kincaid(moderate_text)
        fk_simple = calculate_flesch_kincaid(simplified_text)
        jaccard = calculate_jaccard_similarity(simplified_text, moderate_text)
        
        results.append({
            'instructional_unit_id': unit_id,
            'text': simplified_text,
            'fk_score': fk_simple,
            'fk_diff_from_moderate': fk_moderate - fk_simple,
            'jaccard_similarity': jaccard,
            'constraints_met': success
        })
        
        if not success:
            logger.warning(f"Unit {unit_id} failed constraints: FK_diff={fk_moderate - fk_simple:.2f}, Jaccard={jaccard:.2f}")
    
    return results

def save_simple_tiers(results: List[Dict[str, Any]], output_path: str = "data/explanation_tiers/simple_tiers.csv"):
    """Save the generated simple tiers to CSV."""
    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} simple tiers to {output_path}")

def main():
    """Main entry point for generating simple tiers."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        logger.info("Loading moderate tiers...")
        moderate_df = load_moderate_tiers()
        
        logger.info(f"Loaded {len(moderate_df)} moderate tiers")
        
        logger.info("Generating simple tiers...")
        results = generate_simple_tiers(moderate_df)
        
        logger.info("Saving simple tiers...")
        save_simple_tiers(results)
        
        # Summary
        success_count = sum(1 for r in results if r['constraints_met'])
        logger.info(f"Generation complete: {success_count}/{len(results)} units met constraints")
        
        if success_count < len(results):
            logger.warning("Some units failed to meet constraints. Review logs for details.")
            
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
