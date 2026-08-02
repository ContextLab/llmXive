"""
Script to generate the DAG manifest containing dependency depths for all valid traces.
This script loads the raw dataset, parses traces into DAGs, filters invalid ones,
and outputs a manifest file with logical difficulty scores.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.parser import CoTParser, parse_trace_to_dag, get_logical_difficulty, is_trace_valid
from code.src.data_loader import load_dag_sft_dataset, iterate_dataset_examples
from code.src.parser_utils import load_json_file, save_json_file

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_raw_traces() -> List[Dict[str, Any]]:
    """
    Load raw CoT traces from the dataset.
    Returns a list of dictionaries with 'example_id', 'trace', and 'question'.
    """
    logger.info("Loading raw traces from dataset...")
    try:
        dataset = load_dag_sft_dataset()
        traces = []
        for idx, example in enumerate(iterate_dataset_examples(dataset)):
            trace_text = example.get('cot_trace', '')
            if not trace_text:
                logger.warning(f"Example {idx} has empty trace, skipping.")
                continue
            
            traces.append({
                'example_id': f"ex_{idx:03d}",
                'trace': trace_text,
                'question': example.get('question', '')
            })
        logger.info(f"Loaded {len(traces)} valid traces.")
        return traces
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def generate_dag_manifest(raw_traces: List[Dict[str, Any]], output_path: Path) -> Dict[str, Any]:
    """
    Process raw traces into a DAG manifest.
    - Parses each trace into a DAG.
    - Calculates logical difficulty (max path depth).
    - Filters out invalid traces (cycles, etc.).
    - Returns the manifest structure.
    """
    logger.info(f"Processing {len(raw_traces)} traces to generate DAG manifest...")
    
    manifest = {
        "metadata": {
            "source": "aaabiao/DAG_sft",
            "parser_version": "1.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_entries": 0,
            "valid_entries": 0,
            "invalid_entries": 0
        },
        "entries": []
    }
    
    parser = CoTParser()
    valid_count = 0
    invalid_count = 0
    
    for trace_data in raw_traces:
        example_id = trace_data['example_id']
        trace_text = trace_data['trace']
        
        try:
            # Parse trace to DAG
            dag = parse_trace_to_dag(trace_text)
            
            # Check validity
            if not is_trace_valid(dag):
                logger.debug(f"Example {example_id} is invalid (cycle or structural issue).")
                invalid_count += 1
                continue
            
            # Calculate logical difficulty (max path depth)
            max_depth = get_logical_difficulty(dag)
            
            # Create entry
            entry = {
                "example_id": example_id,
                "logical_difficulty_score": float(max_depth),
                "is_valid": True,
                "max_path_depth": int(max_depth)
            }
            manifest["entries"].append(entry)
            valid_count += 1
            
        except Exception as e:
            logger.error(f"Error processing example {example_id}: {e}")
            invalid_count += 1
    
    manifest["metadata"]["total_entries"] = len(raw_traces)
    manifest["metadata"]["valid_entries"] = valid_count
    manifest["metadata"]["invalid_entries"] = invalid_count
    
    logger.info(f"Manifest generation complete. Valid: {valid_count}, Invalid: {invalid_count}")
    
    # Save to file
    save_json_file(manifest, output_path)
    logger.info(f"Manifest saved to {output_path}")
    
    return manifest

def main():
    """Main entry point for the script."""
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / "data" / "processed" / "dag_manifest.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load raw traces
    raw_traces = load_raw_traces()
    
    if not raw_traces:
        logger.error("No raw traces found. Cannot generate manifest.")
        sys.exit(1)
    
    # Generate manifest
    manifest = generate_dag_manifest(raw_traces, output_path)
    
    # Verify output
    if not output_path.exists():
        logger.error("Failed to write manifest file.")
        sys.exit(1)
    
    logger.info("DAG manifest generation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
