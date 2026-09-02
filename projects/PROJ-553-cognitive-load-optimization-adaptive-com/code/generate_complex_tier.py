import os
import sys
import logging
import re
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from project utils for metrics
from utils import calculate_flesch_kincaid, calculate_jaccard_similarity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for tier generation constraints
MIN_FK_DIFFERENCE = 5.0
MIN_JACCARD_SIMILARITY = 0.85
MAX_ATTEMPTS = 10

def load_moderate_tiers(input_path: str) -> List[Dict[str, Any]]:
    """Load moderate tiers from CSV file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Moderate tiers file not found: {input_path}")
    
    tiers = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tiers.append(row)
    
    logger.info(f"Loaded {len(tiers)} moderate tiers from {input_path}")
    return tiers

def insert_jargon(text: str, complexity_level: float = 0.5) -> str:
    """
    Insert academic jargon and complex sentence structures to increase text complexity.
    Complexity level (0.0 to 1.0) controls the aggressiveness of modifications.
    """
    if not text:
        return text

    # Jargon insertion patterns based on complexity level
    jargon_map = {
        0.3: ["utilize", "facilitate", "implement", "methodology"],
        0.6: ["paradigm", "framework", "mechanism", "correlation", "variable"],
        0.9: ["epistemological", "heuristic", "ontological", "axiomatic", "dialectic"]
    }
    
    # Select jargon based on complexity level
    selected_jargon = []
    for level, words in jargon_map.items():
        if complexity_level >= level:
            selected_jargon.extend(words)
    
    # Simple sentence splitting to allow restructuring
    sentences = re.split(r'([.!?])', text)
    
    # Restructure sentences to be more complex
    complex_sentences = []
    for i, sentence in enumerate(sentences):
        if not sentence.strip():
            continue
        
        # Add academic connectors
        connectors = ["Furthermore,", "Consequently,", "In this regard,", "It is noteworthy that"]
        if i > 0 and selected_jargon and complexity_level > 0.5:
            connector = connectors[i % len(connectors)]
            sentence = f"{connector} {sentence}"
        
        # Insert jargon if possible
        if selected_jargon and len(sentence.split()) > 5:
            words = sentence.split()
            insert_pos = len(words) // 2
            jargon = selected_jargon[i % len(selected_jargon)]
            words.insert(insert_pos, jargon)
            sentence = ' '.join(words)
        
        complex_sentences.append(sentence)
    
    return ' '.join(complex_sentences)

def increase_complexity(text: str, target_fk_increase: float) -> str:
    """
    Iteratively increase text complexity until target Flesch-Kincaid increase is reached.
    Uses a combination of jargon insertion and sentence restructuring.
    """
    if not text:
        return text

    current_text = text
    current_fk = calculate_flesch_kincaid(text)
    target_fk = current_fk + target_fk_increase
    
    attempts = 0
    while attempts < MAX_ATTEMPTS:
        # Increase complexity level based on attempt number
        complexity_level = min(0.9, 0.3 + (attempts * 0.15))
        
        modified_text = insert_jargon(current_text, complexity_level)
        modified_fk = calculate_flesch_kincaid(modified_text)
        
        if modified_fk >= target_fk:
            # Check Jaccard similarity
            jaccard = calculate_jaccard_similarity(text, modified_text)
            if jaccard >= MIN_JACCARD_SIMILARITY:
                return modified_text
            else:
                # If Jaccard is too low, reduce modifications
                complexity_level = max(0.3, complexity_level - 0.1)
                modified_text = insert_jargon(text, complexity_level)
                modified_fk = calculate_flesch_kincaid(modified_text)
                if modified_fk >= target_fk:
                    return modified_text
                else:
                    # Cannot meet both constraints
                    logger.warning(f"Could not meet both FK and Jaccard constraints for text: {text[:50]}...")
                    # Return the best effort that meets FK requirement
                    return modified_text
        
        current_text = modified_text
        attempts += 1
    
    # If we reach max attempts, return the best effort
    logger.warning(f"Max attempts reached for complexity increase. Returning best effort.")
    return current_text

def generate_complex_tier(moderate_text: str, original_text: Optional[str] = None) -> Tuple[str, Dict[str, float]]:
    """
    Generate a complex tier from a moderate tier.
    Returns the complex text and metrics dictionary.
    """
    # Use original text if available for Jaccard calculation, otherwise use moderate
    source_text = original_text if original_text else moderate_text
    
    # Calculate current Flesch-Kincaid of moderate tier
    moderate_fk = calculate_flesch_kincaid(moderate_text)
    target_fk = moderate_fk + MIN_FK_DIFFERENCE
    
    # Generate complex version
    complex_text = increase_complexity(moderate_text, MIN_FK_DIFFERENCE)
    
    # Calculate metrics
    complex_fk = calculate_flesch_kincaid(complex_text)
    fk_difference = complex_fk - moderate_fk
    jaccard = calculate_jaccard_similarity(source_text, complex_text)
    
    metrics = {
        'moderate_fk': moderate_fk,
        'complex_fk': complex_fk,
        'fk_difference': fk_difference,
        'jaccard_similarity': jaccard
    }
    
    # Validate constraints
    if fk_difference < MIN_FK_DIFFERENCE:
        logger.warning(f"FK difference {fk_difference:.2f} is below threshold {MIN_FK_DIFFERENCE}")
    if jaccard < MIN_JACCARD_SIMILARITY:
        logger.warning(f"Jaccard similarity {jaccard:.2f} is below threshold {MIN_JACCARD_SIMILARITY}")
    
    return complex_text, metrics

def generate_complex_tiers(moderate_tiers: List[Dict[str, Any]], output_path: str) -> List[Dict[str, Any]]:
    """
    Generate complex tiers for all moderate tiers and save to CSV.
    Returns a list of results including metrics.
    """
    results = []
    
    for i, tier in enumerate(moderate_tiers):
        interaction_id = tier.get('interaction_id', f'unknown_{i}')
        moderate_text = tier.get('text', tier.get('instructional_unit', ''))
        original_text = tier.get('original_text', moderate_text)
        
        logger.info(f"Processing interaction {interaction_id} ({i+1}/{len(moderate_tiers)})")
        
        try:
            complex_text, metrics = generate_complex_tier(moderate_text, original_text)
            
            result = {
                'interaction_id': interaction_id,
                'original_text': original_text,
                'moderate_text': moderate_text,
                'complex_text': complex_text,
                'moderate_fk': metrics['moderate_fk'],
                'complex_fk': metrics['complex_fk'],
                'fk_difference': metrics['fk_difference'],
                'jaccard_similarity': metrics['jaccard_similarity']
            }
            results.append(result)
            
            # Log validation status
            fk_ok = metrics['fk_difference'] >= MIN_FK_DIFFERENCE
            jaccard_ok = metrics['jaccard_similarity'] >= MIN_JACCARD_SIMILARITY
            status = "PASS" if (fk_ok and jaccard_ok) else "FAIL"
            logger.info(f"  Status: {status} (FK diff: {metrics['fk_difference']:.2f}, Jaccard: {metrics['jaccard_similarity']:.2f})")
            
        except Exception as e:
            logger.error(f"Error processing interaction {interaction_id}: {str(e)}")
            # Still add a result entry with error info
            results.append({
                'interaction_id': interaction_id,
                'original_text': original_text,
                'moderate_text': moderate_text,
                'complex_text': '',
                'moderate_fk': 0.0,
                'complex_fk': 0.0,
                'fk_difference': 0.0,
                'jaccard_similarity': 0.0,
                'error': str(e)
            })
    
    # Save results to CSV
    save_complex_tiers(results, output_path)
    
    return results

def save_complex_tiers(results: List[Dict[str, Any]], output_path: str):
    """Save complex tiers to CSV file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'interaction_id', 'original_text', 'moderate_text', 'complex_text',
        'moderate_fk', 'complex_fk', 'fk_difference', 'jaccard_similarity'
    ]
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    
    logger.info(f"Saved {len(results)} complex tiers to {output_path}")

def main():
    """Main entry point for complex tier generation."""
    # Define paths
    moderate_tiers_path = "data/explanation_tiers/moderate_tiers.csv"
    output_path = "data/explanation_tiers/complex_tiers.csv"
    
    logger.info("Starting complex tier generation...")
    
    try:
        # Load moderate tiers
        moderate_tiers = load_moderate_tiers(moderate_tiers_path)
        
        if not moderate_tiers:
            raise ValueError("No moderate tiers found to process")
        
        # Generate complex tiers
        results = generate_complex_tiers(moderate_tiers, output_path)
        
        # Summary statistics
        total = len(results)
        passed = sum(1 for r in results if r.get('error') is None and 
                    r.get('fk_difference', 0) >= MIN_FK_DIFFERENCE and 
                    r.get('jaccard_similarity', 0) >= MIN_JACCARD_SIMILARITY)
        
        logger.info(f"Generation complete: {passed}/{total} tiers passed validation")
        
        if passed < total:
            logger.warning(f"{total - passed} tiers did not meet all constraints")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to generate complex tiers: {str(e)}")
        raise

if __name__ == "__main__":
    main()
