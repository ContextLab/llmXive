"""
Script to generate the DAG Manifest (T018).
Reads the raw dataset, parses traces into DAGs, validates them (removing invalid ones per T017),
calculates logical difficulty scores, and outputs data/processed/dag_manifest.json.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from project API surface
from code.src.parser import CoTParser, parse_trace_to_dag, get_logical_difficulty, is_trace_valid
from code.src.data_loader import load_dag_sft_dataset, iterate_dataset_examples
from code.src.config import get_config
from code.src.parser_utils import save_json_file

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_raw_traces() -> List[Dict[str, Any]]:
    """
    Loads the raw traces from the configured dataset.
    Uses the real source as defined in data_loader.py (aaabiao/DAG_sft).
    """
    config = get_config()
    dataset_name = config.get("dataset", "name", default="aaabiao/DAG_sft")
    logger.info(f"Loading dataset: {dataset_name}")
    
    try:
        dataset = load_dag_sft_dataset(dataset_name)
        traces = []
        # Iterate to ensure we process the real data stream
        for item in iterate_dataset_examples(dataset):
            traces.append(item)
        logger.info(f"Successfully loaded {len(traces)} raw traces.")
        return traces
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        # Fail loudly - do not return synthetic data
        raise RuntimeError(f"Data source {dataset_name} is unreachable or failed to load. Aborting T018.") from e

def generate_dag_manifest(raw_traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Processes raw traces to generate the DAG manifest.
    - Parses each trace into a DAG.
    - Validates traces (filters out invalid ones with cycles etc.).
    - Calculates logical difficulty (max path depth).
    - Returns the manifest structure.
    """
    manifest = {
        "metadata": {
            "source": raw_traces[0].get("source", "unknown") if raw_traces else "unknown",
            "total_raw_traces": len(raw_traces),
            "valid_traces_count": 0,
            "invalid_traces_count": 0,
            "generated_by": "T018_GenerateDagManifest"
        },
        "entries": []
    }

    parser = CoTParser()
    valid_count = 0
    invalid_count = 0

    for idx, trace_data in enumerate(raw_traces):
        trace_id = trace_data.get("id", f"trace_{idx}")
        trace_text = trace_data.get("trace", "")
        
        if not trace_text:
            invalid_count += 1
            logger.warning(f"Trace {trace_id} is empty, skipping.")
            continue

        # Parse to DAG
        try:
            dag = parse_trace_to_dag(trace_text, parser)
            
            # Validate trace (T017 logic: check for cycles, invalid refs)
            if not is_trace_valid(dag):
                invalid_count += 1
                logger.debug(f"Trace {trace_id} flagged as invalid (cycle or bad ref). Excluding from manifest.")
                continue
            
            # Calculate Logical Difficulty Score (Max Path Depth)
            depth = get_logical_difficulty(dag)
            
            # Create entry
            entry = {
                "id": trace_id,
                "valid": True,
                "dag_depth": depth,
                "node_count": dag.number_of_nodes(),
                "edge_count": dag.number_of_edges(),
                "source_trace_id": trace_data.get("source_id", trace_id)
            }
            
            manifest["entries"].append(entry)
            valid_count += 1

        except Exception as e:
            invalid_count += 1
            logger.error(f"Error processing trace {trace_id}: {e}", exc_info=True)
            continue

    manifest["metadata"]["valid_traces_count"] = valid_count
    manifest["metadata"]["invalid_traces_count"] = invalid_count
    
    logger.info(f"Manifest generation complete. Valid: {valid_count}, Invalid: {invalid_count}")
    return manifest

def main():
    """
    Main entry point for T018.
    1. Loads raw data.
    2. Generates manifest.
    3. Saves to data/processed/dag_manifest.json.
    """
    config = get_config()
    output_path = Path(config.get("paths", "processed_dir", default="data/processed")) / "dag_manifest.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        raw_traces = load_raw_traces()
        if not raw_traces:
            raise ValueError("No raw traces found in the dataset.")
        
        manifest = generate_dag_manifest(raw_traces)
        
        save_json_file(manifest, output_path)
        logger.info(f"DAG Manifest saved to: {output_path}")
        
        # Verify file exists and is non-empty
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError("Output file was not created or is empty.")
            
        return 0

    except Exception as e:
        logger.critical(f"Task T018 failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())