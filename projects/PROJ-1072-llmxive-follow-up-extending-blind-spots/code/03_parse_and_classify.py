import argparse
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

from sentence_transformers import SentenceTransformer
import numpy as np

from utils.logging_config import get_logger, setup_root_logger
from utils.semantic_matcher import encode_texts, cosine_similarity, is_paraphrase

logger = get_logger(__name__)

# --- Configuration Constants ---
TOKEN_WINDOW_SIZE = 256
DEFAULT_THRESHOLD = 0.72  # Fallback if file missing, but task requires reading it

def setup_logging():
    """Configure logging for the script."""
    setup_root_logger()
    return logger

def load_traces(trace_path: Path) -> List[Dict[str, Any]]:
    """Load CoT traces from JSONL file."""
    traces = []
    with open(trace_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                traces.append(json.loads(line))
    logger.info(f"Loaded {len(traces)} traces from {trace_path}")
    return traces

def load_task_records(task_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load task records into a dictionary keyed by task_id."""
    tasks = {}
    with open(task_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                task = json.loads(line)
                tasks[task['task_id']] = task
    logger.info(f"Loaded {len(tasks)} task records from {task_path}")
    return tasks

def load_threshold(threshold_path: Path) -> float:
    """Load the tuned threshold from JSON file."""
    if not threshold_path.exists():
        logger.error(f"Tuned threshold file not found: {threshold_path}")
        raise FileNotFoundError(f"Tuned threshold file not found: {threshold_path}")
    
    with open(threshold_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    threshold = data.get('optimal_threshold')
    if threshold is None:
        logger.error("optimal_threshold key missing in tuned_threshold.json")
        raise ValueError("optimal_threshold key missing in tuned_threshold.json")
    
    logger.info(f"Loaded threshold: {threshold}")
    return threshold

def load_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """Load the semantic matching model."""
    logger.info(f"Loading semantic model: {model_name}")
    model = SentenceTransformer(model_name)
    logger.info("Model loaded successfully")
    return model

def tokenize_text(text: str, tokenizer) -> List[str]:
    """Tokenize text using the provided tokenizer."""
    # Assuming tokenizer is a HuggingFace tokenizer or similar
    # Returns list of tokens (strings)
    return tokenizer.encode(text, add_special_tokens=False, return_tensors='pt')[0].tolist()

def reconstruct_text_from_tokens(tokens: List[int], tokenizer) -> str:
    """Reconstruct text from token IDs."""
    return tokenizer.decode(tokens, skip_special_tokens=True)

def find_exact_match(text: str, constraint: str) -> Optional[Tuple[int, int]]:
    """
    Find exact character offset of constraint string in text.
    Returns (start, end) or None if not found.
    Implements word-boundary check to avoid false positives.
    """
    if not constraint or not text:
        return None
    
    # Use regex with word boundaries for robust matching
    # Escape special regex characters in constraint
    escaped_constraint = re.escape(constraint)
    # Use \b for word boundary, but handle cases where constraint might not be surrounded by standard word chars
    # A more robust approach for "constraint" which might be a phrase:
    pattern = re.compile(r'\b' + escaped_constraint + r'\b', re.IGNORECASE)
    match = pattern.search(text)
    
    if match:
        return (match.start(), match.end())
    return None

def find_semantic_match(text_segment: str, constraint: str, model: SentenceTransformer, threshold: float) -> bool:
    """
    Use semantic matching to detect paraphrased constraints.
    Uses all-MiniLM-L6-v2 and the provided threshold.
    """
    if not text_segment or not constraint:
        return False
    
    try:
        # Encode texts
        embeddings = encode_texts([text_segment, constraint], model)
        
        # Compute cosine similarity
        # embeddings shape: (2, dim)
        sim = cosine_similarity(embeddings[0].unsqueeze(0), embeddings[1].unsqueeze(0))
        similarity_score = float(sim[0][0])
        
        logger.debug(f"Semantic similarity: {similarity_score:.4f} (threshold: {threshold})")
        
        return similarity_score >= threshold
    except Exception as e:
        logger.warning(f"Semantic matching failed: {e}")
        return False

def parse_trace(trace: Dict[str, Any], constraint: str, tokenizer, model: SentenceTransformer, threshold: float) -> Dict[str, Any]:
    """
    Parse a single trace to find first/last constraint offsets.
    Checks first 256 tokens and last 256 tokens.
    Falls back to semantic matching if exact match fails.
    """
    trace_text = trace.get('cot_trace', '')
    task_id = trace.get('task_id', 'unknown')
    
    if not trace_text:
        return {
            'task_id': task_id,
            'first_offset': None,
            'last_offset': None,
            'first_mention_type': 'none',
            'last_mention_type': 'none',
            'error': 'Empty trace'
        }
    
    # Tokenize
    try:
        token_ids = tokenizer.encode(trace_text, add_special_tokens=False, return_tensors='pt')[0].tolist()
    except Exception as e:
        logger.warning(f"Tokenization failed for {task_id}: {e}")
        return {
            'task_id': task_id,
            'first_offset': None,
            'last_offset': None,
            'first_mention_type': 'none',
            'last_mention_type': 'none',
            'error': f'Tokenization failed: {e}'
        }
    
    # Define windows
    first_window_tokens = token_ids[:TOKEN_WINDOW_SIZE]
    last_window_tokens = token_ids[-TOKEN_WINDOW_SIZE:] if len(token_ids) > TOKEN_WINDOW_SIZE else token_ids
    
    # Reconstruct text for windows
    first_window_text = tokenizer.decode(first_window_tokens, skip_special_tokens=True)
    last_window_text = tokenizer.decode(last_window_tokens, skip_special_tokens=True)
    
    # Find first mention
    first_offset = None
    first_type = 'none'
    
    # Try exact match in first window
    exact_match = find_exact_match(first_window_text, constraint)
    if exact_match:
        first_offset = exact_match[0]
        first_type = 'exact'
    else:
        # Try semantic match
        if find_semantic_match(first_window_text, constraint, model, threshold):
            first_offset = 0  # Approximate, as semantic match doesn't give offset
            first_type = 'semantic'
    
    # Find last mention
    last_offset = None
    last_type = 'none'
    
    # Try exact match in last window
    exact_match = find_exact_match(last_window_text, constraint)
    if exact_match:
        # Adjust offset to be relative to full text
        # We need to estimate where this window starts in the full text
        # For simplicity, we report offset within the window if semantic, or approximate
        # A more accurate way: find last occurrence in full text
        last_exact_full = find_exact_match(trace_text, constraint)
        if last_exact_full:
            last_offset = last_exact_full[0]
            last_type = 'exact'
        else:
            last_offset = len(trace_text) - len(last_window_text) + exact_match[0]
            last_type = 'exact'
    else:
        # Try semantic match
        if find_semantic_match(last_window_text, constraint, model, threshold):
            # Estimate position: start of last window
            start_of_last_window = max(0, len(trace_text) - len(last_window_text))
            last_offset = start_of_last_window
            last_type = 'semantic'
    
    return {
        'task_id': task_id,
        'first_offset': first_offset,
        'last_offset': last_offset,
        'first_mention_type': first_type,
        'last_mention_type': last_type,
        'first_mention_found': first_offset is not None,
        'last_mention_found': last_offset is not None
    }

def classify_error(parsed_result: Dict[str, Any], task_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify error type based on temporal pattern of constraint mentions.
    Logic:
    - First Missing = Perceptual
    - First Present / Last Missing = Procedural
    - Both Present = Correct (assuming outcome matches, but we use mention pattern as predictor)
    """
    first_found = parsed_result.get('first_mention_found', False)
    last_found = parsed_result.get('last_mention_found', False)
    
    classification = 'unknown'
    reasoning = ''
    
    if not first_found:
        classification = 'Perceptual'
        reasoning = 'Constraint not mentioned in first window (Perceptual error)'
    elif first_found and not last_found:
        classification = 'Procedural'
        reasoning = 'Constraint mentioned early but not in last window (Procedural error)'
    elif first_found and last_found:
        classification = 'Correct'
        reasoning = 'Constraint mentioned in both windows (Correct execution)'
    else:
        reasoning = 'Unexpected state in classification logic'
    
    return {
        'classification': classification,
        'reasoning': reasoning,
        'first_mention_type': parsed_result.get('first_mention_type'),
        'last_mention_type': parsed_result.get('last_mention_type')
    }

def process_all_traces(traces: List[Dict], tasks: Dict, model: SentenceTransformer, tokenizer, threshold: float) -> List[Dict]:
    """Process all traces and classify errors."""
    results = []
    for trace in traces:
        task_id = trace.get('task_id')
        if task_id not in tasks:
            logger.warning(f"Task {task_id} not found in task records, skipping")
            continue
        
        task_record = tasks[task_id]
        constraint = task_record.get('constraint', '')
        
        if not constraint:
            logger.warning(f"No constraint found for task {task_id}, skipping")
            continue
        
        parsed = parse_trace(trace, constraint, tokenizer, model, threshold)
        classified = classify_error(parsed, task_record)
        
        result = {
            'task_id': task_id,
            'trace_id': trace.get('trace_id', task_id),
            'constraint': constraint,
            'parsed': parsed,
            'classification': classified
        }
        results.append(result)
    
    return results

def write_results(results: List[Dict], output_path: Path):
    """Write results to JSONL file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result) + '\n')
    logger.info(f"Wrote {len(results)} results to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Parse CoT traces and classify errors')
    parser.add_argument('--traces', type=str, required=True, help='Path to traces JSONL')
    parser.add_argument('--tasks', type=str, required=True, help='Path to task records JSONL')
    parser.add_argument('--output', type=str, required=True, help='Path to output JSONL')
    parser.add_argument('--threshold', type=str, required=True, help='Path to tuned threshold JSON')
    args = parser.parse_args()
    
    setup_logging()
    
    # Load resources
    traces = load_traces(Path(args.traces))
    tasks = load_task_records(Path(args.tasks))
    threshold = load_threshold(Path(args.threshold))
    model = load_model()
    
    # Get tokenizer from model
    tokenizer = model.tokenizer
    
    # Process
    results = process_all_traces(traces, tasks, model, tokenizer, threshold)
    
    # Write
    write_results(results, Path(args.output))
    
    logger.info("Processing complete")

if __name__ == '__main__':
    main()
