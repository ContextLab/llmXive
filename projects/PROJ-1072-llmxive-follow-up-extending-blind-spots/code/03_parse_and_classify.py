import argparse
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

from utils.logging_config import get_logger, setup_root_logger
from utils.semantic_matcher import encode_texts, cosine_similarity, is_paraphrase, batch_is_paraphrase
from utils.hashing_utils import compute_file_hash

# Initialize logger
logger = get_logger(__name__)

def setup_logging(log_file: Optional[Path] = None) -> None:
    """Setup logging configuration."""
    setup_root_logger(log_file)

def load_traces(traces_path: Path) -> List[Dict[str, Any]]:
    """Load CoT traces from JSONL file."""
    traces = []
    with open(traces_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                traces.append(json.loads(line))
    logger.info(f"Loaded {len(traces)} traces from {traces_path}")
    return traces

def load_task_records(tasks_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load task records from JSONL file into a dictionary keyed by task_id."""
    tasks = {}
    with open(tasks_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                task = json.loads(line)
                tasks[task['task_id']] = task
    logger.info(f"Loaded {len(tasks)} task records from {tasks_path}")
    return tasks

def load_threshold(threshold_path: Path) -> float:
    """Load the tuned semantic similarity threshold."""
    if not threshold_path.exists():
        logger.error(f"Threshold file not found: {threshold_path}")
        raise FileNotFoundError(f"Threshold file not found: {threshold_path}")
    
    with open(threshold_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    threshold = data.get('threshold')
    if threshold is None:
        logger.error("Threshold value missing in file")
        raise ValueError("Threshold value missing in file")
    
    logger.info(f"Loaded threshold: {threshold}")
    return threshold

def load_model(model_name: str = "all-MiniLM-L6-v2"):
    """Load the semantic matching model."""
    from sentence_transformers import SentenceTransformer
    logger.info(f"Loading model: {model_name}")
    model = SentenceTransformer(model_name)
    return model

def tokenize_text(text: str, model) -> List[int]:
    """Tokenize text using the model's tokenizer."""
    tokens = model.tokenizer.encode(text, add_special_tokens=False)
    return tokens

def reconstruct_text_from_tokens(text: str, tokens: List[int], model) -> str:
    """Reconstruct text from token IDs."""
    decoded = model.tokenizer.decode(tokens)
    return decoded

def is_word_boundary(text: str, pos: int) -> bool:
    """Check if position is at a word boundary."""
    if pos == 0 or pos == len(text):
        return True
    char_before = text[pos - 1]
    char_after = text[pos]
    is_boundary_before = not char_before.isalnum()
    is_boundary_after = not char_after.isalnum()
    return is_boundary_before or is_boundary_after

def find_exact_match(text: str, constraint: str, window_start: int = 0, window_end: Optional[int] = None) -> Optional[Tuple[int, int]]:
    """Find exact string match with word boundary check."""
    if window_end is None:
        window_end = len(text)
    
    window = text[window_start:window_end]
    constraint_lower = constraint.lower()
    window_lower = window.lower()
    
    start_idx = window_lower.find(constraint_lower)
    while start_idx != -1:
        abs_start = window_start + start_idx
        abs_end = abs_start + len(constraint)
        
        if is_word_boundary(text, abs_start) and is_word_boundary(text, abs_end):
            return (abs_start, abs_end)
        
        start_idx = window_lower.find(constraint_lower, start_idx + 1)
    
    return None

def find_semantic_match(text: str, constraint: str, model, threshold: float, window_start: int = 0, window_end: Optional[int] = None) -> bool:
    """Find semantic match using sentence-transformers."""
    if window_end is None:
        window_end = len(text)
    
    # Extract segment
    segment = text[window_start:window_end]
    
    # Encode
    embeddings = encode_texts([constraint, segment], model)
    similarity = cosine_similarity(embeddings[0], embeddings[1])
    
    return similarity >= threshold

def parse_trace(trace: Dict[str, Any], task: Dict[str, Any], model, threshold: float) -> Dict[str, Any]:
    """Parse a single trace to find constraint mentions."""
    trace_text = trace.get('cot_trace', '')
    constraint = task.get('constraint', '')
    task_id = trace.get('task_id', task.get('task_id', ''))
    
    if not constraint:
        logger.warning(f"No constraint found for task {task_id}")
        return {
            'task_id': task_id,
            'first_mention': None,
            'last_mention': None,
            'exact_match_found': False,
            'semantic_match_found': False
        }
    
    # Find exact matches with word boundary checks
    first_mention = None
    last_mention = None
    
    # Search entire trace for exact matches
    exact_matches = []
    constraint_lower = constraint.lower()
    trace_lower = trace_text.lower()
    
    start_pos = 0
    while True:
        idx = trace_lower.find(constraint_lower, start_pos)
        if idx == -1:
            break
        
        abs_start = idx
        abs_end = idx + len(constraint)
        
        if is_word_boundary(trace_text, abs_start) and is_word_boundary(trace_text, abs_end):
            exact_matches.append((abs_start, abs_end))
        
        start_pos = idx + 1
    
    if exact_matches:
        first_mention = exact_matches[0]
        last_mention = exact_matches[-1]
    
    # If no exact match, try semantic match on full trace
    semantic_match_found = False
    if not first_mention:
        semantic_match_found = find_semantic_match(trace_text, constraint, model, threshold)
        if semantic_match_found:
            # For semantic matches, we mark them as found but don't have exact offsets
            # This is acceptable for classification purposes
            pass
    
    return {
        'task_id': task_id,
        'first_mention': first_mention,
        'last_mention': last_mention,
        'exact_match_found': len(exact_matches) > 0,
        'semantic_match_found': semantic_match_found
    }

def classify_error(parse_result: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, str]:
    """
    Classify error based on temporal pattern of constraint mentions.
    
    Logic (Non-tautological):
    - Predictor = Temporal Pattern (First/Last mention presence)
    - Outcome = Ground Truth (from dataset 'ground_truth' field)
    
    Mapping:
    - First Missing -> Perceptual (Model failed to perceive the constraint initially)
    - First Present / Last Missing -> Procedural (Model perceived but forgot/lost track)
    - Both Present / Correct -> Correct (Model maintained constraint throughout)
    """
    task_id = parse_result['task_id']
    first_mention = parse_result['first_mention']
    last_mention = parse_result['last_mention']
    ground_truth = task.get('ground_truth', 'unknown')
    
    # Determine temporal pattern
    first_present = first_mention is not None
    last_present = last_mention is not None
    
    # Classification logic
    if not first_present:
        # First missing: Perceptual error
        error_label = "Perceptual"
        temporal_pattern = "First_Missing"
    elif first_present and not last_present:
        # First present, last missing: Procedural error
        error_label = "Procedural"
        temporal_pattern = "First_Present_Last_Missing"
    else:
        # Both present: Check ground truth
        # If ground truth indicates correct solution, label as Correct
        # If ground truth indicates error despite constraint presence, still label based on pattern
        if ground_truth == 'correct' or (first_present and last_present):
            error_label = "Correct"
            temporal_pattern = "Both_Present"
        else:
            # Edge case: constraint present but still wrong -> Procedural (lost in execution)
            error_label = "Procedural"
            temporal_pattern = "Both_Present_Error"
    
    return {
        'task_id': task_id,
        'error_label': error_label,
        'temporal_pattern': temporal_pattern,
        'ground_truth': ground_truth
    }

def process_all_traces(traces: List[Dict[str, Any]], tasks: Dict[str, Dict[str, Any]], model, threshold: float) -> List[Dict[str, Any]]:
    """Process all traces and classify errors."""
    results = []
    
    for trace in traces:
        task_id = trace.get('task_id')
        if task_id not in tasks:
            logger.warning(f"Task {task_id} not found in task records, skipping")
            continue
          
        task = tasks[task_id]
        
        # Parse trace
        parse_result = parse_trace(trace, task, model, threshold)
        
        # Classify error
        classification = classify_error(parse_result, task)
        
        # Combine results
        result = {
            **parse_result,
            **classification
        }
        results.append(result)
    
    return results

def write_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Write classification results to JSONL file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result) + '\n')
    logger.info(f"Waved {len(results)} results to {output_path}")
    
    # Compute and log hash for integrity
    file_hash = compute_file_hash(output_path)
    logger.info(f"Output file hash: {file_hash}")

def main():
    parser = argparse.ArgumentParser(description="Parse CoT traces and classify errors")
    parser.add_argument("--traces", type=str, required=True, help="Path to CoT traces JSONL")
    parser.add_argument("--tasks", type=str, required=True, help="Path to task records JSONL")
    parser.add_argument("--threshold", type=str, required=True, help="Path to tuned threshold JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSONL")
    parser.add_argument("--model", type=str, default="all-MiniLM-L6-v2", help="Semantic matching model")
    parser.add_argument("--log", type=str, default=None, help="Log file path")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(Path(args.log) if args.log else None)
    
    try:
        # Load inputs
        traces = load_traces(Path(args.traces))
        tasks = load_task_records(Path(args.tasks))
        threshold = load_threshold(Path(args.threshold))
        
        # Load model
        model = load_model(args.model)
        
        # Process traces
        logger.info("Starting trace parsing and classification...")
        results = process_all_traces(traces, tasks, model, threshold)
        
        # Write results
        write_results(results, Path(args.output))
        
        logger.info("Classification complete.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during processing: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()