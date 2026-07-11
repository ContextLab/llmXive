"""
Script to generate data/processed/dag_manifest.json containing dependency depths
for all VALID traces only.

This script:
1. Loads the raw dataset (or pre-processed traces) from data/raw/ or data/processed/
2. Uses CoTParser from code/src/parser.py to parse traces into DAGs
3. Filters out invalid traces (cycles, max incoming edges > 3, etc.)
4. Calculates Logical Difficulty Score (max path depth) for valid traces
5. Generates data/processed/dag_manifest.json with valid entries only
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.src.parser import CoTParser, parse_trace_to_dag, get_logical_difficulty
from code.src.parser_utils import load_json_file, save_json_file
from code.src.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_raw_traces(config) -> List[Dict[str, Any]]:
    """
    Load raw CoT traces from data/processed/raw_traces.json or data/raw/
    Falls back to loading from the HuggingFace dataset if raw file doesn't exist.
    """
    raw_file = config.get_processed_dir() / "raw_traces.json"
    
    if raw_file.exists():
        logger.info(f"Loading raw traces from {raw_file}")
        return load_json_file(raw_file)
    
    # Try to load from HuggingFace dataset
    logger.info("Raw traces file not found, attempting to load from HuggingFace dataset...")
    try:
        from code.src.data_loader import load_dag_sft_dataset, iterate_dataset_examples
        dataset = load_dag_sft_dataset(config)
        traces = []
        for example in iterate_dataset_examples(dataset, max_examples=None):
          # Adjust key names based on actual dataset structure
          trace_text = example.get('cot_trace', example.get('text', ''))
          if trace_text:
              traces.append({
                  'id': example.get('id', example.get('idx', str(len(traces)))),
                  'trace': trace_text,
                  'label': example.get('label', example.get('answer', ''))
              })
        logger.info(f"Loaded {len(traces)} traces from HuggingFace dataset")
        return traces
    except Exception as e:
        logger.error(f"Failed to load from HuggingFace dataset: {e}")
        raise

def generate_dag_manifest(
    traces: List[Dict[str, Any]],
    output_path: Path,
    parser: CoTParser
) -> Dict[str, Any]:
    """
    Parse traces into DAGs, filter invalid ones, and generate manifest.
    
    Returns:
        Dict containing manifest data and statistics
    """
    manifest_entries = []
    stats = {
        'total_traces': len(traces),
        'valid_count': 0,
        'invalid_count': 0,
        'invalid_reasons': {}
    }
    
    logger.info(f"Processing {len(traces)} traces...")
    
    for i, trace_data in enumerate(traces):
        trace_id = trace_data.get('id', f'trace_{i}')
        trace_text = trace_data.get('trace', trace_data.get('text', ''))
        
        if not trace_text or not isinstance(trace_text, str):
            logger.warning(f"Skipping trace {trace_id}: invalid or missing trace text")
            stats['invalid_count'] += 1
            stats['invalid_reasons']['missing_trace'] = stats['invalid_reasons'].get('missing_trace', 0) + 1
            continue
        
        try:
            # Parse trace to DAG
            dag, metadata = parse_trace_to_dag(trace_text, parser)
            
            # Check for validity (cycles, edge constraints)
            is_valid, invalid_reason = parser.is_dag_valid(dag, trace_id)
            
            if not is_valid:
                logger.debug(f"Trace {trace_id} is invalid: {invalid_reason}")
                stats['invalid_count'] += 1
                stats['invalid_reasons'][invalid_reason] = stats['invalid_reasons'].get(invalid_reason, 0) + 1
                continue
            
            # Calculate logical difficulty score (max path depth)
            depth = get_logical_difficulty(dag)
            
            # Create manifest entry
            entry = {
                'id': trace_id,
                'valid': True,
                'logical_difficulty_score': depth,
                'num_nodes': dag.number_of_nodes(),
                'num_edges': dag.number_of_edges(),
                'max_incoming_edges': max(dict(dag.in_degree()).values()) if dag.number_of_nodes() > 0 else 0,
                'metadata': metadata
            }
            
            manifest_entries.append(entry)
            stats['valid_count'] += 1
            
            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1}/{len(traces)} traces...")
                
        except Exception as e:
            logger.error(f"Error processing trace {trace_id}: {e}")
            stats['invalid_count'] += 1
            stats['invalid_reasons']['parse_error'] = stats['invalid_reasons'].get('parse_error', 0) + 1
    
    logger.info(f"Processing complete. Valid: {stats['valid_count']}, Invalid: {stats['invalid_count']}")
    
    manifest = {
        'version': '1.0',
        'generated_at': str(Path(__file__).parent.parent),
        'statistics': stats,
        'entries': manifest_entries
    }
    
    # Save manifest
    save_json_file(output_path, manifest)
    logger.info(f"Manifest saved to {output_path}")
    
    return manifest

def main():
    """Main entry point for generating DAG manifest."""
    config = get_config()
    output_path = config.get_processed_dir() / "dag_manifest.json"
    
    logger.info(f"Generating DAG manifest at {output_path}")
    
    # Initialize parser
    parser = CoTParser()
    
    # Load raw traces
    try:
        traces = load_raw_traces(config)
    except Exception as e:
        logger.error(f"Failed to load traces: {e}")
        sys.exit(1)
    
    if not traces:
        logger.error("No traces found to process")
        sys.exit(1)
    
    # Generate manifest
    try:
        manifest = generate_dag_manifest(traces, output_path, parser)
        
        # Print summary
        stats = manifest['statistics']
        print(f"\nDAG Manifest Generation Summary:")
        print(f"  Total traces: {stats['total_traces']}")
        print(f"  Valid traces: {stats['valid_count']}")
        print(f"  Invalid traces: {stats['invalid_count']}")
        print(f"  Invalid reasons: {stats['invalid_reasons']}")
        
        if stats['valid_count'] == 0:
            logger.error("No valid traces found! Manifest cannot be used for downstream tasks.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to generate manifest: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
