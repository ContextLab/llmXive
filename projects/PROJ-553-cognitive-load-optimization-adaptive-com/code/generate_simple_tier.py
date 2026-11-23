"""
T023: Implement "Simple" tier generation.
Reads from data/processed/instructional_units.csv and writes to data/explanation_tiers/simple_tiers.csv.
Ensures Flesch-Kincaid difference vs moderate >= 5 points AND Jaccard similarity >= 0.85.
Uses a deterministic 3-attempt adjustment loop.
"""
import os
import sys
import logging
import re
import csv
import time
from pathlib import Path
from typing import List, Dict, Tuple

# Import existing utilities from project API surface
try:
    from utils import calculate_flesch_kincaid, calculate_jaccard_similarity
except ImportError:
    # Fallback for direct execution context if utils is not in path yet
    sys.path.insert(0, str(Path(__file__).parent))
    from utils import calculate_flesch_kincaid, calculate_jaccard_similarity

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
JARGON_LIST = [
    'pedagogical', 'scaffolding', 'metacognition', 'heuristic',
    'cognitive load', 'schema', 'interference', 'elaboration'
]
MAX_ATTEMPTS = 3
MIN_JACCARD = 0.85
MIN_FK_DIFF = 5.0  # Moderate - Simple must be >= 5.0

def load_moderate_tiers(filepath: Path) -> List[Dict]:
    """Load the moderate tiers CSV."""
    if not filepath.exists():
        raise FileNotFoundError(f"Moderate tiers file not found: {filepath}")
    
    rows = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    logger.info(f"Loaded {len(rows)} moderate tiers from {filepath}")
    return rows

def save_simple_tiers(rows: List[Dict], filepath: Path):
    """Save the simple tiers to CSV."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ['interaction_id', 'moderate_text', 'simple_text']
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    logger.info(f"Saved {len(rows)} simple tiers to {filepath}")

def simplify_text(text: str, attempt: int) -> str:
    """
    Apply simplification rules based on attempt number.
    Attempt 1: Mild simplification.
    Attempt 2: Moderate simplification.
    Attempt 3: Aggressive simplification.
    """
    if not text:
        return text

    # Convert to lowercase for matching but preserve original case for output where possible
    # We will do replacements on the original text
    simplified = text

    # 1. Remove or replace jargon words
    # Map jargon to simpler alternatives
    jargon_map = {
        'pedagogical': 'teaching',
        'scaffolding': 'support',
        'metacognition': 'thinking about thinking',
        'heuristic': 'rule of thumb',
        'cognitive load': 'mental effort',
        'schema': 'mental model',
        'interference': 'distraction',
        'elaboration': 'detail'
    }
    
    for jargon, simple in jargon_map.items():
        # Case-insensitive replacement
        pattern = re.compile(re.escape(jargon), re.IGNORECASE)
        simplified = pattern.sub(simple, simplified)

    # 2. Reduce sentence length by splitting long sentences
    # Simple heuristic: split on common conjunctions if sentence is too long
    if attempt >= 2:
        long_sentence_threshold = 25 if attempt == 2 else 15
        sentences = re.split(r'(?<=[.!?])\s+', simplified)
        new_sentences = []
        for sent in sentences:
            words = sent.split()
            if len(words) > long_sentence_threshold:
                # Try to split at conjunctions
                split_points = [m.start() for m in re.finditer(r'\s+(and|but|or|so|because)\s+', sent, re.IGNORECASE)]
                if split_points:
                    # Split at the first conjunction found
                    split_idx = split_points[0]
                    part1 = sent[:split_idx].strip()
                    part2 = sent[split_idx:].strip()
                    # Ensure part2 starts with conjunction
                    if not re.match(r'^\s*(and|but|or|so|because)', part2, re.IGNORECASE):
                        part2 = part2.lstrip()
                    new_sentences.append(part1)
                    new_sentences.append(part2)
                else:
                    # Hard split if no conjunctions
                    mid = len(words) // 2
                    part1 = ' '.join(words[:mid])
                    part2 = ' '.join(words[mid:])
                    new_sentences.append(part1)
                    new_sentences.append(part2)
            else:
                new_sentences.append(sent)
        simplified = ' '.join(new_sentences)

    # 3. Simplify syntax (remove complex clauses)
    if attempt >= 3:
        # Remove relative clauses starting with "which", "that", "who" if they are non-essential
        # This is a simplified heuristic
        simplified = re.sub(r'\s+which\s+[^,]+,', ',', simplified, flags=re.IGNORECASE)
        simplified = re.sub(r'\s+that\s+[^,]+,', ',', simplified, flags=re.IGNORECASE)
        
        # Remove passive voice markers (heuristic)
        simplified = re.sub(r'\s+is\s+([a-z]+)ed\s+', r' \1s ', simplified, flags=re.IGNORECASE)
        simplified = re.sub(r'\s+was\s+([a-z]+)ed\s+', r' \1d ', simplified, flags=re.IGNORECASE)

    return simplified.strip()

def iterative_simplify(moderate_text: str, target_fk_diff: float, min_jaccard: float) -> Tuple[str, Dict]:
    """
    Implement the deterministic 3-attempt adjustment loop.
    Returns (simplified_text, metrics_dict).
    """
    best_attempt_text = moderate_text
    best_metrics = {
        'fk_diff': 0.0,
        'jaccard': 0.0,
        'attempt': 0,
        'failed': True,
        'reason': 'No attempt made'
    }

    moderate_fk = calculate_flesch_kincaid(moderate_text)
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        logger.info(f"Attempting simplification (Attempt {attempt}/{MAX_ATTEMPTS})")
        simple_text = simplify_text(moderate_text, attempt)
        
        simple_fk = calculate_flesch_kincaid(simple_text)
        fk_diff = moderate_fk - simple_fk
        jaccard = calculate_jaccard_similarity(moderate_text, simple_text)
        
        metrics = {
            'fk_diff': fk_diff,
            'jaccard': jaccard,
            'attempt': attempt,
            'simple_fk': simple_fk,
            'moderate_fk': moderate_fk
        }
        
        logger.info(f"Attempt {attempt}: FK Diff={fk_diff:.2f}, Jaccard={jaccard:.3f}")
        
        # Update best attempt if this is better or the first one
        if attempt == 1:
            best_attempt_text = simple_text
            best_metrics = metrics
        
        # Check constraints
        if fk_diff >= target_fk_diff and jaccard >= min_jaccard:
            logger.info(f"Constraints met on attempt {attempt}!")
            metrics['failed'] = False
            metrics['reason'] = 'Success'
            return simple_text, metrics
        
        # If this attempt is better than the previous best (closer to constraints), keep it
        # We prioritize meeting FK diff first, then Jaccard
        current_score = (fk_diff if fk_diff >= target_fk_diff else 0) + (jaccard if jaccard >= min_jaccard else 0)
        best_score = (best_metrics['fk_diff'] if best_metrics['fk_diff'] >= target_fk_diff else 0) + (best_metrics['jaccard'] if best_metrics['jaccard'] >= min_jaccard else 0)
        
        if current_score > best_score or (current_score == best_score and fk_diff > best_metrics['fk_diff']):
            best_attempt_text = simple_text
            best_metrics = metrics

    # All attempts failed
    best_metrics['failed'] = True
    best_metrics['reason'] = f"Failed after {MAX_ATTEMPTS} attempts. Best FK Diff: {best_metrics['fk_diff']:.2f} (req: {target_fk_diff}), Best Jaccard: {best_metrics['jaccard']:.3f} (req: {min_jaccard})"
    logger.warning(f"Failed to meet constraints for text. {best_metrics['reason']}")
    return best_attempt_text, best_metrics

def generate_simple_tiers(moderate_rows: List[Dict]) -> List[Dict]:
    """Generate simple tiers for all moderate rows."""
    results = []
    failed_count = 0

    for row in moderate_rows:
        interaction_id = row.get('interaction_id', 'unknown')
        moderate_text = row.get('moderate_text', '')
        
        if not moderate_text:
            logger.warning(f"No text found for interaction {interaction_id}, skipping.")
            continue

        simple_text, metrics = iterative_simplify(moderate_text, MIN_FK_DIFF, MIN_JACCARD)
        
        result_row = {
            'interaction_id': interaction_id,
            'moderate_text': moderate_text,
            'simple_text': simple_text,
            'fk_diff': metrics['fk_diff'],
            'jaccard': metrics['jaccard'],
            'attempts': metrics['attempt'],
            'status': 'success' if not metrics['failed'] else 'failed'
        }
        results.append(result_row)
        
        if metrics['failed']:
            failed_count += 1
            # Raise error if all attempts fail for a specific row as per task requirement
            # The task says "If all 3 attempts fail, raise a ValueError"
            # However, to be robust for the pipeline, we might want to log and continue or stop.
            # The task description: "If all 3 attempts fail, raise a ValueError with the best attempt's metrics..."
            # We will raise the error to strictly follow the task.
            raise ValueError(
                f"Simple tier generation failed for interaction {interaction_id}. "
                f"Metrics: {metrics}"
            )

    if failed_count > 0:
        logger.warning(f"Generated {len(results) - failed_count} simple tiers, {failed_count} failed.")
    else:
        logger.info(f"Successfully generated {len(results)} simple tiers.")
    
    return results

def main():
    """Main entry point for T023."""
    logger.info("Starting Simple Tier Generation (T023)...")
    
    # Define paths
    base_dir = Path(__file__).parent.parent
    input_path = base_dir / 'data' / 'processed' / 'instructional_units.csv'
    moderate_path = base_dir / 'data' / 'explanation_tiers' / 'moderate_tiers.csv'
    output_path = base_dir / 'data' / 'explanation_tiers' / 'simple_tiers.csv'
    
    # Check input files
    if not moderate_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {moderate_path}. "
            "Please ensure T022b (Moderate Tier Generation) has completed successfully."
        )
    
    try:
        # Load moderate tiers
        moderate_rows = load_moderate_tiers(moderate_path)
        
        # Generate simple tiers
        simple_rows = generate_simple_tiers(moderate_rows)
        
        # Save results
        save_simple_tiers(simple_rows, output_path)
        
        logger.info("Simple Tier Generation completed successfully.")
        
    except ValueError as e:
        logger.error(f"Generation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()