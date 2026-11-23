"""
Generate the DAG manifest containing dependency depths for all VALID traces.

This script:
1. Loads the raw CoT traces from the dataset (streamed or loaded).
2. Parses each trace into a DAG.
3. Filters out invalid traces (cycles, threshold violations) using the logic from T017.
4. Calculates the Logical Difficulty Score (max path depth) for valid traces.
5. Saves the resulting manifest to `data/processed/dag_manifest.json`.

It relies on `code/src/parser.py` for parsing and validation logic.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from code.src.parser import parse_trace_to_dag_and_validate, is_trace_valid, get_logical_difficulty
from code.src.parser_utils import load_json_file, save_json_file
from code.src.data_loader import iterate_dataset_examples
from code.src.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG = Config()

def load_raw_traces(max_examples: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Load raw traces from the dataset.
    Uses streaming to handle large datasets without memory exhaustion.
    """
    logger.info("Loading raw traces from dataset...")
    traces = []
    count = 0
    
    try:
        for example in iterate_dataset_examples(CONFIG.get_dataset_name()):
            if max_examples and count >= max_examples:
                break
            
            # Extract the CoT trace. Adjust key based on actual dataset schema.
            # The dataset 'aaabiao/DAG_sft' typically has 'conversations' or 'messages'.
            # Assuming a 'text' or 'cot' field exists, or we construct it from messages.
            # Fallback to a generic 'text' field if specific structure is unknown.
            trace_text = example.get('text') or example.get('cot') or example.get('response')
            
            if not trace_text:
                # Try to construct from messages if 'text' is missing
                messages = example.get('messages', [])
                if messages:
                    # Assume the last message is the reasoning trace
                    trace_text = messages[-1].get('content', '')
            
            if trace_text:
                traces.append({
                    "id": example.get('id', f"example_{count}"),
                    "trace": trace_text,
                    "metadata": {k: v for k, v in example.items() if k not in ['text', 'cot', 'response', 'messages']}
                })
                count += 1
                
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

    logger.info(f"Loaded {len(traces)} raw traces.")
    return traces

def generate_dag_manifest(traces: List[Dict[str, Any]], output_path: Path) -> Dict[str, Any]:
    """
    Generate the DAG manifest for all valid traces.
    
    Args:
        traces: List of raw trace dictionaries.
        output_path: Path to save the manifest JSON.
        
    Returns:
        The generated manifest dictionary.
    """
    logger.info("Parsing traces and generating DAG manifest...")
    
    manifest = {
        "metadata": {
            "total_traces_processed": len(traces),
            "valid_traces_count": 0,
            "invalid_traces_count": 0,
            "generated_by": "T018_generate_dag_manifest.py",
            "config": CONFIG.to_dict()
        },
        "entries": []
    }
    
    valid_count = 0
    invalid_count = 0
    
    for idx, trace_data in enumerate(traces):
        trace_id = trace_data['id']
        trace_text = trace_data['trace']
        
        try:
            # Parse and validate the trace
            dag, is_valid, validation_details = parse_trace_to_dag_and_validate(trace_text)
            
            if not is_valid:
                invalid_count += 1
                logger.debug(f"Trace {trace_id} is INVALID: {validation_details.get('reason', 'Unknown')}")
                continue
            
            # Calculate Logical Difficulty Score (max path depth)
            depth = get_logical_difficulty(dag)
            
            entry = {
                "id": trace_id,
                "depth": depth,
                "node_count": dag.number_of_nodes(),
                "edge_count": dag.number_of_edges(),
                "is_valid": True,
                "validation_details": validation_details
            }
            
            manifest["entries"].append(entry)
            valid_count += 1
            
            if (idx + 1) % 100 == 0:
                logger.info(f"Processed {idx + 1} traces. Valid: {valid_count}, Invalid: {invalid_count}")
                
        except Exception as e:
            invalid_count += 1
            logger.error(f"Error processing trace {trace_id}: {e}", exc_info=True)
            
    manifest["metadata"]["valid_traces_count"] = valid_count
    manifest["metadata"]["invalid_traces_count"] = invalid_count
    
    logger.info(f"Manifest generation complete. Valid: {valid_count}, Invalid: {invalid_count}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the manifest
    save_json_file(manifest, output_path)
    logger.info(f"Manifest saved to {output_path}")
    
    return manifest

def main():
    """Main entry point."""
    # Define paths
    output_path = PROJECT_ROOT / "data" / "processed" / "dag_manifest.json"
    
    # Load raw traces (optionally limit for testing, but production uses full stream)
    # We do not limit here to satisfy the "full dataset" requirement unless specified.
    traces = load_raw_traces()
    
    if not traces:
        logger.error("No traces loaded. Aborting manifest generation.")
        sys.exit(1)
        
    # Generate and save manifest
    manifest = generate_dag_manifest(traces, output_path)
    
    print(f"Successfully generated {output_path}")
    print(f"Valid traces: {manifest['metadata']['valid_traces_count']}")
    print(f"Invalid traces: {manifest['metadata']['invalid_traces_count']}")

if __name__ == "__main__":
    main()
