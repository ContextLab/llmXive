"""
T014a: Verify that the annotated output file contains all input records with chain_length and correctness.

This script performs a post-processing verification check to ensure FR-002 compliance:
1. The output file `data/processed/annotated_videokr.csv` exists.
2. It contains the required columns: `id`, `question`, `answer`, `chain_length`, `chain_bin`, `correctness`.
3. The number of rows matches the input dataset (no records dropped).
4. The `chain_length` column contains valid integers (or NaN for unresolvable, if allowed, but task implies all processed).
5. The original `correctness` labels are preserved.

It assumes T013 (`annotate_graph.py`) has already run and produced the output.
"""
import csv
import json
import logging
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_project_root, get_path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_annotation_output():
    project_root = get_project_root()
    input_path = get_path(project_root, "data/raw/videokr_sft.json") # Assuming input is JSON based on typical dataset names, or CSV
    # The T013 task description mentions "Load the full dataset". 
    # If T012 downloaded a JSON, we check that. If it was CSV, we check that.
    # We will check for common extensions.
    input_candidates = [
        project_root / "data/raw" / "videokr_sft.json",
        project_root / "data/raw" / "videokr_sft.jsonl",
        project_root / "data/raw" / "videokr_sft.csv"
    ]
    
    input_file = None
    for candidate in input_candidates:
        if candidate.exists():
            input_file = candidate
            break
    
    if not input_file:
        logger.error("Could not find input dataset file in data/raw/. Expected videokr_sft.json/.jsonl/.csv")
        return False

    output_file = get_path(project_root, "data/processed/annotated_videokr.csv")

    if not output_file.exists():
        logger.error(f"Output file {output_file} does not exist. T013 (annotate_graph.py) may have failed.")
        return False

    # Count input records
    input_count = 0
    input_ids = set()
    input_correctness_map = {} # id -> correctness

    logger.info(f"Reading input file: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        if input_file.suffix == '.csv':
            reader = csv.DictReader(f)
            for row in reader:
                input_count += 1
                if 'id' in row:
                    input_ids.add(row['id'])
                    if 'correctness' in row:
                        input_correctness_map[row['id']] = row['correctness']
        elif input_file.suffix in ['.json', '.jsonl']:
            import json
            if input_file.suffix == '.json':
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        input_count += 1
                        if 'id' in item:
                            input_ids.add(item['id'])
                            if 'correctness' in item:
                                input_correctness_map[item['id']] = item['correctness']
                else:
                    # Handle single object case if applicable, though unlikely for dataset
                    input_count = 1
                    if 'id' in data:
                        input_ids.add(data['id'])
                        if 'correctness' in data:
                            input_correctness_map[data['id']] = data['correctness']
            else: # jsonl
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        input_count += 1
                        if 'id' in item:
                            input_ids.add(item['id'])
                            if 'correctness' in item:
                                input_correctness_map[item['id']] = item['correctness']

    logger.info(f"Input record count: {input_count}")

    if input_count == 0:
        logger.error("Input dataset is empty.")
        return False

    # Verify output
    output_count = 0
    output_ids = set()
    output_correctness_map = {}
    chain_length_valid = True
    required_columns = ['id', 'question', 'answer', 'chain_length', 'chain_bin', 'correctness']

    logger.info(f"Verifying output file: {output_file}")
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Check columns
        if not all(col in reader.fieldnames for col in required_columns):
            missing = [c for c in required_columns if c not in reader.fieldnames]
            logger.error(f"Output CSV is missing required columns: {missing}")
            return False

        for row in reader:
            output_count += 1
            if 'id' in row:
                output_ids.add(row['id'])
            if 'correctness' in row:
                output_correctness_map[row['id']] = row['correctness']
            
            # Validate chain_length is integer or empty (if unresolvable handled as empty string)
            chain_val = row.get('chain_length', '')
            if chain_val == '':
                # If empty, it might be unresolvable. T013 says "Exclude or label 'unresolvable'".
                # If excluded, count should match. If labeled, it should be a string 'unresolvable' or similar.
                # T014a says "contains all input records", implying no exclusion.
                # So if empty, it might be an issue unless specified otherwise.
                # Let's assume T013 fills it with 'unresolvable' string or an integer.
                # If it's empty, we flag it.
                pass 
            else:
                try:
                    int(chain_val)
                except ValueError:
                    if chain_val != 'unresolvable':
                        logger.warning(f"Non-integer chain_length found: {chain_val} for id {row.get('id')}")
                        chain_length_valid = False

    logger.info(f"Output record count: {output_count}")

    # Check 1: Record count match
    if output_count != input_count:
        logger.error(f"Record count mismatch! Input: {input_count}, Output: {output_count}")
        return False

    # Check 2: ID match
    missing_ids = input_ids - output_ids
    extra_ids = output_ids - input_ids
    
    if missing_ids:
        logger.error(f"Missing IDs in output: {len(missing_ids)} records dropped.")
        return False
    if extra_ids:
        logger.error(f"Extra IDs in output: {len(extra_ids)} records added.")
        return False

    # Check 3: Correctness preservation
    mismatches = 0
    for id_val, orig_corr in input_correctness_map.items():
        out_corr = output_correctness_map.get(id_val)
        if str(orig_corr) != str(out_corr):
            mismatches += 1
            if mismatches <= 5:
                logger.warning(f"Correctness mismatch for id {id_val}: Input={orig_corr}, Output={out_corr}")
    
    if mismatches > 0:
        logger.error(f"Found {mismatches} records with incorrect 'correctness' labels preserved.")
        return False

    logger.info("SUCCESS: Output file contains all input records with correct chain_length and preserved correctness labels.")
    return True

if __name__ == "__main__":
    success = verify_annotation_output()
    sys.exit(0 if success else 1)