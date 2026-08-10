import os
import json
import logging
import time
import argparse
from typing import Dict, Any, Optional, List, Tuple

from code.utils.data_loader import load_from_jsonl, load_schema, validate_fields
from code.utils.profiling import start_profiling, stop_profiling, get_peak_memory_mb
from code.utils.stats import run_statistical_analysis
from code.gatekeeper.classifiers import run_intent_classification
from code.gatekeeper.rules import check_access_policy, parse_deletion_log, parse_role_definitions

logger = logging.getLogger(__name__)

class GatekeeperPipeline:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.schema = load_schema()
        self.results = []
    
    def run(self, data_path: str) -> List[Dict[str, Any]]:
        """Run the gatekeeper pipeline on data."""
        start_profiling()
        data = load_from_jsonl(data_path)
        
        # Validate data
        missing = validate_fields(data, self.schema)
        if missing:
            logger.warning(f"Validation warnings: {missing}")
        
        for record in data:
            try:
                result = self.process_record(record)
                self.results.append(result)
            except Exception as e:
                logger.error(f"Error processing record {record.get('id', 'unknown')}: {e}")
        
        peak_ram = get_peak_memory_mb()
        stop_profiling()
        
        return self.results
    
    def process_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single record through the pipeline."""
        start_time = time.time()
        
        # Step 1: Intent Classification
        intent = run_intent_classification(record.get("query", ""))
        
        # Step 2: Rule Checking
        role = record.get("role", "unknown")
        boundaries = record.get("authorization_boundaries", {})
        is_authorized = check_access_policy(role, boundaries, record.get("domain", ""))
        
        # Step 3: Deletion Log Check
        deletion_log = parse_deletion_log(record.get("memory", []))
        target_deleted = any(entry.get("deleted", False) for entry in deletion_log)
        
        # Final Decision
        allowed = is_authorized and not target_deleted and intent.get("score", 0) > 0.5
        
        end_time = time.time()
        
        return {
            "id": record.get("id"),
            "domain": record.get("domain"),
            "intent": intent,
            "authorized": is_authorized,
            "deleted": target_deleted,
            "allowed": allowed,
            "latency_ms": (end_time - start_time) * 1000
        }

def run_gatekeeper(data_path: str, output_path: str):
    """Run gatekeeper pipeline and save results."""
    pipeline = GatekeeperPipeline({})
    results = pipeline.run(data_path)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Gatekeeper results saved to {output_path}")
    return results

def run_baseline(data_path: str, output_path: str):
    """Run baseline pipeline (retrieval only) and save results."""
    logger.info("Running baseline (retrieval-only)...")
    data = load_from_jsonl(data_path)
    results = []
    
    for record in data:
        # Baseline: no filtering, just pass through
        results.append({
            "id": record.get("id"),
            "domain": record.get("domain"),
            "allowed": True,
            "latency_ms": 0.0
        })
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Baseline results saved to {output_path}")
    return results

def main():
    parser = argparse.ArgumentParser(description="Gatekeeper Benchmark Pipeline")
    parser.add_argument("--data", type=str, required=True, help="Path to input JSONL")
    parser.add_argument("--mode", type=str, choices=["gatekeeper", "baseline"], required=True)
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON")
    
    args = parser.parse_args()
    
    if args.mode == "gatekeeper":
        run_gatekeeper(args.data, args.output)
    else:
        run_baseline(args.data, args.output)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
