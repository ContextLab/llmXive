"""
Script to ensure the contracts directory and schema files exist.
This is a helper script to verify T004 completion.
"""
import os
import yaml

CONTRACTS_DIR = "contracts"
SCHEMAS = {
    "task.schema.yaml": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Task Schema",
        "type": "object",
        "required": ["task_id", "description", "ground_truth_skills", "difficulty_level"],
        "properties": {
            "task_id": {"type": "string"},
            "description": {"type": "string"},
            "ground_truth_skills": {"type": "array", "items": {"type": "string"}},
            "difficulty_level": {"type": "string", "enum": ["low", "medium", "high"]}
        }
    },
    "skill.schema.yaml": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Skill Schema",
        "type": "object",
        "required": ["skill_id", "code", "description", "embedding_vector"],
        "properties": {
            "skill_id": {"type": "string"},
            "code": {"type": "string"},
            "description": {"type": "string"},
            "embedding_vector": {"type": "array", "items": {"type": "number"}}
        }
    },
    "experiment_log.schema.yaml": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Experiment Log Schema",
        "type": "object",
        "required": [
            "task_id", "skill_id", "success", "latency", "tokens",
            "retrieval_precision", "retrieval_diversity",
            "pruning_risk_count", "library_size", "pruning_enabled"
        ],
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
        }
    }
}

def main():
    os.makedirs(CONTRACTS_DIR, exist_ok=True)
    
    for filename, schema in SCHEMAS.items():
        filepath = os.path.join(CONTRACTS_DIR, filename)
        with open(filepath, 'w') as f:
            yaml.dump(schema, f, default_flow_style=False, sort_keys=False)
        print(f"Created {filepath}")

if __name__ == "__main__":
    main()
