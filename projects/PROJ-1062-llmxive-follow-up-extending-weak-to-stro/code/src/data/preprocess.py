"""
Preprocessing module for AIME dataset.
Formats prompts and extracts ground-truth reasoning steps.
"""
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Regex pattern to extract reasoning steps from the solution field
# Matches content between '### Solution:' and either '### Answer:' or end of string
REASONING_PATTERN = re.compile(r'### Solution:(.*?)(?=### Answer|$)', re.DOTALL | re.IGNORECASE)
ANSWER_PATTERN = re.compile(r'### Answer:(.*?)(?=###|$)', re.DOTALL | re.IGNORECASE)

def load_verified_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """
    Load the verified AIME dataset from a JSON/JSONL file.
    
    Args:
        dataset_path: Path to the dataset file (JSON or JSONL)
        
    Returns:
        List of dataset records
        
    Raises:
        FileNotFoundError: If the dataset file does not exist
        ValueError: If the file format is unsupported
    """
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    
    records = []
    
    if path.suffix == '.json':
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict) and 'data' in data:
                records = data['data']
            else:
                raise ValueError(f"Unexpected JSON structure in {dataset_path}")
    elif path.suffix == '.jsonl':
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    records.append(record)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON at line {line_num}: {e}")
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Use .json or .jsonl")
    
    logger.info(f"Loaded {len(records)} records from {dataset_path}")
    return records

def extract_reasoning_steps(solution_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract reasoning steps and final answer from the solution field.
    
    Args:
        solution_text: The raw solution text from the dataset
        
    Returns:
        Tuple of (reasoning_chain, final_answer)
        Returns (None, None) if extraction fails
    """
    if not solution_text or not isinstance(solution_text, str):
        logger.warning("Invalid or empty solution text")
        return None, None
    
    reasoning = None
    answer = None
    
    # Extract reasoning chain
    reasoning_match = REASONING_PATTERN.search(solution_text)
    if reasoning_match:
        reasoning = reasoning_match.group(1).strip()
        # Clean up whitespace
        reasoning = re.sub(r'\n\s*\n', '\n\n', reasoning)
    
    # Extract final answer
    answer_match = ANSWER_PATTERN.search(solution_text)
    if answer_match:
        answer = answer_match.group(1).strip()
    
    # Fallback: if no explicit markers found, treat entire text as reasoning
    if reasoning is None:
        reasoning = solution_text.strip()
        logger.debug("No '### Solution:' marker found, using full text as reasoning")
    
    return reasoning, answer

def format_prompt(problem_text: str, reasoning_chain: str, answer: Optional[str] = None) -> Dict[str, str]:
    """
    Format a complete prompt for training/evaluation.
    
    Args:
        problem_text: The original problem statement
        reasoning_chain: The extracted reasoning steps
        answer: Optional final answer
        
    Returns:
        Dictionary with formatted prompt components
    """
    prompt_parts = [
        "### Problem:",
        problem_text.strip(),
        "",
        "### Solution:",
        reasoning_chain.strip()
    ]
    
    if answer:
        prompt_parts.extend([
            "",
            "### Answer:",
            answer.strip()
        ])
    
    formatted_prompt = "\n".join(prompt_parts)
    
    return {
        "full_prompt": formatted_prompt,
        "problem": problem_text.strip(),
        "reasoning": reasoning_chain.strip(),
        "answer": answer.strip() if answer else None
    }

def preprocess_record(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Preprocess a single dataset record.
    
    Args:
        record: Raw dataset record containing problem and solution fields
        
    Returns:
        Processed record with extracted reasoning and formatted prompt,
        or None if preprocessing fails
    """
    # Identify problem text field
    problem_text = None
    for key in ['problem', 'question', 'problem_text', 'text']:
        if key in record and record[key]:
            problem_text = str(record[key])
            break
    
    if not problem_text:
        logger.warning(f"Could not find problem text in record: {record.get('id', 'unknown')}")
        return None
    
    # Identify solution field
    solution_text = None
    for key in ['solution', 'reasoning', 'answer', 'explanation']:
        if key in record and record[key]:
            solution_text = str(record[key])
            break
    
    if not solution_text:
        logger.warning(f"Could not find solution text in record: {record.get('id', 'unknown')}")
        # Still proceed with empty reasoning if problem exists
        solution_text = ""
    
    # Extract reasoning and answer
    reasoning, answer = extract_reasoning_steps(solution_text)
    
    if reasoning is None:
        logger.warning(f"Failed to extract reasoning from record: {record.get('id', 'unknown')}")
        return None
    
    # Format prompt
    formatted = format_prompt(problem_text, reasoning, answer)
    
    # Construct output record
    processed = {
        "id": record.get('id', record.get('problem_id', f"unknown_{hash(problem_text)}")),
        "original_record": record,
        "problem": problem_text,
        "reasoning": reasoning,
        "answer": answer,
        "formatted_prompt": formatted["full_prompt"],
        "has_answer": answer is not None
    }
    
    return processed

def save_preprocessed_dataset(
    records: List[Dict[str, Any]], 
    output_path: str,
    overwrite: bool = False
) -> int:
    """
    Save preprocessed records to a JSONL file.
    
    Args:
        records: List of processed records
        output_path: Path to output file
        overwrite: Whether to overwrite existing file
        
    Returns:
        Number of records saved
        
    Raises:
        FileExistsError: If file exists and overwrite=False
    """
    output_path = Path(output_path)
    
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output file exists and overwrite=False: {output_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    saved_count = 0
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in records:
            try:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
                saved_count += 1
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to serialize record: {e}")
    
    logger.info(f"Saved {saved_count} records to {output_path}")
    return saved_count

def main():
    """
    Main entry point for preprocessing script.
    Expects input from data/processed/ and outputs to data/processed/
    """
    # Configuration
    input_path = Path("data/processed/aime_verified.jsonl")
    output_path = Path("data/processed/aime_preprocessed.jsonl")
    
    # Check if input exists (should be produced by T005.0)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run T005.0 (download_aime_verified.py) first.")
        sys.exit(1)
    
    logger.info(f"Starting preprocessing of {input_path}")
    
    try:
        # Load dataset
        records = load_verified_dataset(str(input_path))
        
        # Preprocess records
        processed_records = []
        failed_count = 0
        
        for i, record in enumerate(records):
            processed = preprocess_record(record)
            if processed:
                processed_records.append(processed)
            else:
                failed_count += 1
                if failed_count <= 5:
                    logger.warning(f"Failed to process record {i}")
        
        logger.info(f"Successfully processed {len(processed_records)} records, failed {failed_count}")
        
        # Save results
        save_preprocessed_dataset(processed_records, str(output_path), overwrite=True)
        
        # Log summary statistics
        with_answer = sum(1 for r in processed_records if r.get('has_answer'))
        logger.info(f"Records with extracted answer: {with_answer}/{len(processed_records)}")
        
        logger.info("Preprocessing completed successfully")
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()