import os
import sys
import logging
import re
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from existing utils
from utils import calculate_flesch_kincaid, calculate_jaccard_similarity

# Setup logging
logger = logging.getLogger(__name__)

# Predefined Jargon Dictionary (Domain: Cognitive Science & Learning)
JARGON_DICT = {
    "concept": "construct",
    "idea": "theoretical proposition",
    "understand": "comprehend",
    "learn": "acquire knowledge",
    "think": "cognate",
    "memory": "mnemonic retention",
    "problem": "cognitive challenge",
    "solution": "resolution strategy",
    "process": "cognitive mechanism",
    "result": "outcome variable",
    "use": "utilize",
    "show": "demonstrate",
    "help": "facilitate",
    "make": "engineer",
    "get": "obtain",
    "give": "provide",
    "take": "consume",
    "look": "perceive",
    "say": "articulate",
    "tell": "narrate",
    "go": "proceed",
    "come": "arrive",
    "do": "execute",
    "see": "observe",
    "know": "be cognizant",
    "want": "desire",
    "need": "require",
    "can": "possess the capacity",
    "will": "intend to",
    "would": "conditional intent",
    "should": "ought to",
    "must": "necessitate",
    "may": "permit",
    "might": "speculate",
    "could": "potential capacity",
    "shall": "obligation",
    "need": "necessitate",
    "used": "utilized",
    "using": "utilizing",
    "useful": "efficacious",
    "useless": "inefficacious",
    "user": "operator",
    "usage": "utilization",
    "useability": "usability",
    "useable": "usable",
    "usefully": "efficaciously",
    "uselessness": "inefficacy",
    "usefulness": "utility",
    "user-friendly": "ergonomically optimized",
    "user-interface": "human-computer interaction layer",
    "user-experience": "subjective phenomenological engagement",
    "user-centered": "operator-centric",
    "user-defined": "operator-specified",
    "user-generated": "operator-originated",
    "user-specific": "operator-tailored",
    "user-customization": "operator personalization",
    "user-profile": "operator demographic and psychometric profile",
    "user-preference": "operator heuristic bias",
    "user-behavior": "operator action pattern",
    "user-interaction": "operator-system transaction",
    "user-feedback": "operator response vector",
    "user-data": "operator telemetry",
    "user-privacy": "operator information sovereignty",
    "user-security": "operator data integrity",
    "user-safety": "operator physical and digital protection",
    "user-ethics": "operator moral framework",
    "user-legal": "operator compliance framework",
    "user-policy": "operator governance structure",
    "user-guideline": "operator heuristic protocol",
    "user-standard": "operator normative benchmark",
    "user-specification": "operator technical requirement",
    "user-documentation": "operator technical manual",
    "user-manual": "operator operational guide",
    "user-tutorial": "operator instructional module",
    "user-guide": "operator navigational aid",
    "user-help": "operator support system",
    "user-support": "operator assistance framework",
    "user-service": "operator provision",
    "user-product": "operator deliverable",
    "user-feature": "operator capability",
    "user-function": "operator operation",
    "user-module": "operator component",
    "user-component": "operator element",
    "user-system": "operator architecture",
    "user-platform": "operator infrastructure",
    "user-environment": "operator context",
    "user-setting": "operator configuration",
    "user-context": "operator situational frame",
    "user-scenario": "operator narrative",
    "user-case": "operator instance",
    "user-example": "operator illustration",
    "user-sample": "operator subset",
    "user-data-point": "operator telemetry instance",
    "user-record": "operator log entry",
    "user-entry": "operator record",
    "user-recorded": "operator logged",
    "user-logging": "operator telemetry capture",
    "user-tracing": "operator path analysis",
    "user-monitoring": "operator surveillance",
    "user-tracking": "operator trajectory analysis",
    "user-auditing": "operator compliance review",
    "user-reporting": "operator disclosure",
    "user-analysis": "operator investigation",
    "user-evaluation": "operator assessment",
    "user-assessment": "operator evaluation",
    "user-measurement": "operator quantification",
    "user-metric": "operator key performance indicator",
    "user-kpi": "operator performance indicator",
    "user-dashboard": "operator visualization panel",
    "user-chart": "operator graphical representation",
    "user-graph": "operator network diagram",
    "user-table": "operator data matrix",
    "user-list": "operator enumeration",
    "user-array": "operator sequence",
    "user-collection": "operator aggregation",
    "user-group": "operator cluster",
    "user-set": "operator collection",
    "user-union": "operator combination",
    "user-intersection": "operator overlap",
    "user-difference": "operator distinction",
    "user-complement": "operator remainder",
    "user-subset": "operator partial collection",
    "user-superset": "operator complete collection",
    "user-element": "operator constituent",
    "user-member": "operator constituent",
    "user-item": "operator unit",
    "user-unit": "operator element",
    "user-entity": "operator object",
    "user-object": "operator entity",
    "user-subject": "operator topic",
    "user-topic": "operator subject",
    "user-theme": "operator motif",
    "user-category": "operator classification",
    "user-class": "operator type",
    "user-type": "operator category",
    "user-kind": "operator variety",
    "user-sort": "operator classification",
    "user-variety": "operator diversity",
    "user-range": "operator spectrum",
    "user-scale": "operator magnitude",
    "user-level": "operator tier",
    "user-grade": "operator rank",
    "user-rank": "operator grade",
    "user-position": "operator location",
    "user-location": "operator position",
    "user-place": "operator site",
    "user-site": "operator place",
    "user-area": "operator region",
    "user-region": "operator area",
    "user-zone": "operator sector",
    "user-sector": "operator zone",
    "user-section": "operator division",
    "user-division": "operator section",
    "user-part": "operator segment",
    "user-segment": "operator part",
    "user-piece": "operator fragment",
    "user-fragment": "operator piece",
    "user-piece": "operator fragment",
    "user-fragment": "operator piece",
    "user-chunk": "operator unit",
    "user-block": "operator module",
    "user-unit": "operator element",
    "user-element": "operator constituent",
    "user-constituent": "operator element",
    "user-component": "operator element",
    "user-element": "operator constituent",
    "user-constituent": "operator element",
}

def load_moderate_tiers(filepath: str) -> List[Dict[str, Any]]:
    """Load moderate tiers from CSV."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Moderate tiers file not found: {filepath}")
    
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def insert_jargon(text: str, jargon_density: float = 0.3) -> str:
    """
    Insert jargon into text based on density.
    jargon_density: 0.0 to 1.0 (fraction of replaceable words to replace)
    """
    words = text.split()
    if not words:
        return text
    
    # Identify replaceable words (common words in our dict)
    replaceable_indices = []
    for i, word in enumerate(words):
        clean_word = re.sub(r'[^\w]', '', word).lower()
        if clean_word in JARGON_DICT:
            replaceable_indices.append(i)
    
    if not replaceable_indices:
        return text
    
    # Select words to replace based on density
    num_to_replace = max(1, int(len(replaceable_indices) * jargon_density))
    import random
    random.seed(42)  # For reproducibility
    indices_to_replace = random.sample(replaceable_indices, min(num_to_replace, len(replaceable_indices)))
    
    result_words = words.copy()
    for idx in indices_to_replace:
        original = result_words[idx]
        clean_word = re.sub(r'[^\w]', '', original).lower()
        punctuation = re.sub(r'\w', '', original)
        if clean_word in JARGON_DICT:
            replacement = JARGON_DICT[clean_word]
            # Preserve capitalization
            if original[0].isupper():
                replacement = replacement.capitalize()
            result_words[idx] = replacement + punctuation
    
    return ' '.join(result_words)

def increase_complexity(text: str, nesting_depth: int = 1) -> str:
    """
    Increase sentence complexity by adding subordinate clauses and conjunctions.
    nesting_depth: 0 to 3 (how many levels of subordination to add)
    """
    if nesting_depth == 0:
        return text
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    new_sentences = []
    
    for sentence in sentences:
        if len(sentence.strip()) < 10:
            new_sentences.append(sentence)
            continue
        
        # Add complexity based on depth
        if nesting_depth >= 1:
            # Add introductory clause
            intro_clauses = [
                "Given that ",
                "Considering that ",
                "In light of the fact that ",
                "Due to the observation that "
            ]
            import random
            random.seed(42)
            intro = random.choice(intro_clauses)
            sentence = intro + sentence.lower()
            sentence = sentence[0].upper() + sentence[1:]
        
        if nesting_depth >= 2:
            # Add relative clause
            if " that " in sentence.lower():
                # Insert additional clause
                parts = sentence.split(" that ", 1)
                if len(parts) == 2:
                    extra_clause = " which is a significant factor, "
                    sentence = parts[0] + " that" + extra_clause + parts[1]
            else:
                # Add at end
                sentence += " which is a notable consideration."
        
        if nesting_depth >= 3:
            # Add conditional clause
            sentence = "It is imperative to note that " + sentence
        
        new_sentences.append(sentence)
    
    return ' '.join(new_sentences)

def generate_complex_tier(moderate_text: str, target_fk_diff: float = 5.0, 
                          min_jaccard: float = 0.85, max_iterations: int = 10) -> Tuple[str, int]:
    """
    Generate complex tier with iterative refinement.
    Returns (complex_text, iterations_used)
    """
    # Calculate moderate FK score
    moderate_fk = calculate_flesch_kincaid(moderate_text)
    
    best_text = moderate_text
    best_diff = 0.0
    best_jaccard = 0.0
    best_iterations = 0
    
    for iteration in range(1, max_iterations + 1):
        # Adjust parameters based on iteration
        jargon_density = min(0.3, iteration * 0.05)
        nesting_depth = min(3, (iteration + 1) // 3)
        
        # Apply transformations
        text = moderate_text
        if jargon_density > 0:
            text = insert_jargon(text, jargon_density)
        if nesting_depth > 0:
            text = increase_complexity(text, nesting_depth)
        
        # Calculate metrics
        complex_fk = calculate_flesch_kincaid(text)
        fk_diff = complex_fk - moderate_fk
        jaccard = calculate_jaccard_similarity(moderate_text, text)
        
        logger.debug(f"Iteration {iteration}: FK_diff={fk_diff:.2f}, Jaccard={jaccard:.2f}")
        
        # Check if constraints met
        if fk_diff >= target_fk_diff and jaccard >= min_jaccard:
            return text, iteration
        
        # Track best if closer to target
        if fk_diff > best_diff and jaccard >= min_jaccard * 0.9:
            best_diff = fk_diff
            best_jaccard = jaccard
            best_text = text
            best_iterations = iteration
    
    # If we didn't meet constraints, raise error
    if best_diff < target_fk_diff or best_jaccard < min_jaccard:
        raise ValueError(
            f"Complex tier generation failed to meet constraints after {max_iterations} iterations. "
            f"Best FK diff: {best_diff:.2f} (target: {target_fk_diff}), "
            f"Best Jaccard: {best_jaccard:.2f} (target: {min_jaccard})"
        )
    
    return best_text, best_iterations

def generate_complex_tiers(moderate_tiers: List[Dict[str, Any]], 
                           output_path: str,
                           target_fk_diff: float = 5.0,
                           min_jaccard: float = 0.85,
                           max_iterations: int = 10) -> List[Dict[str, Any]]:
    """
    Generate complex tiers for all moderate tiers and save to CSV.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    for i, row in enumerate(moderate_tiers):
        unit_id = row.get('interaction_id', row.get('unit_id', f'unit_{i}'))
        moderate_text = row.get('text', row.get('moderate_tier', ''))
        
        if not moderate_text:
            logger.warning(f"Skipping unit {unit_id}: no text found")
            continue
        
        try:
            complex_text, iterations = generate_complex_tier(
                moderate_text, target_fk_diff, min_jaccard, max_iterations
            )
            results.append({
                'interaction_id': unit_id,
                'moderate_tier': moderate_text,
                'complex_tier': complex_text,
                'iterations_used': iterations,
                'status': 'success'
            })
            logger.info(f"Generated complex tier for {unit_id} in {iterations} iterations")
        except ValueError as e:
            logger.error(f"Failed to generate complex tier for {unit_id}: {e}")
            results.append({
                'interaction_id': unit_id,
                'moderate_tier': moderate_text,
                'complex_tier': '',
                'iterations_used': max_iterations,
                'status': 'failed',
                'error': str(e)
            })
    
    # Save to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['interaction_id', 'moderate_tier', 'complex_tier', 
                    'iterations_used', 'status']
        if any(r.get('status') == 'failed' for r in results):
            fieldnames.append('error')
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saved complex tiers to {output_path}")
    return results

def main():
    """Main entry point for complex tier generation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Paths
    moderate_tiers_path = "data/explanation_tiers/moderate_tiers.csv"
    output_path = "data/explanation_tiers/complex_tiers.csv"
    
    logger.info(f"Loading moderate tiers from {moderate_tiers_path}")
    moderate_tiers = load_moderate_tiers(moderate_tiers_path)
    logger.info(f"Loaded {len(moderate_tiers)} moderate tiers")
    
    logger.info("Generating complex tiers with iterative refinement...")
    results = generate_complex_tiers(
        moderate_tiers,
        output_path,
        target_fk_diff=5.0,
        min_jaccard=0.85,
        max_iterations=10
    )
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    logger.info(f"Generated {success_count}/{len(results)} complex tiers successfully")
    
    if success_count < len(results):
        logger.warning(f"{len(results) - success_count} tiers failed to meet constraints")
        sys.exit(1)
    
    logger.info("Complex tier generation completed successfully")

if __name__ == "__main__":
    main()
