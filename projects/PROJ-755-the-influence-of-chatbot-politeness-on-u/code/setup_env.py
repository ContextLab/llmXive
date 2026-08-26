"""
Setup script for environment configuration management.
Creates .env.example template and ensures .env file exists.
"""
import os
import sys
from pathlib import Path
from utils.env_config import create_env_template, ensure_env_file_exists, validate_env_config, EnvConfigError


def main():
    """
    Main entry point for environment setup.
    
    Actions:
    1. Create .env.example template with HF_TOKEN placeholder.
    2. Ensure .env file exists (copy from .env.example if missing).
    3. Validate that required variables are present (optional check).
    """
    print("Setting up environment configuration...")
    
    # Define the template path (relative to project root)
    # We place .env.example in code/ to keep project root clean, 
    # but the script can run from anywhere if we resolve paths correctly.
    project_root = Path(__file__).resolve().parent.parent
    env_example_path = project_root / "code" / ".env.example"
    env_file_path = project_root / "code" / ".env"
    
    # 1. Create .env.example template
    print(f"Creating environment template at {env_example_path}...")
    template_vars = {
        "HF_TOKEN": "Hugging Face API Token (required for authenticated datasets)"
    }
    create_env_template(env_example_path, template_vars)
    print(f"  -> Template created: {env_example_path}")
    
    # 2. Ensure .env file exists
    print(f"Ensuring .env file exists at {env_file_path}...")
    ensure_env_file_exists(env_file_path)
    print(f"  -> .env file ready: {env_file_path}")
    
    # 3. Optional validation (warn if HF_TOKEN is missing)
    print("Validating environment configuration...")
    try:
        # We check if HF_TOKEN is set, but don't fail if it's missing (user might set it later)
        # Instead, we just warn.
        import os
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            print("  [WARN] HF_TOKEN is not set. Data acquisition steps will fail until this is configured.")
            print("         Please copy code/.env.example to code/.env and add your token.")
        else:
            print("  -> HF_TOKEN is configured.")
    except EnvConfigError as e:
        print(f"  [ERROR] {e}")
        sys.exit(1)
        
    print("Environment setup complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
