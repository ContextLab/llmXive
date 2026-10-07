import json
import csv
import logging
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class MergedResultRow:
    instance_id: str
    strategy: str
    model_size: str
    pass_at_1: bool
    duration_seconds: float
    failure_category: Optional[str]

def validate_input_schema(data: List[Dict]) -> bool:
    required_keys = {"instance_id", "strategy", "model_size", "pass_at_1", "duration_seconds"}
    for item in data:
        if not required_keys.issubset(item.keys()):
            return False
    return True

def validate_strategy_consistency(data: List[Dict]) -> bool:
    strategies = {item.get("strategy") for item in data}
    valid_strategies = {"baseline", "tfidf", "diff_aware", "semantic_summary"}
    return strategies.issubset(valid_strategies)

def validate_model_sizes(data: List[Dict]) -> bool:
    sizes = {item.get("model_size") for item in data}
    valid_sizes = {"1B", "7B"}
    return sizes.issubset(valid_sizes)

def define_aggregation_schema() -> Dict[str, Any]:
    return {
        "instance_id": "str",
        "strategy": "str",
        "model_size": "str",
        "pass_at_1": "bool",
        "duration_seconds": "float",
        "failure_category": "str or null"
    }

def define_merge_logic() -> Dict[str, Any]:
    return {
        "group_by": ["instance_id", "strategy", "model_size"],
        "aggregations": {
            "pass_at_1": "any",
            "duration_seconds": "sum",
            "failure_category": "first_non_null"
        }
    }

def aggregate_jsonl(input_paths: List[str], output_path: str):
    all_data = []
    for path in input_paths:
        try:
            with open(path, 'r') as f:
                for line in f:
                    if line.strip():
                        all_data.append(json.loads(line))
        except FileNotFoundError:
            logging.warning(f"File not found: {path}")

    if not validate_input_schema(all_data):
        raise ValueError("Input data does not match expected schema")

    # Simple aggregation: just flatten for now
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "instance_id", "strategy", "model_size", "pass_at_1", 
            "duration_seconds", "failure_category"
        ])
        writer.writeheader()
        for item in all_data:
            writer.writerow({
                "instance_id": item.get("instance_id"),
                "strategy": item.get("strategy"),
                "model_size": item.get("model_size"),
                "pass_at_1": item.get("pass_at_1"),
                "duration_seconds": item.get("duration_seconds"),
                "failure_category": item.get("failure_category")
            })

    logging.info(f"Merged {len(all_data)} rows to {output_path}")

def compute_row_hash(row: Dict) -> str:
    content = json.dumps(row, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()

def execute_merge(input_paths: List[str], output_path: str):
    aggregate_jsonl(input_paths, output_path)

def main():
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 4:
        logging.error("Usage: python merge_results.py --inputs <path1,path2,...> --output <output_path>")
        sys.exit(1)

    inputs_str = sys.argv[sys.argv.index("--inputs") + 1]
    output_path = sys.argv[sys.argv.index("--output") + 1]
    input_paths = [p.strip() for p in inputs_str.split(",")]

    execute_merge(input_paths, output_path)

if __name__ == "__main__":
    main()
