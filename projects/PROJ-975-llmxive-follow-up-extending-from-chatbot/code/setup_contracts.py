"""
setup_contracts.py

Initializes the schema files if they don't exist (T009).
"""
import os
import yaml

SCHEMAS = {
    "task.schema.yaml": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Task Schema",
        "type": "object",
        "properties": {
            "task_id": {"type": "string"},
            "description": {"type": "string"},
            "ground_truth_path": {"type": "array", "items": {"type": "string"}},
            "complexity": {"type": "integer"}
        },
        "required": ["task_id", "description", "ground_truth_path", "complexity"]
    },
    "skill.schema.yaml": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Skill Schema",
        "type": "object",
        "properties": {
            "skill_id": {"type": "string"},
            "function_code": {"type": "string"},
            "embedding_vector": {"type": "array", "items": {"type": "number"}},
            "usage_count": {"type": "integer"}
        },
        "required": ["skill_id", "function_code", "embedding_vector", "usage_count"]
    },
    "experiment_log.schema.yaml": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Experiment Log Entry Schema",
        "type": "object",
        "properties": {
            "task_id": {"type": "string"},
            "skill_id": {"type": "string"},
            "success": {"type": "boolean"},
            "latency": {"type": "number"},
            "tokens": {"type": "integer"},
            "retrieval_precision": {"type": "number"},
            "retrieval_diversity": {"type": "number"},
            "pruning_risk_count": {"type": "integer"},
            "library_size": {"type": "integer"},
            "pruning_enabled": {"type": "boolean"}
        },
        "required": ["task_id", "skill_id", "success", "latency", "tokens", "retrieval_precision", "retrieval_diversity", "pruning_risk_count", "library_size", "pruning_enabled"]
    }
}

def main():
    contracts_dir = "contracts"
    os.makedirs(contracts_dir, exist_ok=True)
    
    for filename, schema in SCHEMAS.items():
        filepath = os.path.join(contracts_dir, filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                yaml.dump(schema, f, default_flow_style=False, sort_keys=False)
            print(f"Created schema: {filepath}")
        else:
            print(f"Schema already exists: {filepath}")

if __name__ == "__main__":
    main()