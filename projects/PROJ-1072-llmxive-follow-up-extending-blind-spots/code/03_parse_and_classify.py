import argparse
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

import numpy as np
from sentence_transformers import SentenceTransformer

from utils.logging_config import get_logger, setup_root_logger
from utils.semantic_matcher import encode_texts, cosine_similarity, is_paraphrase

logger = get_logger(__name__)


def setup_logging() -> logging.Logger:
    """Setup logging for the parser module."""
    setup_root_logger()
    return logger


def load_traces(traces_path: Path) -> List[Dict[str, Any]]:
    """Load CoT traces from a JSONL file."""
    if not traces_path.exists():
        raise FileNotFoundError(f"Traces file not found: {traces_path}")
    
    traces = []
    with open(traces_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                traces.append(json.loads(line))
    logger.info(f"Loaded {len(traces)} traces from {traces_path}")
    return traces


def load_task_records(filtered_tasks_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load task records from a JSONL file and index by task_id."""
    if not filtered_tasks_path.exists():
        raise FileNotFoundError(f"Filtered tasks file not found: {filtered_tasks_path}")
    
    records = {}
    with open(filtered_tasks_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                task_id = record.get('task_id')
                if task_id:
                    records[task_id] = record
    logger.info(f"Loaded {len(records)} task records from {filtered_tasks_path}")
    return records


def load_threshold(threshold_path: Path) -> float:
    """Load the tuned semantic matching threshold."""
    if not threshold_path.exists():
        raise FileNotFoundError(
            f"Tuned threshold file not found: {threshold_path}. "
            "Please run the pilot study (T019) to generate this file."
        )
    
    with open(threshold_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    threshold = data.get('optimal_threshold')
    if threshold is None:
        raise ValueError(f"optimal_threshold not found in {threshold_path}")
    
    logger.info(f"Loaded semantic matching threshold: {threshold}")
    return float(threshold)


def load_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """Load the semantic matching model."""
    logger.info(f"Loading semantic matching model: {model_name}")
    model = SentenceTransformer(model_name)
    logger.info("Model loaded successfully")
    return model


def tokenize_text(text: str, tokenizer: Any, max_length: int = 512) -> List[int]:
    """Tokenize text using the model's tokenizer."""
    tokens = tokenizer.encode(text, truncation=True, max_length=max_length)
    return tokens


def reconstruct_text_from_tokens(tokens: List[int], tokenizer: Any) -> str:
    """Reconstruct text from token IDs."""
    return tokenizer.decode(tokens)


def find_exact_match(text: str, constraint: str, word_boundary: bool = True) -> Optional[Tuple[int, int]]:
    """
    Find the first and last character offset of the constraint in the text.
    
    Args:
        text: The text to search in.
        constraint: The constraint string to find.
        word_boundary: If True, ensure the match is a whole word.
    
    Returns:
        Tuple of (start_offset, end_offset) or None if not found.
    """
    if not constraint:
        return None
    
    # Escape special regex characters in the constraint
    escaped_constraint = re.escape(constraint)
    
    if word_boundary:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + escaped_constraint + r'\b'
    else:
        pattern = escaped_constraint
    
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        return (match.start(), match.end())
    
    return None


def find_semantic_match(
    text: str,
    constraint: str,
    model: SentenceTransformer,
    threshold: float,
    tokenizer: Any,
    window_size: int = 128
) -> Optional[Tuple[int, int, float]]:
    """
    Find paraphrased constraints using semantic similarity.
    
    Searches sliding windows of the text for semantic matches to the constraint.
    
    Args:
        text: The text to search in.
        constraint: The constraint string to find (potentially paraphrased).
        model: The SentenceTransformer model for embeddings.
        threshold: The cosine similarity threshold for a match.
        tokenizer: The tokenizer for the model.
        window_size: Number of tokens per sliding window.
    
    Returns:
        Tuple of (start_offset, end_offset, similarity_score) or None if no match.
    """
    if not constraint:
        return None
    
    # Tokenize the entire text
    tokens = tokenize_text(text, tokenizer)
    constraint_tokens = tokenize_text(constraint, tokenizer)
    
    # Encode the constraint once
    constraint_embedding = model.encode([constraint_tokens], convert_to_numpy=True)[0]
    
    best_match = None
    best_score = 0.0
    
    # Sliding window search
    for i in range(0, len(tokens) - window_size + 1, window_size // 2):
        window_tokens = tokens[i:i + window_size]
        window_text = reconstruct_text_from_tokens(window_tokens, tokenizer)
        
        # Encode the window
        window_embedding = model.encode([window_tokens], convert_to_numpy=True)[0]
        
        # Calculate cosine similarity
        similarity = cosine_similarity(constraint_embedding, window_embedding)
        
        if similarity > threshold and similarity > best_score:
            # Calculate character offsets
            start_char = len(reconstruct_text_from_tokens(tokens[:i], tokenizer))
            end_char = len(reconstruct_text_from_tokens(tokens[:i + window_size], tokenizer))
            
            best_match = (start_char, end_char, similarity)
            best_score = similarity
    
    return best_match


def parse_trace(trace: Dict[str, Any], constraint: str, model: SentenceTransformer, threshold: float, tokenizer: Any) -> Dict[str, Any]:
    """
    Parse a single trace to find constraint mentions.
    
    Args:
        trace: The trace dictionary containing the generated text.
        constraint: The constraint string to search for.
        model: The semantic matching model.
        threshold: The semantic matching threshold.
        tokenizer: The model's tokenizer.
    
    Returns:
        Dictionary with parsing results including first/last offsets.
    """
    trace_text = trace.get('generated_text', '')
    task_id = trace.get('task_id', 'unknown')
    
    # Split trace into segments (first and last)
    # Assuming the trace is structured with clear segment boundaries
    # For now, we'll treat the entire text as one segment and search within it
    segments = [trace_text]  # Fallback to full text
    
    first_mention = None
    last_mention = None
    
    # Search for exact match first
    exact_match = find_exact_match(trace_text, constraint)
    if exact_match:
        first_mention = {
            'type': 'exact',
            'start': exact_match[0],
            'end': exact_match[1],
            'segment': 0
        }
        last_mention = first_mention
    
    # If no exact match, try semantic matching
    if not first_mention:
        semantic_match = find_semantic_match(
            trace_text, constraint, model, threshold, tokenizer
        )
        if semantic_match:
            first_mention = {
                'type': 'semantic',
                'start': semantic_match[0],
                'end': semantic_match[1],
                'similarity': semantic_match[2],
                'segment': 0
            }
            last_mention = first_mention
    
    return {
        'task_id': task_id,
        'constraint': constraint,
        'first_mention': first_mention,
        'last_mention': last_mention,
        'trace_length': len(trace_text)
    }


def classify_error(parsed_result: Dict[str, Any], task_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify the error type based on constraint mention patterns.
    
    Logic:
    - First Missing = Perceptual
    - First Present / Last Missing = Procedural
    - Both Present / Correct = Correct
    
    Args:
        parsed_result: The parsing results from parse_trace.
        task_record: The original task record with ground truth.
    
    Returns:
        Dictionary with error classification.
    """
    first_mention = parsed_result.get('first_mention')
    last_mention = parsed_result.get('last_mention')
    
    # Determine presence
    first_present = first_mention is not None
    last_present = last_mention is not None
    
    # Classify based on the rule
    if not first_present:
        error_type = 'Perceptual'
        explanation = 'Constraint not mentioned at the beginning (first mention missing)'
    elif first_present and not last_present:
        error_type = 'Procedural'
        explanation = 'Constraint mentioned at the beginning but not at the end'
    elif first_present and last_present:
        # Check if the task was actually correct in the ground truth
        is_correct = task_record.get('is_correct', False)
        if is_correct:
            error_type = 'Correct'
            explanation = 'Constraint mentioned throughout and task was correct'
        else:
            # Both mentioned but task incorrect - could be a different error type
            error_type = 'Procedural'
            explanation = 'Constraint mentioned but task execution failed'
    else:
        error_type = 'Unknown'
        explanation = 'Unable to classify based on mention pattern'
    
    return {
        'error_type': error_type,
        'explanation': explanation,
        'first_mention_present': first_present,
        'last_mention_present': last_present
    }


def process_all_traces(
    traces: List[Dict[str, Any]],
    task_records: Dict[str, Any],
    model: SentenceTransformer,
    threshold: float,
    tokenizer: Any
) -> List[Dict[str, Any]]:
    """
    Process all traces and classify errors.
    
    Args:
        traces: List of trace dictionaries.
        task_records: Dictionary of task records indexed by task_id.
        model: The semantic matching model.
        threshold: The semantic matching threshold.
        tokenizer: The model's tokenizer.
    
    Returns:
        List of processed results with parsing and classification.
    """
    results = []
    
    for trace in traces:
        task_id = trace.get('task_id')
        task_record = task_records.get(task_id, {})
        
        # Get constraint from task record
        constraint = task_record.get('constraint', '')
        
        if not constraint:
            logger.warning(f"No constraint found for task {task_id}, skipping")
            continue
        
        # Parse the trace
        parsed_result = parse_trace(trace, constraint, model, threshold, tokenizer)
        
        # Classify the error
        classification = classify_error(parsed_result, task_record)
        
        # Combine results
        result = {
            **parsed_result,
            **classification,
            'task_category': task_record.get('task_category', 'unknown'),
            'is_correct': task_record.get('is_correct', None)
        }
        
        results.append(result)
    
    logger.info(f"Processed {len(results)} traces")
    return results


def write_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Write processed results to a JSONL file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result) + '\n')
    
    logger.info(f"Wrote {len(results)} results to {output_path}")


def main():
    """Main entry point for the parser and classifier."""
    parser = argparse.ArgumentParser(description="Parse CoT traces and classify errors")
    parser.add_argument(
        '--traces',
        type=str,
        default='data/traces/cot_traces.jsonl',
        help='Path to the CoT traces file'
    )
    parser.add_argument(
        '--tasks',
        type=str,
        default='data/filtered/filtered_tasks.jsonl',
        help='Path to the filtered tasks file'
    )
    parser.add_argument(
        '--threshold',
        type=str,
        default='data/pilot/tuned_threshold.json',
        help='Path to the tuned threshold file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/results/parsed_traces.jsonl',
        help='Path to the output file'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='all-MiniLM-L6-v2',
        help='Semantic matching model name'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    try:
        # Load inputs
        traces = load_traces(Path(args.traces))
        task_records = load_task_records(Path(args.tasks))
        threshold = load_threshold(Path(args.threshold))
        
        # Load model and tokenizer
        model = load_model(args.model)
        tokenizer = model.tokenizer
        
        # Process traces
        results = process_all_traces(traces, task_records, model, threshold, tokenizer)
        
        # Write results
        write_results(results, Path(args.output))
        
        logger.info("Parsing and classification completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        raise


if __name__ == '__main__':
    main()