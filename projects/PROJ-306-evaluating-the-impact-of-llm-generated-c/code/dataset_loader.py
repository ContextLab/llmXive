import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import yaml
import datasets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RAW_MBPP_DIR = Path("data/benchmarks/raw/mbpp")
RAW_HUMANEVAL_DIR = Path("data/benchmarks/raw/humaneval")
PROCESSED_DIR = Path("data/benchmarks/processed")
CATALOG_PATH = PROCESSED_DIR / "catalog.json"
TESTS_DIR = PROCESSED_DIR / "tests"

def load_mbpp_dataset() -> datasets.DatasetDict:
    """Load MBPP dataset from HuggingFace."""
    logger.info("Loading MBPP dataset...")
    try:
        ds = datasets.load_dataset("mbpp", split="train")
        logger.info(f"Loaded MBPP dataset with {len(ds)} records.")
        return ds
    except Exception as e:
        logger.error(f"Failed to load MBPP dataset: {e}")
        raise

def save_raw_mbpp_files(ds: datasets.Dataset) -> None:
    """Save raw MBPP data to disk."""
    RAW_MBPP_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RAW_MBPP_DIR / "mbpp_raw.jsonl"
    logger.info(f"Saving raw MBPP data to {output_path}...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in ds:
            f.write(json.dumps(item) + '\n')
    logger.info(f"Saved {len(ds)} MBPP records.")

def load_humaneval_dataset() -> datasets.DatasetDict:
    """Load HumanEval dataset from HuggingFace."""
    logger.info("Loading HumanEval dataset...")
    try:
        ds_dict = datasets.load_dataset('openai/openai_humaneval')
        # The dataset is usually in 'test' split
        if 'test' in ds_dict:
            ds = ds_dict['test']
        else:
            # Fallback: try to get any split
            ds = next(iter(ds_dict.values()))
        
        logger.info(f"Loaded HumanEval dataset with {len(ds)} records.")
        return ds
    except Exception as e:
        logger.error(f"Failed to load HumanEval dataset: {e}")
        raise

def save_raw_humaneval_files(ds: datasets.Dataset) -> None:
    """Save raw HumanEval data to disk."""
    RAW_HUMANEVAL_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RAW_HUMANEVAL_DIR / "humaneval_raw.jsonl"
    logger.info(f"Saving raw HumanEval data to {output_path}...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in ds:
            f.write(json.dumps(item) + '\n')
    logger.info(f"Saved {len(ds)} HumanEval records.")

def extract_code_patterns(code: str) -> Dict[str, int]:
    """Extract simple code patterns from solution code."""
    patterns = {
        'loops': 0,
        'conditionals': 0,
        'recursion': 0,
        'list_comprehension': 0,
        'lambda': 0
    }
    
    if not code:
        return patterns
        
    # Count loops (for, while)
    patterns['loops'] = len([l for l in code.split('\n') if 'for ' in l or 'while ' in l])
    
    # Count conditionals (if, elif, else)
    patterns['conditionals'] = len([l for l in code.split('\n') if 'if ' in l or 'elif ' in l or 'else:' in l])
    
    # Check for recursion (function calling itself) - simplistic check
    func_name = None
    if 'def ' in code:
        # Try to extract function name
        lines = code.split('\n')
        for line in lines:
            if line.strip().startswith('def '):
                func_name = line.split('def ')[1].split('(')[0].strip()
                break
        if func_name and func_name in code[code.find('def ')+4:]:
            patterns['recursion'] = 1
    
    # List comprehension
    patterns['list_comprehension'] = len([l for l in code.split('\n') if '[' in l and 'for' in l and 'in' in l])
    
    # Lambda
    patterns['lambda'] = len([l for l in code.split('\n') if 'lambda' in l])
    
    return patterns

def validate_and_create_catalog() -> List[Dict[str, Any]]:
    """
    Validate required fields and create a normalized JSON catalog.
    
    Required fields: task_id, prompt, human_solution, test_suite
    Output keys: task_id, prompt, human_solution, test_suite_path, difficulty, code_patterns
    """
    logger.info("Validating datasets and creating catalog...")
    
    catalog = []
    processed_count = 0
    
    # Process MBPP
    mbpp_path = RAW_MBPP_DIR / "mbpp_raw.jsonl"
    if mbpp_path.exists():
        logger.info(f"Processing MBPP from {mbpp_path}")
        with open(mbpp_path, 'r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line)
                
                # Validate required fields
                required = ['task_id', 'prompt', 'canonical_solution', 'test']
                missing = [field for field in required if field not in item]
                
                if missing:
                    logger.warning(f"Skipping MBPP task {item.get('task_id', 'unknown')}: missing fields {missing}")
                    continue
                
                # Map to catalog schema
                task_id = item['task_id']
                prompt = item['prompt']
                human_solution = item['canonical_solution']
                test_suite = item['test']
                
                # Determine difficulty (simplified: based on task_id or heuristics)
                # MBPP doesn't have explicit difficulty, we'll use a heuristic or default
                difficulty = "medium"  # Default for MBPP
                
                # Extract code patterns
                code_patterns = extract_code_patterns(human_solution)
                
                # Determine test suite path (will be created by T007)
                test_filename = f"mbpp_{task_id}.py"
                test_suite_path = str(TESTS_DIR / test_filename)
                
                catalog_entry = {
                    "task_id": str(task_id),
                    "prompt": prompt,
                    "human_solution": human_solution,
                    "test_suite_path": test_suite_path,
                    "difficulty": difficulty,
                    "code_patterns": code_patterns,
                    "dataset_source": "mbpp"
                }
                
                catalog.append(catalog_entry)
                processed_count += 1
    
    # Process HumanEval
    humaneval_path = RAW_HUMANEVAL_DIR / "humaneval_raw.jsonl"
    if humaneval_path.exists():
        logger.info(f"Processing HumanEval from {humaneval_path}")
        with open(humaneval_path, 'r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line)
                
                # Validate required fields (HumanEval uses different field names)
                # task_id, prompt (canonical_solution), human_solution (canonical_solution), test (test)
                required = ['task_id', 'prompt', 'canonical_solution', 'test']
                missing = [field for field in required if field not in item]
                
                if missing:
                    logger.warning(f"Skipping HumanEval task {item.get('task_id', 'unknown')}: missing fields {missing}")
                    continue
                
                task_id = item['task_id']
                prompt = item['prompt']
                human_solution = item['canonical_solution']
                test_suite = item['test']
                
                # HumanEval difficulty is not explicit, use heuristic based on task_id or default
                difficulty = "medium"  # Default
                
                # Extract code patterns
                code_patterns = extract_code_patterns(human_solution)
                
                test_filename = f"humaneval_{task_id}.py"
                test_suite_path = str(TESTS_DIR / test_filename)
                
                catalog_entry = {
                    "task_id": str(task_id),
                    "prompt": prompt,
                    "human_solution": human_solution,
                    "test_suite_path": test_suite_path,
                    "difficulty": difficulty,
                    "code_patterns": code_patterns,
                    "dataset_source": "humaneval"
                }
                
                catalog.append(catalog_entry)
                processed_count += 1
    
    # Validate against schema if it exists
    schema_path = Path("contracts/task_catalog.schema.yaml")
    if schema_path.exists():
        logger.info(f"Validating catalog against schema: {schema_path}")
        try:
            with open(schema_path, 'r') as f:
                schema = yaml.safe_load(f)
            # Simple validation: check required keys in schema
            required_keys = schema.get('required', [])
            for entry in catalog:
                missing_keys = [k for k in required_keys if k not in entry]
                if missing_keys:
                    logger.warning(f"Catalog entry {entry.get('task_id')} missing schema keys: {missing_keys}")
        except Exception as e:
            logger.error(f"Failed to validate against schema: {e}")
    
    # Save catalog
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Catalog created with {processed_count} entries at {CATALOG_PATH}")
    return catalog

def main():
    """Main entry point for dataset loading and catalog creation."""
    logger.info("Starting dataset loading and catalog creation...")
    
    # Load and save raw datasets
    try:
        mbpp_ds = load_mbpp_dataset()
        save_raw_mbpp_files(mbpp_ds)
    except Exception as e:
        logger.error(f"Error loading/saving MBPP: {e}")
    
    try:
        humaneval_ds = load_humaneval_dataset()
        save_raw_humaneval_files(humaneval_ds)
    except Exception as e:
        logger.error(f"Error loading/saving HumanEval: {e}")
    
    # Create catalog
    try:
        catalog = validate_and_create_catalog()
        logger.info(f"Successfully created catalog with {len(catalog)} entries.")
    except Exception as e:
        logger.error(f"Error creating catalog: {e}")
        raise
    
    logger.info("Dataset loading and catalog creation complete.")

if __name__ == "__main__":
    main()
