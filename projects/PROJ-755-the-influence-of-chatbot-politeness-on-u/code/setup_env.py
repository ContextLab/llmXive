"""
Script to initialize environment configuration for the llmXive pipeline.

This script:
1. Creates a .env.template file in the code/ directory
2. Ensures a .env file exists in the project root
3. Validates that required environment variables can be loaded
"""
import sys
from pathlib import Path
from utils.env_config import (
    create_env_template,
    ensure_env_file_exists,
    get_hf_token,
    validate_env_config,
    EnvConfigError
)


def main():
    """Main entry point for environment setup."""
    print("Initializing environment configuration...")
    
    # Step 1: Create template
    try:
        template_path = create_env_template()
        print(f"✓ Created template at: {template_path}")
    except Exception as e:
        print(f"✗ Failed to create template: {e}", file=sys.stderr)
        return 1
    
    # Step 2: Ensure .env exists
    try:
        env_path = ensure_env_file_exists()
        print(f"✓ Ensured .env file exists at: {env_path}")
    except Exception as e:
        print(f"✗ Failed to create .env: {e}", file=sys.stderr)
        return 1
    
    # Step 3: Validate (check if HF_TOKEN is set, warn if not)
    try:
        # We don't require HF_TOKEN for the setup itself, just warn
        token = get_hf_token(required=False)
        if token:
            print("✓ HF_TOKEN is configured")
        else:
            print("⚠ HF_TOKEN is not configured. "
                 "Download will fail until you set it in .env or export HF_TOKEN.")
    except EnvConfigError as e:
        print(f"✗ Environment validation failed: {e}", file=sys.stderr)
        return 1
    
    print("\nEnvironment setup complete.")
    print("Next steps:")
    print("  1. Edit .env to add your HF_TOKEN")
    print("  2. Run the pipeline scripts")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())