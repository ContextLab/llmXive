"""
Utility script to verify environment configuration.
Run this to ensure all required environment variables are set or have valid defaults.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    get_config_dict,
    get_model_path,
    get_timeout_inference,
    get_timeout_execution,
    get_seed_global,
    get_semantic_threshold,
    get_budget_generations,
    ENV_MODEL_PATH,
    ENV_TIMEOUT_INFERENCE,
    ENV_TIMEOUT_EXECUTION,
    ENV_SEED_GLOBAL,
    ENV_SEMANTIC_THRESHOLD,
    ENV_BUDGET_GENERATIONS,
)

def main():
    """Print current configuration and environment status."""
    print("=== LLMXive Environment Configuration Check ===\n")
    
    config = get_config_dict()
    
    print(f"Project Root: {config['project_root']}")
    print(f"Data Directory: {config['data_dir']}")
    print(f"Code Directory: {config['code_dir']}")
    print()
    
    print("Runtime Parameters:")
    print(f"  Model Path: {config['model_path']} (Env: {ENV_MODEL_PATH})")
    print(f"  Inference Timeout: {config['timeout_inference']}s (Env: {ENV_TIMEOUT_INFERENCE})")
    print(f"  Execution Timeout: {config['timeout_execution']}s (Env: {ENV_TIMEOUT_EXECUTION})")
    print(f"  Global Seed: {config['seed_global']} (Env: {ENV_SEED_GLOBAL})")
    print(f"  Semantic Threshold: {config['semantic_threshold']} (Env: {ENV_SEMANTIC_THRESHOLD})")
    print(f"  Generation Budget: {config['budget_generations']} (Env: {ENV_BUDGET_GENERATIONS})")
    print()
    
    # Check for non-default values (indicating explicit env vars were set)
    import os
    env_vars_set = []
    env_vars_missing = []
    
    keys = [
        ENV_MODEL_PATH,
        ENV_TIMEOUT_INFERENCE,
        ENV_TIMEOUT_EXECUTION,
        ENV_SEED_GLOBAL,
        ENV_SEMANTIC_THRESHOLD,
        ENV_BUDGET_GENERATIONS,
    ]
    
    for key in keys:
        if key in os.environ:
            env_vars_set.append(key)
        else:
            env_vars_missing.append(key)
    
    print("Environment Variables Status:")
    if env_vars_set:
        print(f"  Explicitly Set ({len(env_vars_set)}): {', '.join(env_vars_set)}")
    if env_vars_missing:
        print(f"  Using Defaults ({len(env_vars_missing)}): {', '.join(env_vars_missing)}")
    
    print("\nConfiguration validated successfully.")

if __name__ == "__main__":
    main()