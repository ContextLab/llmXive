"""
Preprocessing module for AIME dataset.

Formats prompts and extracts ground-truth reasoning steps for the AIME subset.
Reads from data/raw/aime_2024_verified.jsonl and outputs to data/processed/aime_preprocessed.jsonl.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "aime_2024_verified.jsonl"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "aime_preprocessed.jsonl"
PROMPT_TEMPLATE = "Solve the following math problem step-by-step. Ensure your final answer is boxed.\n\nProblem: {problem_text}\n\nReasoning Steps:\n"

def load_verified_dataset(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load the verified AIME dataset from JSONL file.
    
    Args:
        input_path: Path to the input JSONL file
        
    Returns:
        List of dataset records
        
    Raises:
        FileNotFoundError: If the input file does not exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    records = []
    logger.info(f"Loading dataset from {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                records.append(record)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON at line {line_num}: {e}")
                raise
    
    logger.info(f"Loaded {len(records)} records from {input_path}")
    return records

def extract_reasoning_steps(record: Dict[str, Any]) -> List[str]:
    """
    Extract reasoning steps from a dataset record.
    
    Args:
        record: A single dataset record
        
    Returns:
        List of reasoning step strings
    """
    # Expected fields: 'reasoning_trace' (string or list), 'ground_truth_answer'
    reasoning_trace = record.get('reasoning_trace', '')
    ground_truth = record.get('ground_truth_answer', '')
    
    # If reasoning_trace is a string, split by common delimiters
    if isinstance(reasoning_trace, str):
        # Try to split by common step indicators
        steps = []
        # Look for numbered steps or explicit step markers
        lines = reasoning_trace.split('\n')
        current_step = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_step:
                    steps.append(' '.join(current_step))
                    current_step = []
                continue
            
            # Check if this looks like a new step
            if line.lower().startswith(('step', '1.', '2.', '3.', '4.', '5.', 'first', 'next', 'then', 'finally')):
                if current_step:
                    steps.append(' '.join(current_step))
                current_step = [line]
            else:
                current_step.append(line)
        
        if current_step:
            steps.append(' '.join(current_step))
        
        # If no steps found, treat the whole trace as one step
        if not steps and reasoning_trace:
            steps = [reasoning_trace]
        
        return steps
    
    # If reasoning_trace is already a list
    elif isinstance(reasoning_trace, list):
        return [str(step).strip() for step in reasoning_trace if str(step).strip()]
    
    # Fallback
    return [str(ground_truth)] if ground_truth else ["No reasoning trace available"]

def format_prompt(record: Dict[str, Any]) -> str:
    """
    Format a prompt for the model based on the problem text.
    
    Args:
        record: A single dataset record
        
    Returns:
        Formatted prompt string
    """
    problem_text = record.get('problem_text', record.get('problem', ''))
    if not problem_text:
        raise ValueError("Problem text is missing from record")
    
    return PROMPT_TEMPLATE.format(problem_text=problem_text)

def preprocess_record(record: Dict[str, Any], idx: int) -> Dict[str, Any]:
    """
    Preprocess a single dataset record.
    
    Args:
        record: Original dataset record
        idx: Record index (for tracking)
        
    Returns:
        Preprocessed record with formatted prompt and extracted steps
    """
    try:
        problem_text = record.get('problem_text', record.get('problem', ''))
        if not problem_text:
            logger.warning(f"Record {idx}: Missing problem text, skipping")
            return None
        
        # Extract reasoning steps
        reasoning_steps = extract_reasoning_steps(record)
        
        # Format prompt
        formatted_prompt = format_prompt(record)
        
        # Get human verified label if available
        human_verified_label = record.get('human_verified_label', None)
        
        # Create preprocessed record
        preprocessed = {
            'id': record.get('id', f'aime_{idx}'),
            'problem_text': problem_text,
            'formatted_prompt': formatted_prompt,
            'reasoning_steps': reasoning_steps,
            'num_steps': len(reasoning_steps),
            'ground_truth_answer': record.get('ground_truth_answer', ''),
            'human_verified_label': human_verified_label,
            'original_record': {
                'source': record.get('source', 'unknown'),
                'difficulty': record.get('difficulty', 'unknown'),
                'year': record.get('year', 'unknown')
            }
        }
        
        return preprocessed
        
    except Exception as e:
        logger.error(f"Failed to preprocess record {idx}: {e}")
        return None

def save_preprocessed_dataset(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save preprocessed records to JSONL file.
    
    Args:
        records: List of preprocessed records
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving {len(records)} preprocessed records to {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in records:
            if record is not None:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    logger.info(f"Successfully saved preprocessed dataset to {output_path}")

def main() -> None:
    """Main entry point for preprocessing."""
    logger.info("Starting AIME dataset preprocessing")
    
    # Load dataset
    try:
        raw_records = load_verified_dataset(INPUT_PATH)
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("Please run T005.0 first to download the verified AIME dataset.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)
    
    # Preprocess records
    preprocessed_records = []
    for idx, record in enumerate(raw_records):
        processed = preprocess_record(record, idx)
        if processed:
            preprocessed_records.append(processed)
    
    if not preprocessed_records:
        logger.error("No records were successfully preprocessed.")
        sys.exit(1)
    
    logger.info(f"Successfully preprocessed {len(preprocessed_records)} records")
    
    # Save preprocessed dataset
    try:
        save_preprocessed_dataset(preprocessed_records, OUTPUT_PATH)
    except Exception as e:
        logger.error(f"Failed to save preprocessed dataset: {e}")
        sys.exit(1)
    
    # Print summary statistics
    total_steps = sum(r['num_steps'] for r in preprocessed_records)
    avg_steps = total_steps / len(preprocessed_records)
    logger.info(f"Summary: {len(preprocessed_records)} problems, "
               f"avg {avg_steps:.2f} reasoning steps per problem, "
               f"total {total_steps} steps")
    
    # Count human verified labels
    verified_count = sum(1 for r in preprocessed_records if r['human_verified_label'] is not None)
    logger.info(f"Human verified labels: {verified_count}/{len(preprocessed_records)}")
    
    logger.info("Preprocessing completed successfully")

if __name__ == '__main__':
    main()