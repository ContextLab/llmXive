import os
from pathlib import Path
from code.src.config import PROJECT_ROOT

def generate_env_template():
    """Generates a .env.example file if it doesn't exist."""
    env_example_path = PROJECT_ROOT / ".env.example"
    if env_example_path.exists():
        print(f".env.example already exists at {env_example_path}. Skipping generation.")
        return

    content = """# Environment Configuration for llmXive Project
# Copy this file to .env and fill in your specific values.
# Environment variables take precedence over config.yaml.

# Random seeds for reproducibility (comma-separated)
SEEDS=42,123,456

# Model Paths (relative to project root or absolute)
# MODEL_PATHS_REASONING=models/reasoning_model.gguf
# MODEL_PATHS_NON_REASONING=models/non_reasoning_model.gguf

# Inference Parameters
# INFERENCE_PARAMS={"temperature": 0.7, "max_tokens": 2048, "top_p": 0.9, "repeat_penalty": 1.1}

# Parser Parameters
# PARSER_PARAMS={"max_cycle_length": 5, "max_incoming_edges": 3}

# Dataset Configuration
# DATASET_NAME=aaabiao/DAG_sft
# DATASET_SPLIT=train

# Data Directories (relative to project root)
# DATA_DIRS_RAW=data/raw
# DATA_DIRS_PROCESSED=data/processed
# DATA_DIRS_RESULTS=data/results
# DATA_DIRS_ARTIFACTS=artifacts
"""

    with open(env_example_path, 'w') as f:
        f.write(content)
    
    print(f"Generated .env template at {env_example_path}")

if __name__ == "__main__":
    generate_env_template()
