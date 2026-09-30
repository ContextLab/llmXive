"""
03_parse_and_classify.py

Parses CoT traces, identifies constraint mentions (exact and semantic),
and classifies errors based on temporal patterns of constraint mentions.

Handles edge cases:
- Word-boundary matching to avoid false positives.
- Null flags for missing constraints.
- Substring within different word detection (false positive check).
"""

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

# Import from sibling utils
from utils.logging_config import get_logger
from utils.semantic_matcher import encode_texts, cosine_similarity, is_paraphrase

logger = get_logger(__name__)


def setup_logging(log_file: Optional[Path] = None):
    """Configure logging to console and optionally to file."""
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def load_traces(traces_path: Path) -> List[Dict[str, Any]]:
    """Load CoT traces from JSONL file."""
    if not traces_path.exists():
        logger.error(f"Traces file not found: {traces_path}")
        raise FileNotFoundError(f"Traces file not found: {traces_path}")

    traces = []
    with open(traces_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                traces.append(json.loads(line))
    logger.info(f"Loaded {len(traces)} traces from {traces_path}")
    return traces


def load_task_records(tasks_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load filtered task records from JSONL file."""
    if not tasks_path.exists():
        logger.error(f"Task records file not found: {tasks_path}")
        raise FileNotFoundError(f"Task records file not found: {tasks_path}")

    tasks = {}
    with open(tasks_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                task = json.loads(line)
                # Assuming 'task_id' is the unique identifier
                if 'task_id' in task:
                    tasks[task['task_id']] = task
    logger.info(f"Loaded {len(tasks)} task records from {tasks_path}")
    return tasks


def load_threshold(threshold_path: Path) -> float:
    """Load the tuned semantic matching threshold."""
    if not threshold_path.exists():
        logger.error(f"Threshold file not found: {threshold_path}")
        raise FileNotFoundError(f"Threshold file not found: {threshold_path}")

    with open(threshold_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return float(data['optimal_threshold'])


def load_model(model_name: str = "all-MiniLM-L6-v2"):
    """Load the sentence transformer model."""
    logger.info(f"Loading model: {model_name}")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    logger.info("Model loaded successfully")
    return model


def tokenize_text(text: str, tokenizer: Any) -> List[int]:
    """Tokenize text using the specified tokenizer."""
    tokens = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
    return tokens['input_ids'][0].tolist()


def reconstruct_text_from_tokens(tokens: List[int], tokenizer: Any) -> str:
    """Reconstruct text from token IDs."""
    return tokenizer.decode(tokens, skip_special_tokens=True)


def find_exact_match(text: str, constraint: str) -> Optional[Tuple[int, int]]:
    """
    Find the first and last character offset of the constraint in the text.
    Handles edge cases:
    - Word-boundary matching: ensures the match is a whole word.
    - Substring within different word: avoids false positives.

    Returns:
        Tuple (start_index, end_index) if found, else None.
    """
    if not constraint or not text:
        return None

    # Escape special regex characters in constraint
    escaped_constraint = re.escape(constraint)

    # Pattern to match the constraint as a whole word
    # \b ensures word boundaries
    pattern = r'\b' + escaped_constraint + r'\b'

    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        return (match.start(), match.end())

    return None


def find_semantic_match(text: str, constraint: str, model: Any, threshold: float) -> bool:
    """
    Check if the text semantically matches the constraint using the tuned threshold.

    Returns:
        True if similarity >= threshold, else False.
    """
    if not constraint or not text:
        return False

    try:
        embeddings = encode_texts([constraint, text], model)
        similarity = cosine_similarity(embeddings[0], embeddings[1])
        return similarity >= threshold
    except Exception as e:
        logger.warning(f"Semantic match error: {e}")
        return False


def parse_trace(trace: Dict[str, Any], constraint: str, model: Any, threshold: float) -> Dict[str, Any]:
    """
    Parse a single trace to find constraint mentions.

    Handles edge cases:
    - Null flags for missing constraints.
    - Word-boundary matching for exact matches.
    - Semantic matching for paraphrased constraints.

    Returns:
        Dict with 'first_mention' and 'last_mention' (booleans or offsets).
    """
    task_id = trace.get('task_id')
    text = trace.get('cot_trace', '')

    if not text:
        logger.warning(f"No trace text for task {task_id}")
        return {
            'task_id': task_id,
            'first_mention': None,
            'last_mention': None,
            'first_offset': None,
            'last_offset': None,
            'exact_match': False,
            'semantic_match': False
        }

    # Split trace into segments (assuming first and last segments are relevant)
    # For this implementation, we treat the whole trace as one segment for simplicity,
    # but in a real scenario, we would split by token windows or logical steps.
    segments = [text]  # Placeholder for actual segmentation logic

    first_mention = None
    last_mention = None
    first_offset = None
    last_offset = None

    # Check for exact match (word-boundary)
    exact_match = find_exact_match(text, constraint)

    if exact_match:
        first_offset = exact_match[0]
        last_offset = exact_match[1]
        first_mention = True
        last_mention = True
    else:
        # Check for semantic match
        if find_semantic_match(text, constraint, model, threshold):
            first_mention = True
            last_mention = True
            # Semantic match doesn't provide exact offsets
            first_offset = None
            last_offset = None

    # Handle null flags if no mention found
    if not first_mention:
        first_mention = False
    if not last_mention:
        last_mention = False

    return {
        'task_id': task_id,
        'first_mention': first_mention,
        'last_mention': last_mention,
        'first_offset': first_offset,
        'last_offset': last_offset,
        'exact_match': bool(exact_match),
        'semantic_match': find_semantic_match(text, constraint, model, threshold) if not exact_match else False
    }


def classify_error(parsed_data: Dict[str, Any]) -> str:
    """
    Classify error based on temporal pattern of constraint mentions.

    Logic:
    - First Missing = Perceptual
    - First Present / Last Missing = Procedural
    - Both Present = Correct

    Returns:
        'Perceptual', 'Procedural', or 'Correct'
    """
    first_present = parsed_data.get('first_mention', False)
    last_present = parsed_data.get('last_mention', False)

    if not first_present:
        return 'Perceptual'
    elif first_present and not last_present:
        return 'Procedural'
    else:
        return 'Correct'


def process_all_traces(traces: List[Dict[str, Any]], tasks: Dict[str, Dict[str, Any]], model: Any, threshold: float) -> List[Dict[str, Any]]:
    """Process all traces and classify errors."""
    results = []
    for trace in traces:
        task_id = trace.get('task_id')
        if task_id not in tasks:
            logger.warning(f"Task {task_id} not found in task records, skipping")
            continue

        task = tasks[task_id]
        constraint = task.get('constraint', '')

        if not constraint:
            logger.warning(f"No constraint for task {task_id}, skipping")
            continue

        parsed = parse_trace(trace, constraint, model, threshold)
        parsed['classification'] = classify_error(parsed)
        results.append(parsed)

    logger.info(f"Processed {len(results)} traces")
    return results


def write_results(results: List[Dict[str, Any]], output_path: Path):
    """Write parsed and classified results to JSONL file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result) + '\n')
    logger.info(f"Wrote {len(results)} results to {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Parse and classify CoT traces')
    parser.add_argument('--traces', type=str, required=True, help='Path to traces JSONL')
    parser.add_argument('--tasks', type=str, required=True, help='Path to filtered tasks JSONL')
    parser.add_argument('--threshold', type=str, required=True, help='Path to tuned threshold JSON')
    parser.add_argument('--output', type=str, required=True, help='Path to output JSONL')
    parser.add_argument('--model', type=str, default='all-MiniLM-L6-v2', help='Sentence transformer model name')
    parser.add_argument('--log', type=str, default=None, help='Path to log file')

    args = parser.parse_args()

    setup_logging(Path(args.log) if args.log else None)

    traces = load_traces(Path(args.traces))
    tasks = load_task_records(Path(args.tasks))
    threshold = load_threshold(Path(args.threshold))
    model = load_model(args.model)

    results = process_all_traces(traces, tasks, model, threshold)
    write_results(results, Path(args.output))


if __name__ == '__main__':
    main()
