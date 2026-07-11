import yaml
from pathlib import Path
from code.src.config import PROJECT_ROOT

def generate_config_template():
    """Generates a template config.yaml file if it doesn't exist."""
    config_path = PROJECT_ROOT / "config.yaml"
    if config_path.exists():
        print(f"config.yaml already exists at {config_path}. Skipping generation.")
        return

    template = {
        "seeds": [42, 123, 456],
        "model_paths": {
            "reasoning": "models/reasoning_model.gguf",
            "non_reasoning": "models/non_reasoning_model.gguf"
        },
        "inference_params": {
            "temperature": 0.7,
            "max_tokens": 2048,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        },
        "parser_params": {
            "max_cycle_length": 5,
            "max_incoming_edges": 3
        },
        "dataset": {
            "name": "aaabiao/DAG_sft",
            "split": "train"
        },
        "data_dirs": {
            "raw": "data/raw",
            "processed": "data/processed",
            "results": "data/results",
            "artifacts": "artifacts"
        }
    }

    with open(config_path, 'w') as f:
        yaml.dump(template, f, default_flow_style=False, sort_keys=False)
    
    print(f"Generated config template at {config_path}")

if __name__ == "__main__":
    generate_config_template()
