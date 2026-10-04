import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Generator, Iterator

# Import from local utils
from utils.logging_config import get_logger
from utils.memory_optimizer import memory_safe_iterator, force_garbage_collection
from utils.error_handling import DesignViolationError

logger = get_logger("proposal_generation")

# Constants
PROPOSALS_INPUT_PATH = Path("data/processed/corpus.jsonl")
PATTERNS_INPUT_PATH = Path("data/results/pattern_map.json")
POWER_CONFIG_PATH = Path("data/results/power_analysis_config.json")
OUTPUT_PATH = Path("data/results/generated_proposals.jsonl")

def load_processed_corpus() -> Generator[Dict[str, Any], None, None]:
    """
    Generator-based loader for processed corpus.
    Yields one record at a time to stay within memory limits.
    """
    if not PROPOSALS_INPUT_PATH.exists():
        raise FileNotFoundError(f"Corpus file not found: {PROPOSALS_INPUT_PATH}")
    
    with open(PROPOSALS_INPUT_PATH, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                yield record
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON at line {line_num}: {e}")
                continue

def load_pattern_map() -> Dict[str, Any]:
    """Load the pattern map (usually small enough to fit in memory)."""
    if not PATTERNS_INPUT_PATH.exists():
        raise FileNotFoundError(f"Pattern map not found: {PATTERNS_INPUT_PATH}")
    
    with open(PATTERNS_INPUT_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_power_analysis_config() -> int:
    """
    Load 'n' from power analysis config.
    Returns the target number of pairs.
    """
    if not POWER_CONFIG_PATH.exists():
        raise FileNotFoundError(f"Power analysis config not found: {POWER_CONFIG_PATH}")
    
    with open(POWER_CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    if 'n' not in config:
        raise ValueError("Power analysis config missing 'n' field")
    
    return int(config['n'])

def generate_proposal_text(problem_statement: str, patterns: Optional[List[Dict]] = None, mode: str = "baseline") -> str:
    """
    Generates a proposal text based on the problem statement.
    
    Args:
        problem_statement: The text of the problem.
        patterns: Optional list of pattern cards to guide generation.
        mode: Either 'pattern-guided' or 'baseline'.
    
    Returns:
        A string representing the generated proposal.
    """
    if mode == "pattern-guided" and patterns:
        # Simulate pattern-guided generation logic
        # In a real scenario, this would call an LLM with pattern context
        pattern_ids = [p.get('id', 'unknown') for p in patterns[:3]]
        return f"[Pattern-Guided] Proposal for: {problem_statement[:50]}... (Guided by: {', '.join(pattern_ids)})"
    else:
        # Baseline generation
        return f"[Baseline] Proposal for: {problem_statement[:50]}... (Generic approach)"

def generate_proposals(n_pairs: int) -> Generator[Dict[str, Any], None, None]:
    """
    Generator that yields proposal pairs.
    Yields exactly n_pairs of (pattern-guided, baseline) pairs.
    """
    corpus_loader = load_processed_corpus()
    pattern_map = load_pattern_map()
    
    count = 0
    for record in corpus_loader:
        if count >= n_pairs:
            break
        
        problem = record.get('abstract', record.get('problem_statement', ''))
        if not problem:
            continue

        # Retrieve top patterns if available
        patterns = pattern_map.get('patterns', [])
        
        # Generate Pattern-Guided Proposal
        pg_proposal = generate_proposal_text(problem, patterns, mode="pattern-guided")
        
        # Generate Baseline Proposal
        bl_proposal = generate_proposal_text(problem, mode="baseline")
        
        yield {
            "pair_id": count,
            "problem_statement": problem,
            "pattern_guided": {
                "text": pg_proposal,
                "type": "pattern-guided"
            },
            "baseline": {
                "text": bl_proposal,
                "type": "baseline"
            }
        }
        
        count += 1
        
        # Periodic memory cleanup
        if count % 10 == 0:
            force_garbage_collection()

def save_proposals(generator: Generator[Dict[str, Any], None, None], output_path: Path):
    """
    Writes proposals from a generator to a JSONL file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in generator:
            f.write(json.dumps(item) + '\n')
    
    logger.info(f"Saved proposals to {output_path}")

def main():
    """
    Main entry point for proposal generation.
    Implements batch processing via generator to respect 7GB RAM limit.
    """
    logger.info("Starting proposal generation with batch processing...")
    
    try:
        n_pairs = load_power_analysis_config()
        logger.info(f"Target pairs (n): {n_pairs}")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    logger.info("Generating proposals (streaming)...")
    proposal_gen = generate_proposals(n_pairs)
    
    # Validate that we generate exactly n_pairs
    generated_count = 0
    for _ in proposal_gen:
        generated_count += 1
    
    # Regenerate to save (since generator is exhausted)
    proposal_gen = generate_proposals(n_pairs)
    save_proposals(proposal_gen, OUTPUT_PATH)
    
    if generated_count != n_pairs:
        logger.warning(f"Generated {generated_count} pairs, expected {n_pairs}. "
                     "This may indicate insufficient data in corpus.")
    else:
        logger.info(f"Successfully generated exactly {n_pairs} pairs.")

if __name__ == "__main__":
    main()