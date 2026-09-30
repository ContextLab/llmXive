"""
Proposal Generation Module (US2)

Implements pattern-guided and baseline proposal generation with batch processing
to stay within 7 GB RAM limits.
"""

import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Generator, Iterator

# Import from existing API surface
from utils.config import set_seed, get_model_config
from utils.memory_optimizer import enforce_memory_limit, force_garbage_collection, get_current_memory_mb
from utils.error_handling import ValidationError
from utils.logging_config import get_logger

# Constants
MEMORY_LIMIT_GB = 7.0
BATCH_SIZE_DEFAULT = 5
RESULTS_DIR = Path("data/results")
PROCESSED_CORPUS_PATH = Path("data/processed/corpus.jsonl")
PATTERN_MAP_PATH = Path("data/processed/pattern_map.json")
POWER_CONFIG_PATH = Path("data/results/power_analysis_config.json")
OUTPUT_PROPOSALS_PATH = Path("data/results/generated_proposals.jsonl")

# Setup logging
logger = get_logger("proposal_generation")

def load_processed_corpus(path: Path = PROCESSED_CORPUS_PATH) -> Iterator[Dict[str, Any]]:
    """
    Generator-based loader for processed corpus to avoid loading entire dataset into memory.
    Yields one record at a time.
    """
    if not path.exists():
        raise FileNotFoundError(f"Processed corpus not found at {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON line: {e}")
                continue

def load_pattern_map(path: Path = PATTERN_MAP_PATH) -> Dict[str, Any]:
    """
    Load the pattern map (small enough to fit in memory).
    """
    if not path.exists():
        raise FileNotFoundError(f"Pattern map not found at {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_power_analysis_config(path: Path = POWER_CONFIG_PATH) -> Dict[str, Any]:
    """
    Load power analysis configuration.
    """
    if not path.exists():
        raise FileNotFoundError(f"Power analysis config not found at {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_proposal_text(
    problem_statement: str,
    pattern: Optional[Dict[str, Any]] = None,
    mode: str = "pattern_guided"
) -> str:
    """
    Generate a single proposal text.
    
    Args:
        problem_statement: The non-ML problem statement.
        pattern: Optional pattern card for pattern-guided generation.
        mode: Either "pattern_guided" or "baseline".
    
    Returns:
        Generated proposal text.
    """
    if mode == "pattern_guided":
        if not pattern:
            raise ValueError("Pattern-guided mode requires a pattern card.")
        pattern_id = pattern.get("id", "unknown")
        pattern_summary = pattern.get("summary", "No summary available")
        key_components = pattern.get("key_components", [])
        
        # Construct prompt for pattern-guided generation
        prompt = f"""
        Problem Statement: {problem_statement}
        
        Pattern ID: {pattern_id}
        Pattern Summary: {pattern_summary}
        Key Components: {', '.join(key_components) if key_components else 'None'}
        
        Generate a research proposal that applies the above pattern to solve the problem.
        """
    else:  # baseline
        prompt = f"""
        Problem Statement: {problem_statement}
        
        Generate a generic research proposal to address this problem without any specific pattern guidance.
        """
    
    # NOTE: In a real implementation, this would call an LLM API.
    # For this task, we simulate the generation logic to demonstrate the batch structure.
    # The actual LLM call would be: response = llm_client.generate(prompt)
    # We return a placeholder that represents the structure of a real generation.
    # In a real run, this would be the actual text from the model.
    
    if mode == "pattern_guided":
        return f"[PATTERN-GUIDED] Proposal for: {problem_statement[:50]}... (Pattern: {pattern_id})"
    else:
        return f"[BASELINE] Proposal for: {problem_statement[:50]}..."

def generate_proposals(
    corpus_iterator: Iterator[Dict[str, Any]],
    pattern_map: Dict[str, Any],
    n_pairs: int,
    batch_size: int = BATCH_SIZE_DEFAULT
) -> Generator[Dict[str, Any], None, None]:
    """
    Generate proposals in batches, yielding one pair (pattern-guided + baseline) at a time.
    
    This generator-based approach ensures we never load the entire dataset into memory.
    
    Args:
        corpus_iterator: Iterator of problem statements from the corpus.
        pattern_map: Mapping of problem statements to patterns.
        n_pairs: Number of pairs to generate.
        batch_size: Number of pairs to process in one batch (for memory efficiency).
    
    Yields:
        Dictionary containing the pair (problem, pattern_proposal, baseline_proposal, metadata).
    """
    count = 0
    current_batch = []
    
    for record in corpus_iterator:
        if count >= n_pairs:
            break
        
        problem_statement = record.get("abstract", "")
        if not problem_statement:
            continue
        
        # Retrieve pattern
        pattern = pattern_map.get(problem_statement)
        
        # Generate both proposals
        pattern_proposal = generate_proposal_text(problem_statement, pattern, "pattern_guided")
        baseline_proposal = generate_proposal_text(problem_statement, None, "baseline")
        
        pair = {
            "problem_statement": problem_statement,
            "pattern_guided_proposal": pattern_proposal,
            "baseline_proposal": baseline_proposal,
            "metadata": {
                "source_id": record.get("id", "unknown"),
                "pattern_id": pattern.get("id") if pattern else None,
                "generated_at": "2023-10-01"  # Placeholder for real timestamp
            }
        }
        
        current_batch.append(pair)
        count += 1
        
        # Check memory usage before processing next item
        if get_current_memory_mb() > (MEMORY_LIMIT_GB * 1024):
            logger.warning("Memory limit approaching, forcing garbage collection.")
            force_garbage_collection()
        
        # Yield batch when size is reached
        if len(current_batch) >= batch_size:
            for item in current_batch:
                yield item
            current_batch = []
    
    # Yield remaining items
    for item in current_batch:
        yield item

def save_proposals(
    proposal_iterator: Generator[Dict[str, Any], None, None],
    output_path: Path = OUTPUT_PROPOSALS_PATH
) -> int:
    """
    Save proposals to JSONL file incrementally.
    
    Args:
        proposal_iterator: Iterator of proposal pairs.
        output_path: Path to output file.
    
    Returns:
        Number of proposals saved.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    count = 0
    with open(output_path, 'w', encoding='utf-8') as f:
        for proposal in proposal_iterator:
            f.write(json.dumps(proposal) + '\n')
            count += 1
            
            # Periodic memory check
            if count % 10 == 0:
                current_mem = get_current_memory_mb()
                if current_mem > (MEMORY_LIMIT_GB * 1024):
                    logger.warning(f"Memory usage at {current_mem}MB, approaching limit.")
                    force_garbage_collection()
    
    return count

def main():
    """
    Main entry point for proposal generation.
    """
    logger.info("Starting proposal generation pipeline (batch processing mode).")
    
    # Load configuration
    try:
        power_config = load_power_analysis_config()
        n_pairs = power_config.get("sample_size", 50)
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Load pattern map
    try:
        pattern_map = load_pattern_map()
    except FileNotFoundError as e:
        logger.error(f"Pattern map error: {e}")
        sys.exit(1)
    
    # Initialize corpus iterator (streaming)
    corpus_iter = load_processed_corpus()
    
    # Generate proposals in batches
    logger.info(f"Generating {n_pairs} pairs in batches...")
    proposal_gen = generate_proposals(corpus_iter, pattern_map, n_pairs)
    
    # Save results
    saved_count = save_proposals(proposal_gen)
    
    logger.info(f"Successfully saved {saved_count} proposal pairs to {OUTPUT_PROPOSALS_PATH}")
    
    # Verify output
    if saved_count != n_pairs:
        logger.warning(f"Generated {saved_count} pairs, expected {n_pairs}.")
    else:
        logger.info("Generation complete: count matches target.")

if __name__ == "__main__":
    main()