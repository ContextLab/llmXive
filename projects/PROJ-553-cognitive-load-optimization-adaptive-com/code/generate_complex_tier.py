import os
import sys
import logging
import re
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import shared utilities from utils.py as per API surface
from utils import calculate_flesch_kincaid, calculate_jaccard_similarity

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for complexity adjustment
JARGON_LIST = [
    'pedagogical', 'scaffolding', 'metacognition', 'heuristic', 
    'cognitive load', 'schema', 'interference', 'elaboration'
]
MAX_ATTEMPTS = 3
# Aggressiveness levels for complexity injection
AGGRESSIVENESS_LEVELS = [
    {'jargon_factor': 1, 'clause_factor': 1, 'len_factor': 1.1},
    {'jargon_factor': 2, 'clause_factor': 2, 'len_factor': 1.25},
    {'jargon_factor': 3, 'clause_factor': 3, 'len_factor': 1.4}
]

def load_moderate_tiers(file_path: str) -> List[Dict[str, Any]]:
    """Load moderate tiers from CSV."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Moderate tiers file not found: {file_path}")
    
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def insert_jargon(text: str, count: int) -> str:
    """Insert jargon terms into the text to increase complexity."""
    words = text.split()
    # Simple heuristic: insert jargon at random-ish positions based on count
    # We use a deterministic approach based on text length to avoid randomness
    if count <= 0 or len(words) == 0:
        return text
    
    insert_positions = []
    step = max(1, len(words) // (count + 1))
    for i in range(1, count + 1):
        pos = min(i * step, len(words) - 1)
        insert_positions.append(pos)
    
    new_words = []
    jargon_idx = 0
    for i, word in enumerate(words):
        new_words.append(word)
        if i in insert_positions:
            jargon = JARGON_LIST[jargon_idx % len(JARGON_LIST)]
            # Insert jargon with a comma or space
            if i > 0 and not word.endswith(','):
                new_words.append(',')
            new_words.append(jargon)
            new_words.append(',')
        jargon_idx += 1
    
    return ' '.join(new_words)

def increase_complexity(text: str, jargon_factor: int, clause_factor: int, len_factor: float) -> str:
    """Increase text complexity by adding jargon, nested clauses, and lengthening sentences."""
    modified_text = text
    
    # 1. Insert jargon
    if jargon_factor > 0:
        # Estimate number of jargon insertions based on text length and factor
        num_jargon = max(1, int(len(text.split()) / 10 * jargon_factor))
        modified_text = insert_jargon(modified_text, num_jargon)
    
    # 2. Increase sentence length and add clauses
    # Simple heuristic: split by periods and recombine with added complexity markers
    sentences = re.split(r'([.!?])', modified_text)
    new_sentences = []
    
    for i in range(0, len(sentences) - 1, 2):
        sentence = sentences[i]
        punct = sentences[i+1] if i+1 < len(sentences) else '.'
        
        if len(sentence.strip()) > 0:
            # Add a clause if clause_factor > 0
            if clause_factor > 0:
                # Add a subordinate clause
                clauses = ['which implies that', 'given that', 'inasmuch as', 'whereas', 'notwithstanding that']
                clause = clauses[clause_factor % len(clauses)]
                # Insert clause in the middle of the sentence
                words = sentence.split()
                if len(words) > 2:
                    mid = len(words) // 2
                    words.insert(mid, clause)
                    sentence = ' '.join(words)
            
            new_sentences.append(sentence + punct)
        
        if i+2 < len(sentences):
            new_sentences.append(sentences[i+2]) # Keep the next sentence start if exists
    
    modified_text = ' '.join(new_sentences)
    
    # 3. Increase length factor (simple expansion)
    # This is a placeholder for more sophisticated expansion logic
    # We can repeat certain phrases or add filler words based on len_factor
    if len_factor > 1.0:
        words = modified_text.split()
        target_len = int(len(words) * len_factor)
        if target_len > len(words):
            # Add filler words or repeat key concepts
            filler_words = ['furthermore', 'moreover', 'consequently', 'indeed', 'thus']
            current_len = len(words)
            while current_len < target_len:
                filler = filler_words[current_len % len(filler_words)]
                words.append(filler)
                current_len += 1
            modified_text = ' '.join(words)
    
    return modified_text

def generate_complex_tier(moderate_text: str, target_fk_diff: float = 5.0, min_jaccard: float = 0.85) -> Tuple[str, Dict[str, float]]:
    """
    Generate a complex tier from moderate text with a 3-attempt adjustment loop.
    Returns (complex_text, metrics_dict).
    """
    metrics = {}
    
    # Calculate baseline FK of moderate text
    base_fk = calculate_flesch_kincaid(moderate_text)
    target_fk = base_fk + target_fk_diff
    
    best_attempt_text = moderate_text
    best_attempt_metrics = {'fk_diff': 0.0, 'jaccard': 1.0, 'fk_score': base_fk}
    
    for attempt_idx, params in enumerate(AGGRESSIVENESS_LEVELS):
        logger.info(f"Attempt {attempt_idx + 1}/{MAX_ATTEMPTS} with params: {params}")
        
        complex_text = increase_complexity(
            moderate_text, 
            jargon_factor=params['jargon_factor'], 
            clause_factor=params['clause_factor'], 
            len_factor=params['len_factor']
        )
        
        # Calculate metrics
        fk_score = calculate_flesch_kincaid(complex_text)
        fk_diff = fk_score - base_fk
        jaccard = calculate_jaccard_similarity(moderate_text, complex_text)
        
        current_metrics = {
            'fk_diff': fk_diff,
            'jaccard': jaccard,
            'fk_score': fk_score
        }
        
        # Check constraints
        if fk_diff >= target_fk_diff and jaccard >= min_jaccard:
            logger.info(f"Success on attempt {attempt_idx + 1}: FK diff={fk_diff:.2f}, Jaccard={jaccard:.2f}")
            return complex_text, current_metrics
        
        # Track best attempt for potential fallback or error reporting
        # We prefer higher FK diff if Jaccard is met, or higher Jaccard if FK is close
        if jaccard >= min_jaccard and fk_diff > best_attempt_metrics['fk_diff']:
            best_attempt_text = complex_text
            best_attempt_metrics = current_metrics
        elif jaccard > best_attempt_metrics['jaccard'] and fk_diff >= target_fk_diff * 0.8: # Allow some slack
            best_attempt_text = complex_text
            best_attempt_metrics = current_metrics
    
    # If all attempts fail
    logger.warning(f"All {MAX_ATTEMPTS} attempts failed to meet constraints.")
    logger.warning(f"Best attempt metrics: {best_attempt_metrics}")
    logger.warning(f"Constraints required: FK diff >= {target_fk_diff}, Jaccard >= {min_jaccard}")
    
    # Raise ValueError as per task requirement
    raise ValueError(
        f"Failed to generate complex tier meeting constraints after {MAX_ATTEMPTS} attempts. "
        f"Best attempt FK diff: {best_attempt_metrics['fk_diff']:.2f} (required >= {target_fk_diff}), "
        f"Jaccard: {best_attempt_metrics['jaccard']:.2f} (required >= {min_jaccard}). "
        f"Moderate text length: {len(moderate_text)}."
    )

def generate_complex_tiers(moderate_tiers: List[Dict[str, Any]], target_fk_diff: float = 5.0, min_jaccard: float = 0.85) -> List[Dict[str, Any]]:
    """Generate complex tiers for all moderate tiers."""
    complex_tiers = []
    for i, row in enumerate(moderate_tiers):
        unit_id = row.get('unit_id', row.get('id', f'unit_{i}'))
        moderate_text = row.get('text', row.get('content', ''))
        
        if not moderate_text:
            logger.warning(f"Skipping unit {unit_id}: no text found.")
            continue
        
        try:
            complex_text, metrics = generate_complex_tier(moderate_text, target_fk_diff, min_jaccard)
            complex_tiers.append({
                'unit_id': unit_id,
                'text': complex_text,
                'source_text': moderate_text,
                'fk_diff': metrics['fk_diff'],
                'jaccard': metrics['jaccard'],
                'fk_score': metrics['fk_score']
            })
            logger.info(f"Generated complex tier for {unit_id}")
        except ValueError as e:
            logger.error(f"Failed to generate complex tier for {unit_id}: {e}")
            # Re-raise to fail the task as per requirement
            raise e
    
    return complex_tiers

def save_complex_tiers(complex_tiers: List[Dict[str, Any]], output_path: str):
    """Save complex tiers to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['unit_id', 'text', 'source_text', 'fk_diff', 'jaccard', 'fk_score']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in complex_tiers:
            writer.writerow(row)
    logger.info(f"Saved {len(complex_tiers)} complex tiers to {output_path}")

def main():
    """Main entry point for generating complex tiers."""
    # Define paths
    moderate_tiers_path = 'data/explanation_tiers/moderate_tiers.csv'
    output_path = 'data/explanation_tiers/complex_tiers.csv'
    
    # Load moderate tiers
    logger.info(f"Loading moderate tiers from {moderate_tiers_path}")
    try:
        moderate_tiers = load_moderate_tiers(moderate_tiers_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    if not moderate_tiers:
        logger.error("No moderate tiers found to process.")
        sys.exit(1)
    
    # Generate complex tiers
    logger.info(f"Generating complex tiers (target FK diff >= 5.0, Jaccard >= 0.85)")
    try:
        complex_tiers = generate_complex_tiers(moderate_tiers, target_fk_diff=5.0, min_jaccard=0.85)
    except ValueError as e:
        logger.error(f"Complex tier generation failed: {e}")
        sys.exit(1)
    
    # Save results
    save_complex_tiers(complex_tiers, output_path)
    logger.info("Complex tier generation completed successfully.")

if __name__ == '__main__':
    main()
