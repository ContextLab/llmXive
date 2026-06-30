"""
Script to write validated misleading medical questions to JSONL.

This task (T020) implements the final step of User Story 1:
Writing the validated data to `code/data/processed/mislead_questions.jsonl`
with a `validation_status` field.

It depends on T019 (`validate_injection`) which is already implemented in
`code/scripts/generate_mislead.py`.
"""
import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import existing utilities
from scripts.config import get_project_root, load_config, get_seed, resolve_path
from scripts.generate_mislead import validate_injection, load_prompt_template, inject_false_claim

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_and_validate_dataset(
    source_path: Path,
    prompt_template_path: Path,
    seed: int
) -> List[Dict[str, Any]]:
    """
    Load the source dataset, inject false claims, validate injections,
    and return a list of validated items.
    """
    # Load source data (assuming JSONL or JSON based on T001 output)
    if not source_path.exists():
        raise FileNotFoundError(f"Source dataset not found: {source_path}")
    
    logger.info(f"Loading source dataset from {source_path}")
    source_items = []
    with open(source_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                source_items.append(json.loads(line))
    
    logger.info(f"Loaded {len(source_items)} items")

    # Load prompt template
    prompt_template = load_prompt_template(prompt_template_path)

    validated_items = []
    skipped_count = 0
    error_count = 0

    for idx, item in enumerate(source_items):
        try:
            # Inject false claim
            # Note: inject_false_claim returns a dict with 'stem', 'injected_claim', 'options', 'answer', etc.
            # We assume the item structure matches what T019 expects.
            mislead_item = inject_false_claim(item, prompt_template, seed)
            
            # Validate the injection
            validation_result = validate_injection(mislead_item)
            
            if validation_result['is_valid']:
                # Add validation status and metadata
                mislead_item['validation_status'] = 'valid'
                mislead_item['validation_details'] = validation_result.get('details', {})
                validated_items.append(mislead_item)
            else:
                logger.warning(f"Item {idx} failed validation: {validation_result.get('reason', 'Unknown')}")
                skipped_count += 1
                # Optionally add to output with 'invalid' status if required, 
                # but task implies writing VALIDATED data. 
                # We will log it and skip writing to the main processed file 
                # unless the task implies keeping them with a flag. 
                # The task says "Write validated data... with validation_status field".
                # Usually this means only valid items go to the processed file, 
                # or all items go with a status. Let's include all with status.
                
                mislead_item['validation_status'] = 'invalid'
                mislead_item['validation_details'] = validation_result.get('details', {})
                validated_items.append(mislead_item)
                
        except Exception as e:
            logger.error(f"Error processing item {idx}: {e}")
            error_count += 1
            continue

    logger.info(f"Processing complete. Valid: {len([x for x in validated_items if x['validation_status'] == 'valid'])}, Invalid: {skipped_count}, Errors: {error_count}")
    return validated_items

def write_to_jsonl(items: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write the list of items to a JSONL file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing {len(items)} items to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in items:
            # Ensure deterministic output if needed, though json dumps is standard
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    logger.info(f"Successfully wrote {len(items)} items to {output_path}")

def main():
    """
    Main entry point for T020.
    """
    project_root = get_project_root()
    config = load_config()
    seed = get_seed()
    
    # Define paths
    # Assuming T001 fetched data to data/raw/medmcqa.jsonl or similar
    # The tasks.md says T001 fetches to verify checksum. 
    # We need to locate the raw data. Usually data/raw/medmcqa.jsonl
    raw_data_path = resolve_path("data/raw/medmcqa.jsonl")
    
    # Fallback if the file name is different or in a subdirectory
    if not raw_data_path.exists():
        # Try to find any jsonl in raw
        raw_dir = project_root / "code" / "data" / "raw"
        if raw_dir.exists():
            possible_files = list(raw_dir.glob("*.jsonl"))
            if possible_files:
                raw_data_path = possible_files[0]
                logger.info(f"Using found file: {raw_data_path}")
            else:
                logger.error("No JSONL file found in data/raw/")
                sys.exit(1)
        else:
            logger.error("data/raw/ directory does not exist")
            sys.exit(1)

    prompt_path = resolve_path("prompts/eval_mislead.txt")
    if not prompt_path.exists():
        logger.error(f"Prompt template not found: {prompt_path}")
        sys.exit(1)

    output_path = resolve_path("data/processed/mislead_questions.jsonl")

    # Process
    try:
        validated_items = process_and_validate_dataset(
            source_path=raw_data_path,
            prompt_template_path=prompt_path,
            seed=seed
        )
        
        write_to_jsonl(validated_items, output_path)
        
        logger.info("Task T020 completed successfully.")
        
    except Exception as e:
        logger.error(f"Task T020 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
